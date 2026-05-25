"""
Unit tests for the blog generation service in ai.py.
Tests use mock_gemini_client to avoid real Gemini API calls.
"""


class TestGenerateBlog:

    def test_generate_blog_returns_string(
        self, app_module, mock_gemini_client
    ):
        """generate_blog returns a non-empty string."""
        from ai import generate_blog
        from types import SimpleNamespace

        problem = SimpleNamespace(
            title="Two Sum",
            description="Given an array...",
            code="def twoSum(): pass",
            author="testuser",
            client_time=None,
        )
        result = generate_blog(problem)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_blog_calls_gemini_once(
        self, app_module, mock_gemini_client
    ):
        """generate_blog calls the Gemini model exactly once."""
        from ai import generate_blog
        from types import SimpleNamespace

        problem = SimpleNamespace(
            title="Two Sum",
            description="Given an array...",
            code="def twoSum(): pass",
            author="testuser",
            client_time=None,
        )
        generate_blog(problem)
        mock_gemini_client["model"].generate_content.assert_called_once()

    def test_generate_blog_includes_title_in_prompt(
        self, app_module, mock_gemini_client
    ):
        """The prompt sent to Gemini includes the problem title."""
        from ai import generate_blog
        from types import SimpleNamespace

        problem = SimpleNamespace(
            title="Unique Problem Title XYZ",
            description="Some description",
            code="def solve(): pass",
            author="testuser",
            client_time=None,
        )
        generate_blog(problem)
        call_args = mock_gemini_client["model"].generate_content.call_args
        prompt_text = call_args[1].get("contents") or call_args[0][0]
        assert "Unique Problem Title XYZ" in prompt_text
