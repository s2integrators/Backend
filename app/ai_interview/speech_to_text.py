# app/ai_interview/speech_to_text.py
import base64
import requests

class SpeechToText:
    """
    Converts user microphone audio → text using OpenAI Whisper API
    """

    def __init__(self):
        self.api_key = "YOUR_OPENAI_API_KEY"

    def transcribe(self, audio_base64: str) -> str:
        """
        Takes audio in base64 format and returns text transcription.
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)

            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                },
                files={
                    "file": ("audio.wav", audio_bytes, "audio/wav")
                },
                data={
                    "model": "whisper-1"
                }
            )

            text = response.json().get("text", "")
            return text

        except Exception as e:
            print("STT Error:", e)
            return ""
