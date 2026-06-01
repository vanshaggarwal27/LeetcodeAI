from types import SimpleNamespace

import httpx
import openai
import pytest

import ai_core.providers.openai_provider as openai_provider_module
from ai_core.providers.openai_provider import OpenAIProvider


class SequenceCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.requested_models = []

    def create(self, **kwargs):
        self.requested_models.append(kwargs["model"])
        outcome = self.outcomes.pop(0)

        if isinstance(outcome, BaseException):
            raise outcome

        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=outcome))]
        )


def make_provider(outcomes):
    provider = OpenAIProvider.__new__(OpenAIProvider)
    completions = SequenceCompletions(outcomes)
    provider.models = ("gpt-4o-mini", "gpt-4o")
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    return provider, completions


def api_error(error_type, status_code):
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return error_type("request failed", response=response, body=None)


def test_init_uses_low_cost_default_and_bounded_client(monkeypatch):
    client_options = {}

    def fake_client(**kwargs):
        client_options.update(kwargs)
        return object()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_FALLBACK_MODEL", raising=False)
    monkeypatch.setattr(openai_provider_module, "OpenAI", fake_client)

    provider = OpenAIProvider()

    assert provider.models == ("gpt-4o-mini", "gpt-4o")
    assert client_options["max_retries"] == 0
    assert client_options["timeout"] == 30.0


def test_clean_response_removes_only_outer_markdown_fence():
    wrapped = "```markdown\n# Title\n\n```python\nprint('ok')\n```\n```"

    assert OpenAIProvider.clean_response(wrapped) == "# Title\n\n```python\nprint('ok')\n```"


def test_clean_response_preserves_valid_final_code_fence():
    blog = "# Title\n\n```python\nprint('ok')\n```"

    assert OpenAIProvider.clean_response(blog) == blog


def test_model_not_found_uses_configured_fallback():
    provider, completions = make_provider(
        [
            api_error(openai.NotFoundError, 404),
            "# Blog content",
        ]
    )

    assert provider.generate("prompt") == "# Blog content"
    assert completions.requested_models == ["gpt-4o-mini", "gpt-4o"]


def test_rate_limit_returns_control_without_trying_expensive_fallback():
    provider, completions = make_provider([api_error(openai.RateLimitError, 429)])

    with pytest.raises(Exception, match="quota or rate limit"):
        provider.generate("prompt")

    assert completions.requested_models == ["gpt-4o-mini"]
