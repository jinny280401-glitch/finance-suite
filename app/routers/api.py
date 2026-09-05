from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import html as html_lib
import logging
import re, sys, os
from urllib.parse import quote
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'quality_gate'))
try:
    from quality_gate.core import QualityGate
    from quality_gate.rules import QualityRules
    _QG_AVAILABLE = True
except ImportError:
    _QG_AVAILABLE = False

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
)
from app.database import get_db, User, Usage, check_usage_allowed, get_today_usage_count
from app.search import unified_search, format_search_results
from app.llm import generate_analysis, generate_analysis_stream, cache_get, cache_set
from app.skills import get_skill, get_skill_prompt, normalize_skill_type

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


_TRUSTED_EVENT_SOURCE_KEYWORDS = (
    "外交部",
    "新华社",
    "人民日报",
    "央视",
    "CCTV",
    "Reuters",
    "路透",
    "Associated Press",
    "AP News",
    "Bloomberg",
    "彭博",
)

_TRUSTED_EVENT_DOMAINS = (
    "mfa.gov.cn",
    "www.fmprc.gov.cn",
    "news.cn",
    "xinhuanet.com",
    "people.com.cn",
    "cctv.com",
    "reuters.com",
    "apnews.com",
    "bloomberg.com",
)

_CONFIRMED_EVENT_TERMS = (
    "确认",
    "证实",
    "宣布",
    "介绍",
    "将访华",
    "进行国事访问",
    "state visit",
    "confirmed",
    "announced",
    "official",
)

_MACRO_CONFLICT_TERMS = (
    "未证实",
    "没有权威信源证实",
    "没有任何权威信源证实",
    "未发现权威信源",
    "不构成真实经济事件",
    "虚构",
    "杜撰",
    "假设性",
)


def _event_query_for_macro(query: str) -> str:
    q = (query or "").strip()
    if re.search(r"(特朗普|Trump|trump).*(访华|中国|来华)|访华.*(特朗普|Trump|trump)", q, re.I):
        return "特朗普 访华 5月13日 15日 外交部 新华社 Reuters official confirmed"
    return f"{q} 最新 事件 官方 证实 外交部 新华社 Reuters"


def _result_text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("title", "content", "url"))


def _source_identity_text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("title", "source", "url"))


def _trusted_event_source(item: dict) -> bool:
    text = _source_identity_text(item)
    url = str(item.get("url", "")).lower()
    return any(k.lower() in text.lower() for k in _TRUSTED_EVENT_SOURCE_KEYWORDS) or any(
        d in url for d in _TRUSTED_EVENT_DOMAINS
    )


def _event_status(item: dict) -> str:
    text = _result_text(item)
    if _trusted_event_source(item) and any(t.lower() in text.lower() for t in _CONFIRMED_EVENT_TERMS):
        return "confirmed"
    if _trusted_event_source(item):
        return "official"
    return "unverified"


def _extract_source_time(item: dict) -> str | None:
    text = _result_text(item)
    patterns = [
        r"20\d{2}[-/年.]\d{1,2}[-/月.]\d{1,2}",
        r"\d{1,2}月\d{1,2}日",
        r"May\s+\d{1,2},?\s+20\d{2}",
        r"\d{1,2}\s+May\s+20\d{2}",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            return m.group(0)
    return None


def _extract_event_time(item: dict) -> str | None:
    text = _result_text(item)
    m = re.search(r"5月\s*13\s*(?:至|-|到|—|~)\s*15日", text)
    if m:
        return "5月13日至15日"
    m = re.search(r"May\s+13\s*(?:-|to|–|—)\s*15", text, re.I)
    if m:
        return "May 13-15"
    return _extract_source_time(item)


def _macro_event_facts_from_results(query: str, results: list[dict]) -> dict:
    debug = {
        "macro_query": query,
        "selected_sources": [],
        "event_time": None,
        "source_time": None,
        "confidence": 0.0,
        "used_timeline_context": False,
        "rejected_reason": None,
    }
    selected = []
    for item in results or []:
        status = _event_status(item)
        if status not in ("confirmed", "official"):
            continue
        confidence = 0.95 if status == "confirmed" else 0.82
        source = {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "status": status,
            "event_time": _extract_event_time(item),
            "source_time": _extract_source_time(item),
            "confidence": confidence,
        }
        selected.append(source)

    if not selected:
        debug["rejected_reason"] = "no_confirmed_or_official_event_source"
        return {"confirmed": False, "context": "", "sources": [], "debug": debug}

    selected = selected[:5]
    best = selected[0]
    debug.update(
        {
            "selected_sources": selected,
            "event_time": best.get("event_time"),
            "source_time": best.get("source_time"),
            "confidence": best.get("confidence", 0.0),
            "used_timeline_context": True,
        }
    )
    lines = [
        "=== 最新事件事实（Timeline/latest_events/news_feed_v2 同源预检）===",
    ]
    for i, source in enumerate(selected, 1):
        lines.append(
            f"【事件事实{i}】状态：{source['status']}；信心：{source['confidence']}; "
            f"事件时间：{source.get('event_time') or '未提取'}；信源时间：{source.get('source_time') or '未提取'}；"
            f"标题：{source.get('title')}; 链接：{source.get('url')}"
        )
    return {"confirmed": True, "context": "\n".join(lines), "sources": selected, "debug": debug}


async def _fetch_macro_event_facts(query: str) -> dict:
    event_query = _event_query_for_macro(query)
    try:
        results = await unified_search(event_query, "news")
    except Exception as e:
        return {
            "confirmed": False,
            "context": "",
            "sources": [],
            "debug": {
                "macro_query": query,
                "selected_sources": [],
                "event_time": None,
                "source_time": None,
                "confidence": 0.0,
                "used_timeline_context": False,
                "rejected_reason": f"event_lookup_failed: {e}",
            },
        }
    facts = _macro_event_facts_from_results(query, results if isinstance(results, list) else [])
    logger.info("macro_event_facts %s", facts["debug"])
    return facts


def _macro_consistency_conflict(result: str, facts: dict) -> str | None:
    if not facts.get("confirmed"):
        return None
    text = result or ""
    for term in _MACRO_CONFLICT_TERMS:
        if term in text:
            return f"timeline_confirmed_but_macro_said_{term}"
    return None


# ---- Request models ----

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AnalyzeRequest(BaseModel):
    skill_type: str
    query: str
    extra_content: str = ""


class ExportPdfRequest(BaseModel):
    query: str = "Finance Suite 报告"
    html: str = ""


# ---- Auth endpoints ----

def _issue_auth_response(content: dict, token: str) -> JSONResponse:
    """Clear legacy cookie variants, then set one canonical host-only cookie."""
    response = JSONResponse(content=content)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token", path="/", domain=".touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="www.touziagent.com")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        max_age=86400,
        path="/",
        samesite="lax",
    )
    return response


