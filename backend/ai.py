import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

# Model fallback chain: try fastest/cheapest first, fall back on quota errors
MODEL_FALLBACK_CHAIN = [
    "models/gemini-2.5-flash",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
]

# Retry config for 429 rate-limit errors
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 35  # Free tier asks to retry after ~35s


def _difficulty_badge(difficulty: str) -> str:
    badges = {"Easy": "🟢 Easy", "Medium": "🟡 Medium", "Hard": "🔴 Hard"}
    return badges.get(difficulty, f"⚪ {difficulty}")


def _build_prompt(problem, current_time: str) -> str:
    """
    Builds a structured prompt for Gemini AI using LeetCode problem details,
    solution code, author information, and optional custom instructions.

    Args:
        problem: Object containing the LeetCode problem title, description,
            code, author, difficulty, and custom prompt.
        current_time (str): Timestamp used in the generated blog footer.

    Returns:
        str: Formatted prompt string for Gemini AI
    """
    badge = _difficulty_badge(getattr(problem, "difficulty", None) or "Unknown")
    custom_instructions = ""
    badge = _difficulty_badge(getattr(problem, 'difficulty', 'Unknown'))

    default_prompt = f"""
You are a professional technical writer and competitive programmer.

Generate a highly engaging, beginner-friendly Dev.to blog post about a LeetCode problem.

Author Account: {problem.author}
Publishing Time: {current_time}
Title: {problem.title}
Difficulty: {badge}

Problem Description:
{problem.description}

Solution Code:
{problem.code}

Strictly follow this structure:
1. Title (Use an engaging # Title instead of YAML)
2. Difficulty Badge — render it prominently right below the title as: **Difficulty:** {badge}
3. Problem Explanation (explain it simply, as if to a beginner)
4. Intuition (the "aha!" moment)
5. Approach (step-by-step logic)
6. Code (formatted clearly inside markdown code blocks, specify language if obvious)
7. Time & Space Complexity Analysis
8. Key Takeaways
9. Submission Details (MUST include the Author Account [{problem.author}] and the Time Published [{current_time}] in a concluding footnote)

CRITICAL INSTRUCTIONS:
- DO NOT wrap the output in ```markdown or ``` tags. Return raw markdown text.
- DO NOT output YAML frontmatter (no --- blocks).
- TABLE FORMATTING (STRICT RULES):
  - If you use a Markdown table, it MUST be perfectly formatted to render correctly.
  - Each row (header, separator, or data) MUST start with `|` and end with `|`.
  - A table row MUST be on exactly ONE single line. DO NOT use line breaks inside rows.
  - The header row, separator row (e.g., `|---|---|`), and all data rows MUST have the EXACT same number of columns.
  - CELL CONTENT: If a cell contains a bitwise OR operator `|` or any pipe character, you MUST escape it as `\\|` (e.g., `(a \\| b)`). Failing to escape pipes inside cells will break the table structure.
  - Ensure the separator line is continuous (no line breaks) and uses at least 3 dashes per column.
  - Always provide an EMPTY LINE before and after the table to ensure correct rendering.
"""

    if hasattr(problem, "custom_prompt") and problem.custom_prompt:
        cleaned = problem.custom_prompt.strip()
        if cleaned:
            custom_instructions = f"""
Additional User Prompt Preferences:
{cleaned}
"""

    return f"{default_prompt}{custom_instructions}"


