import logging
import os

from .providers.gemini_provider import GeminiProvider
from .providers.grok_provider import GrokProvider
from .providers.openai_provider import OpenAIProvider
from .providers.perplexity_provider import PerplexityProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    def __init__(self):

        self.providers = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "perplexity": PerplexityProvider,
            "grok": GrokProvider,
        }

    def get_provider_order(self, selected_provider: str | None = None) -> list[str]:
        """
        Returns ordered provider fallback chain.
        Selected provider is always tried first.
        """

        selected_provider = (
            selected_provider or os.getenv("AI_PROVIDER", "gemini")
        ).lower()

        fallback_order = [
            "gemini",
            "openai",
            "perplexity",
            "grok",
        ]

        provider_order = [
            selected_provider,
            *[provider for provider in fallback_order if provider != selected_provider],
        ]

        return provider_order

    def get_provider(self, provider_name: str, credentials: dict | None = None):

        provider_class = self.providers.get(provider_name)

        if not provider_class:
            raise Exception(f"Unsupported AI provider: {provider_name}")

        credential_names = {
            "gemini": "gemini_api_key",
            "openai": "openai_api_key",
            "perplexity": "perplexity_api_key",
            "grok": "grok_api_key",
        }
        api_key = (credentials or {}).get(credential_names.get(provider_name, ""))
        return provider_class(api_key=api_key)

    def generate(self, prompt: str, credentials: dict | None = None) -> str:

        provider_order = self.get_provider_order((credentials or {}).get("ai_provider"))

        last_error = None

        for provider_name in provider_order:
            try:
                logger.info(
                    "Trying provider: %s",
                    provider_name,
                )

                provider = self.get_provider(provider_name, credentials)

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

        raise Exception(f"All AI providers failed. Last error: {last_error}")
