from fastapi import APIRouter
from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .session_manager import SessionManager
from .interview_agent import InterviewAgent
from .evaluation import parse_evaluation

router = APIRouter(prefix="/ai-interview", tags=["AI Interview"])

stt = SpeechToText()
tts = TextToSpeech()
session = SessionManager()
agent = InterviewAgent()


@router.post("/start/{room_id}")
def start_interview(room_id: str):

    session.start_session(room_id)

    # First question
    question = "Welcome to the interview! Can you introduce yourself?"

    session.add_message(room_id, "assistant", question)

    audio_base64 = tts.synthesize(question)

    return {"audio": audio_base64, "text": question}


@router.post("/voice/{room_id}")
def process_voice(room_id: str, audio_base64: str):

    text = stt.transcribe(audio_base64)
    session.add_message(room_id, "user", text)

    next_question = agent.ask_next_question(session.get_history(room_id))
    session.add_message(room_id, "assistant", next_question)

    audio = tts.synthesize(next_question)

    return {"audio": audio, "text": next_question}


@router.get("/result/{room_id}")
def final_result(room_id: str):

    history = session.get_history(room_id)
    evaluation = agent.evaluate_candidate(history)
    structured = parse_evaluation(evaluation)

    session.finish(room_id, structured)

    return structured
