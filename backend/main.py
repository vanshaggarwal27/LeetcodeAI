from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from ai import generate_blog
from devto import post_to_platform
import uvicorn
import os, random, requests
from twilio.rest import Client
from datetime import date
from dotenv import load_dotenv

load_dotenv()

# Simple in-memory storage for today's completions
# In production, use Redis or a Database!
COMPLETED_TODAY = set()
LAST_CLEARED_DATE = date.today()

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
    client_time: str = None  # Optional client time string

class ReminderData(BaseModel):
    phone: str = None  # Make optional to allow hardcoded fallback
    type: str = "whatsapp" # "whatsapp" or "call"

QUOTES = [
    "The journey to FAANG starts with a single 'Accepted' submission. Keep grindin' DSA!",
    "Recursion is thinking in circles until you break the cycle. Just like your career path, stay persistent!",
    "Your future job is at the end of this Array. Don't stop until you reach the target!",
    "Time complexity is O(life). Master DSA now, enjoy the rewards later!",
    "Coding isn't about being a genius, it's about being 1% better than yesterday. Do your DSA!",
    "Each problem you solve is a brick in the foundation of your future high-paying job. Build it today!",
    "The best way to predict your career's future is to code it. Start your LeetCode session now!",
    "Hard work beats talent when talent doesn't work hard. Grind the DSA, secure the bag!"
]

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

@app.post("/send-reminder")
def send_reminder(data: ReminderData):
    global LAST_CLEARED_DATE
    
    # Auto-clear memory if a new day has started
    if date.today() > LAST_CLEARED_DATE:
        COMPLETED_TODAY.clear()
        LAST_CLEARED_DATE = date.today()

    receiver_phone = data.phone if data.phone and data.phone.strip() != "" else "+917819834452"
    
    # Check if already completed today
    if receiver_phone in COMPLETED_TODAY:
        return {"status": "skipped", "message": f"User {receiver_phone} already completed LeetCode today."}

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE", "+12603772827") 
    from_whatsapp = os.getenv("TWILIO_FROM_WHATSAPP", "whatsapp:+14155238886")
    
    if not account_sid or not auth_token:
         return {"status": "error", "message": "Twilio credentials missing on server."}

    try:
        quote = random.choice(QUOTES)
        client = Client(account_sid, auth_token)

        if data.type == "call":
            call = client.calls.create(
                from_=from_phone,
                to=receiver_phone,
                url=f"https://leetcodeai-backend.onrender.com/twiml/reminder?quote={requests.utils.quote(quote)}"
            )
            return {"status": "success", "message": f"Reminder CALL initiated to {receiver_phone} (SID: {call.sid})"}
        else:
            # Default to WhatsApp message
            message_body = f"🚀 LeetLog Reminder: You haven't done any DSA today!\n\n💡 Quote of the Day:\n\"{quote}\"\n\n👉 Go to leetcode.com/problemset and get one done for your future job!"
            message = client.messages.create(
                from_=from_whatsapp,
                body=message_body,
                to=f"whatsapp:{receiver_phone}"
            )
            return {"status": "success", "message": f"WhatsApp Message sent to {receiver_phone} (SID: {message.sid})"}
            
    except Exception as e:
        return {"status": "error", "message": f"Twilio {data.type.capitalize()} Error: {str(e)}"}

@app.post("/mark-done")
def mark_done(data: ReminderData):
    receiver_phone = data.phone if data.phone and data.phone.strip() != "" else "+917819834452"
    COMPLETED_TODAY.add(receiver_phone)
    return {"status": "success", "message": f"Recorded completion for {receiver_phone}"}

@app.get("/twiml/reminder")
def get_reminder_twiml(quote: str = "Keep grindin' DSA!"):
    from fastapi.responses import Response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="en-IN">Namaste! This is your LeetLog A-I reminder. You haven't done any D-S-A problems today!</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Motivational quote of the day: {quote}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Aditi" language="en-IN">Go and solve a LeetCode problem now to secure your future job. Goodbye!</Say>
</Response>"""
    return Response(content=twiml, media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000, reload=True)
