import logging
import os

from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)


# Setup a clean logger for exception visibility
logger = logging.getLogger(__name__)


def make_call(to_number: str, audio_url: str = None, text_to_say: str = None):
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER", "")
    # Remove 'whatsapp:' prefix if it exists when making a voice call
    from_number = twilio_number.replace("whatsapp:", "") if twilio_number else ""

    if not from_number:
        raise ValueError(
            "TWILIO_PHONE_NUMBER is not set in environment variables! You need an active Twilio Voice number to make phone calls."
        )

    if audio_url:
        twiml = f"<Response><Play>{audio_url}</Play></Response>"
    else:
        # Add 'angry' tone using SSML prosody (faster, louder, lower pitch)
        # And completely map the string to Devanagari for perfect Hindi pronunciation
        if not text_to_say:
            text_to_say = ""

        if "6 Lakh" in text_to_say:
            spoken_text = '<prosody rate="85%">छह लाख की मेहनत करके, <break time="400ms"/> पैंतीस लाख के सपने <emphasis level="strong">नहीं</emphasis> देखे जाते! <break time="500ms"/> <prosody volume="x-loud" pitch="low">DSA सॉल्व कर चल!</prosody></prosody>'
        else:
            spoken_text = (
                text_to_say.replace("Lakh", "Laakh")
                .replace("krke", "karke")
                .replace("chl", "chal")
            )

        twiml = f"<Response><Say voice='Google.hi-IN-Wavenet-A' language='hi-IN'>{spoken_text}</Say></Response>"

    try:
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=twiml,
        )
        return call.sid
    except Exception as e:
        logger.error(f"Failed to initiate Twilio voice call to {to_number}: {str(e)}")
        return None


def send_whatsapp_message(to_number: str, body: str):
    # Use explicit WhatsApp number if set, otherwise default to Twilio Sandbox number
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    formatted_to = (
        to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    )

    try:
        message = client.messages.create(
            from_=whatsapp_from, body=body, to=formatted_to
        )
        return message.sid
    except Exception as e:
        logger.error(f"Failed to send Twilio WhatsApp message to {to_number}: {str(e)}")
        return None
