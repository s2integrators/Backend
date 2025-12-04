import imaplib
import email
import os
import time
import threading
import asyncio
import uuid
import json
from email.header import decode_header
from io import BytesIO
from fastapi import UploadFile

from app.services.resume_service import ResumeService
from app.core.database import get_connection

EMAIL_USER = "s2integratorshiring@gmail.com"
EMAIL_PASS = "yiza womg qyrc vtjj"

IMAP_SERVER = "imap.gmail.com"
UPLOAD_DIR = "app/uploads"

service = ResumeService()


# --------------------------------------------------
# Safe helpers
# --------------------------------------------------
def normalize(value):
    """
    Always return a CLEAN STRING.
    - list/dict/None -> ""
    - everything else -> stripped str(...)
    """
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return ""
    return str(value).strip()


def normalize_int(value):
    """
    Safely convert to INT.
    - list/dict/None/"" -> 0
    - "3.5" -> 3
    - invalid -> 0
    """
    try:
        if value is None:
            return 0
        if isinstance(value, (list, dict)):
            return 0
        s = str(value).strip()
        if s == "":
            return 0
        return int(float(s))
    except Exception:
        return 0


def ensure_list(x):
    """
    Convert whatever comes from LLM into a Python list for JSON storage.
    """
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        # try JSON decode
        try:
            j = json.loads(x)
            if isinstance(j, list):
                return j
        except Exception:
            pass
        # fallback to comma-split
        return [s.strip() for s in x.split(",") if s.strip()]
    # last resort: single value list
    return [str(x)]


def json_dump_safe(obj) -> str:
    """
    Safely json.dumps for MySQL TEXT/VARCHAR columns that store JSON.
    """
    try:
        return json.dumps(obj)
    except TypeError:
        return json.dumps(str(obj) if obj is not None else "")


# --------------------------------------------------
# Convert saved file → UploadFile
# --------------------------------------------------
def create_fake_uploadfile(file_path: str, filename: str) -> UploadFile:
    with open(file_path, "rb") as f:
        data = f.read()
    return UploadFile(filename=filename, file=BytesIO(data))


# --------------------------------------------------
# Save attachment locally
# --------------------------------------------------
def save_attachment(part, filename: str) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(part.get_payload(decode=True))
    return file_path


