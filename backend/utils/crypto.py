# backend/utils/crypto.py

import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

cipher = Fernet(os.environ["ENCRYPTION_KEY"])

def encrypt(value: str) -> str:
    return cipher.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return cipher.decrypt(value.encode()).decode()