def _clean_response(text: str) -> str:
    """
    Strip accidental markdown fences Gemini sometimes wraps output in.

    Args:
       text: Raw response text from Gemini API

    Returns:
       str: Cleaned markdown text without code fences
    """
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def generate_blog(problem) -> str:
    """
    Generate a Dev.to blog post for a LeetCode problem using Gemini AI.

    Handles:
    - 429 Rate-limit errors → retries with exponential backoff
    - Model quota exhausted → falls back to next model in chain
    - Leaked / invalid key → raises a clean, user-friendly error
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set. Add it to backend/.env")

    client = genai.Client(api_key=api_key)

    current_time = (
        problem.client_time
        if hasattr(problem, "client_time") and problem.client_time
        else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    prompt = _build_prompt(problem, current_time)

    last_error = None

    for model_name in MODEL_FALLBACK_CHAIN:
        logger.info("Trying model: %s", model_name)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt
                )

                if not response.text:
                    raise Exception("Received empty response from Gemini API.")

                return _clean_response(response.text)

            except Exception as e:
                error_str = str(e)

                # --- Leaked / invalid key: no point retrying ---
                if "403" in error_str and (
                    "leaked" in error_str.lower() or "invalid" in error_str.lower()
                ):
                    raise Exception(
                        "Your Gemini API key is invalid or has been reported as leaked. "
                        "Please generate a new key at https://aistudio.google.com/app/apikey "
                        "and update the GEMINI_API_KEY in your backend/.env file."
                    )

                # --- Rate limited: wait and retry ---
                if (
                    "429" in error_str
                    or "quota" in error_str.lower()
                    or "rate" in error_str.lower()
                ):
                    if attempt < MAX_RETRIES:
                        wait = INITIAL_BACKOFF_SECONDS * attempt
                        logger.warning(
                            "Rate limited on %s (attempt %d/%d). Retrying in %ds...",
                            model_name,
                            attempt,
                            MAX_RETRIES,
                            wait,
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.warning(
                            "Quota exhausted on %s. Falling back to next model.",
                            model_name,
                        )
                        last_error = Exception(
                            f"Rate limit hit on {model_name} after {MAX_RETRIES} retries. "
                            "Please wait a minute and try again, or upgrade your Gemini API plan."
                        )
                        break  # break retry loop → next model

                # --- Any other unexpected error ---
                raise Exception(f"Gemini API error: {error_str}")

    # All models exhausted
    raise last_error or Exception(
        "All Gemini models are currently quota-limited. Please wait a minute and try again."
    )


# -----------------------------
# Code Efficiency Rater
# -----------------------------


def _build_efficiency_prompt(title: str, code: str, language: str) -> str:
    """
    Build the prompt string for code efficiency analysis.

    Args:
        title: LeetCode problem title
        code: Submitted solution code
        language: Programming language of the solution

    Returns:
        str: Formatted prompt string for Gemini AI
    """
    return f"""
        You are an expert competitive programmer and algorithm analyst.

        Analyze the following LeetCode solution and return a structured efficiency report.

        Problem Title: {title}
        Language: {language}
        Solution Code:
        {code}

        Return your analysis in the following format exactly:

        SCORE: <letter grade from S, A, B, C, D>
        TIME_COMPLEXITY: <e.g. O(n log n)>
        SPACE_COMPLEXITY: <e.g. O(n)>
        APPROACH_TYPE: <one of: Brute Force, Suboptimal, Optimal>
        SUMMARY: <one sentence summary of the approach>
        SUGGESTION: <one concrete suggestion to improve efficiency, or 'None' if already optimal>

        CRITICAL INSTRUCTIONS:
        - Return only the six fields above. No extra text, no markdown, no code blocks.
        - Each field must be on its own line.
        - Do not include explanations outside the defined fields.
        - Score S means optimal solution, A means near-optimal, B means acceptable,
          C means inefficient, D means highly inefficient.
    """


def _parse_efficiency_response(raw: str) -> dict:
    """
    Parse the structured efficiency report returned by Gemini.

    Args:
        raw: Raw text response from Gemini

    Returns:
        dict: Parsed fields as a dictionary

    Raises:
        Exception: If any required field is missing from the response
    """
    expected_fields = [
        "SCORE",
        "TIME_COMPLEXITY",
        "SPACE_COMPLEXITY",
        "APPROACH_TYPE",
        "SUMMARY",
        "SUGGESTION",
    ]

    parsed = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip().upper()
            if key in expected_fields:
                parsed[key] = value.strip()

    missing = [f for f in expected_fields if f not in parsed]
    if missing:
        raise Exception(
            f"Gemini returned an incomplete efficiency report. Missing fields: {missing}"
        )

    return {
        "score": parsed["SCORE"],
        "time_complexity": parsed["TIME_COMPLEXITY"],
        "space_complexity": parsed["SPACE_COMPLEXITY"],
        "approach_type": parsed["APPROACH_TYPE"],
        "summary": parsed["SUMMARY"],
        "suggestion": parsed["SUGGESTION"],
    }


def rate_code_efficiency(title: str, code: str, language: str = "python") -> dict:
    """
    Analyze a LeetCode solution and return an efficiency rating using Gemini AI.

    Handles:
    - 429 Rate-limit errors → retries with exponential backoff
    - Model quota exhausted → falls back to next model in chain
    - Malformed response → raises a descriptive error

    Args:
        title: LeetCode problem title
        code: Submitted solution code
        language: Programming language of the solution (default: python)

    Returns:
        dict: Parsed efficiency report with score, complexities, approach and suggestion
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set. Add it to backend/.env")

    client = genai.Client(api_key=api_key)
    prompt = _build_efficiency_prompt(title, code, language)

    last_error = None

    for model_name in MODEL_FALLBACK_CHAIN:
        logger.info("Efficiency rater trying model: %s", model_name)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt
                )

                if not response.text:
                    raise Exception("Received empty response from Gemini API.")

                raw = response.text.strip()
                return _parse_efficiency_response(raw)

            except Exception as e:
                error_str = str(e)

                if "403" in error_str and (
                    "leaked" in error_str.lower() or "invalid" in error_str.lower()
                ):
                    raise Exception(
                        "Your Gemini API key is invalid or has been reported as leaked. "
                        "Please generate a new key at https://aistudio.google.com/app/apikey "
                        "and update the GEMINI_API_KEY in your backend/.env file."
                    )

                if (
                    "429" in error_str
                    or "quota" in error_str.lower()
                    or "rate" in error_str.lower()
                ):
                    if attempt < MAX_RETRIES:
                        wait = INITIAL_BACKOFF_SECONDS * attempt
                        logger.warning(
                            "Rate limited on %s (attempt %d/%d). Retrying in %ds...",
                            model_name,
                            attempt,
                            MAX_RETRIES,
                            wait,
                        )
                        time.sleep(wait)
                        continue
                    else:
                        logger.warning(
                            "Quota exhausted on %s. Falling back to next model.",
                            model_name,
                        )
                        last_error = Exception(
                            f"Rate limit hit on {model_name} after {MAX_RETRIES} retries. "
                            "Please wait a minute and try again, or upgrade your Gemini API plan."
                        )
                        break

                raise Exception(
                    f"Gemini API error during efficiency rating: {error_str}"
                )

    raise last_error or Exception(
        "All Gemini models are currently quota-limited. Please wait a minute and try again."
    )
