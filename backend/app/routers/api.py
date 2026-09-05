"""
API router — analyze endpoint (delegates to services layer).
Auth routes → routers/auth_routes.py
PDF export → routers/export.py
Business logic → services/analyze_service.py, services/report_qc.py, services/event_facts.py
"""
import logging
import re
from datetime import date, datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.database import get_db, User, Usage, check_usage_allowed
from backend.engine.registry import ScenarioRegistry, normalize_scenario_type
from backend.app.services.analyze_service import (
    run_analysis,
    get_cached_result,
    build_cached_response,
)

# ---------------------------------------------------------------------------
# Backward-compatible re-exports (tests import these from backend.app.routers.api)
# ---------------------------------------------------------------------------
from backend.app.services.report_qc import (  # noqa: F401
    sanitize_report_body as _sanitize_report_body,
    normalize_entity_name as _normalize_entity_name,
    source_matches_query as _source_matches_query,
    compute_report_as_of as _compute_report_as_of,
    build_report_qc as _build_report_qc,
    trust_availability_entry as _trust_availability_entry,
    build_analyze_data_availability as _build_analyze_data_availability,
    with_trust_contract as _with_trust_contract,
    apply_publication_containment as _apply_publication_containment,
    _SAFE_BODY,
)
from backend.app.services.event_facts import (  # noqa: F401
    event_status as _event_status,
    macro_consistency_conflict as _macro_consistency_conflict,
)
from backend.app.routers.export import (  # noqa: F401
    _safe_pdf_filename,
    _sanitize_report_html,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    skill_type: str
    query: str
    extra_content: str = ""


@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate skill
    req.skill_type = normalize_scenario_type(req.skill_type)
    skill = ScenarioRegistry().get_metadata(req.skill_type)
    if not skill:
        raise HTTPException(status_code=400, detail="未知的分析技能")

    # Check usage
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"今日免费额度已用完（{used}/{limit}次），请升级VIP获取无限使用",
        )

    # Check cache
    cached = get_cached_result(req.skill_type, req.query)
    if cached:
        usage = Usage(user_id=user.id, skill_type=req.skill_type, query=req.query[:500])
        db.add(usage)
        db.commit()
        cached_response = build_cached_response(cached, req.skill_type, req.query)
        cached_response["usage_used"] = used + 1
        cached_response["usage_limit"] = limit
        return cached_response

    # Run analysis via service layer
    response_data = await run_analysis(
        skill_type=req.skill_type,
        query=req.query,
        extra_content=req.extra_content,
    )

    # Handle error from service
    if response_data.get("error"):
        raise HTTPException(status_code=400, detail=response_data["error"])

    # Record usage
    usage = Usage(
        user_id=user.id,
        skill_type=req.skill_type,
        query=req.query[:500],
    )
    db.add(usage)
    db.commit()

    response_data["usage_used"] = used + 1
    response_data["usage_limit"] = limit

    return response_data
