from typing import Optional

from pydantic import BaseModel


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
