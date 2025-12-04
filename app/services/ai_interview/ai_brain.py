from app.services.ai_interview.stt_service import STTService
from app.services.ai_interview.tts_service import TTSService
from app.services.ai_interview.llm_service import LLMService

class AIInterviewBrain:
    def __init__(self):
        self.stt = STTService()
        self.tts = TTSService()
        self.llm = LLMService()

        self.state = {
            "current_question": 0,
            "questions": [
                "Tell me about yourself.",
                "What programming languages are you strong in?",
                "Explain any project you built recently.",
                "Why should we hire you?"
            ],
            "transcript": []
        }

    def process_audio(self, audio_bytes: bytes):
        # 1. Convert voice → text
        text = self.stt.transcribe(audio_bytes)
        if not text.strip():
            return {"error": "No speech detected.", "audio": None}

        self.state["transcript"].append({"candidate": text})

        # 2. Send text to LLM to evaluate and generate next step
        result = self.llm.chat(
            f"You are an interview bot. Candidate said: {text}. "
            f"Give a short reply and then ask the next interview question."
        )

        self.state["transcript"].append({"bot": result})

        # 3. Convert reply to speech
        audio_reply = self.tts.synthesize(result)

        return {
            "text": result,
            "audio": audio_reply
        }
