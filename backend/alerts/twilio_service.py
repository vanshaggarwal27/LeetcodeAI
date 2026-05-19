import os

from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

def make_call(to_number: str, audio_url: str):
    call = client.calls.create(
        to=to_number,
        from_=twilio_number,
        twiml=f'<Response><Play>{audio_url}</Play></Response>'
    )

    return call.sid
