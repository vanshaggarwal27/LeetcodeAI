import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# DIRECT CALL SCRIPT (Bypasses Backend for testing)
def trigger_direct_call():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE", "+12603772827")
    to_phone = "+917819834452"
    
    if not account_sid or not auth_token:
        print("❌ Twilio credentials missing in .env!")
        return

    # This is the XML message your phone will speak
    twiml_msg = f"""<Response>
    <Say voice="Polly.Aditi" language="en-IN">Namaste! This is your LeetLog A-I direct reminder. Your hard work in D-S-A will pay off! Go and solve a LeetCode problem now to secure your job. Goodbye!</Say>
</Response>"""

    print(f"📞 Initiating DIRECT CALL from {from_phone} to {to_phone}...")
    
    try:
        client = Client(account_sid, auth_token)
        call = client.calls.create(
            from_=from_phone,
            to=to_phone,
            twiml=twiml_msg  # Raw TwiML is used to bypass backend dependencies
        )
        print("✅ SUCCESS! Your phone should be ringing now.")
        print("Call SID:", call.sid)
    except Exception as e:
        print("❌ FAILED to initiate call:", e)

if __name__ == "__main__":
    trigger_direct_call()
