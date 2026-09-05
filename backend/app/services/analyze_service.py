"""
Analyze service — orchestrates data fetching, LLM calls, QC, Trust, and publication.
Extracted from routers/api.py analyze() endpoint.
"""
import asyncio
import logging
from backend.engine.providers.search_provider import unified_search, format_search_results
from backend.engine.llm.client import generate_analysis
from backend.engine.cache import cache_get, cache_set
from backend.engine.registry import ScenarioRegistry, normalize_scenario_type
from backend.engine.quality.core import QualityGate
from backend.engine.quality.rules import QualityRules

_QG_AVAILABLE = True
from backend.app.services.event_facts import (
    fetch_macro_event_facts,
    macro_consistency_conflict,
)
from backend.app.services.report_qc import (
    build_report_qc,
    sanitize_report_body,
    source_matches_query,
    compute_report_as_of,
    with_trust_contract,
    apply_publication_containment,
    normalize_entity_name,
    check_report_numbers,
)

logger = logging.getLogger(__name__)

# Safe body for insufficient data
_SAFE_BODY = """\
公开资料不足，无法生成可靠的分析报告。

当前搜索结果未能提供足够的结构化数据支撑，报告内容可能主要来自模型训练知识，\
存在较高的幻觉风险。

建议：
1. 补充更具体的查询关键词
2. 提供更详细的背景资料
3. 使用结构化数据源（如 AkShare 行情数据）
"""


def _build_final_dispatch_trace(
    skill_type: str,
    input_text: str,
    resolved_name: str | None = None,
    resolved_symbol: str | None = None,
    resolver_source: str | None = None,
    matched_text: str | None = None,
) -> dict:
    selected_route = normalize_scenario_type(skill_type or "")
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


async def _fetch_stock_data(query: str, search_query: str):
    """Fetch stock data: AkShare structured + Tavily search."""
    from backend.engine.skills.stock_skill import resolve_stock, get_stock_full_data, format_stock_data, resolve_stock_detail
    from backend.engine.providers.search_provider import multi_search_stock, format_search_results_grouped

    loop = asyncio.get_event_loop()
    resolver_source = None
    matched_text = None

    # Step 1: Resolve stock name/code
    try:
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
        "stock",
        query,
        resolved_name=stock_name,
        resolved_symbol=stock_code,
        resolver_source=resolver_source,
        matched_text=matched_text,
    )

    # Step 2: Concurrent fetch AkShare + Tavily
    akshare_task = get_stock_full_data(stock_code)
    tavily_task = multi_search_stock(f"{stock_name} {stock_code}")
    akshare_data, tavily_results = await asyncio.gather(
        akshare_task, tavily_task, return_exceptions=True
    )

    sources = []
    structured_text = ""
    if isinstance(akshare_data, dict):
        structured_text = format_stock_data(akshare_data, stock_name, stock_code)
        ak_news = akshare_data.get("news") or []
        for n in ak_news[:5]:
            if n.get("url"):
                sources.append({"title": n.get("title", ""), "url": n["url"]})

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

    search_results_text = structured_text
    if search_text:
        search_results_text += f"\n\n=== 搜索引擎补充信息 ===\n{search_text}"

    # Extract kline
    kline_data = None
    if isinstance(akshare_data, dict):
        ph = akshare_data.get("price_history")
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

    has_structured = isinstance(akshare_data, dict)

    # ---- 维度级 QC：检查每个数据维度的可用性和时效 ----
    dimension_status = {}
    stale_data = []
    if isinstance(akshare_data, dict):
        from datetime import date as _date
        _today = _date.today()
        # 各维度时效阈值（天）
        _stale_thresholds = {
            "price_history": 3,
            "fund_flow": 3,
            "realtime": 1,
            "financials": 90,
            "news": 7,
        }
        for dim in ("financials", "price_history", "fund_flow", "news", "dividends", "realtime", "valuation"):
            raw = akshare_data.get(dim)
            if dim == "realtime":
                # realtime_availability 由 stock_skill 提供
                rt_avail = akshare_data.get("realtime_availability", {})
                has_data = rt_avail.get("status") == "available"
            else:
                has_data = bool(raw and ((isinstance(raw, list) and len(raw) > 0) or (isinstance(raw, dict) and len(raw) > 0)))
            dimension_status[dim] = "available" if has_data else "missing"
            # 时效检查：从数据中提取最新日期
            if has_data and dim in _stale_thresholds:
                data_date_str = None
                records = raw if isinstance(raw, list) else []
                for row in reversed(records):
                    if isinstance(row, dict):
                        for key in ("日期", "date", "Date"):
                            val = row.get(key)
                            if val:
                                data_date_str = str(val)[:10]
                                break
                    if data_date_str:
                        break
                if data_date_str:
                    try:
                        data_date = _date.fromisoformat(data_date_str)
                        days_old = (_today - data_date).days
                        threshold = _stale_thresholds[dim]
                        if days_old > threshold:
                            stale_data.append(f"{dim}: {data_date_str} ({days_old}天前, 阈值{threshold}天)")
                    except (ValueError, TypeError):
                        pass

    return {
        "search_results_text": search_results_text,
        "sources": sources,
        "kline_data": kline_data,
        "has_structured": has_structured,
        "final_dispatch_trace": final_dispatch_trace,
        "dimension_status": dimension_status,
        "stale_data": stale_data,
    }


