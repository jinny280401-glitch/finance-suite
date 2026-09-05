"""
Macro event fact pre-check service.
Extracted from routers/api.py — handles event source verification and fact extraction.
"""
import logging
import re

from backend.engine.providers.search_provider import unified_search

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TRUSTED_EVENT_SOURCE_KEYWORDS = (
    "外交部",
    "新华社",
    "国务院",
    "央视",
    "人民日报",
    "Reuters",
    "AP News",
    "Bloomberg",
    "官方",
    "证实",
    "确认",
)

_TRUSTED_EVENT_DOMAINS = (
    "mfa.gov.cn",
    "xinhuanet.com",
    "gov.cn",
    "reuters.com",
    "apnews.com",
    "bloomberg.com",
)

_CONFIRMED_EVENT_TERMS = (
    "确认",
    "证实",
    "达成",
    "签署",
    "宣布",
    "正式",
    "confirmed",
    "announced",
    "agreed",
    "signed",
)

_MACRO_CONFLICT_TERMS = (
    "未证实",
    "不实",
    "假消息",
    "谣言",
    "未确认",
    "无法证实",
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


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


def event_status(item: dict) -> str:
    """Determine the verification status of an event item."""
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


def event_query_for_macro(query: str) -> str:
    """Build an optimized search query for macro event fact lookup."""
    q = (query or "").strip()
    if re.search(r"(特朗普|Trump|trump).*(访华|中国|来华)|访华.*(特朗普|Trump|trump)", q, re.I):
        return "特朗普 访华 5月13日 15日 外交部 新华社 Reuters official confirmed"
    return f"{q} 最新 事件 官方 证实 外交部 新华社 Reuters"


def macro_event_facts_from_results(query: str, results: list[dict]) -> dict:
    """Extract structured event facts from search results."""
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
        status = event_status(item)
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


async def fetch_macro_event_facts(query: str) -> dict:
    """Fetch and verify macro event facts via news search."""
    event_query = event_query_for_macro(query)
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
    facts = macro_event_facts_from_results(query, results if isinstance(results, list) else [])
    logger.info("macro_event_facts %s", facts["debug"])
    return facts


def macro_consistency_conflict(result: str, facts: dict) -> str | None:
    """Check if the analysis result conflicts with confirmed event facts."""
    if not facts.get("confirmed"):
        return None
    text = result or ""
    for term in _MACRO_CONFLICT_TERMS:
        if term in text:
            return f"timeline_confirmed_but_macro_said_{term}"
    return None
