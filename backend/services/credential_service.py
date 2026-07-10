# backend/services/credential_service.py

import os
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from utils.crypto import decrypt


async def resolve_user_credentials(
    db: AsyncIOMotorDatabase,
    user_id: str,
    platform: str
) -> Dict[str, Any]:
    """
    Fetches, un-shields, and normalizes target credentials from target database records.
    Falls back to global environment settings if database structures lack explicit values.
    """
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {}

    credentials_map = user.get("credentials", {})
    platform_data = credentials_map.get(platform.lower())

    if platform_data:
        # Decrypt stored credentials securely
        decrypted_token = decrypt(platform_data["access_token"])
        return {
            "access_token": decrypted_token,
            "person_urn": platform_data.get("person_urn"),
            "refresh_token": decrypt(platform_data["refresh_token"]) if platform_data.get("refresh_token") else None
        }

    # Backward compatibility fallback layer referencing internal environmental attributes
    if platform.lower() == "devto":
        return {"access_token": os.getenv("DEVTO_API_KEY")}
    if platform.lower() == "linkedin":
        return {
            "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
            "person_urn": os.getenv("LINKEDIN_PERSON_URN")
        }

    return {}
