# # app/main.py
# # @app.get("/health")
# # async def health_check():
# #     return {"status": "healthy", "service": APP_TITLE}

# """
# FastAPI Resume Parser Application
# Main application entry point
# """
# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse

# from app.core.config import (
#     API_V1_PREFIX,
#     APP_TITLE,
#     APP_DESCRIPTION,
#     APP_VERSION,
#     CORS_ORIGINS,
# )


# # ✅ Existing imports (kept)
# from app.api.jobs import router as jobs_router
# from app.api.match import router as match_router


# # ✅ Optional feature imports (guarded)
# tts_router = None
# interview_router = None
# # 🔶 ADD: hr router guard
# hr_router = None

# try:
#     from app.api.tts import router as _tts_router  # noqa
#     tts_router = _tts_router
# except Exception:
#     # WHY: Avoid startup crash if feature not present
#     tts_router = None

# try:
#     from app.api.interview import router as _interview_router  # noqa
#     interview_router = _interview_router
# except Exception:
#     interview_router = None

# # 🔶 ADD: hr import guard
# try:
#     from app.api.hr import router as _hr_router  # noqa
#     hr_router = _hr_router
# except Exception:
#     hr_router = None

# # Try to load recommendations router (we will mount it in several places for compatibility)
# rec_router = None
# try:
#     from app.api.recommendations import router as _rec_router  # noqa
#     rec_router = _rec_router
# except Exception:
#     rec_router = None

# # import recommendation service (used by the forwarders below)
# recommendation_service = None
# try:
#     from app.services import recommendation_service as _recommendation_service  # noqa
#     recommendation_service = _recommendation_service
# except Exception:
#     recommendation_service = None

# from app.services.email_poller import start_email_poller
# # ---------------------------------------------------------
# # Create FastAPI app
# # ---------------------------------------------------------
# app = FastAPI(
#     title=APP_TITLE,
#     description=APP_DESCRIPTION,
#     version=APP_VERSION,
#     docs_url="/docs",
#     redoc_url="/redoc",
# )


# # ---------------------------------------------------------
# # CORS Middleware
# # ---------------------------------------------------------
# # combine configured origins + dev origins; fallback to "*" for dev ease
# _allow_origins = (CORS_ORIGINS or []) + [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]
# if not _allow_origins:
#     _allow_origins = ["*"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=_allow_origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # ---------------------------------------------------------
# # Include API Routers
# # ---------------------------------------------------------
# # Grouped v1 router (this mounts resume/jobs/match/recommendations under API_V1_PREFIX)
# from app.api.routes import api_router
# app.include_router(api_router, prefix=API_V1_PREFIX)

# # Jobs + Match routers (v1)
# app.include_router(jobs_router, prefix=API_V1_PREFIX)
# app.include_router(match_router, prefix=API_V1_PREFIX)

# # ---------------------------------------------------------
# # Compatibility mounts for recommendations
# # (Mount the same router under multiple prefixes so older frontend paths work)
# # ---------------------------------------------------------
# if rec_router is not None:
#     # 1) Non-versioned `/api/recommendations/*`
#     try:
#         app.include_router(rec_router, prefix="/api/recommendations")
#         print("Mounted recommendations at /api/recommendations")
#     except Exception as e:
#         print("Failed to mount /api/recommendations:", e)

#     # 2) Top-level `/recommendations/*`
#     try:
#         app.include_router(rec_router, prefix="/recommendations")
#         print("Mounted recommendations at /recommendations")
#     except Exception as e:
#         print("Failed to mount /recommendations:", e)

#     # 3) Also mount under /api/v1/recommendations if for any reason not already present
#     try:
#         app.include_router(rec_router, prefix=f"{API_V1_PREFIX}/recommendations")
#         print(f"Mounted recommendations at {API_V1_PREFIX}/recommendations")
#     except Exception as e:
#         print(f"Failed to mount {API_V1_PREFIX}/recommendations:", e)


# # New feature routers (mount only if present)  ➜ mount UNDER /api/v1
# if tts_router is not None:
#     app.include_router(tts_router, prefix=API_V1_PREFIX)

# if interview_router is not None:
#     app.include_router(interview_router, prefix=API_V1_PREFIX)

# # 🔶 ADD: mount HR router under /api/v1  ➜ fixes 404 on /api/v1/hr/roles
# if hr_router is not None:
#     app.include_router(hr_router, prefix=API_V1_PREFIX)


# # ---------------------------------------------------------
# # TEMP HOTFIX: Forwarding endpoints to handle mismatched frontend URLs
# # ---------------------------------------------------------
# # These endpoints call the underlying recommendation service directly so requests
# # to /recommendations/search or /api/recommendations/search succeed even if the
# # router prefixes do not match. This is temporary — long-term fix is to align
# # router prefixes and update frontend to use API base (apiBase()).
# if recommendation_service is not None:
#     @app.post("/recommendations/search")
#     async def forward_recommendations_search(req: Request):
#         """
#         Temporary forwarder so frontend requests to /recommendations/search succeed
#         even if the recommendations router prefix differs.
#         """
#         try:
#             payload = await req.json()
#         except Exception:
#             payload = {}

