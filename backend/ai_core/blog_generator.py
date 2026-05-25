from .prompts import build_prompt, get_current_time
from .provider_manager import ProviderManager


def generate_blog(problem) -> str:

    current_time = get_current_time(problem)

    prompt = build_prompt(
        problem,
        current_time,
    )

    manager = ProviderManager()

    return manager.generate(prompt)
