from ai import generate_blog
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class DummyProblem:
    pass

problem = DummyProblem()
problem.title = "Two Sum"
problem.description = "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
problem.code = "def twoSum(nums, target): return [0, 1]"

print("Testing Gemini Generation...")
try:
    content = generate_blog(problem)
    print("SUCCESS! Generated Content:")
    print("=========================")
    print(content[:500] + "...\n[TRUNCATED]")
except Exception as e:
    print(f"FAILED: {e}")
