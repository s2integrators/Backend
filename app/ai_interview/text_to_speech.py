# app/ai_interview/text_to_speech.py
import base64
import requests

class TextToSpeech:
    """
    Converts AI text → spoken voice output (mp3 base64)
    """

    def __init__(self):
        self.api_key = "YOUR_OPENAI_API_KEY"

    def synthesize(self, text: str) -> str:
        """
        Returns base64 MP3 audio string
        """
        try:
            payload = {
                "model": "gpt-4o-mini-tts",
                "voice": "alloy",
                "input": text
            }

            response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )

            audio_bytes = response.content
            audio_base64 = base64.b64encode(audio_bytes).decode()

            return audio_base64

        except Exception as e:
            print("TTS Error:", e)
            return ""