# --------------------------------------------------
# Run pipeline + save into DB (resumes + parsed_resumes)
# --------------------------------------------------
async def async_process_resume(file_path: str, filename: str) -> None:
    try:
        fake_file = create_fake_uploadfile(file_path, filename)
        result = await service.full_pipeline(fake_file)
    except Exception as e:
        print("❌ ERROR Pipeline:", e)
        return

    # ------------------ PIPELINE SHAPE DEFENCE ------------------
    # Typical shape:
    # {
    #   "status": "...",
    #   "filename": "...",
    #   "pipeline_results": {
    #       "resume_text": "...",
    #       "resume_text_length": 1234,
    #       "extracted_data": { ... },
    #       "key_categories": { ... }
    #   }
    # }
    pipeline_results = result.get("pipeline_results") or {}
    extracted = (
        pipeline_results.get("extracted_data")
        or result.get("extracted_data")
        or {}
    )
    key_categories = (
        pipeline_results.get("key_categories")
        or result.get("key_categories")
        or {}
    )

    # This is used as the FK between resumes and parsed_resumes
    resume_id = str(uuid.uuid4())

    # --------------------------------------------------
    # FIELD MAPPING (matches LLM output, with fallbacks)
    # --------------------------------------------------
    name = normalize(
        extracted.get("full_name")
        or extracted.get("name")
    )

    email_id = normalize(
        extracted.get("email_id")
        or extracted.get("email_address")
        or extracted.get("email")
    )

    phone = normalize(
        extracted.get("mobile")
        or extracted.get("phone")
        or extracted.get("phone_number")
    )

    # Skills for resumes table → simple string, with many fallbacks
    skills_raw = (
        extracted.get("skills")
        or extracted.get("technical_skills")
        or extracted.get("technologies")
        or extracted.get("tech_stack")
        or extracted.get("skills_list")
    )
    skills_list = ensure_list(skills_raw)
    skills_str = ", ".join(skills_list) if skills_list else ""

    # Raw text (if provided)
    raw_text = normalize(
        pipeline_results.get("resume_text")
        or result.get("resume_text")
        or extracted.get("raw_text")
    )

    # Experience → integer
    years_experience = normalize_int(
        extracted.get("work_experience")
        or extracted.get("years_experience")
        or extracted.get("experience_years")
    )

    # Education:
    #   - resumes.education (VARCHAR simple string)
    #   - parsed_resumes.education (JSON stored string)
    edu_val = (
        extracted.get("education_level")
        or extracted.get("highest_education")
        or extracted.get("education")
    )
    education_str = normalize(edu_val)  # for resumes table
    education_json = ensure_list(extracted.get("education") or edu_val)

    # Key projects / internships from pipeline (if any)
    projects_json = ensure_list(
        extracted.get("key_projects") or extracted.get("projects")
    )
    internships_json = ensure_list(
        extracted.get("internships") or extracted.get("experience")
    )

    # Key categories for DB (if column exists)
    key_categories_json_str = json_dump_safe(key_categories)

    skills_json_str = json_dump_safe(skills_list)
    education_json_str = json_dump_safe(education_json)
    projects_json_str = json_dump_safe(projects_json)
    internships_json_str = json_dump_safe(internships_json)

    text_len = normalize_int(
        pipeline_results.get("resume_text_length")
        or result.get("resume_text_length")
        or (len(raw_text) if raw_text else 0)
    )

    # --------------------------------------------------
    # INSERT INTO DB
    #   1) resumes           (upload metadata + simple info)
    #   2) parsed_resumes    (rich parsed JSON used by /resume/resumes)
    #   3) OPTIONAL: key_categories column if present
    # --------------------------------------------------
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1) base upload record
        cursor.execute(
            """
            INSERT INTO resumes (
                id, file_name, file_path,
                name, email, phone,
                skills, years_experience, education,
                raw_text, source
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'email')
            """,
            (
                resume_id,
                filename,
                file_path,
                name,
                email_id,
                phone,
                skills_str,
                years_experience,
                education_str,
                raw_text,
            ),
        )

        # 2) parsed_resumes row (used by /api/v1/resume/resumes on dashboard)
        cursor.execute(
            """
            INSERT INTO parsed_resumes (
                resume_id,
                full_name,
                email_id,
                github_portfolio,
                linkedin_id,
                skills,
                education,
                key_projects,
                internships,
                parsed_text_length
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                full_name          = VALUES(full_name),
                email_id           = VALUES(email_id),
                github_portfolio   = VALUES(github_portfolio),
                linkedin_id        = VALUES(linkedin_id),
                skills             = VALUES(skills),
                education          = VALUES(education),
                key_projects       = VALUES(key_projects),
                internships        = VALUES(internships),
                parsed_text_length = VALUES(parsed_text_length),
                updated_at         = CURRENT_TIMESTAMP
            """,
            (
                resume_id,
                name,
                email_id,
                None,  # github_portfolio
                None,  # linkedin_id
                skills_json_str,
                education_json_str,
                projects_json_str,
                internships_json_str,
                text_len,
            ),
        )

        # 3) OPTIONAL: store key_categories JSON if column exists
        try:
            cursor.execute(
                "SHOW COLUMNS FROM parsed_resumes LIKE 'key_categories'"
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    UPDATE parsed_resumes
                    SET key_categories = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE resume_id = %s
                    """,
                    (key_categories_json_str, resume_id),
                )
        except Exception as inner_e:
            # Don't break the pipeline if column isn't there
            print("ℹ️ Skipping key_categories column update:", inner_e)

        conn.commit()
        print(f"✔ Email Resume Saved + Parsed: {filename} ({resume_id})")

    except Exception as e:
        print("❌ DB ERROR while inserting email resume:", e)

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# --------------------------------------------------
# Simple wrapper to run async from thread
# --------------------------------------------------
def process_resume_from_email(file_path: str, filename: str):
    asyncio.run(async_process_resume(file_path, filename))


# --------------------------------------------------
# Poll Gmail for new resumes
# --------------------------------------------------
def poll_email():
    print("📥 Polling Gmail...")

    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()

            for msg_id in email_ids:
                _, data = mail.fetch(msg_id, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])

                for part in msg.walk():
                    if part.get_content_disposition() != "attachment":
                        continue

                    filename = part.get_filename()
                    if not filename:
                        continue

                    filename = decode_header(filename)[0][0]
                    if isinstance(filename, bytes):
                        filename = filename.decode()

                    # only accept common resume formats
                    if not filename.lower().endswith((".pdf", ".doc", ".docx")):
                        continue

                    print(f"📎 Attachment Found: {filename}")

                    file_path = save_attachment(part, filename)
                    process_resume_from_email(file_path, filename)

            mail.logout()

        except Exception as e:
            print("❌ Poller Error:", e)

        # poll every 20 seconds
        time.sleep(20)


# --------------------------------------------------
# Start background poller
# --------------------------------------------------
def start_email_poller():
    t = threading.Thread(target=poll_email, daemon=True)
    t.start()
    print("🚀 Email Poller Started")
