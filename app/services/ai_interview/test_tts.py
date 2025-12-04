from app.services.ai_interview.tts_service import TTSService

tts = TTSService()

audio = tts.synthesize("Hello, this is a test of the AI interviewer.")

with open("tts_output.wav", "wb") as f:
    f.write(audio)

print("Generated: tts_output.wav")
