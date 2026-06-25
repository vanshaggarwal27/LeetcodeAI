import logging

from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

from .prompts import build_prompt, build_tag_prompt, get_current_time
from .provider_manager import ProviderManager

# 1. Set up logging
logger = logging.getLogger(__name__)


# 2. Create a helper function with the Retry logic
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_provider_with_retries(manager, prompt, credentials):
    if credentials:
        return manager.generate(prompt, credentials)
    return manager.generate(prompt)


# 3. Main function with Graceful Error Handling
def generate_blog(problem, credentials: dict | None = None) -> str:
    current_time = get_current_time(problem)

    prompt = build_prompt(
        problem,
        current_time,
    )

    manager = ProviderManager()

    try:
        # We call our retrying helper function instead of calling the manager directly
        return _call_provider_with_retries(manager, prompt, credentials)
    except Exception as e:
        # If it fails all 3 retries, catch it and return a clean 503 error
        logger.error(f"AI Provider failed after retries: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="The AI provider is currently unavailable or experiencing high traffic. Please try again later.",
        )


def generate_tags(
    problem,
    blog_content: str,
    credentials: dict | None = None,
) -> str:

    prompt = build_tag_prompt(
        problem,
        blog_content,
    )

    manager = ProviderManager()

    if credentials:
        return manager.generate(prompt, credentials)

    return manager.generate(prompt)
