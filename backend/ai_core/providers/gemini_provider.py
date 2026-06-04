import logging
import os
import time

from dotenv import load_dotenv
from google import genai

from .base import AIProvider

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_FALLBACK_CHAIN = [
    "models/gemini-2.5-flash",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
]

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 35


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise Exception("GEMINI_API_KEY is missing")

        self.client = genai.Client(api_key=api_key)

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

        last_error = None

        for model_name in MODEL_FALLBACK_CHAIN:
            logger.info("Trying Gemini model: %s", model_name)

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )

                    if not response.text:
                        raise Exception("Empty response from Gemini")

                    return self.clean_response(response.text)

                except Exception as e:
                    error_str = str(e)

                    if (
                        "429" in error_str
                        or "quota" in error_str.lower()
                        or "rate" in error_str.lower()
                    ):
                        if attempt < MAX_RETRIES:
                            wait = INITIAL_BACKOFF_SECONDS * attempt

                            logger.warning(
                                "Rate limited on %s. Retrying in %ds",
                                model_name,
                                wait,
                            )

                            time.sleep(wait)

                            continue

                        last_error = Exception(f"Quota exceeded for {model_name}")

                        break

                    if "403" in error_str and (
                        "invalid" in error_str.lower() or "leaked" in error_str.lower()
                    ):
                        raise Exception("Invalid or leaked Gemini API key")

                    raise Exception(f"Gemini error: {error_str}")

        raise last_error or Exception("All Gemini models failed")
