import asyncio
import os
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import motor.motor_asyncio
import pytz
import requests

from alerts.elevenlabs_service import generate_message
from alerts.twilio_service import send_whatsapp_message

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client.leetcodeai


    phone = user.get("whatsapp_number")
    if not phone:
        return

