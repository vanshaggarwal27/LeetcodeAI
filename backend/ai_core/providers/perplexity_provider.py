import os

from dotenv import load_dotenv
from openai import OpenAI

from .base import AIProvider

load_dotenv()


class PerplexityProvider(AIProvider):

    def __init__(self, api_key: str | None = None):

        api_key = api_key or os.getenv("PERPLEXITY_API_KEY")


        if not api_key:
            raise Exception("PERPLEXITY_API_KEY missing")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai/",
        )

    def generate(self, prompt: str) -> str:

        response = self.client.chat.completions.create(
            model="sonar",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.choices[0].message.content.strip()
