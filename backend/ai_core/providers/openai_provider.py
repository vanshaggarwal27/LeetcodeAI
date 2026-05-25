import os

from dotenv import load_dotenv
from openai import OpenAI

from .base import AIProvider

load_dotenv()


class OpenAIProvider(AIProvider):

    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")


        if not api_key:
            raise Exception("OPENAI_API_KEY missing")

        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content.strip()
