import logging
import os

import requests
from dotenv import load_dotenv

from .base import AIProvider

load_dotenv()

logger = logging.getLogger(__name__)


class GrokProvider(AIProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")

        if not self.api_key:
            raise Exception("XAI_API_KEY is missing")

        self.base_url = "https://api.x.ai/v1/chat/completions"

    def clean_response(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```markdown"):
            text = text[11:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def generate(self, prompt: str) -> str:

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "grok-2-latest",  # you can change if xAI updates it
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that writes clean technical content.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.7,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Grok API error {response.status_code}: {response.text}"
                )

            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content")

            if not content:
                raise Exception("Empty response from Grok API")

            return self.clean_response(content)

        except Exception as e:
            logger.error("Grok generation failed: %s", str(e))
            raise Exception(f"Grok error: {str(e)}")
