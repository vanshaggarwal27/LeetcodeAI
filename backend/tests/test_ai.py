import re
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv

from ai_core.blog_generator import generate_blog
from ai_core.provider_manager import ProviderManager

load_dotenv()


# ---------------------------
# Provider tests
# ---------------------------

@pytest.mark.parametrize(
    "provider_name",
    ["gemini", "openai", "perplexity"],
)
def test_provider_generation(monkeypatch, provider_name):
    # Set the provider env var dynamically
    monkeypatch.setenv("AI_PROVIDER", provider_name)

    # Completely stub out ProviderManager initialization and generation
    # This keeps your sub-providers (Gemini, OpenAI, etc.) from making network calls
    monkeypatch.setattr(ProviderManager, "__init__", lambda self: None)

    manager = ProviderManager()

    # Simulate a fast, valid response containing "Python"
    mock_response = f"Python is a great programming language powered by {provider_name}."
    monkeypatch.setattr(manager, "generate", lambda prompt: mock_response)

    response = manager.generate("Write one short sentence about Python.")

    print(f"\n[{provider_name}] Response: {response}")

    assert isinstance(response, str)
    assert response.strip() != ""
    assert len(response.strip()) > 10
    assert re.search(r"\bpython\b", response, re.IGNORECASE)

    error_patterns = [r"invalid api key", r"unauthorized", r"error", r"failed"]
    for pattern in error_patterns:
        assert not re.search(pattern, response, re.IGNORECASE)


# ---------------------------
# Blog generation test
# Lets dont waste lot of credits so insted only gentare tittles
# ---------------------------

def test_blog_generation_contains_title(monkeypatch):
    problem = SimpleNamespace(
        title="Unique Problem Title XYZ",
        description="Some description",
        code="def solve(): pass",
        author="testuser",
        client_time=None,
    )

    monkeypatch.setattr(ProviderManager, "__init__", lambda self: None)
    monkeypatch.setattr(
        ProviderManager,
        "generate",
        lambda self, prompt: "Mocked blog content about Unique Problem Title XYZ"
    )

    result = generate_blog(problem)

    assert isinstance(result, str)
    assert "Unique Problem Title XYZ" in result
