# app/api/interview.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_connection
import traceback
import secrets
import string

# Import Gmail service
try:
    from app.services.gmail_services import GmailService
    gmail_service_available = True
except Exception as e:
    GmailService = None
    gmail_service_available = False
    gmail_import_error = str(e)

router = APIRouter(prefix="/interview", tags=["Interview"])


# ---------------------------------------------------------
# Generate ONLY the Jitsi room name (branding handled in FE)
# ---------------------------------------------------------
def generate_jitsi_link() -> str:
    """
    Return only the Jitsi room name.
    Example: AIInterviewRoom-Ab12Xy
    """
    random_id = ''.join(
        secrets.choice(string.ascii_letters + string.digits)
        for _ in range(6)
    )
    return f"AIInterviewRoom-{random_id}"


# ---------------------------------------------------------
# Request body for scheduling interview
# ---------------------------------------------------------
class InterviewSchedule(BaseModel):
    interview_date: str  # YYYY-MM-DD
    interview_time: str  # HH:MM (24-hour)


# ---------------------------------------------------------
# Schedule Interview API
# ---------------------------------------------------------
@router.post("/schedule/{resume_id}")
async def schedule_interview(resume_id: str, data: InterviewSchedule):

    # Gmail check
    if not gmail_service_available:
        raise HTTPException(
            status_code=500,
            detail=f"Gmail service not configured: {gmail_import_error}"
        )

    # Fetch candidate
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT full_name, email_id
            FROM parsed_resumes
            WHERE resume_id = %s
        """, (resume_id,))
        row = cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate_name = row.get("full_name") or "Candidate"
    candidate_email = row.get("email_id")

    if not candidate_email:
        raise HTTPException(status_code=400, detail="Candidate email missing")

    # -----------------------------------------------------
    # Generate ROOM NAME (not URL)
    # -----------------------------------------------------
    room_name = generate_jitsi_link()

    # -----------------------------------------------------
    # Build FRONTEND LINK
    # -----------------------------------------------------
    frontend_url = "http://localhost:5173"   # change after deployment
    meeting_link = f"{frontend_url}/interview-room/{room_name}"

    # -----------------------------------------------------
    # Email Body
    # -----------------------------------------------------
    email_body = f"""Dear {candidate_name},

Congratulations! You have been shortlisted for an interview at S2Integrators.

Interview Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {data.interview_date}
🕐 Time: {data.interview_time}
🔗 Meeting Link: {meeting_link}

Please join the meeting at the scheduled time using the link above.

Instructions:
• Click the meeting link 5 minutes before the scheduled time
• No account or app installation required
• Allow camera and microphone access when prompted
• Ensure you have a stable internet connection

If you have any questions or need to reschedule, please contact our HR team.

Best regards,
S2Integrators HR Team
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Technical Support: Jitsi Meet works on all browsers. If you face any issues,
try using Chrome or Firefox.
""".strip()

    # -----------------------------------------------------
    # Send email
    # -----------------------------------------------------
    try:
        gmail = GmailService()
        result = gmail.send_email(
            to_email=candidate_email,
            subject="Interview Scheduled – S2Integrators",
            message_text=email_body
        )

        return {
            "success": True,
            "message": "Interview email sent successfully",
            "email_sent_to": candidate_email,
            "candidate_name": candidate_name,
            "interview_date": data.interview_date,
            "interview_time": data.interview_time,
            "meeting_link": meeting_link,
            "message_id": result.get("message_id")
        }

    except Exception as e:
        print("Email error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


# ---------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------
@router.get("/health")
async def interview_health_check():
    return {
        "status": "healthy",
        "gmail_service_available": gmail_service_available,
        "meeting_service": "Jitsi Meet (iframe based)",
    }
