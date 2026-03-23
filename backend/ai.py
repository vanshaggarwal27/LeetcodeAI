import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

def generate_blog(problem):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
You are a professional technical writer and competitive programmer.

Generate a highly engaging, beginner-friendly Dev.to blog post about a LeetCode problem.

Author Account: {problem.author}
Publishing Time: {current_time}
Title: {problem.title}

Problem Description:
{problem.description}

Solution Code:
{problem.code}

Strictly follow this structure:
1. Title (Use an engaging # Title instead of YAML)
2. Problem Explanation (explain it simply, as if to a beginner)
3. Intuition (the "aha!" moment)
4. Approach (step-by-step logic)
5. Code (formatted clearly inside markdown code blocks, specify language if obvious)
6. Time & Space Complexity Analysis
7. Key Takeaways
8. Submission Details (MUST include the Author Account [{problem.author}] and the Time Published [{current_time}] in a concluding footnote)

CRITICAL INSTRUCTIONS:
- DO NOT wrap the output in ```markdown or ``` tags. Return raw markdown text.
- DO NOT output YAML frontmatter (no --- blocks).
- TABLE FORMATTING (STRICT RULES):
  - If you use a Markdown table, it MUST be perfectly formatted to render correctly.
  - Each row (header, separator, or data) MUST start with `|` and end with `|`.
  - A table row MUST be on exactly ONE single line. DO NOT use line breaks inside rows.
  - The header row, separator row (e.g., `|---|---|`), and all data rows MUST have the EXACT same number of columns.
  - CELL CONTENT: If a cell contains a bitwise OR operator `|` or any pipe character, you MUST escape it as `\|` (e.g., `(a \| b)`). Failing to escape pipes inside cells will break the table structure.
  - Ensure the separator line is continuous (no line breaks) and uses at least 3 dashes per column.
  - Always provide an EMPTY LINE before and after the table to ensure correct rendering.
"""
    response = model.generate_content(prompt)
    if not response.text:
         raise Exception("Received empty response from Gemini API.")
         
    text = response.text.strip()
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()
