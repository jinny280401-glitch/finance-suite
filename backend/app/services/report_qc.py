"""
Report QC (Quality Check) + Trust Contract + Publication Containment service.
Extracted from routers/api.py — handles report quality assessment and publishing controls.
"""
import re
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATE_CUTOFF_PATTERN = re.compile(
    r"数据截止[：:][^\n]*\n"
)

_SAFE_BODY = """\
公开资料不足，无法生成可靠的分析报告。

当前搜索结果未能提供足够的结构化数据支撑，报告内容可能主要来自模型训练知识，\
存在较高的幻觉风险。

建议：
1. 补充更具体的查询关键词
2. 提供更详细的背景资料
3. 使用结构化数据源（如 AkShare 行情数据）
"""

_TRUST_DIMENSIONS = (
    "fundamental",
    "realtime",
    "news",
    "research",
    "market_context",
)

_PUBLICATION_SAFETY_LABEL = "TEMPORARY PUBLICATION SAFETY / NOT TRUST GATE"

_PUBLICATION_CONCLUSION_POLICY = {
    "valuation": {
        "rules": [
            ("dcf", r"(?:DCF|现金流折现|内在价值|估值模型)"),
            ("pe_target", r"(?:目标价|目标价[格]?|估值.*(?:元|倍))"),
            ("premium_discount", r"(?:溢价|折价|低估|高估|合理估值)"),
        ],
    },
    "realtime": {
        "rules": [
            ("intraday_call", r"(?:今日.*(?:买入|卖出|加仓|减仓))"),
            ("live_signal", r"(?:实时.*信号|盘面.*(?:建议|操作))"),
        ],
    },
    "fund_flow": {
        "rules": [
            ("flow_direction", r"(?:主力.*(?:流入|流出|净买入|净卖出))"),
            ("smart_money", r"(?:聪明钱|北向资金.*(?:大幅|持续))"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Report sanitization
# ---------------------------------------------------------------------------


def sanitize_report_body(result: str, report_as_of: dict) -> str:
    """Remove LLM-written date cutoff lines and replace with system-generated line."""
    if not result:
        return result
    if report_as_of.get("source_date_unknown"):
        replacement = f"数据截止：未能从信源确认，系统生成日期：{date.today().isoformat()}\n"
    else:
        replacement = f"数据截止：{report_as_of['date']}\n"
    return _DATE_CUTOFF_PATTERN.sub(replacement, result)


def normalize_entity_name(text: str) -> str:
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


def source_matches_query(source: dict, query: str) -> bool:
    """Return True only when a source strongly matches the requested entity."""
    raw_query = (query or "").strip()
    if not raw_query:
        return False
    source_text = " ".join(
        str(source.get(k, "") or "") for k in ("title", "content", "raw_content")
    )
    if raw_query in source_text:
        return True
    normalized_query = normalize_entity_name(raw_query)
    normalized_source = normalize_entity_name(source_text)
    return bool(normalized_query and normalized_query in normalized_source)


def compute_report_as_of(sources: list[dict]) -> dict:
    """Extract latest published date from Tavily sources. Falls back to today with flag."""
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


# ---------------------------------------------------------------------------
# Report number validation (Phase 2c)
# ---------------------------------------------------------------------------


def _extract_key_numbers(kline_data: list[dict] | None, structured_text: str = "") -> dict[str, float]:
    """从结构化数据中提取关键数字，供报告比对。
    返回 {label: value}，如 {"latest_close": 123.45}
    """
    result: dict[str, float] = {}
    if not kline_data:
        return result
    # K线最新收盘价
    last = kline_data[-1] if kline_data else None
    if last and isinstance(last, dict):
        close = last.get("close")
        if close is not None:
            try:
                result["latest_close"] = float(close)
            except (ValueError, TypeError):
                pass
    return result


def _extract_report_numbers(report_text: str) -> dict[str, float]:
    """从 LLM 报告文本中提取关键数字。
    使用启发式规则提取价格、涨跌幅等。
    """
    result: dict[str, float] = {}
    if not report_text:
        return result
    # 提取「最新价/收盘价/现价 XX.XX 元」模式
    price_match = re.search(r"(?:最新价|收盘价|现价|股价)[^\d]{0,5}(\d+\.?\d*)\s*(?:元)?", report_text)
    if price_match:
        try:
            result["latest_close"] = float(price_match.group(1))
        except (ValueError, TypeError):
            pass
    return result


def check_report_numbers(report_text: str, kline_data: list[dict] | None) -> dict:
    """比对 LLM 报告中的数字与结构化数据。
    返回 {"checked": int, "mismatches": list[str], "match_rate": float}
    """
    expected = _extract_key_numbers(kline_data)
    reported = _extract_report_numbers(report_text)

    mismatches: list[str] = []
    checked = 0
    for key, exp_val in expected.items():
        rep_val = reported.get(key)
        if rep_val is None:
            continue  # 报告未提及，不算不匹配
        checked += 1
        if exp_val != 0 and abs(rep_val - exp_val) / abs(exp_val) > 0.10:
            mismatches.append(f"{key}: 数据={exp_val}, 报告={rep_val} (偏差{abs(rep_val - exp_val) / abs(exp_val) * 100:.0f}%)")

    match_rate = (checked - len(mismatches)) / checked if checked > 0 else 1.0
    return {
        "checked": checked,
        "mismatches": mismatches,
        "match_rate": round(match_rate, 2),
    }


# ---------------------------------------------------------------------------
# Extended QC
# ---------------------------------------------------------------------------


def build_report_qc(
    skill_type: str,
    sources: list[dict],
    matched_sources: list[dict],
    has_structured: bool,
    search_results_text: str,
    report_as_of: dict,
    dimension_status: dict | None = None,
    stale_data: list[str] | None = None,
) -> dict:
    """Build extended _qc: freshness / fact_coverage / hallucination_risk / dimension_status."""
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
        "missing_dimensions": [dim for dim, st in (dimension_status or {}).items() if st == "missing"],
        "dimension_status": dimension_status or {},
        "stale_data": stale_data or [],
        "freshness": freshness,
        "fact_coverage": fact_coverage,
        "hallucination_risk": hallucination_risk,
    }


# ---------------------------------------------------------------------------
# Trust Contract
# ---------------------------------------------------------------------------


def trust_availability_entry(status: str, available: list[str] | None = None, missing: list[str] | None = None, source_type: str = "derived", latency_ms: int | None = None) -> dict:
    return {
        "status": status,
        "available": available or [],
        "missing": missing or [],
        "as_of": datetime.now().replace(microsecond=0).isoformat() if available else None,
        "source_type": source_type,
        "latency_ms": latency_ms,
    }


def build_analyze_data_availability(response: dict) -> dict:
    qc = response.get("_qc") or {}
    fact = qc.get("fact_coverage") or {}
    has_structured = bool(fact.get("structured_data_available") or response.get("kline"))
    has_sources = bool(response.get("sources") or qc.get("sources"))
    has_result = bool(response.get("result"))
    source_type = "real" if (has_structured or has_sources) else "missing"

    availability = {
        key: trust_availability_entry("unavailable", missing=[key], source_type="missing")
        for key in _TRUST_DIMENSIONS
    }

    availability["fundamental"] = trust_availability_entry(
        "partial" if has_structured else "unavailable",
        available=["structured_financial_or_kline"] if has_structured else [],
        missing=[] if has_structured else ["fundamental"],
        source_type=source_type if has_structured else "missing",
    )
    availability["realtime"] = trust_availability_entry(
        "partial" if response.get("kline") else "unavailable",
        available=["kline"] if response.get("kline") else [],
        missing=[] if response.get("kline") else ["realtime"],
        source_type="real" if response.get("kline") else "missing",
    )
    availability["news"] = trust_availability_entry(
        "partial" if has_sources else "unavailable",
        available=["search_sources"] if has_sources else [],
        missing=[] if has_sources else ["news"],
        source_type="real" if has_sources else "missing",
    )
    availability["research"] = trust_availability_entry(
        "partial" if has_sources else "unavailable",
        available=["search_sources"] if has_sources else [],
        missing=[] if has_sources else ["research"],
        source_type="real" if has_sources else "missing",
    )
    availability["market_context"] = trust_availability_entry(
        "partial" if has_result else "unavailable",
        available=["report_context"] if has_result else [],
        missing=[] if has_result else ["market_context"],
        source_type="derived" if has_result else "missing",
    )
    return availability


def with_trust_contract(response: dict) -> dict:
    if not isinstance(response, dict):
        return response
    data_availability = response.get("data_availability")
    if not isinstance(data_availability, dict):
        data_availability = build_analyze_data_availability(response)
        response["data_availability"] = data_availability

    if "section_data_usage" not in response:
        response["section_data_usage"] = {}

    qc = response.setdefault("_qc", {})
    if isinstance(qc, dict):
        qc.setdefault("data_availability", data_availability)
        qc.setdefault("section_data_usage", response.get("section_data_usage"))
    return response


# ---------------------------------------------------------------------------
# Publication Containment
# ---------------------------------------------------------------------------


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


def apply_publication_containment(response: dict) -> dict:
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
