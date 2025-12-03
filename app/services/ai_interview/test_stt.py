from app.services.ai_interview.stt_service import STTService

# load sample audio
with open("/Users/zoro/Downloads/final.wav", "rb") as f:
    audio_data = f.read()

stt = STTService()
text = stt.transcribe(audio_data)

print("\n--- TRANSCRIBED TEXT ---\n")
print(text)
print("\n------------------------\n")