#         # normalize payload
#         if not isinstance(payload, dict):
#             payload = {}

#         topN = int(payload.get("topN", 20))
#         criteria = {k: v for k, v in payload.items() if k != "topN"}

#         try:
#             # call the service (synchronous) and wrap any exception to a JSONResponse
#             results = recommendation_service.search_candidates(criteria, topN=topN)
#             return JSONResponse({"success": True, "results": results}, status_code=200)
#         except Exception as e:
#             # log server-side for debugging
#             print("forward_recommendations_search error:", repr(e))
#             # return a JSON response with 500 and a message (CORS middleware will add headers)
#             return JSONResponse({"success": False, "detail": str(e)}, status_code=500)

#     @app.post("/api/recommendations/search")
#     async def forward_api_recommendations_search(req: Request):
#         # reuse forwarder logic so behavior is identical
#         return await forward_recommendations_search(req)
# else:
#     # If recommendation service not available, provide a helpful error
#     @app.post("/recommendations/search")
#     async def forward_recommendations_search_unavailable():
#         return JSONResponse({"success": False, "detail": "Recommendation service not available on server"}, status_code=503)

#     @app.post("/api/recommendations/search")
#     async def forward_api_recommendations_search_unavailable():
#         return JSONResponse({"success": False, "detail": "Recommendation service not available on server"}, status_code=503)


# # ---------------------------------------------------------
# # (Optional) Print registered routes to help debugging
# # ---------------------------------------------------------
# try:
#     import pprint
#     pprint.pprint([r.path for r in app.routes])
# except Exception:
#     pass


# # ---------------------------------------------------------
# # Root Endpoints
# # ---------------------------------------------------------
# @app.get("/")
# async def root():
#     return {
#         "message": "Resume Parser API",
#         "version": APP_VERSION,
#         "docs": "/docs",
#         "endpoints": {
#             "parse_resume": f"{API_V1_PREFIX}/resume/parse",
#             "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
#             "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
#             "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline",
#         },
#     }


# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": APP_TITLE}

# @app.on_event("startup")
# def start_poller_on_startup():
#     start_email_poller()
#     print("✅ Email Poller Attached to FastAPI Startup")




# app/main.py
"""
FastAPI Resume Parser Application
Main application entry point (merged + improved)

Features added / fixed:
- Safe import guards for optional routers (tts, interview, hr, recommendations)
- Mount recommendations router under multiple prefixes for compatibility
- Mount `bin` router (POST /api/v1/bin/delete/{id})
- Forwarding endpoints for recommendations when service present
- Start email poller during startup
- Improved startup route-printing / verification
- Robust CORS origins list with sensible fallbacks
"""
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.interview_access import router as interview_access_router

from app.core.config import (
    API_V1_PREFIX,
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    CORS_ORIGINS,
)

# main API routers (core)
from app.api.routes import api_router
from app.api.jobs import router as jobs_router
from app.api.match import router as match_router

# optional routers (guarded imports)
tts_router = None
interview_router = None
hr_router = None
rec_router = None
bin_router = None

# recommendation service (optional)
recommendation_service = None

# --------- guarded imports ----------
try:
    from app.api.tts import router as _tts_router  # noqa
    tts_router = _tts_router
except Exception:
    tts_router = None

try:
    from app.api.interview import router as _interview_router  # noqa
    interview_router = _interview_router
except Exception:
    interview_router = None

try:
    from app.api.hr import router as _hr_router  # noqa
    hr_router = _hr_router
except Exception:
    hr_router = None

# recommendations router (may or may not exist)
try:
    from app.api.recommendations import router as _rec_router  # noqa
    rec_router = _rec_router
except Exception:
    rec_router = None

# bin router (explicitly required in the merged file)
try:
    from app.api import bin as _bin_module  # noqa
    # bin module should expose `router`
    bin_router = getattr(_bin_module, "router", None)
except Exception:
    bin_router = None

# recommendation service (used by forwarders)
try:
    from app.services import recommendation_service as _recommendation_service  # noqa
    recommendation_service = _recommendation_service
except Exception:
    recommendation_service = None

# email poller (optional; safe import)
try:
    from app.services.email_poller import start_email_poller  # noqa
except Exception:
    # fallback no-op
    def start_email_poller():
        print("Email poller not available (skipped).")

# ---------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# then where your app includes routers:interview_access_router
app.include_router(interview_access_router)




# ---------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------
# combine configured origins + common dev origins; allow "*" as last resort
_dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_allow_origins = []
if CORS_ORIGINS:
    try:
        _allow_origins = list(CORS_ORIGINS) + _dev_origins
    except Exception:
        _allow_origins = _dev_origins
else:
    _allow_origins = _dev_origins or ["*"]

# if still empty, default to "*"
if not _allow_origins:
    _allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Include API Routers
# ---------------------------------------------------------
# 1. Core parsing / v1 router (grouped)
app.include_router(api_router, prefix=API_V1_PREFIX)

# 2. Core feature routers (jobs + match)
app.include_router(jobs_router, prefix=API_V1_PREFIX)
app.include_router(match_router, prefix=API_V1_PREFIX)

