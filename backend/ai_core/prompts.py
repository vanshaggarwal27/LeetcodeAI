from datetime import datetime


def build_prompt(problem, current_time: str) -> str:
    custom_instructions = ""

    default_prompt = f"""
You are a professional technical writer and competitive programmer.

Generate a highly engaging, beginner-friendly Dev.to blog post about a LeetCode problem.

Author Account: {problem.author}
Publishing Time: {current_time}
Title: {problem.title}

Difficulty: {getattr(problem, "difficulty", "Unknown")}
Problem Description:
{problem.description}

Solution Code:
{problem.code}

Strictly follow this structure:
1. Title(include a difficulty badge: 🟢 Easy/ 🟡 Medium/ 🔴 Hard based on the difficulty feild)
2. Problem Explanation
3. Intuition
4. Approach
5. Code
6. Time & Space Complexity Analysis
7. Key Takeaways
8. Submission Details

CRITICAL:
- Return raw markdown only
- No markdown fences
- No YAML
"""

    if hasattr(problem, "custom_prompt") and problem.custom_prompt:
        cleaned = problem.custom_prompt.strip()

        if cleaned:
            custom_instructions = f"""
Additional User Prompt Preferences:
{cleaned}
"""

    return f"""
{default_prompt}

{custom_instructions}
"""


def get_current_time(problem):
    return (
        problem.client_time
        if hasattr(problem, "client_time") and problem.client_time
        else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def build_tag_prompt(problem, blog_content: str) -> str:
    return f"""

You are an SEO and technical content expert.

Analyze the following LeetCode blog and generate 5 to 8 highly relevant tags.

Problem Title:
{problem.title}

Blog Content:
{blog_content}

Requirements:
- Tags should be lowercase
- Use hyphens where appropriate
- Focus on algorithms, data structures, interview preparation, and programming concepts
- Return only comma-separated tags
- Do not include explanations

Example Output:
leetcode, binary-tree, bfs, algorithms, interview-prep
"""