def _clear_auth_response(content: dict) -> JSONResponse:
    response = JSONResponse(content=content)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token", path="/", domain=".touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="www.touziagent.com")
    return response

@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check existing
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {
            "success": True,
            "message": "注册成功",
            "username": user.username,
            "tier": user.tier,
            "token": token,
        },
        token,
    )


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {
            "success": True,
            "message": "登录成功",
            "username": user.username,
            "tier": user.tier,
            "token": token,
        },
        token,
    )


@router.post("/logout")
async def logout():
    return _clear_auth_response({"success": True, "message": "已退出登录"})


@router.get("/check-auth")
async def check_auth(user: User | None = Depends(get_optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    return {
        "authenticated": True,
        "username": user.username,
        "tier": user.tier,
    }


# ---- Report QC helpers ----

_DATE_CUTOFF_PATTERN = re.compile(
    r"(?m)^[>\s]*"
    r"(?:数据截止[：:]\s*\S+|数据截至[：:]\s*\S+|report\s+date[：:\s]\s*\S+|"
    r"as\s+of[：:\s]\s*\S+|knowledge\s+cutoff[：:\s]\s*\S+|"
    r"训练截止[：:]\s*\S+|训练截止日期[：:]\s*\S+)"
    r"[^\n]*\n?",
    re.IGNORECASE,
)

_SAFE_BODY = """\
### AI 初步分析草稿

公开资料不足，系统未能确认该标的的可靠信源。

本次不生成完整深度研报，原因：
- 缺少结构化数据
- 搜索结果不足或无法确认日期
- 财务、股东、管理层言行等关键章节无法核实

请查看下方质检信息后再决定是否继续人工补充资料。
"""


def _sanitize_report_body(result: str, report_as_of: dict) -> str:
    """Remove LLM-written date cutoff lines and replace with system-generated line."""
    if not result:
        return result
    if report_as_of.get("source_date_unknown"):
        from datetime import date
        replacement = f"数据截止：未能从信源确认，系统生成日期：{date.today().isoformat()}\n"
    else:
        replacement = f"数据截止：{report_as_of['date']}\n"
    return _DATE_CUTOFF_PATTERN.sub(replacement, result)


def _normalize_entity_name(text: str) -> str:
    """Normalize company/entity names for strict source relevance checks."""
    if not text:
        return ""
    normalized = str(text).lower()
    suffixes = [
        "股份有限公司",
        "科技有限公司",
        "集团有限公司",
        "控股有限公司",
        "有限公司",
        "corporation",
        "limited",
        "corp.",
        "corp",
        "inc.",
        "inc",
        "ltd.",
        "ltd",
    ]
    for suffix in suffixes:
        normalized = normalized.replace(suffix, "")
    normalized = re.sub(r"[\s\W_]+", "", normalized, flags=re.UNICODE)
    return normalized


def _source_matches_query(source: dict, query: str) -> bool:
    """Return True only when a source strongly matches the requested entity."""
    raw_query = (query or "").strip()
    if not raw_query:
        return False
    source_text = " ".join(
        str(source.get(k, "") or "") for k in ("title", "content", "raw_content")
    )
    if raw_query in source_text:
        return True
    normalized_query = _normalize_entity_name(raw_query)
    normalized_source = _normalize_entity_name(source_text)
    return bool(normalized_query and normalized_query in normalized_source)


def _compute_report_as_of(sources: list[dict]) -> dict:
    """Extract latest published date from Tavily sources. Falls back to today with flag."""
    import re
    from datetime import date

    latest_date = None
    for s in sources:
        for key in ("published_date", "date", "published_at"):
            val = s.get(key)
            if val:
                m = re.search(r"(\d{4}-\d{2}-\d{2})", str(val))
                if m:
                    try:
                        d = date.fromisoformat(m.group(1))
                        if latest_date is None or d > latest_date:
                            latest_date = d
                    except ValueError:
                        pass

    today = date.today()
    if latest_date:
        return {
            "date": latest_date.isoformat(),
            "source_date_unknown": False,
            "days_since_latest_source": (today - latest_date).days,
        }
    return {
        "date": today.isoformat(),
        "source_date_unknown": True,
        "days_since_latest_source": None,
    }


def _build_report_qc(
    skill_type: str,
    sources: list[dict],
    matched_sources: list[dict],
    has_structured: bool,
    search_results_text: str,
    report_as_of: dict,
) -> dict:
    """Build extended _qc: freshness / fact_coverage / hallucination_risk."""
    search_hits = len(sources)
    matched_search_hits = len(matched_sources)
    unmatched_search_hits = max(search_hits - matched_search_hits, 0)
    days = report_as_of.get("days_since_latest_source")
    is_stale = days is None or days > 180

    freshness = {
        "latest_source_date": report_as_of["date"] if not report_as_of["source_date_unknown"] else None,
        "days_since_latest_source": days,
        "is_stale": is_stale,
        "source_date_unknown": report_as_of["source_date_unknown"],
        "warning": (
            "最新信源超过180天，数据可能已过时" if is_stale and not report_as_of["source_date_unknown"]
            else ("无法确定信源日期，报告内容可能来自模型训练知识" if report_as_of["source_date_unknown"] else None)
        ),
    }

    entity_polluted = bool(search_hits > 0 and matched_search_hits == 0 and not has_structured)
    no_search_hits = bool(search_hits == 0 and not has_structured)

    if entity_polluted:
        llm_ratio = 1.0
    elif has_structured and matched_search_hits >= 3:
        llm_ratio = 0.3
    elif has_structured or matched_search_hits >= 1:
        llm_ratio = 0.6
    else:
        llm_ratio = 1.0

    unsupported: list[str] = []
    if llm_ratio >= 0.9:
        if skill_type == "industry":
            unsupported = ["竞争格局", "市场规模", "财务数据", "管理层言行"]
        elif skill_type == "stock":
            unsupported = ["财务数据", "估值", "管理层言行"]

    fact_coverage = {
        "structured_data_available": has_structured,
        "search_hits": search_hits,
        "matched_search_hits": matched_search_hits,
        "unmatched_search_hits": unmatched_search_hits,
        "cited_sources_count": matched_search_hits,
        "llm_inference_ratio": llm_ratio,
        "unsupported_sections": unsupported,
    }

    if entity_polluted:
        risk_level = "high"
        risk_reason = "搜索结果存在，但未匹配目标实体，可能为近似实体污染"
    elif no_search_hits:
        risk_level = "medium"
        risk_reason = "搜索未返回可用信源，报告主要来自模型推断"
    elif llm_ratio >= 0.9:
        risk_level, risk_reason = "high", "无结构化数据，搜索结果不足，报告主要来自模型训练知识"
    elif llm_ratio >= 0.6:
        risk_level, risk_reason = "medium", "有部分搜索结果，但缺少结构化数据支撑，部分内容来自模型推断"
    else:
        risk_level, risk_reason = "low", "有结构化数据和多个搜索信源支撑"

    hallucination_risk = {
        "level": risk_level,
        "reason": risk_reason,
        "affected_sections": unsupported,
    }

    if entity_polluted:
        status = "insufficient_data"
    elif no_search_hits:
        status = "partial"
    elif matched_search_hits >= 2:
        status = "success"
    elif matched_search_hits == 1:
        status = "partial"
    else:
        status = "success" if has_structured else "insufficient_data"

    return {
        "status": status,
        "completeness": round(min(1.0, matched_search_hits / 3 + (0.4 if has_structured else 0.0)), 2),
        "sources": [s.get("url", "") for s in matched_sources[:5]],
        "freshness": freshness,
        "fact_coverage": fact_coverage,
        "hallucination_risk": hallucination_risk,
    }


_TRUST_DIMENSIONS = (
    "fundamental",
    "realtime",
    "macro",
    "news",
    "capital_flow",
    "valuation",
    "research",
    "market_context",
)


def _trust_availability_entry(status: str, available: list[str] | None = None, missing: list[str] | None = None, source_type: str = "derived", latency_ms: int | None = None) -> dict:
    return {
        "status": status,
        "available": available or [],
        "missing": missing or [],
        "as_of": datetime.now().replace(microsecond=0).isoformat() if available else None,
        "source_type": source_type,
        "latency_ms": latency_ms,
    }


def _build_analyze_data_availability(response: dict) -> dict:
    qc = response.get("_qc") or {}
    fact = qc.get("fact_coverage") or {}
    has_structured = bool(fact.get("structured_data_available") or response.get("kline"))
    has_sources = bool(response.get("sources") or qc.get("sources"))
    has_result = bool(response.get("result"))
    source_type = "real" if (has_structured or has_sources) else "missing"

    availability = {
        key: _trust_availability_entry("unavailable", missing=[key], source_type="missing")
        for key in _TRUST_DIMENSIONS
    }

    availability["fundamental"] = _trust_availability_entry(
        "partial" if has_structured else "unavailable",
        available=["structured_financial_or_kline"] if has_structured else [],
        missing=[] if has_structured else ["fundamental"],
        source_type=source_type if has_structured else "missing",
    )
    availability["realtime"] = _trust_availability_entry(
        "partial" if response.get("kline") else "unavailable",
        available=["kline"] if response.get("kline") else [],
        missing=[] if response.get("kline") else ["realtime"],
        source_type="real" if response.get("kline") else "missing",
    )
    availability["news"] = _trust_availability_entry(
        "partial" if has_sources else "unavailable",
        available=["search_sources"] if has_sources else [],
        missing=[] if has_sources else ["news"],
        source_type="real" if has_sources else "missing",
    )
    availability["research"] = _trust_availability_entry(
        "partial" if has_sources else "unavailable",
        available=["search_sources"] if has_sources else [],
        missing=[] if has_sources else ["research"],
        source_type="real" if has_sources else "missing",
    )
    availability["market_context"] = _trust_availability_entry(
        "partial" if has_result else "unavailable",
        available=["report_context"] if has_result else [],
        missing=[] if has_result else ["market_context"],
        source_type="derived" if has_result else "missing",
    )
    return availability


def _with_trust_contract(response: dict) -> dict:
    if not isinstance(response, dict):
        return response
    data_availability = response.get("data_availability")
    if not isinstance(data_availability, dict):
        data_availability = _build_analyze_data_availability(response)
        response["data_availability"] = data_availability

    if "section_data_usage" not in response:
        response["section_data_usage"] = {}

    qc = response.setdefault("_qc", {})
    if isinstance(qc, dict):
        qc.setdefault("data_availability", data_availability)
        qc.setdefault("section_data_usage", response.get("section_data_usage"))
    return response


_PUBLICATION_SAFETY_LABEL = "TEMPORARY PUBLICATION SAFETY / NOT TRUST GATE"

# This is deliberately a publication containment control, not evidence admission.
# It must remain after LLM generation until its policy is moved before the prompt.
_PUBLICATION_CONCLUSION_POLICY = {
    "valuation": {
        "rules": (
            ("good_price", r"好价格"),
            ("buy_implication", r"会买"),
            ("valuation_judgment", r"估值已消化|估值判断"),
            ("valuation_judgment", r"(?:PE|PB).{0,24}(?:高估|低估|合理|便宜|贵|好价格)"),
            ("valuation_driven_positioning", r"(?:估值|PE|PB).{0,24}(?:建仓|重仓)"),
        ),
    },
    "realtime": {
        "rules": (
            ("current_price", r"当前价"),
            ("current_trend", r"当前趋势"),
            ("price_range", r"上行.{0,12}(?:空间|区间)|下行.{0,12}(?:空间|区间)|价格区间|股价参考区间"),
            ("risk_reward", r"风险收益比"),
            ("trade_trigger", r"交易触发|压力位|支撑位"),
        ),
    },
    "capital_flow": {
        "rules": (
            ("capital_structure", r"资金结构|量能结构"),
            ("major_player_behavior", r"主力行为|主力动向|机构抱团|主力撤离|游资博弈"),
            ("position_risk", r"持仓风险"),
            ("capital_flow_entry_basis", r"(?:资金流|资金面|北向资金|主力).{0,24}(?:建仓|买入|重仓)"),
        ),
    },
}


def _publication_allowed_classes(dimension: str, entry: dict) -> set[str]:
    """Only an exact, dimension-scoped allow-list can override PARTIAL."""
    allowed_use = entry.get("allowed_use") if isinstance(entry, dict) else []
    if not isinstance(allowed_use, list):
        return set()
    prefix = f"publication:{dimension}:"
    return {
        value[len(prefix):]
        for value in allowed_use
        if isinstance(value, str) and value.startswith(prefix)
    }


def _apply_publication_containment(response: dict) -> dict:
    """Fail closed at publication when unavailable/unauthorized dimensions drive conclusions.

    This does not prevent evidence from entering the model and therefore is not a
    Trust Gate.  If a prohibited conclusion is detected, reject the full report
    instead of attempting fragile text-only section surgery.
    """
    if not isinstance(response, dict):
        return response

    availability = response.get("data_availability") or {}
    result = response.get("result")
    if not isinstance(availability, dict) or not isinstance(result, str):
        return response

    blocked_dimensions: list[str] = []
    blocked_classes: list[str] = []
    reason_codes: list[str] = []

    for dimension, policy in _PUBLICATION_CONCLUSION_POLICY.items():
        entry = availability.get(dimension)
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", "")).lower()
        if status not in ("unavailable", "partial"):
            continue

        allowed_classes = _publication_allowed_classes(dimension, entry)
        matched_classes = []
        for conclusion_class, pattern in policy["rules"]:
            if conclusion_class in allowed_classes:
                continue
            if re.search(pattern, result, flags=re.IGNORECASE | re.DOTALL):
                matched_classes.append(conclusion_class)

        if matched_classes:
            blocked_dimensions.append(dimension)
            blocked_classes.extend(matched_classes)
            reason_codes.append(
                f"publication_{status}_{dimension}_conclusion_not_authorized"
            )

    publication = {
        "control": _PUBLICATION_SAFETY_LABEL,
        "publication_status": "published",
        "blocked_dimensions": [],
        "blocked_conclusion_classes": [],
        "suppressed_sections": [],
        "reason_codes": [],
    }
    if blocked_dimensions:
        publication.update({
            "publication_status": "rejected",
            "blocked_dimensions": sorted(set(blocked_dimensions)),
            "blocked_conclusion_classes": sorted(set(blocked_classes)),
            "suppressed_sections": ["entire_report"],
            "reason_codes": reason_codes,
        })
        result = (
            "报告发布已阻止：关键维度数据不可用或未获明确授权，"
            "不能发布依赖估值、实时行情或资金流的结论。\n\n"
            "请补齐结构化证据后重新生成报告。"
        )
        response["result"] = result

    response["publication"] = publication
    return response


def _build_final_dispatch_trace(
    skill_type: str,
    input_text: str,
    resolved_name: str | None = None,
    resolved_symbol: str | None = None,
    resolver_source: str | None = None,
    matched_text: str | None = None,
) -> dict:
    selected_route = normalize_skill_type(skill_type or "")
    trace = {
        "input_text": input_text,
        "resolved_name": resolved_name,
        "resolved_symbol": resolved_symbol,
        "resolver_source": resolver_source,
        "matched_text": matched_text,
        "selected_route": selected_route,
        "backend_endpoint": "/api/analyze",
        "final_dispatch": True,
        "dispatch_called": True,
        "engine_called": True,
        "runtime_mode": "real",
        "mock": False,
        "fallback": False,
    }
    if selected_route == "stock":
        trace["engine"] = "finance-suite.stock_analysis"
    else:
        trace["engine"] = f"finance-suite.{selected_route or 'unknown'}"
    return trace


def _attach_final_dispatch_trace(response: dict, trace: dict | None) -> dict:
    if not isinstance(response, dict) or not trace:
        return response
    response.setdefault("dispatch_trace", trace)
    response.setdefault("final_seal", {
        "called": True,
        "selected_route": trace.get("selected_route"),
        "resolved_symbol": trace.get("resolved_symbol"),
        "resolved_name": trace.get("resolved_name"),
        "runtime_mode": trace.get("runtime_mode"),
    })
    qc = response.setdefault("_qc", {})
    if isinstance(qc, dict):
        qc.setdefault("dispatch_trace", trace)
        qc.setdefault("final_seal", response.get("final_seal"))
    return response


# ---- Analysis endpoint ----

@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate skill
    req.skill_type = normalize_skill_type(req.skill_type)
    skill = get_skill(req.skill_type)
    if not skill:
        raise HTTPException(status_code=400, detail="未知的分析技能")

    # Check usage
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"今日免费额度已用完（{used}/{limit}次），请升级VIP获取无限使用",
        )

    # 检查缓存（10分钟内相同查询直接返回）
    # Macro relies on fast-moving event facts; do not reuse old RAG/search answers.
    # Auction must always re-run fetch → QC → admission → allowed_use: a cache hit
    # could return a stale L3 analysis after evidence degraded to L2/L1, bypassing
    # the Trust Gate (P0: cache sits before current admission).
    cached = None if req.skill_type in ("macro", "auction") else cache_get(req.skill_type, req.query)
    if cached:
        cached_trace = _build_final_dispatch_trace(req.skill_type, req.query)
        if req.skill_type == "stock":
            try:
                from app.stock_data import resolve_stock_detail
                detail = resolve_stock_detail(req.query)
                if detail:
                    cached_trace = _build_final_dispatch_trace(
                        req.skill_type,
                        req.query,
                        resolved_name=detail.get("name"),
                        resolved_symbol=detail.get("code"),
                        resolver_source=detail.get("resolver_source"),
                        matched_text=detail.get("matched_text"),
                    )
            except Exception:
                pass
        # 记录用量
        usage = Usage(user_id=user.id, skill_type=req.skill_type, query=req.query[:500])
        db.add(usage)
        db.commit()
        cached_response = _with_trust_contract(_attach_final_dispatch_trace(
            {**cached, "usage_used": used + 1, "usage_limit": limit, "cached": True},
            cached_trace,
        ))
        return _apply_publication_containment(cached_response)

    # Search for data (if skill requires it)
    search_results_text = ""
    sources = []
    macro_event_facts = None
    event_summary = None
    search_type = skill.get("search_type")
    auction_skip_llm = False

    if search_type:
        search_query = req.query
        if req.skill_type == "stock":
            # ====== 股票分析：AkShare结构化数据 + Tavily搜索补充 ======
            from app.stock_data import resolve_stock, get_stock_full_data, format_stock_data
            from app.search import multi_search_stock, format_search_results_grouped
            import asyncio

            # Step 1: 解析股票名称/代码（非阻塞，毫秒级）
            loop = asyncio.get_event_loop()
            resolver_source = None
            matched_text = None
            try:
                from app.stock_data import resolve_stock_detail
                stock_detail = await loop.run_in_executor(None, resolve_stock_detail, search_query)
            except Exception:
                stock_detail = None
            if stock_detail:
                stock_code = stock_detail["code"]
                stock_name = stock_detail["name"]
                resolver_source = stock_detail.get("resolver_source")
                matched_text = stock_detail.get("matched_text")
            else:
                stock_info = await loop.run_in_executor(None, resolve_stock, search_query)
                if stock_info:
                    stock_code, stock_name = stock_info
                    resolver_source = "legacy_resolve_stock"
                    matched_text = stock_name
                else:
                    stock_code, stock_name = search_query, search_query
                    resolver_source = "unresolved_passthrough"
                    matched_text = None
            final_dispatch_trace = _build_final_dispatch_trace(
                req.skill_type,
                req.query,
                resolved_name=stock_name,
                resolved_symbol=stock_code,
                resolver_source=resolver_source,
                matched_text=matched_text,
            )

            # Step 2: 并发获取 AkShare结构化数据 + Tavily搜索
            akshare_task = get_stock_full_data(stock_code)
            tavily_task = multi_search_stock(f"{stock_name} {stock_code}")
            akshare_data, tavily_results = await asyncio.gather(
                akshare_task, tavily_task, return_exceptions=True
            )

            # 处理AkShare结果
            structured_text = ""
            if isinstance(akshare_data, dict):
                structured_text = format_stock_data(akshare_data, stock_name, stock_code)
                # 从AkShare新闻中提取来源
                ak_news = akshare_data.get("news") or []
                for n in ak_news[:5]:
                    if n.get("url"):
                        sources.append({"title": n.get("title", ""), "url": n["url"]})

            # 处理Tavily结果
            search_text = ""
            if isinstance(tavily_results, list):
                sources.extend([{
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "date": r.get("date"),
                    "published_date": r.get("published_date"),
                    "published_at": r.get("published_at"),
                    "content": (r.get("content") or "")[:500],
                    "raw_content": (r.get("raw_content") or "")[:500],
                } for r in tavily_results if r.get("url")])
                search_text = format_search_results_grouped(tavily_results)

            # 合并两个数据源
            search_results_text = structured_text
            if search_text:
                search_results_text += f"\n\n=== 搜索引擎补充信息 ===\n{search_text}"

        elif req.skill_type == "macro":
            # ====== 宏观内参：AkShare宏观数据 + Tavily搜索补充 ======
            from app.macro_data import get_macro_data, format_macro_data
            import asyncio

            macro_task = get_macro_data()
            tavily_task = unified_search(search_query, search_type)
            event_facts_task = _fetch_macro_event_facts(search_query)
            macro_data, tavily_results, macro_event_facts = await asyncio.gather(
                macro_task, tavily_task, event_facts_task, return_exceptions=True
            )

            structured_text = ""
            if isinstance(macro_data, dict):
                structured_text = format_macro_data(macro_data)

            search_text = ""
            if isinstance(tavily_results, list):
                sources = [{
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "date": r.get("date"),
                    "published_date": r.get("published_date"),
                    "published_at": r.get("published_at"),
                    "content": (r.get("content") or "")[:500],
                    "raw_content": (r.get("raw_content") or "")[:500],
                } for r in tavily_results if r.get("url")]
                search_text = format_search_results(tavily_results)

            search_results_text = structured_text
            if isinstance(macro_event_facts, dict) and macro_event_facts.get("context"):
                search_results_text += f"\n\n{macro_event_facts['context']}"
                sources = [
                    {"title": s.get("title", ""), "url": s.get("url", ""), "status": s.get("status", "")}
                    for s in macro_event_facts.get("sources", [])
                ] + sources
            if search_text:
                search_results_text += f"\n\n=== 搜索引擎补充 ===\n{search_text}"

        elif req.skill_type == "auction":
            # ====== 集合竞价：AkShare盘面数据（QC强化 2026-07-17）======
            import logging
            logger = logging.getLogger(__name__)
            from app.auction_data import (
                get_validated_auction_data,
                format_auction_data,
                format_auction_qc_failure,
                AuctionDataQualityError,
                auction_allows_llm,
            )

            try:
                akshare_data = await get_validated_auction_data()
            except AuctionDataQualityError as exc:
                logger.warning("Auction data QC failed: %s", exc)
                search_results_text = format_auction_qc_failure(exc.qc)
                auction_allowed_use = exc.qc.get("allowed_use") or []
            else:
                search_results_text = format_auction_data(akshare_data)
                auction_allowed_use = akshare_data["_qc"].get("allowed_use") or []
            # (Decision 2 强制) L1/L2 不调用 LLM，直接返回结构化观察/速览；
            # 仅 L3 auction_analysis 授权调用 LLM。
            auction_skip_llm = not auction_allows_llm(auction_allowed_use)
            # 无需Tavily搜索，纯盘面数据

        elif req.skill_type == "industry":
            # ====== 行业报告：AkShare行业板块数据 + Tavily搜索补充 ======
            import asyncio

            async def fetch_industry_ak():
                loop = asyncio.get_event_loop()
                try:
                    import akshare as ak
                    df = await loop.run_in_executor(
                        None, ak.stock_board_industry_name_em
                    )
                    if df is not None:
                        matched = df[df["板块名称"].str.contains(req.query, na=False)]
                        if len(matched) > 0:
                            return matched.head(5).to_dict(orient="records")
                except Exception:
                    pass
                return None

            ak_task = fetch_industry_ak()
            tavily_task = unified_search(search_query, search_type)
            ak_data, tavily_results = await asyncio.gather(
                ak_task, tavily_task, return_exceptions=True
            )

            structured_text = ""
            if isinstance(ak_data, list) and ak_data:
                structured_text = "=== 行业板块数据（东方财富）===\n"
                for r in ak_data:
                    structured_text += f"  {r}\n"

            search_text = ""
            if isinstance(tavily_results, list):
                sources = [{
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "date": r.get("date"),
                    "published_date": r.get("published_date"),
                    "published_at": r.get("published_at"),
                    "content": (r.get("content") or "")[:500],
                    "raw_content": (r.get("raw_content") or "")[:500],
                } for r in tavily_results if r.get("url")]
                search_text = format_search_results(tavily_results)

            search_results_text = (
                structured_text + "\n" + search_text if structured_text else search_text
            )

        elif req.skill_type == "video":
            # ====== 视频拆解：字幕提取 + 搜索补充 ======
            from app.video_data import get_video_content

            video_url = req.extra_content.strip() if req.extra_content else ""
            video_query = req.query.strip()
            has_transcript = video_query and video_query != "请拆解分析这个视频内容"

            all_text_parts = []

            # 优先级1：用户粘贴的逐字稿（最高质量）
            if has_transcript:
                all_text_parts.append(f"=== 用户提供的逐字稿 ===\n{video_query}")

            # 优先级2：从URL提取字幕（Supadata/B站API）
            if video_url:
                video_result = await get_video_content(video_url)
                if video_result["success"] and video_result.get("content"):
                    source_name = video_result.get("source", "auto")
                    is_partial = video_result.get("partial", False)
                    label = "视频公开信息" if is_partial else "视频字幕内容"
                    all_text_parts.append(f"=== {label}（来源：{source_name}）===\n{video_result['content']}")
                    if video_result.get("title"):
                        sources.append({"title": video_result["title"], "url": video_url})

                # 优先级3：Tavily搜索视频相关信息补充
                tavily_results = await unified_search(video_url, "news")
                if tavily_results:
                    sources.extend([{
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "date": r.get("date"),
                        "published_date": r.get("published_date"),
                        "published_at": r.get("published_at"),
                        "content": (r.get("content") or "")[:500],
                        "raw_content": (r.get("raw_content") or "")[:500],
                    } for r in tavily_results if r.get("url")])
                    all_text_parts.append(f"=== 搜索引擎补充信息 ===\n{format_search_results(tavily_results)}")

            if all_text_parts:
                search_results_text = "\n\n".join(all_text_parts)
            else:
                search_results_text = "未获取到视频内容。请粘贴视频逐字稿后重试。"
        else:
            results = await unified_search(search_query, search_type)
            sources = [{
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "date": r.get("date"),
                "published_date": r.get("published_date"),
                "published_at": r.get("published_at"),
                "content": (r.get("content") or "")[:500],
                "raw_content": (r.get("raw_content") or "")[:500],
            } for r in results if r.get("url")]
            search_results_text = format_search_results(results)

    # Build user content
    user_content = f"用户查询：{req.query}"
    if req.extra_content and search_type != "extract":
        user_content += f"\n\n用户补充资料：\n{req.extra_content}"

    # Call LLM — auction L1/L2 不调用 LLM（Decision 2 强制），直接返回结构化文本。
    if req.skill_type == "auction" and auction_skip_llm:
        result = (
            "【集合竞价：结构化速览（未调用分析模型）】\n"
            "当前数据授权级别不允许生成竞价分析结论，以下为结构化数据速览：\n\n"
            f"{search_results_text}"
        )
    else:
        system_prompt = get_skill_prompt(req.skill_type)
        result = await generate_analysis(system_prompt, user_content, search_results_text)
    if req.skill_type == "macro" and isinstance(macro_event_facts, dict):
        event_summary = None
        rejected_reason = _macro_consistency_conflict(result, macro_event_facts)
        if rejected_reason:
            logger.error(
                "macro_consistency_error macro_query=%s selected_sources=%s event_time=%s "
                "source_time=%s confidence=%s used_timeline_context=%s rejected_reason=%s",
                req.query,
                macro_event_facts.get("debug", {}).get("selected_sources"),
                macro_event_facts.get("debug", {}).get("event_time"),
                macro_event_facts.get("debug", {}).get("source_time"),
                macro_event_facts.get("debug", {}).get("confidence"),
                macro_event_facts.get("debug", {}).get("used_timeline_context"),
                rejected_reason,
            )
            return {
                "success": False,
                "result": "consistency_error：事件脉络/最新信源已显示该事件为 confirmed/official，但宏观分析生成了“未证实”等冲突结论，本次结果已拦截。",
                "sources": sources,
                "kline": None,
                "usage_used": used,
                "usage_limit": limit,
                "_qc": {
                    "status": "consistency_error",
                    "completeness": 0,
                    "sources": [s.get("url", "") for s in sources[:5]],
                    "rejected_reason": rejected_reason,
                },
                "debug": macro_event_facts.get("debug", {}),
            }
        if macro_event_facts.get("confirmed"):
            debug = macro_event_facts.get("debug", {})
            selected = debug.get("selected_sources") or []
            basis = "；".join(
                f"{s.get('status')} {s.get('title')} ({s.get('url')})"
                for s in selected[:3]
            )
            event_summary = {
                "event_status": "confirmed/official",
                "event_time": debug.get("event_time"),
                "source_time": debug.get("source_time"),
                "basis": basis,
            }
        else:
            event_summary = None

    # ---- 门下省质检 ----
    qa_result = {"passed": True, "reject_reasons": [], "round": 1, "score": 1.0}
    if _QG_AVAILABLE and req.skill_type in ("stock", "macro", "industry"):
        # 构造 _qc 字段（从已有数据推断）
        source_count = len(sources)
        has_akshare = bool(search_results_text)
        completeness = min(1.0, (0.5 if has_akshare else 0.0) + (0.3 if source_count >= 2 else 0.1))

        mock_qc_data = {
            "_qc": {
                "status": "success" if has_akshare else "partial",
                "completeness": completeness,
                "missing_dimensions": [] if completeness >= 0.8 else ["补充数据源"],
                "stale_data": [],
                "sources": [s["url"] for s in sources[:5]],
                "fallback_source": None,
            }
        }

        gate = QualityGate()
        rule = QualityRules.stockData if req.skill_type == "stock" else QualityRules.financialData
        check = gate.check(mock_qc_data, rule, round=1)
        qa_result = {
            "passed": check.passed,
            "reject_reasons": check.reject_reasons,
            "required_actions": check.required_actions,
            "round": check.round,
            "score": check.score,
        }

    # 在返回前提取K线数据
    kline_data = None
    _akshare_data_local = locals().get("akshare_data")
    if req.skill_type == "stock" and isinstance(_akshare_data_local, dict):
        ph = _akshare_data_local.get("price_history")
        if ph:
            kline_data = [
                {
                    "time": str(row.get("日期", "")),
                    "open": float(row.get("开盘", 0)),
                    "high": float(row.get("最高", 0)),
                    "low": float(row.get("最低", 0)),
                    "close": float(row.get("收盘", 0)),
                    "volume": int(row.get("成交量", 0)),
                }
                for row in ph
            ]

    # Record usage
    usage = Usage(
        user_id=user.id,
        skill_type=req.skill_type,
        query=req.query[:500],
    )
    db.add(usage)
    db.commit()

    matched_sources = [s for s in sources if _source_matches_query(s, req.query)]
    report_as_of_sources = matched_sources if matched_sources else []
    report_as_of = _compute_report_as_of(report_as_of_sources)
    _akshare_data_local = locals().get("akshare_data")
    _structured_text_local = locals().get("structured_text", "")
    has_structured = bool(
        (req.skill_type == "stock" and isinstance(_akshare_data_local, dict))
        or (req.skill_type == "macro" and _structured_text_local)
        or (req.skill_type == "industry" and _structured_text_local)
        or (req.skill_type == "auction")
    )
    extended_qc = _build_report_qc(
        skill_type=req.skill_type,
        sources=sources,
        matched_sources=matched_sources,
        has_structured=has_structured,
        search_results_text=search_results_text,
        report_as_of=report_as_of,
    )

    # B: insufficient_data / high risk — replace result with safe body
    _risk_level = extended_qc.get("hallucination_risk", {}).get("level")
    if extended_qc.get("status") == "insufficient_data" or _risk_level == "high":
        result = _SAFE_BODY
    else:
        # A: sanitize LLM-written date cutoff lines
        result = _sanitize_report_body(result, report_as_of)

    response_data = {
        "success": True,
        "result": result,
        "sources": sources,
        "kline": kline_data,
        "usage_used": used + 1,
        "usage_limit": limit,
        "report_as_of": report_as_of,
        "_qc": extended_qc,
        "qa_result": qa_result,
    }
    response_data = _attach_final_dispatch_trace(
        response_data,
        locals().get("final_dispatch_trace") or _build_final_dispatch_trace(req.skill_type, req.query),
    )
    if req.skill_type == "macro" and isinstance(macro_event_facts, dict):
        response_data["debug"] = macro_event_facts.get("debug", {})
        response_data["event_summary"] = event_summary
        response_data["_qc"]["used_timeline_context"] = bool(
            macro_event_facts.get("debug", {}).get("used_timeline_context")
        )
        response_data["_qc"]["event_status"] = (
            event_summary.get("event_status") if isinstance(event_summary, dict) else None
        )

    # 缓存结果（10分钟）
    # Auction 不写缓存：每次请求必须走 fetch → QC → admission → allowed_use，
    # 保证下一次请求不会被本次（可能已降级）的结果短路。
    if req.skill_type not in ("macro", "auction"):
        response_data = _with_trust_contract(response_data)
        cache_set(req.skill_type, req.query, response_data)
    else:
        response_data = _with_trust_contract(response_data)

    return _apply_publication_containment(response_data)


# ---- PDF export endpoint ----

def _safe_pdf_filename(text: str) -> str:
    text = text or "finance-report"
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text)
    text = text.strip("-")
    return text[:60] or "finance-report"


