import json

import requests

url = "https://leetcodeai-backend.onrender.com/generate-blog"
payload = {
  "title": "Two Sum",
  "difficulty": "Easy",
  "tags": ["Array", "Hash Table"],
  "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
  "code": "class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n        pass",
  "language": "python",
  "custom_prompt": ""
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error:", e)
