from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ReminderSettings(BaseModel):
    user_id: str
    phone_number: str
    timezone: str = "Asia/Kolkata"
    cutoff_hour: int = 23
    enabled: bool = True

class PublishRecord(BaseModel):
    title: str
    date: str
    platforms: list[str]
    status: str
    author: Optional[str] = "Anonymous Developer"
    user_email: Optional[str] = None
    # New fields for failure tracking and recovery
    error_message: Optional[str] = None
    failed_platforms: list[str] = Field(default_factory=list)
    attempted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    recovery_eligible: bool = False
