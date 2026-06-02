import base64
import hashlib
import hmac
import json
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Optional

import motor.motor_asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from twilio.rest import Client

# --- UPDATED AI PATH ---
from ai_core.blog_generator import generate_blog
from devto import publish_to_platforms
from models.reminder import PublishRecord
from services.reminder_scheduler import start_scheduler
from social import share_to_platforms

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start background schedulers when server starts.
    """
    try:
        start_scheduler()
        print("Reminder scheduler started successfully.")
    except Exception as e:
        print(f"Reminder scheduler failed to start: {e}")
    yield


app = FastAPI(title="LeetLog AI", version="1.0.0", lifespan=lifespan)

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
# MongoDB Setup
# -----------------------------
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))

db = mongo_client.leetcodeai


# -----------------------------
# Models
# -----------------------------
class Problem(BaseModel):
    title: str
    description: str
    code: str
    author: str = "Anonymous Developer"
    difficulty: str | None = None
    client_time: str | None = None  # Optional client time string
    custom_prompt: str | None = None  # custom_prompt for the user
    platforms: list[str] | None = None
    publish_as_draft: bool = False
    share_to_social: bool = True
    tags: list[str] | None = None


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
    devto_api_key: str | None = None
    whatsapp_number: str | None = None
    timezone: str = "Asia/Kolkata"
    reminder_time: str = "09:00"
    is_whatsapp_enabled: bool = False
    ai_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    perplexity_api_key: str | None = None
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
    settings_doc = await db.integration_settings.find_one({"user_id": user_id}, {"_id": 0})
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
        "whatsapp": bool(settings_doc.get("whatsapp_number")),
        "ai_provider": bool(
            settings_doc.get("gemini_api_key")
            or settings_doc.get("openai_api_key")
            or settings_doc.get("perplexity_api_key")
        ),
    }


def _token_for(user: dict[str, Any]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
    return _sign_token({"sub": user["id"], "email": user["email"], "exp": exp.timestamp()})


@app.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(credentials: AuthCredentials):
    email = credentials.email.strip().lower()
    if len(credentials.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    salt, password_hash = _hash_password(credentials.password)
    user = {
        "id": secrets.token_urlsafe(16),
        "name": (credentials.name or email.split("@")[0]).strip(),
        "email": email,
        "timezone": credentials.timezone,
        "password_salt": salt,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
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
    return IntegrationSettingsResponse(**settings_doc, connected=_connected(settings_doc))


@app.put("/settings/integrations", response_model=IntegrationSettingsResponse)
async def update_integration_settings(
    settings: IntegrationSettings,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
):
    allowed_providers = {"gemini", "openai", "perplexity"}
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

    return IntegrationSettingsResponse(**settings_doc, connected=_connected(settings_doc))




# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def health_check():
    return {"status": "ok", "message": "LeetLog AI backend is running."}


# -----------------------------
# Blog Generator Endpoint
# -----------------------------
@app.post("/generate-blog")
async def create_blog(
    problem: Problem,
    x_user_email: Optional[str] = Header(default=None),
    current_user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
):
    """
    Accepts a LeetCode problem and:
    1. Generates a blog using the unified ai.providers module
    2. Publishes it to one or more configured platforms
    """
    user_email = require_user(x_user_email)
    # Check if the user has already published a successful blog for this problem
    existing_record = await db.problem_info.find_one(
        {"title": problem.title, "author": problem.author, "status": "success"}
    )

    if existing_record:
        return {
            "status": "error",
            "message": f"Solution for '{problem.title}' has already been published! Keep up the great streak!",
        }

    if problem.custom_prompt and len(problem.custom_prompt.strip()) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Custom prompt exceeds maximum length of 1000 characters.",
        )

    if not problem.code or problem.code.strip() == "":
        return {"status": "error", "message": "Code is empty, cannot generate blog."}

    user_settings = await _settings_for_user(current_user["id"]) if current_user else {}

    try:
        blog_content = generate_blog(problem, credentials=user_settings)
    except Exception as e:
        return {"status": "error", "message": f"AI provider failure: {str(e)}"}

    try:
        platform_results = await publish_to_platforms(
            problem.title,
            blog_content,
            platforms=problem.platforms or user_settings.get("publish_platforms"),
            published=not problem.publish_as_draft,
            tags=problem.tags,
            credentials=user_settings,
        )
        successful = [r for r in platform_results if r.get("status") == "success"]
        overall_status = (
            "success"
            if len(successful) == len(platform_results)
            else "partial_success"
            if successful
            else "error"
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
            {
                "title": problem.title,
                "author": problem.author,
                "user_email": user_email,
            },
            {
                "$set": record.model_dump(),
            },
            upsert=True,
        )

    except Exception as e:
        print(f"Database logging failed: {e}")

    social_results = []
    if problem.share_to_social and successful:
        # Find the first URL to share from successful platforms
        post_url = None
        for res in successful:
            if res.get("url"):
                post_url = res["url"]
                break

        if post_url:
            try:
                social_results = share_to_platforms(
                    title=problem.title,
                    post_url=post_url,
                    tags=problem.tags,
                    credentials=user_settings,
                )
            except Exception as e:
                print(f"Social sharing failed: {e}")

    return {
        "status": overall_status,
        "data": {
            "blog_content": blog_content,
            "platforms": platform_results,
            "social": social_results,
        },
    }


# -----------------------------
# Dashboard Endpoints
# -----------------------------
@app.get("/dashboard/stats")
async def get_dashboard_stats(x_user_email: Optional[str] = Header(default=None)):
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
        platform_counts = {doc["_id"]: doc["count"] async for doc in platform_cursor}

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
    """
    Health check endpoint for reminder services.
    """
    return {"status": "active", "message": "Reminder call infrastructure is running."}


@app.get("/test-whatsapp")
def test_whatsapp():
    try:
        import os

        from alerts.twilio_service import send_whatsapp_message

        phone = os.getenv("TEST_PHONE_NUMBER")
        if not phone:
            return {
                "status": "error",
                "message": "TEST_PHONE_NUMBER is not set in environment.",
            }
        sid = send_whatsapp_message(
            phone,
            "Hello Vansh! Your Twilio WhatsApp integration on Render is working perfectly! 🚀",
        )
        return {
            "status": "success",
            "sid": sid,
            "message": "WhatsApp message sent successfully.",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/test-call")
def test_call():
    try:
        import os

        from alerts.elevenlabs_service import generate_audio, generate_message
        from alerts.twilio_service import make_call

        message = generate_message("Vansh")

        try:
            audio_file = generate_audio(message)
            backend_url = os.getenv(
                "BACKEND_URL", "https://leetcodeai-backend.onrender.com"
            )
            if backend_url.endswith("/"):
                backend_url = backend_url[:-1]
            audio_url = f"{backend_url}/{audio_file}"

            phone = os.getenv("TEST_PHONE_NUMBER")
            if not phone:
                return {
                    "status": "error",
                    "message": "TEST_PHONE_NUMBER is not set in environment.",
                }

            sid = make_call(phone, audio_url=audio_url)
            return {
                "status": "success",
                "sid": sid,
                "audio_url": audio_url,
                "message": "Call initiated successfully with ElevenLabs.",
            }
        except Exception as el_err:
            print("ElevenLabs Error in Test Route:", el_err)
            # Fallback to Twilio TTS
            phone = os.getenv("TEST_PHONE_NUMBER")
            if not phone:
                return {
                    "status": "error",
                    "message": "TEST_PHONE_NUMBER is not set in environment.",
                }

            sid = make_call(phone, text_to_say=message)
            return {
                "status": "success",
                "sid": sid,
                "message": "ElevenLabs failed (Free Tier VPN block), but Twilio TTS call initiated successfully.",
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
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
