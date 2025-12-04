# app/ai_interview/evaluation.py

def parse_evaluation(raw_text: str) -> dict:
    """
    Converts AI's text block into structured dictionary (JSON)
    """

    return {
        "raw_report": raw_text
    }
