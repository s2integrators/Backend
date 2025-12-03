# # app/services/recommendation_service.py
# import csv
# import io
# from typing import List, Dict, Any, Optional
# from datetime import datetime

# # ✅ Import from existing database module instead of redefining
# from app.core.database import get_connection

# def _get_conn():
#     """Use the existing database connection from core/database.py"""
#     return get_connection()

# def _split_csv_like(text: Optional[str]):
#     if not text:
#         return []
#     return [s.strip().lower() for s in str(text).split(",") if s.strip()]

# def compute_score(candidate: Dict[str, Any], criteria: Dict[str, Any]) -> int:
#     """Return 0-100 score (simple heuristic based on available data)."""
#     score = 50  # Base score since we have limited data
    
#     # Check if file_name matches search criteria
#     file_name = (candidate.get("candidate_name") or "").lower()
#     role = (criteria.get("role") or "").lower()
#     skills = [s.lower() for s in (criteria.get("skills") or []) if s]
    
#     # Simple name/role matching
#     if role and role in file_name:
#         score += 30
    
#     # Simple skill matching in filename
#     if skills:
#         matches = sum(1 for s in skills if s in file_name)
#         if matches > 0:
#             score += min(20, matches * 10)
    
#     return min(100, int(round(score)))

# def get_all_resume_links(limit: int = 1000) -> List[Dict[str, Any]]:
#     """Return list of {id, candidate_name, resume_link}."""
#     conn = _get_conn()
#     cur = conn.cursor(dictionary=True)
    
#     # Use existing columns: file_name as candidate_name, file_path as resume_link
#     sql = """
#         SELECT 
#             id, 
#             file_name as candidate_name, 
#             file_path as resume_link,
#             uploaded_at as created_at
#         FROM resumes 
#         ORDER BY uploaded_at DESC 
#         LIMIT %s
#     """
    
#     print(f"📝 SQL: {sql}")
#     cur.execute(sql, (limit,))
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
    
#     # Clean up the candidate names (remove file extensions) and convert datetime
#     for row in rows:
#         if row.get("candidate_name"):
#             # Remove .pdf, .docx extensions and clean up
#             name = row["candidate_name"]
#             for ext in [".pdf", ".docx", ".doc", ".txt"]:
#                 name = name.replace(ext, "")
#             row["candidate_name"] = name.strip()
        
#         # Convert datetime to string (fix JSON serialization)
#         if row.get("created_at"):
#             if isinstance(row["created_at"], datetime):
#                 row["created_at"] = row["created_at"].isoformat()
    
#     return rows

# def search_candidates(criteria: Dict[str, Any], topN: int = 50) -> List[Dict[str, Any]]:
#     """
#     Search candidates using available columns.
#     Since we only have file_name and file_path, we'll do simple text matching.
#     """
#     role = criteria.get("role")
#     skills = criteria.get("skills") or []
#     max_rows = 2000

#     where_clauses = []
#     params = []

#     # Search in file_name for role
#     if role:
#         where_clauses.append("file_name LIKE %s")
#         params.append(f"%{role}%")

#     # Search in file_name for skills
#     if skills:
#         skill_clauses = " OR ".join(["file_name LIKE %s" for _ in skills])
#         where_clauses.append(f"({skill_clauses})")
#         for s in skills:
#             params.append(f"%{s}%")

#     where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

#     conn = _get_conn()
#     cur = conn.cursor(dictionary=True)
    
#     sql = f"""
#         SELECT 
#             id, 
#             file_name as candidate_name, 
#             file_path as resume_link,
#             uploaded_at as created_at,
#             NULL as best_role,
#             NULL as skills,
#             NULL as keywords,
#             0 as years_experience,
#             0 as completeness_score
#         FROM resumes 
#         WHERE {where_sql} 
#         ORDER BY uploaded_at DESC
#         LIMIT %s
#     """
    
#     print(f"📝 Search SQL: {sql}")
#     params.append(max_rows)
#     cur.execute(sql, tuple(params))
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()

#     # Clean up candidate names and compute scores
#     scored = []
#     for r in rows:
#         # Remove file extensions from name
#         if r.get("candidate_name"):
#             name = r["candidate_name"]
#             for ext in [".pdf", ".docx", ".doc", ".txt"]:
#                 name = name.replace(ext, "")
#             r["candidate_name"] = name.strip()
        
#         # Convert datetime to string (fix JSON serialization)
#         if r.get("created_at"):
#             if isinstance(r["created_at"], datetime):
#                 r["created_at"] = r["created_at"].isoformat()
        
#         # Compute score
#         score = compute_score(r, criteria)
#         r["score"] = score
#         r["best_role"] = role if role else "Not specified"
#         scored.append(r)

#     scored.sort(key=lambda x: x["score"], reverse=True)
#     return scored[:topN]

