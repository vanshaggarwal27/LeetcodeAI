from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from ai import generate_blog
from devto import post_to_platform
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Problem(BaseModel):
    title: str
    description: str
    code: str
    author: str = "Anonymous Developer"

@app.post("/generate-blog")
def create_blog(problem: Problem):
    if not problem.code or problem.code.strip() == "":
        return {"status": "error", "message": "Code is empty, cannot generate blog."}
        
    try:
        blog_content = generate_blog(problem)
    except Exception as e:
        return {"status": "error", "message": f"Gemini API failure: {str(e)}"}
        
    try:
        response = post_to_platform(problem.title, blog_content)
        return {"status": "success", "data": response}
    except Exception as e:
        return {"status": "error", "message": f"Dev.to API failure: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