async def _fetch_macro_data(search_query: str):
    """Fetch macro data: AkShare macro + Tavily + event facts."""
    from backend.engine.skills.macro_skill import get_macro_data, format_macro_data

    macro_task = get_macro_data()
    tavily_task = unified_search(search_query, "news")
    event_facts_task = fetch_macro_event_facts(search_query)
    macro_data, tavily_results, macro_event_facts = await asyncio.gather(
        macro_task, tavily_task, event_facts_task, return_exceptions=True
    )

    sources = []
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

    return {
        "search_results_text": search_results_text,
        "sources": sources,
        "macro_event_facts": macro_event_facts if isinstance(macro_event_facts, dict) else None,
        "has_structured": bool(structured_text),
    }


async def _fetch_auction_data():
    """Fetch auction data with QC."""
    from backend.engine.skills.auction_skill import (
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

    auction_skip_llm = not auction_allows_llm(auction_allowed_use)

    return {
        "search_results_text": search_results_text,
        "sources": [],
        "auction_skip_llm": auction_skip_llm,
        "has_structured": True,
    }


async def _fetch_industry_data(query: str, search_query: str):
    """Fetch industry data: AkShare industry board + Tavily search."""
    async def fetch_industry_ak():
        loop = asyncio.get_event_loop()
        try:
            import akshare as ak
            df = await loop.run_in_executor(
                None, ak.stock_board_industry_name_em
            )
            if df is not None:
                matched = df[df["板块名称"].str.contains(query, na=False)]
                if len(matched) > 0:
                    return matched.head(5).to_dict(orient="records")
        except Exception:
            pass
        return None

    ak_task = fetch_industry_ak()
    tavily_task = unified_search(search_query, "industry")
    ak_data, tavily_results = await asyncio.gather(
        ak_task, tavily_task, return_exceptions=True
    )

    sources = []
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

    return {
        "search_results_text": search_results_text,
        "sources": sources,
        "has_structured": bool(structured_text),
    }


async def _fetch_video_data(query: str, extra_content: str):
    """Fetch video content: transcript extraction + search supplement."""
    from backend.engine.skills.video_skill import get_video_content

    video_url = extra_content.strip() if extra_content else ""
    video_query = query.strip()
    has_transcript = video_query and video_query != "请拆解分析这个视频内容"

    sources = []
    all_text_parts = []

    if has_transcript:
        all_text_parts.append(f"=== 用户提供的逐字稿 ===\n{video_query}")

    if video_url:
        video_result = await get_video_content(video_url)
        if video_result["success"] and video_result.get("content"):
            source_name = video_result.get("source", "auto")
            is_partial = video_result.get("partial", False)
            label = "视频公开信息" if is_partial else "视频字幕内容"
            all_text_parts.append(f"=== {label}（来源：{source_name}）===\n{video_result['content']}")
            if video_result.get("title"):
                sources.append({"title": video_result["title"], "url": video_url})

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

    return {
        "search_results_text": search_results_text,
        "sources": sources,
        "has_structured": False,
    }


async def _fetch_generic_data(search_query: str, search_type: str):
    """Generic search fallback for other skill types."""
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

    return {
        "search_results_text": search_results_text,
        "sources": sources,
        "has_structured": False,
    }


async def run_analysis(
    skill_type: str,
    query: str,
    extra_content: str = "",
    scenario_config=None,  # engine.registry.ScenarioConfig（可选，Pipeline 传入）
) -> dict:
    """
    Main analysis orchestration.
    Returns the full response dict (without usage fields — caller adds these).

    Args:
        scenario_config: 可选 ScenarioConfig，Pipeline 传入时使用配置驱动的 prompt/QC。
    """
    skill = ScenarioRegistry().get_metadata(skill_type)
    if not skill:
        return {"error": "未知的分析技能"}

    search_type = skill.get("search_type")
    search_query = query
    sources = []
    kline_data = None
    macro_event_facts = None
    event_summary = None
    final_dispatch_trace = None
    has_structured = False

    # ---- Data fetching by skill type ----
    if search_type:
        if skill_type == "stock":
            data = await _fetch_stock_data(query, search_query)
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            kline_data = data["kline_data"]
            has_structured = data["has_structured"]
            final_dispatch_trace = data["final_dispatch_trace"]
            dimension_status = data.get("dimension_status", {})
            stale_data = data.get("stale_data", [])

        elif skill_type == "macro":
            data = await _fetch_macro_data(search_query)
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            macro_event_facts = data["macro_event_facts"]
            has_structured = data["has_structured"]

        elif skill_type == "auction":
            data = await _fetch_auction_data()
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            has_structured = data["has_structured"]
            auction_skip_llm = data["auction_skip_llm"]

        elif skill_type == "industry":
            data = await _fetch_industry_data(query, search_query)
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            has_structured = data["has_structured"]

        elif skill_type == "video":
            data = await _fetch_video_data(query, extra_content)
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            has_structured = data["has_structured"]

        else:
            data = await _fetch_generic_data(search_query, search_type)
            search_results_text = data["search_results_text"]
            sources = data["sources"]
            has_structured = data["has_structured"]
    else:
        search_results_text = ""

    # ---- Build user content ----
    user_content = f"用户查询：{query}"
    if extra_content and search_type != "extract":
        user_content += f"\n\n用户补充资料：\n{extra_content}"

    # ---- Call LLM ----
    auction_skip_llm = locals().get("auction_skip_llm", False)
    if skill_type == "auction" and auction_skip_llm:
        result = (
            "【集合竞价：结构化速览（未调用分析模型）】\n"
            "当前数据授权级别不允许生成竞价分析结论，以下为结构化数据速览：\n\n"
            f"{search_results_text}"
        )
    else:
        # Prompt: 优先使用 scenario_config.prompt（配置驱动），否则从 ScenarioRegistry 加载
        if scenario_config and scenario_config.prompt:
            system_prompt = scenario_config.prompt
        else:
            _scenario = ScenarioRegistry().get(skill_type)
            system_prompt = _scenario.prompt if _scenario else ""
        result = await generate_analysis(system_prompt, user_content, search_results_text)

    # ---- Macro consistency check ----
    if skill_type == "macro" and isinstance(macro_event_facts, dict):
        rejected_reason = macro_consistency_conflict(result, macro_event_facts)
        if rejected_reason:
            logger.error(
                "macro_consistency_error macro_query=%s selected_sources=%s event_time=%s "
                "source_time=%s confidence=%s used_timeline_context=%s rejected_reason=%s",
                query,
                macro_event_facts.get("debug", {}).get("selected_sources"),
                macro_event_facts.get("debug", {}).get("event_time"),
                macro_event_facts.get("debug", {}).get("source_time"),
                macro_event_facts.get("debug", {}).get("confidence"),
                macro_event_facts.get("debug", {}).get("used_timeline_context"),
                rejected_reason,
            )
            return {
                "success": False,
                "result": "consistency_error：事件脉络/最新信源已显示该事件为 confirmed/official，但宏观分析生成了\u201c未证实\u201d等冲突结论，本次结果已拦截。",
                "sources": sources,
                "kline": None,
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

    # ---- 维度状态和 stale_data（非 stock 场景默认空） ----
    dimension_status = locals().get("dimension_status") or {}
    stale_data = locals().get("stale_data") or []
    missing_dimensions = [dim for dim, status in dimension_status.items() if status == "missing"] if dimension_status else []

    # ---- Quality Gate (门下省质检) ----
    qa_result = {"passed": True, "reject_reasons": [], "round": 1, "score": 1.0}
    if _QG_AVAILABLE and skill_type in ("stock", "macro", "industry"):
        source_count = len(sources)
        has_akshare = bool(search_results_text)
        # 用真实维度数据计算 completeness
        if dimension_status:
            available_count = sum(1 for s in dimension_status.values() if s == "available")
            total_count = len(dimension_status) or 1
            completeness = round(available_count / total_count, 2)
        else:
            completeness = min(1.0, (0.5 if has_akshare else 0.0) + (0.3 if source_count >= 2 else 0.1))

        mock_qc_data = {
            "_qc": {
                "status": "success" if has_akshare else "partial",
                "completeness": completeness,
                "missing_dimensions": missing_dimensions,
                "stale_data": stale_data,
                "sources": [s["url"] for s in sources[:5]],
                "fallback_source": None,
            }
        }

        gate = QualityGate()
        rule = QualityRules.stockData if skill_type == "stock" else QualityRules.financialData
        check = gate.check(mock_qc_data, rule, round=1)
        qa_result = {
            "passed": check.passed,
            "reject_reasons": check.reject_reasons,
            "required_actions": check.required_actions,
            "round": check.round,
            "score": check.score,
        }

    # ---- Post-processing: QC, sanitize, trust, publication ----
    matched_sources = [s for s in sources if source_matches_query(s, query)]
    report_as_of = compute_report_as_of(matched_sources if matched_sources else [])
    extended_qc = build_report_qc(
        skill_type=skill_type,
        sources=sources,
        matched_sources=matched_sources,
        has_structured=has_structured,
        search_results_text=search_results_text,
        report_as_of=report_as_of,
        dimension_status=dimension_status,
        stale_data=stale_data,
    )

    _risk_level = extended_qc.get("hallucination_risk", {}).get("level")
    if extended_qc.get("status") == "insufficient_data" or _risk_level == "high":
        result = _SAFE_BODY
    else:
        result = sanitize_report_body(result, report_as_of)

    # ---- 报告数字校验（Phase 2c）----
    number_check = check_report_numbers(result if isinstance(result, str) else "", kline_data)
    if isinstance(extended_qc, dict):
        extended_qc["number_validation"] = number_check

    response_data = {
        "success": True,
        "result": result,
        "sources": sources,
        "kline": kline_data,
        "report_as_of": report_as_of,
        "_qc": extended_qc,
        "qa_result": qa_result,
    }

    response_data = _attach_final_dispatch_trace(
        response_data,
        final_dispatch_trace or _build_final_dispatch_trace(skill_type, query),
    )

    if skill_type == "macro" and isinstance(macro_event_facts, dict):
        response_data["debug"] = macro_event_facts.get("debug", {})
        response_data["event_summary"] = event_summary
        response_data["_qc"]["used_timeline_context"] = bool(
            macro_event_facts.get("debug", {}).get("used_timeline_context")
        )
        response_data["_qc"]["event_status"] = (
            event_summary.get("event_status") if isinstance(event_summary, dict) else None
        )

    response_data = with_trust_contract(response_data)

    # Cache (not macro/auction)
    if skill_type not in ("macro", "auction"):
        cache_set(skill_type, query, response_data)

    return apply_publication_containment(response_data)


def get_cached_result(skill_type: str, query: str) -> dict | None:
    """Get cached analysis result if available."""
    if skill_type in ("macro", "auction"):
        return None
    return cache_get(skill_type, query)


def build_cached_response(cached: dict, skill_type: str, query: str) -> dict:
    """Build a full response from a cached result."""
    cached_trace = _build_final_dispatch_trace(skill_type, query)
    if skill_type == "stock":
        try:
            from backend.engine.skills.stock_skill import resolve_stock_detail
            detail = resolve_stock_detail(query)
            if detail:
                cached_trace = _build_final_dispatch_trace(
                    skill_type,
                    query,
                    resolved_name=detail.get("name"),
                    resolved_symbol=detail.get("code"),
                    resolver_source=detail.get("resolver_source"),
                    matched_text=detail.get("matched_text"),
                )
        except Exception:
            pass
    cached_response = with_trust_contract(_attach_final_dispatch_trace(
        {**cached, "cached": True},
        cached_trace,
    ))
    return apply_publication_containment(cached_response)
