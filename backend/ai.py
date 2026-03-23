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
1. Title (Use an engaging title)
2. Problem Explanation (explain it simply, as if to a beginner)
3. Intuition (the "aha!" moment)
4. Approach (step-by-step logic)
5. Code (formatted clearly inside markdown code blocks, specify language if obvious)
6. Time & Space Complexity Analysis
7. Key Takeaways
8. Submission Details (MUST include the Author Account [{problem.author}] and the Time Published [{current_time}] in a concluding footnote)

Make the content Markdown-formatted. Do not include extra conversational text outside the blog content itself. The output should be ready to be published.
"""
    response = model.generate_content(prompt)
    if not response.text:
         raise Exception("Received empty response from Gemini API.")
    return response.text
