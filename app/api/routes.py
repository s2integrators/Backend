# # =========================================
# # filepath: AI_Screen/app/api/routes.py
# # =========================================
# """
# Main API routes aggregator
# """
# from fastapi import APIRouter

# # import router objects
# from app.api.resume import router as resume_router   # resume router has no prefix
# from app.api.jobs import router as jobs_router       # has prefix="/jobs"
# from app.api.match import router as match_router     # has prefix="/match"
# from fastapi import APIRouter
# from app.api import resume, jobs, interview
# from app.api.recommendations import router as rec_router

# api_router = APIRouter()

# # Final paths mounted under /api/v1/...
# api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
# # IMPORTANT: don't add an extra prefix here; routers already have one
# api_router.include_router(jobs_router,   tags=["jobs"])
# api_router.include_router(match_router,  tags=["match"])
# """
# Main API routes aggregator
# """
# # from fastapi import APIRouter
# # from app.api import resume, jobs, interview

# # Create main API router
# # api_router = APIRouter()

# # Include all route modules
# # api_router.include_router(resume.router, prefix="/resume")
# # api_router.include_router(jobs.router, prefix="/job")
# api_router.include_router(interview.router, prefix="/interview")

# # recommendations router
# app.include_router(rec_router)



# # =========================================
# # filepath: AI_Screen/app/api/routes.py
# # =========================================
# """
# Main API routes aggregator.
# This file ONLY creates `api_router`.
# DO NOT import or use `app` here.
# """
# from fastapi import APIRouter
# import logging

# logger = logging.getLogger(__name__)

# api_router = APIRouter()

# # -------------------------------
# # Resume Router
# # -------------------------------
# try:
#     from app.api.resume import router as resume_router
#     api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
# except Exception as e:
#     logger.error(f"Resume router load error: {e}")

# # -------------------------------
# # Jobs Router
# # -------------------------------
# try:
#     from app.api.jobs import router as jobs_router
#     api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
# except Exception as e:
#     logger.error(f"Jobs router load error: {e}")

# # -------------------------------
# # Match Router
# # -------------------------------
# try:
#     from app.api.match import router as match_router
#     api_router.include_router(match_router, prefix="/match", tags=["Match"])
# except Exception as e:
#     logger.error(f"Match router load error: {e}")

# # -------------------------------
# # Interview Router (optional)
# # -------------------------------
# try:
#     from app.api.interview import router as interview_router
#     api_router.include_router(interview_router, prefix="/interview", tags=["Interview"])
# except Exception:
#     pass

# # -------------------------------
# # Recommendations Router (NEW)
# # -------------------------------
# try:
#     from app.api.recommendations import router as rec_router
#     api_router.include_router(rec_router, prefix="/recommendations", tags=["Recommendations"])
# except Exception as e:
#     logger.error(f"Recommendations router load error: {e}")

# logger.info("API Router Loaded Successfully.")



# =========================================
# filepath: AI_Screen/app/api/routes.py
# =========================================
"""
Main API routes aggregator.
This file ONLY creates `api_router`.
DO NOT import or use `app` here.
"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# -------------------------------
# Resume Router
# -------------------------------
try:
    from app.api.resume import router as resume_router
    api_router.include_router(resume_router, prefix="/resume", tags=["Resume"])
except Exception as e:
    logger.error(f"Resume router load error: {e}")

# -------------------------------
# Jobs Router
# -------------------------------
try:
    from app.api.jobs import router as jobs_router
    api_router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
except Exception as e:
    logger.error(f"Jobs router load error: {e}")

# -------------------------------
# Match Router
# -------------------------------
try:
    from app.api.match import router as match_router
    api_router.include_router(match_router, prefix="/match", tags=["Match"])
except Exception as e:
    logger.error(f"Match router load error: {e}")

# -------------------------------
# Interview Router
# -------------------------------
try:
    from app.api.interview import router as interview_router
    api_router.include_router(interview_router, prefix="/interview", tags=["Interview"])
except Exception as e:
    logger.error(f"Interview router load error: {e}")

# -------------------------------
# Auth Router
# -------------------------------
# try:
#     from app.api import auth as auth_router
#     api_router.include_router(auth_router.router, tags=["Auth"])
# except Exception as e:
#     logger.error(f"Auth router load error: {e}")


    # import the router object directly — more robust and easier to debug
from app.api import auth  # imports the APIRouter object
api_router.include_router(auth.router)  # auth_router already has prefix="/auth" and tags
logger.info("Auth router mounted at /auth (on api_router).")




# -------------------------------
# Recommendations Router
# -------------------------------
try:
    from app.api.recommendations import router as rec_router
    api_router.include_router(rec_router, prefix="/recommendations", tags=["Recommendations"])
except Exception as e:
    logger.error(f"Recommendations router load error: {e}")

logger.info("API Router Loaded Successfully.")