# def export_resume_links_csv() -> bytes:
#     rows = get_all_resume_links(limit=100000)
#     buffer = io.StringIO()
#     writer = csv.writer(buffer)
#     writer.writerow(["id", "candidate_name", "resume_link"])
#     for r in rows:
#         writer.writerow([r.get("id"), r.get("candidate_name"), r.get("resume_link")])
#     return buffer.getvalue().encode("utf-8")




# app/services/recommendation_service.py
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime

# ✅ Import from existing database module
from app.core.database import get_connection

def _get_conn():
    """Use the existing database connection from core/database.py"""
    return get_connection()

def _split_csv_like(text: Optional[str]):
    if not text:
        return []
    return [s.strip() for s in str(text).split(",") if s.strip()]

def compute_score(candidate: Dict[str, Any], criteria: Dict[str, Any]) -> int:
    """Return 0-100 score based on matching criteria."""
    score = 40  # Base score
    
    # Get candidate data
    cand_name = (candidate.get("candidate_name") or "").lower()
    cand_skills = (candidate.get("skills") or "").lower()
    
    # Get search criteria
    role = (criteria.get("role") or "").lower()
    skills = [s.lower() for s in (criteria.get("skills") or []) if s]
    
    # Role matching (30 points)
    if role:
        if role in cand_name or role in cand_skills:
            score += 30
    
    # Skills matching (30 points) - Check if any search skill is in candidate skills
    if skills:
        matches = sum(1 for s in skills if s in cand_skills)
        if matches > 0:
            score += min(30, matches * 15)  # Up to 30 points for skill matches
    
    return min(100, int(round(score)))

def get_all_resume_links(limit: int = 1000) -> List[Dict[str, Any]]:
    """Return list of resumes from parsed_resumes table."""
    conn = _get_conn()
    cur = conn.cursor(dictionary=True)
    
    sql = """
        SELECT 
            resume_id as id,
            full_name as candidate_name,
            email_id as resume_link,
            skills,
            education,
            key_projects,
            internships
        FROM parsed_resumes 
        ORDER BY resume_id DESC 
        LIMIT %s
    """
    
    print(f"📝 Get All SQL: {sql}")
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Process rows
    for row in rows:
        # Ensure skills is a string
        if row.get("skills"):
            row["skills"] = str(row["skills"])
        else:
            row["skills"] = ""
        
        # Add missing fields with defaults
        row["best_role"] = "Not specified"
        row["years_experience"] = 0
        row["score"] = 50
        row["created_at"] = datetime.now().isoformat()
    
    return rows

def search_candidates(criteria: Dict[str, Any], topN: int = 50) -> List[Dict[str, Any]]:
    """
    Search candidates in parsed_resumes table by role and skills.
    """
    role = criteria.get("role", "")
    skills = criteria.get("skills") or []
    max_rows = 2000

    where_clauses = []
    params = []

    # Build WHERE clause for role (search in full_name and skills)
    if role:
        where_clauses.append("(full_name LIKE %s OR skills LIKE %s)")
        params.append(f"%{role}%")
        params.append(f"%{role}%")

    # Build WHERE clause for skills - search each skill with OR
    if skills:
        skill_clauses = []
        for skill in skills:
            skill_clauses.append("skills LIKE %s")
            params.append(f"%{skill}%")
        
        if skill_clauses:
            where_clauses.append(f"({' OR '.join(skill_clauses)})")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    conn = _get_conn()
    cur = conn.cursor(dictionary=True)
    
    sql = f"""
        SELECT 
            resume_id as id,
            full_name as candidate_name,
            email_id as resume_link,
            github_portfolio,
            linkedin_id,
            skills,
            education,
            key_projects,
            internships
        FROM parsed_resumes 
        WHERE {where_sql} 
        ORDER BY resume_id DESC
        LIMIT %s
    """
    
    print(f"📝 Search SQL: {sql}")
    print(f"📝 Params: {params}")
    
    params.append(max_rows)
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Process results and compute scores
    scored = []
    for r in rows:
        # Ensure skills is a string
        if r.get("skills"):
            r["skills"] = str(r["skills"])
        else:
            r["skills"] = ""
        
        # Add computed fields
        r["keywords"] = r.get("key_projects", "")
        r["best_role"] = role if role else "Not specified"
        r["years_experience"] = 0  # Can be enhanced later
        r["completeness_score"] = 0
        r["created_at"] = datetime.now().isoformat()
        
        # Compute match score
        score = compute_score(r, criteria)
        r["score"] = score
        
        scored.append(r)

    # Sort by score (highest first)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:topN]

def export_resume_links_csv() -> bytes:
    rows = get_all_resume_links(limit=100000)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "candidate_name", "email", "skills"])
    for r in rows:
        writer.writerow([
            r.get("id"), 
            r.get("candidate_name"), 
            r.get("resume_link"),
            r.get("skills", "")
        ])
    return buffer.getvalue().encode("utf-8")