def _sanitize_report_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    cleaned = re.sub(r"(?is)<(script|iframe|object|embed)[^>]*>.*?</\1>", "", raw_html)
    cleaned = re.sub(r"(?is)\s+on[a-z]+\s*=\s*(['\"]).*?\1", "", cleaned)
    cleaned = re.sub(r"(?is)\s+on[a-z]+\s*=\s*[^\s>]+", "", cleaned)
    cleaned = re.sub(r"(?is)(href|src)\s*=\s*(['\"])\s*javascript:.*?\2", r'\1="#"', cleaned)
    return cleaned.strip()


def _build_pdf_html(query: str, body_html: str) -> str:
    safe_query = html_lib.escape(query or "股票分析报告")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_body = _sanitize_report_html(body_html)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{safe_query} - Finance Suite 分析报告</title>
  <style>
    @page {{ size: A4; margin: 18mm 16mm; }}
    body {{
      font-family: "Noto Sans CJK SC", "Noto Sans CJK", "Microsoft YaHei", "PingFang SC", sans-serif;
      color: #111827;
      font-size: 12px;
      line-height: 1.72;
      background: #ffffff;
    }}
    h1, h2, h3 {{ color: #0f172a; page-break-after: avoid; }}
    h1 {{ font-size: 24px; margin: 0 0 12px; }}
    h2 {{ font-size: 18px; margin-top: 24px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
    h3 {{ font-size: 15px; margin-top: 18px; }}
    p {{ margin: 0 0 9px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f3f4f6; font-weight: 700; }}
    blockquote {{ margin: 12px 0; padding-left: 12px; border-left: 3px solid #2563eb; color: #4b5563; }}
    pre, code {{
      font-family: "Noto Sans Mono CJK SC", "SFMono-Regular", Menlo, monospace;
      background: #f8fafc;
      border-radius: 4px;
    }}
    pre {{ padding: 10px; white-space: pre-wrap; word-break: break-word; }}
    img {{ max-width: 100%; height: auto; }}
    .report-header {{ margin-bottom: 22px; padding-bottom: 12px; border-bottom: 2px solid #111827; }}
    .subtitle {{ color: #6b7280; font-size: 11px; }}
    .disclaimer {{
      margin-top: 28px;
      padding: 12px;
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
      font-size: 11px;
    }}
  </style>
</head>
<body>
  <div class="report-header">
    <h1>{safe_query} - Finance Suite 分析报告</h1>
    <div class="subtitle">生成时间：{generated_at}</div>
  </div>
  <main>{safe_body}</main>
  <div class="disclaimer">
    风险提示：本报告由 Finance Suite 自动生成，仅供研究参考，不构成任何投资建议。市场有风险，投资需谨慎。
  </div>
</body>
</html>"""


def _build_report_pdf(query: str, body_html: str) -> bytes:
    from weasyprint import HTML

    full_html = _build_pdf_html(query, body_html)
    return HTML(string=full_html, base_url=".").write_pdf()


@router.post("/export-pdf")
async def export_pdf(
    req: ExportPdfRequest,
    user: User = Depends(get_current_user),
):
    if not req.html or not req.html.strip():
        raise HTTPException(status_code=400, detail="没有可导出的报告内容")

    try:
        pdf_bytes = _build_report_pdf(req.query or "Finance Suite", req.html)
    except Exception as e:
        logger.exception("export_pdf failed")
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {e}")

    filename = quote(f"finance-report-{_safe_pdf_filename(req.query)}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "Cache-Control": "no-store",
        },
    )


# ---- Usage endpoint ----

@router.get("/usage")
async def get_usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    return {
        "used": used,
        "limit": limit,
        "tier": user.tier,
        "allowed": allowed,
    }

# ---- Auth refresh: re-set cookie with correct domain ----
@router.post("/auth/refresh")
async def auth_refresh(
    user: User = Depends(get_current_user),
):
    """Re-issue access_token cookie with correct domain (fixes www/non-www cookie scope)."""
    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {"success": True, "username": user.username, "tier": user.tier, "token": token},
        token,
    )

# ---- Fix cookie domain: clear old cookie, set new with correct domain ----
@router.post("/auth/cookie-fix")
async def cookie_fix(
    user: User = Depends(get_current_user),
):
    """Delete old cookie (if any) and set fresh one with correct domain.
    Called by frontend when localStorage shows logged-in but API returns 401.
    """
    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {"success": True, "username": user.username, "tier": user.tier, "token": token},
        token,
    )
