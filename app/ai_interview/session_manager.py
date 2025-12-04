# app/ai_interview/session_manager.py

class SessionManager:
    """
    Stores conversation history + tracks interview state.
    """

    def __init__(self):
        self.sessions = {}  # key = roomId

    def start_session(self, room_id: str):
        self.sessions[room_id] = {
            "messages": [],
            "status": "waiting",  # waiting, interviewing, completed
            "score": None
        }

    def add_message(self, room_id: str, role: str, text: str):
        if room_id not in self.sessions:
            self.start_session(room_id)

        self.sessions[room_id]["messages"].append({
            "role": role,
            "text": text
        })

    def get_history(self, room_id: str):
        return self.sessions.get(room_id, {}).get("messages", [])

    def finish(self, room_id: str, score: dict):
        if room_id in self.sessions:
            self.sessions[room_id]["status"] = "completed"
            self.sessions[room_id]["score"] = score
