import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEVTO_API_KEY")

def post_to_platform(title, content):
    if not API_KEY:
        raise Exception("Dev.to API key missing. Please set DEVTO_API_KEY in .env.")
        
    url = "https://dev.to/api/articles"

    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Dev.to accepts native markdown, which is exactly what Gemini outputs!
    data = {
        "article": {
            "title": f"LeetCode Solution: {title}",
            "body_markdown": content,
            "published": True, # Set to False if you want it as a draft first
            "tags": ["leetcode", "dsa", "programming", "tutorial"]
        }
    }

    retries = 2
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                 if attempt < retries:
                     time.sleep(1)
                 else:
                     raise Exception(f"Dev.to API Error {response.status_code}: {response.text}")
        except Exception as e:
            if attempt == retries:
                raise Exception(f"Network Error: {str(e)}")
            time.sleep(1)
