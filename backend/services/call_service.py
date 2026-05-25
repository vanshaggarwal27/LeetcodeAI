import os

from twilio.rest import Client

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def make_call(to_number: str, audio_url: str):
    return client.calls.create(
        to=to_number,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        twiml=f'<Response><Play>{audio_url}</Play></Response>'
    )
