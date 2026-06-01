import os

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs


def get_elevenlabs_client():
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return None
    return ElevenLabs(api_key=api_key)

def generate_message(user_name: str):
    return "6 Lakh ki mehnat krke 35 Lakh ke sapne nhi dekhe jate, DSA Solve kar chl"

def generate_audio(text: str) -> str:
    """Generates audio and saves it to static/reminder.mp3. Returns the file path."""
    client = get_elevenlabs_client()
    if not client:
        raise ValueError("ELEVENLABS_API_KEY is not set")

    # Resolve voice ID dynamically
    target_voice_name = "Anya"
    selected_voice_id = "21m00Tcm4TlvDq8ikWAM" # Fallback Rachel
    try:
        voices = client.voices.get_all().voices
        for v in voices:
            if target_voice_name.lower() in v.name.lower():
                selected_voice_id = v.voice_id
                break
    except Exception as e:
        print("Could not fetch voices list:", e)

    response = client.text_to_speech.convert(
        voice_id=selected_voice_id,
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    os.makedirs("static", exist_ok=True)
    file_path = "static/reminder.mp3"
    with open(file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    return file_path
