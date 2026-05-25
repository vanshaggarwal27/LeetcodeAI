import logging
import os

from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.perplexity_provider import PerplexityProvider

logger = logging.getLogger(__name__)


class ProviderManager:

    def __init__(self):

        self.providers = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "perplexity": PerplexityProvider,
        }

    def get_provider_order(self) -> list[str]:
        """
        Returns ordered provider fallback chain.
        Selected provider is always tried first.
        """

        selected_provider = os.getenv(
            "AI_PROVIDER",
            "gemini",
        ).lower()

        fallback_order = [
            "gemini",
            "openai",
            "perplexity",
        ]

        provider_order = [
            selected_provider,
            *[
                provider
                for provider in fallback_order
                if provider != selected_provider
            ],
        ]

        return provider_order

    def get_provider(self, provider_name: str):

        provider_class = self.providers.get(provider_name)

        if not provider_class:
            raise Exception(
                f"Unsupported AI provider: {provider_name}"
            )

        return provider_class()

    def generate(self, prompt: str) -> str:

        provider_order = self.get_provider_order()

        last_error = None

        for provider_name in provider_order:

            try:

                logger.info(
                    "Trying provider: %s",
                    provider_name,
                )

                provider = self.get_provider(
                    provider_name
                )

                response = provider.generate(prompt)

                logger.info(
                    "Provider %s succeeded",
                    provider_name,
                )

                return response

            except Exception as e:

                logger.error(
                    "Provider %s failed: %s",
                    provider_name,
                    str(e),
                )

                last_error = e

                continue

        raise Exception(
            f"All AI providers failed. "
            f"Last error: {last_error}"
        )
