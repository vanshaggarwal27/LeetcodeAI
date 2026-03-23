import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    models = genai.list_models()
    print("AVAILABLE MODELS:")
    valid_models = []
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
            valid_models.append(m.name)
    if not valid_models:
        print("No models support generateContent!")
except Exception as e:
    print(f"Error listing models: {e}")
