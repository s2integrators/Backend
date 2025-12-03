# file: app/ai_interview/interview_agent.py

import ollama
from typing import List, Dict

class AIInterviewAgent:
    """
    Core AI engine that runs the interview conversation using Llama 3.1.
    """

    def __init__(self):
        self.model = "llama3.1:8b"

        # System persona for the AI interviewer
        self.system_prompt = """
You are an AI HR interviewer for S2 Integrators.

Your goal:
- Conduct a professional job interview
- Ask one question at a time
- Wait for the candidate response
- Analyse response and pick next question
- Maintain a friendly tone but professional
- No long paragraphs, keep questions crisp

Interview Structure:
1. Greeting
2. Basic introduction questions
3. Technical questions (IT)
4. Behavioural questions
5. Final summary and wrap-up

After the interview ends, generate:
- Candidate strengths
- Weaknesses
- Overall communication rating (1–10)
- Technical skill rating (1–10)
- Confidence rating (1–10)
- Final hire/no-hire suggestion
"""

        # store conversation history
        self.chat_history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
        ]

    def ask(self, candidate_answer: str) -> str:
        """
        Send candidate answer to model and get next AI question.
        """

        # Add candidate answer to history
        if candidate_answer:
            self.chat_history.append({"role": "user", "content": candidate_answer})

        # Query Llama model
        result = ollama.chat(
            model=self.model,
            messages=self.chat_history
        )

        ai_reply = result["message"]["content"]

        # Add AI reply to history
        self.chat_history.append({"role": "assistant", "content": ai_reply})

        return ai_reply

    def final_evaluation(self) -> str:
        """
        After interview is done, generate evaluation summary.
        """

        evaluation_prompt = """
Create a structured evaluation of the candidate based on the interview.
Return JSON ONLY with this structure:

{
 "strengths": "...",
 "weaknesses": "...",
 "communication_rating": 1-10,
 "technical_rating": 1-10,
 "confidence_rating": 1-10,
 "summary": "...",
 "hire_recommendation": "Yes" or "No"
}
"""

        self.chat_history.append({"role": "user", "content": evaluation_prompt})

        result = ollama.chat(
            model=self.model,
            messages=self.chat_history
        )

        return result["message"]["content"]
