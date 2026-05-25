import os

import motor.motor_asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client

from ai import generate_blog
from devto import publish_to_platforms
from services.reminder_scheduler import start_scheduler

load_dotenv()

app = FastAPI(
    title="LeetLog AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Twilio Setup
# -----------------------------
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# -----------------------------
# MongoDB Setup
# -----------------------------
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
    os.getenv("MONGODB_URI")
)

db = mongo_client.leetcodeai


# -----------------------------
# Models
# -----------------------------
class Problem(BaseModel):
    title: str
    description: str
    code: str
    author: str = "Anonymous Developer"
    client_time: str | None = None
    difficulty: str | None = "Unknown"
    custom_prompt: str | None = None
    platforms: list[str] | None = None
    publish_as_draft: bool = False
    tags: list[str] | None = None


class ReminderPreference(BaseModel):
    whatsapp_number: str
    reminder_time: str = "09:00"
    timezone: str = "Asia/Kolkata"
    is_opted_in: bool = True


# -----------------------------
# Startup Event
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """
    Start background schedulers when server starts.
    """

    try:
        start_scheduler()
        print("Reminder scheduler started successfully.")
    except Exception as e:
        print(f"Reminder scheduler failed to start: {e}")


# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "LeetLog AI backend is running."
    }


# -----------------------------
# Blog Generator Endpoint
# -----------------------------
@app.post("/generate-blog")
async def create_blog(problem: Problem):
    """
    Accepts a LeetCode problem and:
    1. Generates a blog using Gemini AI
    2. Publishes it to one or more configured platforms
    """
    if problem.custom_prompt and len(problem.custom_prompt.strip()) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Custom prompt exceeds maximum length of 1000 characters."
        )

    if not problem.code or problem.code.strip() == "":
        return {
            "status": "error",
            "message": "Code is empty, cannot generate blog."
        }

    try:
        blog_content = await run_in_threadpool(generate_blog, problem)

    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini API failure: {str(e)}"
        }

    try:
        platform_results = publish_to_platforms(
            problem.title,
            blog_content,
            platforms=problem.platforms,
            published=not problem.publish_as_draft,
            tags=problem.tags,
        )
        successful_results = [
            result for result in platform_results if result.get("status") == "success"
        ]
        overall_status = "error"
        if len(successful_results) == len(platform_results):
            overall_status = "success"
        elif successful_results:
            overall_status = "partial_success"

        return {
            "status": overall_status,
            "data": {
                "blog_content": blog_content,
                "platforms": platform_results,
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Publishing failure: {str(e)}"
        }


# -----------------------------
# Reminder Infrastructure
# -----------------------------
@app.get("/reminder-health")
def reminder_health():
    """
    Health check endpoint for reminder services.
    """

    return {
        "status": "active",
        "message": "Reminder call infrastructure is running."
    }


@app.post("/reminder/subscribe")
async def subscribe(pref: ReminderPreference):
    await db.preferences.update_one(
        {"whatsapp_number": pref.whatsapp_number},
        {"$set": pref.dict()},
        upsert=True
    )

    return {
        "status": "success",
        "message": "Subscribed!"
    }


@app.post("/reminder/unsubscribe")
async def unsubscribe(data: dict):
    await db.preferences.update_one(
        {"whatsapp_number": data["whatsapp_number"]},
        {"$set": {"is_opted_in": False}}
    )

    return {
        "status": "success",
        "message": "Unsubscribed!"
    }


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000,
        reload=True
    )
