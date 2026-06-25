import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

import httpx
import motor.motor_asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from twilio.rest import Client

from ai import rate_code_efficiency

# --- UPDATED AI PATH ---
from ai_core.blog_generator import generate_blog, generate_tags
from devto import publish_to_platforms
from github_integration import push_solution_to_github
from models.reminder import PublishRecord
from models.user import PlatformCredential
from services.complexity_analyzer import analyze_code
from services.credential_service import resolve_user_credentials
from services.reminder_scheduler import start_scheduler
from social import share_to_platforms
from utils.crypto import encrypt

load_dotenv()

logger = logging.getLogger("leetcodeai")

# -----------------------------
# MongoDB Setup
# -----------------------------
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client.leetcodeai


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start background schedulers and initialize MongoDB indexes when server starts.
    """
    try:
        # Create indexes to prevent COLLSCAN on dashboard queries
        await db.problem_info.create_index(
            [("user_email", 1), ("date", -1)],
            background=True
        )
        await db.users.create_index(
            [("email", 1)],
            unique=True,
            background=True
        )
        print("MongoDB indexes ensured successfully.")
    except Exception as e:
        logger.error(f"Failed to create MongoDB indexes: {e}")

    try:
        start_scheduler()
        print("Reminder scheduler started successfully.")
    except Exception as e:
        print(f"Reminder scheduler failed to start: {e}")
    yield


# Initialize FastAPI with the incoming lifespan configuration intact
app = FastAPI(title="LeetLog AI", version="1.0.0", lifespan=lifespan)

# Initialize the rate limiter using our custom safe IP function
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Attach your custom global database exception handler
@app.exception_handler(PyMongoError)
async def mongodb_exception_handler(request: Request, exc: PyMongoError):
    logger.error(f"Database error encountered: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content={
            "status": "error",
            "message": "Database connection failed. Please ensure MongoDB is running.",
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# -----------------------------
# Twilio Setup
# -----------------------------
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))



# -----------------------------
# Models
# -----------------------------
class Problem(BaseModel):
    title: str
    description: str
    code: str
    author: str = "Anonymous Developer"
    difficulty: str | None = None
    language: str | None = None
    client_time: str | None = None
    custom_prompt: str | None = None
    platforms: list[str] | None = None
    publish_as_draft: bool = False
    share_to_social: bool = True
    tags: list[str] | None = None

class CodeAnalysisRequest(BaseModel):
    code: str

class ReminderPreference(BaseModel):
    whatsapp_number: str
    reminder_time: str = "09:00"
    timezone: str = "Asia/Kolkata"
    is_opted_in: bool = True


def require_user(x_user_email: Optional[str]) -> str:
    """Extract and validate user email from header."""
    if not x_user_email or "@" not in x_user_email:
        raise HTTPException(
            status_code=401, detail="Missing or invalid X-User-Email header."
        )
    return x_user_email.lower().strip()


class AuthCredentials(BaseModel):
    name: str | None = None
    email: str
    password: str
    timezone: str = "Asia/Kolkata"


class LoginCredentials(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    timezone: str = "Asia/Kolkata"


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


class IntegrationSettings(BaseModel):
    linkedin_access_token: str | None = None
    linkedin_person_urn: str | None = None
    twitter_api_key: str | None = None
    twitter_api_secret: str | None = None
    twitter_access_token: str | None = None
    twitter_access_secret: str | None = None
    github_access_token: str | None = None
    github_repo_name: str | None = None
    devto_api_key: str | None = None
    whatsapp_number: str | None = None
    timezone: str = "Asia/Kolkata"
    reminder_time: str = "09:00"
    is_whatsapp_enabled: bool = False
    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    perplexity_api_key: str | None = None
    grok_api_key: str | None = None
    publish_platforms: list[str] = ["devto"]


class IntegrationSettingsResponse(IntegrationSettings):
    connected: dict[str, bool]


TOKEN_TTL_HOURS = 24 * 7


def _secret_key() -> str:
    return os.getenv("APP_SECRET_KEY") or "dev-only-change-me"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign_token(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_payload}".encode()
    signature = hmac.new(_secret_key().encode(), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64url(signature)}"


def _decode_token(token: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}".encode()
        expected = _b64url(
            hmac.new(_secret_key().encode(), signing_input, hashlib.sha256).digest()
        )
        if not hmac.compare_digest(encoded_signature, expected):
            raise ValueError("Invalid signature")
        padding = "=" * (-len(encoded_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token expired.",
        )
    return payload


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return salt, digest.hex()


def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, candidate_hash = _hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, expected_hash)


def _public_user(user: dict[str, Any]) -> UserPublic:
    return UserPublic(
        id=user["id"],
        name=user.get("name") or user["email"].split("@")[0],
        email=user["email"],
        timezone=user.get("timezone", "Asia/Kolkata"),
    )


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_token(token)
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user


async def get_optional_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any] | None:
    if not authorization:
        return None
    return await get_current_user(authorization)


async def _settings_for_user(user_id: str) -> dict[str, Any]:
    settings_doc = await db.integration_settings.find_one(
        {"user_id": user_id}, {"_id": 0}
    )
    if not settings_doc:
        return IntegrationSettings().model_dump()
    settings_doc.pop("user_id", None)
    return IntegrationSettings(**settings_doc).model_dump()


def _connected(settings_doc: dict[str, Any]) -> dict[str, bool]:
    return {
        "devto": bool(settings_doc.get("devto_api_key")),
        "linkedin": bool(
            settings_doc.get("linkedin_access_token")
            and settings_doc.get("linkedin_person_urn")
        ),
        "twitter": bool(
            settings_doc.get("twitter_api_key")
            and settings_doc.get("twitter_api_secret")
            and settings_doc.get("twitter_access_token")
            and settings_doc.get("twitter_access_secret")
        ),
        "github": bool(
            settings_doc.get("github_access_token")
            and settings_doc.get("github_repo_name")
        ),
        "whatsapp": bool(settings_doc.get("whatsapp_number")),
        "ai_provider": bool(
            settings_doc.get("gemini_api_key")
            or settings_doc.get("openai_api_key")
            or settings_doc.get("perplexity_api_key")
            or settings_doc.get("grok_api_key")
        ),
    }


def _token_for(user: dict[str, Any]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
    return _sign_token(
        {"sub": user["id"], "email": user["email"], "exp": exp.timestamp()}
    )


@app.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(credentials: AuthCredentials):
    email = credentials.email.strip().lower()
    if len(credentials.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters."
        )
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists."
        )

    salt, password_hash = _hash_password(credentials.password)
    user = {
    "id": secrets.token_urlsafe(16),
    "name": (credentials.name or email.split("@")[0]).strip(),
    "email": email,
    "timezone": credentials.timezone,
    "password_salt": salt,
    "password_hash": password_hash,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "credentials": {},
    }
    await db.users.insert_one(user)
    await db.integration_settings.update_one(
        {"user_id": user["id"]},
        {"$set": {"user_id": user["id"], **IntegrationSettings().model_dump()}},
        upsert=True,
    )
    return AuthResponse(token=_token_for(user), user=_public_user(user))


@app.post("/auth/login", response_model=AuthResponse)
async def login(credentials: LoginCredentials):
    email = credentials.email.strip().lower()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not _verify_password(
        credentials.password,
        user["password_salt"],
        user["password_hash"],
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return AuthResponse(token=_token_for(user), user=_public_user(user))


@app.get("/auth/me", response_model=UserPublic)
async def me(current_user: Annotated[dict[str, Any], Depends(get_current_user)]):
    return _public_user(current_user)


@app.get("/settings/integrations", response_model=IntegrationSettingsResponse)
async def get_integration_settings(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
):
    settings_doc = await _settings_for_user(current_user["id"])
    return IntegrationSettingsResponse(
        **settings_doc, connected=_connected(settings_doc)
    )


@app.put("/settings/integrations", response_model=IntegrationSettingsResponse)
async def update_integration_settings(
    settings: IntegrationSettings,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
):
    allowed_providers = {"gemini", "openai", "perplexity", "grok"}
    if settings.ai_provider not in allowed_providers:
        raise HTTPException(status_code=400, detail="Unsupported AI provider.")

    settings_doc = settings.model_dump()
    await db.integration_settings.update_one(
        {"user_id": current_user["id"]},
        {"$set": {"user_id": current_user["id"], **settings_doc}},
        upsert=True,
    )
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"timezone": settings.timezone}},
    )

    if settings.whatsapp_number:
        await db.preferences.update_one(
            {"user_id": current_user["id"]},
            {
                "$set": {
                    "user_id": current_user["id"],
                    "whatsapp_number": settings.whatsapp_number,
                    "reminder_time": settings.reminder_time,
                    "timezone": settings.timezone,
                    "is_opted_in": settings.is_whatsapp_enabled,
                }
            },
            upsert=True,
        )

    return IntegrationSettingsResponse(
        **settings_doc, connected=_connected(settings_doc)
    )


# -----------------------------
# Health Check
@app.post("/analyze-code")
async def analyze_complexity(payload: CodeAnalysisRequest):
    return analyze_code(payload.code)
# -----------------------------
@app.get("/")
def health_check():
    return {"status": "ok", "message": "LeetLog AI backend is running."}


# -----------------------------
# Blog Generator Endpoint
# -----------------------------
@app.post("/generate-blog")
@limiter.limit("15/hour")
async def create_blog(
    request: Request,
    problem: Problem,
    current_user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
    x_user_email: Optional[str] = Header(default=None),
):
    """
    Accepts a LeetCode problem, pulls user-specific database integration credentials,
    generates a blog post using AI, and publishes it dynamically.
    """
    user_email = require_user(x_user_email)
    user_id = current_user["id"] if current_user else "anonymous"

    existing_record = await db.problem_info.find_one(
        {"title": problem.title, "author": problem.author, "status": "success"}
    )

    if existing_record:
        return {
            "status": "error",
            "message": f"Solution for '{problem.title}' has already been published!",
        }

    if problem.custom_prompt and len(problem.custom_prompt.strip()) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Custom prompt exceeds maximum length of 1000 characters.",
        )

    if not problem.code or problem.code.strip() == "":
        return {"status": "error", "message": "Code is empty, cannot generate blog."}

    user_settings = await _settings_for_user(user_id)

    try:
        blog_content = await run_in_threadpool(generate_blog, problem, credentials=user_settings)
        efficiency = rate_code_efficiency(
            problem.title,
            problem.code,
            problem.language or "python"
        )
    except Exception as e:
        return {"status": "error", "message": f"AI provider failure: {str(e)}"}

    # Resolve platform-specific credentials from database securely at runtime
    devto_creds = await resolve_user_credentials(db, user_id, "devto")

    try:
        _ = await run_in_threadpool(
            generate_tags,
            problem,
            blog_content,
            credentials=user_settings,
        )
    except Exception:
        pass

    try:
        platform_results = await publish_to_platforms(
            problem.title,
            blog_content,
            platforms=problem.platforms or user_settings.get("publish_platforms"),
            published=not problem.publish_as_draft,
            tags=problem.tags,
            credentials=devto_creds,  # Using user specific keys
        )
        successful = [r for r in platform_results if r.get("status") == "success"]
        overall_status = (
            "success"
            if len(successful) == len(platform_results)
            else "partial_success" if successful else "error"
        )
    except Exception as e:
        return {"status": "error", "message": f"Publishing failure: {str(e)}"}

    try:
        record = PublishRecord(
            title=problem.title,
            date=datetime.now(timezone.utc).isoformat(),
            platforms=[r["platform"] for r in successful],
            status=overall_status,
            author=problem.author,
            user_email=user_email,
        )

        await db.problem_info.update_one(
            {"title": problem.title, "author": problem.author, "user_email": user_email},
            {"$set": record.model_dump()},
            upsert=True,
        )

    except Exception as e:
        print(f"Database logging failed: {e}")

    social_results = []
    if problem.share_to_social and successful:
        post_url = next((res["url"] for res in successful if res.get("url")), None)

        if post_url:
            try:
                # Dynamically fetch encrypted LinkedIn credentials
                linkedin_creds = await resolve_user_credentials(db, user_id, "linkedin")
                social_results = share_to_platforms(
                    title=problem.title,
                    post_url=post_url,
                    tags=problem.tags,
                    credentials=linkedin_creds,  # Decrypted user scope profile object
                )
            except Exception as e:
                print(f"Social sharing failed: {e}")

    # GitHub automatic commit integration
    if successful and user_settings.get("github_access_token") and user_settings.get("github_repo_name"):
        try:
            await run_in_threadpool(
                push_solution_to_github,
                problem.title,
                problem.code,
                user_settings["github_access_token"],
                user_settings["github_repo_name"]
            )
        except Exception as e:
            print(f"GitHub push failed: {e}")

    return {
        "status": overall_status,
        "data": {
            "blog_content": blog_content,"efficiency": efficiency,
            "platforms": platform_results,
            "social": social_results,
        },
    }


# -----------------------------
# Publish Blog Endpoint
# -----------------------------
class EditedBlog(BaseModel):
    title: str
    content: str
    author: str = "Anonymous Developer"
    platforms: list[str] | None = None
    publish_as_draft: bool = False
    share_to_social: bool = True
    tags: list[str] | None = None


@app.post("/publish-blog")
async def publish_blog(
    blog: EditedBlog,
    current_user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
    x_user_email: Optional[str] = Header(default=None),
):
    """
    Accepts an edited blog post and distributes it using safe user-isolated tokens.
    """
    user_email = require_user(x_user_email)
    user_id = current_user["id"] if current_user else "anonymous"

    user_settings = await _settings_for_user(user_id)
    devto_creds = await resolve_user_credentials(db, user_id, "devto")

    try:
        platform_results = await publish_to_platforms(
            blog.title,
            blog.content,
            platforms=blog.platforms or user_settings.get("publish_platforms"),
            published=not blog.publish_as_draft,
            tags=blog.tags,
            credentials=devto_creds,
        )
        successful = [r for r in platform_results if r.get("status") == "success"]
        overall_status = (
            "success"
            if len(successful) == len(platform_results)
            else "partial_success" if successful else "error"
        )
    except Exception as e:
        return {"status": "error", "message": f"Publishing failure: {str(e)}"}

    try:
        record = PublishRecord(
            title=blog.title,
            date=datetime.now(timezone.utc).isoformat(),
            platforms=[r["platform"] for r in successful],
            status=overall_status,
            author=blog.author,
            user_email=user_email,
        )

        await db.problem_info.update_one(
            {"title": blog.title, "author": blog.author, "user_email": user_email},
            {"$set": record.model_dump()},
            upsert=True,
        )
    except Exception as e:
        print(f"Database logging failed: {e}")

    social_results = []
    if blog.share_to_social and successful:
        post_url = next((res["url"] for res in successful if res.get("url")), None)

        if post_url:
            try:
                linkedin_creds = await resolve_user_credentials(db, user_id, "linkedin")
                social_results = share_to_platforms(
                    title=blog.title,
                    post_url=post_url,
                    tags=blog.tags,
                    credentials=linkedin_creds,
                )
            except Exception as e:
                print(f"Social sharing failed: {e}")

    return {
        "status": overall_status,
        "data": {
            "blog_content": blog.content,
            "platforms": platform_results,
            "social": social_results,
        },
    }


# -----------------------------
# Dashboard Endpoints
# -----------------------------
@app.get("/dashboard/stats")
async def get_dashboard_stats(
    x_user_email: Optional[str] = Header(default=None),
    current_user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
):
    if current_user:
        user_email = current_user["email"]
    else:
        user_email = require_user(x_user_email)

    user_filter = {"user_email": user_email}

    try:
        total = await db.problem_info.count_documents(user_filter)

        pipeline_platforms = [
            {"$match": user_filter},
            {"$unwind": "$platforms"},
            {"$group": {"_id": "$platforms", "count": {"$sum": 1}}},
        ]
        platform_cursor = db.problem_info.aggregate(pipeline_platforms)
        platform_counts = [{"name": doc["_id"], "value": doc["count"]} async for doc in platform_cursor]

        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        pipeline_week = [
            {"$match": {**user_filter, "date": {"$gte": seven_days_ago}}},
            {
                "$group": {
                    "_id": {"$substr": ["$date", 0, 10]},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        week_cursor = db.problem_info.aggregate(pipeline_week)
        week_activity = {doc["_id"]: doc["count"] async for doc in week_cursor}

        # All time daily activity for the heatmap
        pipeline_all_time = [
            {"$match": user_filter},
            {
                "$group": {
                    "_id": {"$substr": ["$date", 0, 10]},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        all_time_cursor = db.problem_info.aggregate(pipeline_all_time)
        daily_activity = [{"date": doc["_id"], "count": doc["count"], "level": min(doc["count"], 4)} async for doc in all_time_cursor]

        # Calculate streak
        current_streak = 0
        if daily_activity:
            dates_set = {doc["date"] for doc in daily_activity}
            today = datetime.now(timezone.utc).date()

            current_date = today
            if current_date.isoformat() not in dates_set:
                current_date = today - timedelta(days=1)

            while current_date.isoformat() in dates_set:
                current_streak += 1
                current_date -= timedelta(days=1)

        recent_cursor = (
            db.problem_info.find(
                user_filter,
                {
                    "_id": 0,
                    "title": 1,
                    "date": 1,
                    "platforms": 1,
                    "status": 1,
                    "author": 1,
                },
            )
            .sort("date", -1)
            .limit(10)
        )
        recent = [doc async for doc in recent_cursor]

        return {
            "total_posts": total,
            "platform_counts": platform_counts,
            "week_activity": week_activity,
            "daily_activity": daily_activity,
            "current_streak": current_streak,
            "recent": recent,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.get("/dashboard/history")
async def get_dashboard_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    x_user_email: Optional[str] = Header(default=None),
):
    user_email = require_user(x_user_email)
    user_filter = {"user_email": user_email}
    skip = (page - 1) * page_size
    cursor = (
        db.problem_info.find(user_filter, {"_id": 0})
        .sort("date", -1)
        .skip(skip)
        .limit(page_size)
    )
    records = [doc async for doc in cursor]
    total = await db.problem_info.count_documents(user_filter)
    return {"page": page, "page_size": page_size, "total": total, "records": records}


@app.post("/dashboard/record")
async def record_publish(
    record: PublishRecord, x_user_email: Optional[str] = Header(default=None)
):
    user_email = require_user(x_user_email)
    data = record.model_dump()
    data["user_email"] = user_email
    await db.problem_info.update_one(
        {"title": record.title, "user_email": user_email},
        {"$set": data},
        upsert=True,
    )
    return {"status": "ok"}


# -----------------------------
# Reminder Infrastructure
# -----------------------------
@app.get("/reminder-health")
def reminder_health():
    return {"status": "active", "message": "Reminder call infrastructure is running."}


@app.get("/test-whatsapp")
def test_whatsapp():
    try:
        from alerts.twilio_service import send_whatsapp_message

        phone = os.getenv("TEST_PHONE_NUMBER")
        if not phone:
            return {"status": "error", "message": "TEST_PHONE_NUMBER is not set."}
        sid = send_whatsapp_message(
            phone,
            "Hello Vansh! Your Twilio WhatsApp integration on Render is working perfectly! 🚀",
        )
        return {"status": "success", "sid": sid, "message": "WhatsApp message sent successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/test-call")
def test_call():
    try:
        from alerts.elevenlabs_service import generate_audio, generate_message
        from alerts.twilio_service import make_call

        message = generate_message("Vansh")

        try:
            audio_file = generate_audio(message)
            backend_url = os.getenv("BACKEND_URL", "https://leetcodeai-backend.onrender.com")
            if backend_url.endswith("/"):
                backend_url = backend_url[:-1]
            audio_url = f"{backend_url}/{audio_file}"

            phone = os.getenv("TEST_PHONE_NUMBER")
            if not phone:
                return {"status": "error", "message": "TEST_PHONE_NUMBER is not set."}

            sid = make_call(phone, audio_url=audio_url)
            return {
                "status": "success",
                "sid": sid,
                "audio_url": audio_url,
                "message": "Call initiated successfully with ElevenLabs.",
            }
        except Exception as el_err:
            print("ElevenLabs Error:", el_err)
            phone = os.getenv("TEST_PHONE_NUMBER")
            if not phone:
                return {"status": "error", "message": "TEST_PHONE_NUMBER is not set."}

            sid = make_call(phone, text_to_say=message)
            return {
                "status": "success",
                "sid": sid,
                "message": "ElevenLabs failed, fallback to Twilio TTS succeeded.",
                "elevenlabs_error": str(el_err),
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/reminder/subscribe")
async def subscribe(pref: ReminderPreference):
    await db.preferences.update_one(
        {"whatsapp_number": pref.whatsapp_number},
        {"$set": pref.model_dump()},
        upsert=True,
    )
    return {"status": "success", "message": "Subscribed!"}


@app.post("/reminder/unsubscribe")
async def unsubscribe(data: dict):
    await db.preferences.update_one(
        {"whatsapp_number": data["whatsapp_number"]}, {"$set": {"is_opted_in": False}}
    )
    return {"status": "success", "message": "Unsubscribed!"}


# -----------------------------
# LinkedIn OAuth 2.0
# -----------------------------
@app.get("/auth/linkedin/login")
async def linkedin_login():
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization"
        "?response_type=code"
        f"&client_id={os.getenv('LINKEDIN_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('LINKEDIN_REDIRECT_URI')}"
        "&scope=openid profile email"
    )
    return RedirectResponse(auth_url)


@app.get("/auth/linkedin/callback")
async def linkedin_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    state: Optional[str] = None,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)] = None,
):
    """
    OAuth2 Callback processor handling authorization responses from LinkedIn API servers.
    Validates authorizations, queries tokens, fetches user URN identifiers, and saves encrypted data.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authorization failed from LinkedIn: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization challenge token parameter code missing.",
        )

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
                "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI"),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed retrieving access tokens from LinkedIn: {token_response.text}",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")

        calculated_expiry = None
        if expires_in:
            calculated_expiry = int(datetime.now(timezone.utc).timestamp()) + int(expires_in)

        # Query OpenID Connect endpoint for user details
        userinfo_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed gathering profile details from Identity service endpoints.",
            )

        userinfo_data = userinfo_response.json()
        sub_id = userinfo_data.get("sub")
        person_urn = f"urn:li:person:{sub_id}"

        # Encrypt access token before storing
        encrypted_token = encrypt(access_token)

        credential_record = PlatformCredential(
            access_token=encrypted_token,
            refresh_token=encrypt(token_data["refresh_token"]) if "refresh_token" in token_data else None,
            expires_at=calculated_expiry,
            person_urn=person_urn,
        )

        # Update specific platform schema map inside user document
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"credentials.linkedin": credential_record.model_dump()}},
        )

        # Sync legacy flat document structure for settings backward compatibility
        await db.integration_settings.update_one(
            {"user_id": current_user["id"]},
            {
                "$set": {
                    "linkedin_access_token": encrypted_token,
                    "linkedin_person_urn": person_urn,
                }
            },
            upsert=True,
        )

    frontend_dashboard_url = os.getenv("FRONTEND_REDIRECT_URL", "http://localhost:3000/settings")
    return RedirectResponse(url=frontend_dashboard_url)


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
