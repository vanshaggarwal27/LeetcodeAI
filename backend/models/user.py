# backend/models/user.py

from typing import Dict, Optional

from pydantic import BaseModel, Field


class PlatformCredential(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None  # UNIX timestamp
    person_urn: Optional[str] = None  # Crucial for LinkedIn UGC workflows

class User(BaseModel):
    id: str = Field(alias="id")  # Matches your application's string identification structure
    name: str
    email: str
    timezone: str = "Asia/Kolkata"
    password_salt: str
    password_hash: str
    created_at: str
    # Map from lowercased platform identifiers (e.g. "linkedin", "devto") to platform records
    credentials: Dict[str, PlatformCredential] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
