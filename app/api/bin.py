# # filepath: AI_Screen/app/api/bin.py
# from fastapi import APIRouter, HTTPException
# from typing import List
# from app.services.db_ops import soft_delete_resume, restore_resume
# from app.api.resume import list_parsed_resumes # Reuse the listing logic

# router = APIRouter(tags=["Bin/SoftDelete"])

# @router.get("/bin", response_model=List[dict])
# async def list_deleted_resumes():
#     """List resumes currently marked as deleted (in the Bin)."""
#     # NOTE: list_parsed_resumes needs to be adapted to fetch deleted items.
#     # Since we can't easily modify the original list_parsed_resumes here,
#     # we'll use a placeholder for now and recommend a DB change.
#     # RECOMMENDED: Filter on is_deleted = TRUE in the DB layer.
#     return [] # Placeholder, requires modification to /resumes endpoint logic.

# @router.post("/bin/delete/{resume_id}")
# async def send_to_bin(resume_id: str):
#     """Soft deletes a resume by ID (moves to Bin)."""
#     if soft_delete_resume(resume_id):
#         return {"message": "Resume successfully moved to Bin."}
#     raise HTTPException(status_code=404, detail="Resume not found or soft-delete failed.")

# @router.post("/bin/restore/{resume_id}")
# async def restore_from_bin(resume_id: str):
#     """Restores a soft-deleted resume from the Bin."""
#     if restore_resume(resume_id):
#         return {"message": "Resume successfully restored."}
#     raise HTTPException(status_code=404, detail="Resume not found or restore failed.")



# ============================================================================
# filepath: AI_Screen/app/api/bin.py
# ============================================================================
# from fastapi import APIRouter, HTTPException
# from typing import List
# from app.services.db_ops import (
#     soft_delete_resume, 
#     restore_resume, 
#     get_deleted_resumes,
#     permanently_delete_resume_by_id
# )

# router = APIRouter(tags=["Bin/SoftDelete"])

# @router.get("/bin", response_model=List[dict])
# async def list_deleted_items():
#     """List resumes currently marked as deleted (in the Bin)."""
#     return get_deleted_resumes()

# @router.post("/bin/delete/{resume_id}")
# async def send_to_bin(resume_id: str):
#     """Soft deletes a resume by ID (moves to Bin)."""
#     if soft_delete_resume(resume_id):
#         return {"message": "Resume successfully moved to Bin."}
#     raise HTTPException(status_code=404, detail="Resume not found or soft-delete failed.")

# @router.post("/bin/restore/{resume_id}")
# async def restore_from_bin(resume_id: str):
#     """Restores a soft-deleted resume from the Bin."""
#     if restore_resume(resume_id):
#         return {"message": "Resume successfully restored."}
#     raise HTTPException(status_code=404, detail="Resume not found or restore failed.")

# @router.delete("/bin/permanent/{resume_id}")
# async def permanently_delete_item(resume_id: str):
#     """Permanently remove a resume from the DB."""
#     if permanently_delete_resume_by_id(resume_id):
#         return {"message": "Resume permanently deleted."}
#     raise HTTPException(status_code=404, detail="Resume not found or delete failed.")

from fastapi import APIRouter, HTTPException
from typing import List

# Wrap imports in try-except to identify if db_ops is the issue
try:
    from app.services.db_ops import (
        soft_delete_resume, 
        restore_resume, 
        get_deleted_resumes,
        permanently_delete_resume_by_id
    )
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Could not import db_ops: {e}")
    # Define dummy functions so the server doesn't crash, allowing us to see the error
    soft_delete_resume = None

router = APIRouter() # Removed tags here since we added them in main.py

@router.get("/bin", response_model=List[dict])
async def list_deleted_items():
    return get_deleted_resumes()

# Explicitly define the full path part here to be safe
@router.post("/bin/delete/{resume_id}")
async def send_to_bin(resume_id: str):
    if not soft_delete_resume:
        raise HTTPException(status_code=500, detail="Server Error: DB Ops not loaded")
        
    print(f"Attempting to delete: {resume_id}") # Debug log
    if soft_delete_resume(resume_id):
        return {"message": "Resume successfully moved to Bin."}
    raise HTTPException(status_code=404, detail="Resume not found or soft-delete failed.")

@router.post("/bin/restore/{resume_id}")
async def restore_from_bin(resume_id: str):
    if restore_resume(resume_id):
        return {"message": "Resume successfully restored."}
    raise HTTPException(status_code=404, detail="Resume not found or restore failed.")

@router.delete("/bin/permanent/{resume_id}")
async def permanently_delete_item(resume_id: str):
    if permanently_delete_resume_by_id(resume_id):
        return {"message": "Resume permanently deleted."}
    raise HTTPException(status_code=404, detail="Resume not found or delete failed.")