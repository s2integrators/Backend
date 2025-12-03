from fastapi import APIRouter, UploadFile, File
from app.services.ai_interview.ai_brain import AIInterviewBrain

router = APIRouter()
brain = AIInterviewBrain()

@router.post("/interview/process")
async def process_audio(audio: UploadFile = File(...)):
    # Read uploaded audio file
    audio_bytes = await audio.read()

    # Pass to AI brain
    result = brain.process_audio(audio_bytes)

    return {
        "text": result["text"],
        "audio_base64": result["audio"].decode("latin1")  # to send safely
    }
