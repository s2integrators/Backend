# app/api/recommendations.py
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import logging
import decimal
import datetime

from app.services import recommendation_service as svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


class SearchRequest(BaseModel):
    role: Optional[str] = None
    skills: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    years: Optional[float] = None
    topN: Optional[int] = 20


def _sanitize_value(v: Any) -> Any:
    """
    Convert some DB types (Decimal, datetime, bytes) into JSON-serializable types.
    """
    if isinstance(v, decimal.Decimal):
        # keep integer-like decimals as int, otherwise float
        if v == v.to_integral():
            return int(v)
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except Exception:
            return str(v)
    return v


def _sanitize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _sanitize_value(v) for k, v in (row.items() if isinstance(row, dict) else dict(row).items())}


@router.get("/links")
def get_links(limit: int = 1000):
    """
    Return minimal resume link records:
      GET /api/recommendations/links?limit=1000
    """
    try:
        rows = svc.get_all_resume_links(limit=limit)
        sanitized = [_sanitize_row(r) for r in rows]
        return {"success": True, "data": sanitized}
    except Exception as e:
        logger.exception("Failed to get resume links")
        raise HTTPException(status_code=500, detail="Failed to get resume links")


@router.post("/search")
def search(req: SearchRequest):
    """
    Search candidates and return top-ranked results according to the service scoring.
    POST /api/recommendations/search
    body: { role, skills, keywords, years, topN }
    """
    try:
        criteria = req.dict(exclude_none=True)
        topN = int(criteria.pop("topN", 20))
        results = svc.search_candidates(criteria, topN=topN)

        # sanitize DB rows + include score if present
        sanitized = []
        for r in results:
            row = _sanitize_row(r)
            # ensure score is int if present
            if "score" in row:
                try:
                    row["score"] = int(row["score"])
                except Exception:
                    row["score"] = row["score"]
            sanitized.append(row)

        return {"success": True, "results": sanitized}
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/export")
def export_csv():
    """
    Export resume links as a CSV file.
    GET /api/recommendations/export
    """
    try:
        data = svc.export_resume_links_csv()  # expected bytes or str
        # Ensure bytes
        if isinstance(data, str):
            data = data.encode("utf-8")
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=resumes_links.csv"},
        )
    except Exception as e:
        logger.exception("Export CSV failed")
        raise HTTPException(status_code=500, detail="Export CSV failed")
