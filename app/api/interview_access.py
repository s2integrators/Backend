# FILE: app/api/interview_access.py
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from app.core.database import get_connection
import logging

router = APIRouter(prefix="/interview-access", tags=["InterviewAccess"])
logger = logging.getLogger("uvicorn.error")

# -------------------------
# DB table creation (raw SQL)
# -------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS interview_room_state (
  room_name VARCHAR(255) NOT NULL PRIMARY KEY,
  hr_accepted TINYINT(1) NOT NULL DEFAULT 0,
  ai_accepted TINYINT(1) NOT NULL DEFAULT 0,
  meeting_active TINYINT(1) NOT NULL DEFAULT 0,
  meeting_url TEXT,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def ensure_table_exists():
    conn = get_connection()
    if conn is None:
        logger.warning("Database connection unavailable; cannot ensure interview_room_state table.")
        return
    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.exception("Failed to create or verify interview_room_state table: %s", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass

# Run on import to create the table if possible
ensure_table_exists()

# -------------------------
# Pydantic schemas
# -------------------------
class InterviewRoomStateRead(BaseModel):
    room_name: str
    hr_accepted: bool
    ai_accepted: bool
    meeting_active: bool
    meeting_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AcceptRequest(BaseModel):
    by: str = Field(..., description="Either 'hr' or 'ai'")
    accept: bool = Field(True)

# -------------------------
# Helper DB functions
# -------------------------
def _get_conn_or_500():
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    return conn

def _row_to_state(row) -> InterviewRoomStateRead:
    # expected order: room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at
    room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at = row
    return InterviewRoomStateRead(
        room_name=room_name,
        hr_accepted=bool(hr_accepted),
        ai_accepted=bool(ai_accepted),
        meeting_active=bool(meeting_active),
        meeting_url=meeting_url,
        created_at=created_at,
        updated_at=updated_at,
    )

# -------------------------
# Endpoints
# -------------------------
@router.get("/status/{room_name}", response_model=InterviewRoomStateRead)
def get_room_status(room_name: str):
    """
    Return the waiting/accept state for a room. Creates default row if missing.
    """
    conn = _get_conn_or_500()
    try:
        cur = conn.cursor()
        # Try select
        cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE room_name = %s", (room_name,))
        row = cur.fetchone()
        if row:
            state = _row_to_state(row)
            cur.close()
            conn.close()
            return state

        # Insert default row
        now = datetime.utcnow().replace(microsecond=0)
        cur.execute(
            "INSERT INTO interview_room_state (room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at) VALUES (%s, 0, 0, 0, NULL, %s, %s)",
            (room_name, now, now),
        )
        conn.commit()

        # Read back
        cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE room_name = %s", (room_name,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            raise HTTPException(500, "Failed to create interview room record.")
        return _row_to_state(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in get_room_status for %s: %s", room_name, e)
        # return a friendly 500
        raise HTTPException(status_code=500, detail="Internal server error while fetching room status")


@router.post("/accept/{room_name}", response_model=InterviewRoomStateRead)
def accept_room(room_name: str, payload: AcceptRequest = Body(...)):
    """
    HR or AI accepts the room. When both accepted, meeting is activated and a meeting_url is generated.
    """
    if payload.by not in ("hr", "ai"):
        raise HTTPException(400, "Invalid 'by' value. Use 'hr' or 'ai'.")

    conn = _get_conn_or_500()
    try:
        cur = conn.cursor()
        # Ensure a row exists
        cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE room_name = %s FOR UPDATE", (room_name,))
        row = cur.fetchone()
        now = datetime.utcnow().replace(microsecond=0)
        if not row:
            # create initial row
            hr_val = 1 if payload.by == "hr" and payload.accept else 0
            ai_val = 1 if payload.by == "ai" and payload.accept else 0
            meeting_active = 0
            meeting_url = None
            cur.execute(
                "INSERT INTO interview_room_state (room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (room_name, hr_val, ai_val, meeting_active, meeting_url, now, now),
            )
            conn.commit()
            # read back
            cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE room_name = %s", (room_name,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                raise HTTPException(500, "Failed to create interview room record.")
            return _row_to_state(row)

        # update row
        _, hr_val, ai_val, meeting_active_val, meeting_url_val, created_at, updated_at = row
        hr_val = int(bool(hr_val))
        ai_val = int(bool(ai_val))
        meeting_active_val = int(bool(meeting_active_val))

        if payload.by == "hr":
            hr_val = 1 if payload.accept else 0
        else:
            ai_val = 1 if payload.accept else 0

        # If both accepted and not active yet -> activate and create meeting url
        if hr_val and ai_val and not meeting_active_val:
            meeting_active_val = 1
            meeting_url_val = f"https://meet.jit.si/{room_name}?config.prejoinPageEnabled=false"
        else:
            # keep existing meeting_url_val (could be None)
            meeting_url_val = meeting_url_val

        # perform update
        cur.execute(
            "UPDATE interview_room_state SET hr_accepted=%s, ai_accepted=%s, meeting_active=%s, meeting_url=%s, updated_at=%s WHERE room_name=%s",
            (hr_val, ai_val, meeting_active_val, meeting_url_val, now, room_name),
        )
        conn.commit()

        # fetch updated
        cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE room_name = %s", (room_name,))
        updated_row = cur.fetchone()
        cur.close()
        conn.close()
        if not updated_row:
            raise HTTPException(500, "Failed to read updated interview room record.")
        return _row_to_state(updated_row)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in accept_room for %s: %s", room_name, e)
        raise HTTPException(status_code=500, detail="Internal server error while updating room status")


@router.get("/waiting", response_model=List[InterviewRoomStateRead])
def list_waiting_rooms():
    """
    List rooms that are not yet active (waiting for acceptance).
    """
    conn = get_connection()
    if conn is None:
        # safe fallback: return empty list (frontend will show "No pending interviews")
        logger.warning("DB connection unavailable in list_waiting_rooms; returning empty list.")
        return []

    try:
        cur = conn.cursor()
        cur.execute("SELECT room_name, hr_accepted, ai_accepted, meeting_active, meeting_url, created_at, updated_at FROM interview_room_state WHERE meeting_active = 0 ORDER BY updated_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [_row_to_state(r) for r in rows]
    except Exception as e:
        logger.exception("Failed to list waiting rooms: %s", e)
        # return empty list on error (keeps frontend stable)
        return []
