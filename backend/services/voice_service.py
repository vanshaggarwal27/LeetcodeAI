import os

from elevenlabs.client import ElevenLabs

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

def generate_voice_message(text: str):
    audio = client.text_to_speech.convert(
        voice_id="EXAVITQu4vr4xnSDxMaL",
        text=text
    )

    return audio
