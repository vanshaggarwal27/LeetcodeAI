import asyncio
import logging
import os

import openai
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from .base import AIProvider

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_FALLBACK_MODEL = "gpt-4o"
GENERATION_TEMPERATURE = 0.7
MAX_TOKENS = 4000
REQUEST_TIMEOUT_SECONDS = 30.0
SDK_MAX_RETRIES = 0


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise Exception("OPENAI_API_KEY is missing")

        preferred_model = (
            os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        )
        fallback_model = os.getenv(
            "OPENAI_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL
        ).strip()
        self.models = tuple(
            dict.fromkeys(model for model in (preferred_model, fallback_model) if model)
        )
        # Authentic production client configuration
        self.client = OpenAI(
            api_key=api_key,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        # Safely bind the concurrency lock to the provider instance context
        self._lock = asyncio.Lock()

    @staticmethod
    def clean_response(text: str) -> str:
        """Remove an accidental outer Markdown wrapper without harming code fences."""
        text = text.strip()
        for opening_fence in ("```markdown", "```"):
            for line_break in ("\r\n", "\n"):
                prefix = f"{opening_fence}{line_break}"
                suffix = f"{line_break}```"

                if text.startswith(prefix) and text.endswith(suffix):
                    return text[len(prefix) : -len(suffix)].strip()

        return text

    def generate(self, prompt: str) -> str:
        last_error = None

        for model_name in self.models:
            logger.info("Trying OpenAI model: %s", model_name)

            try:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=GENERATION_TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
            except openai.NotFoundError as exc:
                logger.warning(
                    "OpenAI model %s is unavailable. Trying configured fallback.",
                    model_name,
                )
                last_error = exc
                continue
            except openai.AuthenticationError as exc:
                raise Exception(
                    "Invalid OpenAI API key. Check your OPENAI_API_KEY."
                ) from exc
            except openai.PermissionDeniedError as exc:
                raise Exception(
                    "The OpenAI API key does not have access to the requested model."
                ) from exc
            except openai.RateLimitError as exc:
                raise Exception("OpenAI quota or rate limit exceeded.") from exc
            except (openai.APITimeoutError, openai.APIConnectionError) as exc:
                raise Exception(
                    "OpenAI request timed out or could not connect."
                ) from exc
            except openai.APIStatusError as exc:
                logger.error(
                    "OpenAI request failed for %s with status %s (request_id=%s).",
                    model_name,
                    exc.status_code,
                    getattr(exc, "request_id", None),
                )
                raise Exception(
                    f"OpenAI request failed with HTTP {exc.status_code}."
                ) from exc
            except openai.APIError as exc:
                logger.error("OpenAI request failed for %s: %s", model_name, exc)
                raise Exception("OpenAI request failed.") from exc

            try:
                content = response.choices[0].message.content
            except (AttributeError, IndexError) as exc:
                raise Exception("OpenAI returned an invalid response.") from exc

            if content and content.strip():
                logger.info("OpenAI model %s succeeded", model_name)
                return self.clean_response(content)

            logger.warning(
                "OpenAI model %s returned empty content. Trying configured fallback.",
                model_name,
            )
            last_error = Exception(f"Empty response from {model_name}")

        raise last_error or Exception("All configured OpenAI models failed")

    async def generate_blog(self, payload: dict):
        if self._lock.locked():
            raise HTTPException(
                status_code=429,
                detail="A blog generation request is already in progress. Please wait."
            )

        async with self._lock:
            user_prompt = payload.get(
                "prompt",
                "Write a technical blog post about solving LeetCode problems efficiently.",
            )
            model_name = payload.get("model", "gpt-4o")

            try:
                # Run the synchronous OpenAI SDK call inside a thread pool
                # to keep the FastAPI async event loop completely non-blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are LeetLog AI, an expert technical writer and "
                                    "software engineer. Generate a structured, markdown-formatted "
                                    "blog post based on the problem description provided."
                                ),
                            },
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.7,
                    )
                )

                return {
                    "status": "success",
                    "message": "Blog created successfully",
                    "data": response.choices[0].message.content,
                }

            except openai.OpenAIError as e:
                raise HTTPException(status_code=502, detail=f"OpenAI service error: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Unexpected internal error: {str(e)}")
