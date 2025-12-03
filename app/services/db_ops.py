# ============================================================================
# filepath: AI_Screen/app/services/db_ops.py
# ============================================================================
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.core.database import get_connection

def soft_delete_resume(resume_id: str, months_to_keep: int = 2) -> bool:
    """
    Marks a resume as deleted and sets an automatic permanent deletion date.
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            print("❌ DB Connection failed during soft delete")
            return False
            
        cursor = conn.cursor()

        # 1. Safety Check: Does the resume exist?
        cursor.execute("SELECT id, name FROM resumes WHERE id = %s", (resume_id,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"❌ DELETE FAILED: Resume ID {resume_id} does not exist in database.")
            return False

        print(f"🔍 Found resume: {exists[1]} (ID: {exists[0]}). Proceeding to soft delete...")
        
        # 2. Calculate dates
        permanent_delete_at = datetime.utcnow() + timedelta(days=30 * months_to_keep)
        current_time = datetime.utcnow()

        # 3. Perform Update
        cursor.execute(
            """
            UPDATE resumes
            SET is_deleted = TRUE, 
                deleted_at = %s, 
                updated_at = %s
            WHERE id = %s
            """,
            (permanent_delete_at, current_time, resume_id)
        )
        
        conn.commit()
        print(f"✅ SUCCESS: Resume {resume_id} soft-deleted. Expires at {permanent_delete_at}")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during soft delete for resume {resume_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def restore_resume(resume_id: str) -> bool:
    """
    Restores a soft-deleted resume, making it active again in the system.
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        current_time = datetime.utcnow()
        
        # Remove deleted status and clear deletion timestamp
        cursor.execute(
            """
            UPDATE resumes
            SET is_deleted = FALSE, 
                deleted_at = NULL, 
                updated_at = %s
            WHERE id = %s AND is_deleted = TRUE
            """,
            (current_time, resume_id)
        )
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ SUCCESS: Resume {resume_id} restored.")
            return True
        else:
            print(f"⚠️ RESTORE FAILED: Resume {resume_id} not found or was not deleted.")
            return False
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during resume restore for {resume_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def permanently_delete_resume_by_id(resume_id: str) -> bool:
    """
    Permanently removes a specific resume from the database (Physical Delete).
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        # Hard Delete
        cursor.execute(
            "DELETE FROM resumes WHERE id = %s",
            (resume_id,)
        )
        
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ SUCCESS: Resume {resume_id} PERMANENTLY deleted.")
            return True
        else:
            print(f"⚠️ PERMANENT DELETE FAILED: Resume {resume_id} not found.")
            return False
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error permanently deleting resume {resume_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()


def get_deleted_resumes() -> List[Dict[str, Any]]:
    """
    Retrieves all soft-deleted resumes (currently in the Bin).
    """
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            return []
            
        cursor = conn.cursor()
        
        # Fetch all deleted resumes
        cursor.execute(
            """
            SELECT id, name, email, phone, years_experience, skills, 
                   education, raw_text, created_at, updated_at, deleted_at
            FROM resumes
            WHERE is_deleted = TRUE
            ORDER BY deleted_at DESC
            """
        )
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            resume_dict = dict(zip(columns, row))
            # Calculate days remaining until permanent deletion
            if resume_dict.get('deleted_at'):
                days_remaining = (resume_dict['deleted_at'] - datetime.utcnow()).days
                resume_dict['days_until_permanent_delete'] = max(0, days_remaining)
            results.append(resume_dict)
            
        return results
        
    except Exception as e:
        print(f"❌ Error fetching deleted resumes: {e}")
        return []
    finally:
        if conn:
            conn.close()