# 3. Register BIN router (if available) under /api/v1
if bin_router is not None:
    try:
        app.include_router(bin_router, prefix=f"{API_V1_PREFIX}", tags=["Bin"])
        print("Mounted bin router under", f"{API_V1_PREFIX}")
    except Exception as e:
        print("Failed to mount bin router:", e)

# 4. Optional feature routers (mount under API_V1_PREFIX)
if tts_router is not None:
    app.include_router(tts_router, prefix=API_V1_PREFIX)

if interview_router is not None:
    app.include_router(interview_router, prefix=API_V1_PREFIX)

if hr_router is not None:
    app.include_router(hr_router, prefix=API_V1_PREFIX)

# ---------------------------------------------------------
# Recommendations compatibility mounts
# - Mount same router under several prefixes so older frontend paths work
# ---------------------------------------------------------
if rec_router is not None:
    try:
        # Non-versioned: /api/recommendations/*
        app.include_router(rec_router, prefix="/api/recommendations")
        print("Mounted recommendations at /api/recommendations")
    except Exception as e:
        print("Failed to mount /api/recommendations:", e)

    try:
        # Top-level: /recommendations/*
        app.include_router(rec_router, prefix="/recommendations")
        print("Mounted recommendations at /recommendations")
    except Exception as e:
        print("Failed to mount /recommendations:", e)

    try:
        # Ensure it's mounted under API_V1_PREFIX as well
        app.include_router(rec_router, prefix=f"{API_V1_PREFIX}/recommendations")
        print(f"Mounted recommendations at {API_V1_PREFIX}/recommendations")
    except Exception as e:
        print(f"Failed to mount {API_V1_PREFIX}/recommendations:", e)

# ---------------------------------------------------------
# TEMP HOTFIX: Forwarding endpoints for recommendation service
# These allow requests to /recommendations/search and /api/recommendations/search
# to succeed even when router prefixes differ.
# ---------------------------------------------------------
if recommendation_service is not None:
    @app.post("/recommendations/search")
    async def forward_recommendations_search(req: Request):
        try:
            payload = await req.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            payload = {}

        try:
            topN = int(payload.get("topN", 20))
        except Exception:
            topN = 20
        criteria = {k: v for k, v in payload.items() if k != "topN"}

        try:
            # call the recommendation service synchronously (common pattern)
            results = recommendation_service.search_candidates(criteria, topN=topN)
            return JSONResponse({"success": True, "results": results}, status_code=200)
        except Exception as e:
            print("forward_recommendations_search error:", repr(e))
            return JSONResponse({"success": False, "detail": str(e)}, status_code=500)

    @app.post("/api/recommendations/search")
    async def forward_api_recommendations_search(req: Request):
        return await forward_recommendations_search(req)
else:
    # provide helpful 503 responses so frontend sees useful error payload
    @app.post("/recommendations/search")
    async def forward_recommendations_search_unavailable():
        return JSONResponse({"success": False, "detail": "Recommendation service not available on server"}, status_code=503)

    @app.post("/api/recommendations/search")
    async def forward_api_recommendations_search_unavailable():
        return JSONResponse({"success": False, "detail": "Recommendation service not available on server"}, status_code=503)

# ---------------------------------------------------------
# Root Endpoints
# ---------------------------------------------------------
@app.get("/")
async def root():
    endpoints = {
        "parse_resume": f"{API_V1_PREFIX}/resume/parse",
        "extract_keys": f"{API_V1_PREFIX}/resume/extract-keys",
        "generate_questions": f"{API_V1_PREFIX}/resume/generate-questions",
        "full_pipeline": f"{API_V1_PREFIX}/resume/full-pipeline",
         "auth_login": f"{API_V1_PREFIX}/auth/login",       # <-- add for clarity
            "auth_register": f"{API_V1_PREFIX}/auth/register"
    }
    # include bin endpoint if we mounted it
    if bin_router is not None:
        endpoints["bin_delete"] = f"{API_V1_PREFIX}/bin/delete/{{id}}"

    return {
        "message": "Resume Parser API",
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": endpoints,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": APP_TITLE}

# ---------------------------------------------------------
# Startup event - attach email poller + print registered routes
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # start poller (if available)
    try:
        start_email_poller()
        print("✅ Email Poller Attached to FastAPI Startup")
    except Exception as e:
        print("Email poller failed to start or not present:", e)

    # print registered routes to aid debugging
    print("\n" + "=" * 60)
    print("🚀 SERVER STARTUP - REGISTERED ROUTES")
    print("=" * 60)
    found_bin = False
    found_recs = False
    for route in app.routes:
        try:
            path = getattr(route, "path", None)
            methods = getattr(route, "methods", None)
            if path:
                print(f"  {methods}  {path}")
                if "bin/delete" in path or "/bin" in path:
                    found_bin = True
                if "recommendations" in path:
                    found_recs = True
        except Exception:
            continue
    print("-" * 60)
    print(f"Bin route present: {'✅' if found_bin else '❌'}")
    print(f"Recommendations routes present: {'✅' if found_recs else '❌'}")
    print("=" * 60 + "\n")
