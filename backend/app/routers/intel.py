"""市场情报 API.

Runtime recovery scope: keep this layer data-only. Do not call prompts or LLM.
Provider failures return HTTP 200 with `_qc.status="failure"` so callers can
degrade explicitly instead of treating HTTP 200 as business success.
"""
from fastapi import APIRouter, Depends
from backend.app.auth import get_current_user
import asyncio
import json
from collections import Counter
from datetime import datetime
import time

import requests

router = APIRouter(prefix="/api/intel")


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _intel_failure(error: Exception | str, module: str = "intel") -> dict:
    """Return a successful HTTP response carrying a failed intel QC envelope."""
    return {
        '_qc': {
            'status': 'failure',
            'sources': [],
            'completeness': 0,
            'error': str(error),
            'module': module,
            'source_type': 'not_connected',
            'generated_at': _now_iso(),
        },
        'data': [],
        'count': 0,
    }


def _qc(status: str, sources: list[str], completeness: float, source_type: str = "real", **extra) -> dict:
    allowed_status = {"success", "partial", "fallback", "failure"}
    normalized_status = status if status in allowed_status else "failure"
    payload = {
        "status": normalized_status,
        "sources": sources,
        "source_type": source_type,
        "completeness": completeness,
        "generated_at": _now_iso(),
    }
    payload.update(extra)
    return payload


def _availability(status: str, available: list[str], missing: list[str], as_of: str | None, source_type: str, latency_ms: int | None) -> dict:
    return {
        "status": status,
        "available": available,
        "missing": missing,
        "as_of": as_of,
        "source_type": source_type,
        "latency_ms": latency_ms,
    }


async def _collect_market_context_inputs(timeout: float = 10.0) -> dict:
    """Collect market-context inputs without letting one provider stall the layer."""
    tasks = {
        "hot_stocks": asyncio.create_task(_get_hot_stocks()),
        "news": asyncio.create_task(_get_market_news()),
        "auction_data": asyncio.create_task(_get_auction_data()),
    }
    done, pending = await asyncio.wait(tasks.values(), timeout=timeout)
    task_names = {task: name for name, task in tasks.items()}
    results = {}
    status = {}

    for task in pending:
        name = task_names[task]
        task.cancel()
        results[name] = [] if name != "auction_data" else {}
        status[name] = {"status": "timeout", "reason": "timeout"}

    for task in done:
        name = task_names[task]
        try:
            value = task.result()
        except asyncio.TimeoutError:
            value = [] if name != "auction_data" else {}
            status[name] = {"status": "timeout", "reason": "timeout"}
        except Exception as exc:
            value = [] if name != "auction_data" else {}
            status[name] = {
                "status": "degraded",
                "reason": "provider_error",
                "error": str(exc),
            }
        else:
            is_empty = not bool(value)
            results[name] = value
            status[name] = {
                "status": "empty" if is_empty else "complete",
                "reason": "empty" if is_empty else None,
            }
            continue
        results[name] = value

    return {"results": results, "status": status}


def _panel_timeout(module: str, timeout: float) -> dict:
    return {
        "_qc": _qc(
            "failure",
            [],
            0,
            source_type="timeout",
            module=module,
            error=f"{module} panel timed out after {timeout:g}s",
            missing_dimensions=[module],
            timeout_dimensions=[module],
        ),
        "data": [],
        "count": 0,
    }


async def _run_panel(module: str, coro, timeout: float = 12.0) -> dict:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return _panel_timeout(module, timeout)


def _empty_data_availability(latency_ms: int | None = None) -> dict:
    return {
        "market_context": _availability("unavailable", [], ["market_context"], None, "not_connected", latency_ms),
        "news": _availability("unavailable", [], ["news"], None, "missing", latency_ms),
        "capital_flow": _availability("unavailable", [], ["capital_flow"], None, "missing", latency_ms),
        "research": _availability("unavailable", [], ["research"], None, "missing", latency_ms),
        "realtime": _availability("unavailable", [], ["realtime"], None, "missing", latency_ms),
        "valuation": _availability("unavailable", [], ["valuation"], None, "missing", latency_ms),
    }


def _limit(items: list[dict], limit: int) -> list[dict]:
    return items[: max(1, min(int(limit or 10), 50))]


async def _run_blocking(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args))


async def _safe_auction_dimension(name: str, func, *args, timeout: float = 4.0, trace_token: str | None = None) -> tuple[str, object, dict]:
    """Outcome receipt taxonomy：None→unavailable，[]→valid_empty，异常→单一 failure taxonomy。"""
    from backend.engine.skills.auction_skill import _build_dimension_receipt

    started = time.monotonic()

    def _fail(outcome: str, exc: Exception) -> tuple[str, None, dict]:
        return name, None, _build_dimension_receipt(
            name, outcome, elapsed_s=time.monotonic() - started,
            completed_at=_now_iso(), error=f"{type(exc).__name__}: {exc}",
            trace_token=trace_token,
        )

    try:
        value = await asyncio.wait_for(_run_blocking(func, *args), timeout=timeout)
    except asyncio.TimeoutError as exc:
        return _fail("timeout", exc)
    except json.JSONDecodeError as exc:
        return _fail("parse_error", exc)
    except requests.Timeout as exc:
        return _fail("timeout", exc)
    except (requests.ConnectionError, requests.HTTPError) as exc:
        return _fail("provider_error", exc)
    except Exception as exc:
        return _fail("unknown_error", exc)

    if value is None:
        outcome = "unavailable"
    elif isinstance(value, list) and len(value) == 0:
        outcome = "valid_empty"
    else:
        outcome = "success_with_data"
    return name, value, _build_dimension_receipt(
        name, outcome, value=value, elapsed_s=time.monotonic() - started,
        completed_at=_now_iso(), trace_token=trace_token,
    )


async def _get_hot_stocks():
    """东方财富热股榜（人气排行）"""
    def _fetch():
        import akshare as ak
        df = ak.stock_hot_rank_em()
        items = []
        for _, row in df.head(20).iterrows():
            change = float(row.get('涨跌幅', 0) or 0)
            items.append({
                'rank': int(row.get('当前排名', 0)),
                'code': str(row.get('代码', '')),
                'name': str(row.get('股票名称', '')).strip(),
                'price': float(row.get('最新价', 0) or 0),
                'change': round(change, 2),
                'source': '东方财富',
            })
        return items
    return await _run_blocking(_fetch)


async def _get_market_news():
    """东方财富市场快讯（用大盘新闻代替雪球热门讨论）"""
    def _fetch():
        import akshare as ak
        df = ak.stock_info_global_em()
        items = []
        for _, row in df.head(15).iterrows():
            items.append({
                'title': str(row.get('标题', '')),
                'time': str(row.get('发布时间', '')),
                'source': '东方财富',
                'url': str(row.get('链接', '')),
            })
        return items
    return await _run_blocking(_fetch)


async def _get_auction_data(trace_token: str | None = None):
    from backend.engine.skills import auction_skill as auction_data
    from backend.engine.skills.auction_skill import _build_dimension_receipt, _SHANGHAI_TZ

    requested_at = datetime.now(_SHANGHAI_TZ)

    dimensions = [
        ("zt_pool", auction_data._fetch_zt_pool, (None,), 5.0),
        ("strong_pool", auction_data._fetch_strong_pool, (None,), 5.0),
        ("previous_zt", auction_data._fetch_previous_zt, (None,), 5.0),
        ("big_buy", auction_data._fetch_changes, ("大笔买入",), 5.0),
        ("hot_rank", auction_data._fetch_hot_rank, (), 2.5),
        ("hot_up", auction_data._fetch_hot_up, (), 2.5),
    ]
    collected = await asyncio.gather(*[
        _safe_auction_dimension(name, func, *args, timeout=timeout, trace_token=trace_token)
        for name, func, args, timeout in dimensions
    ])

    results = {}
    dimension_status = {}
    for name, value, status in collected:
        results[name] = value
        dimension_status[name] = status

    # top_gainers depends on the full-market spot ranking, which is too slow for
    # the P0 market-context path. Keep it explicit and missing instead of letting
    # it erase available auction core metrics.
    results["top_gainers"] = None
    results["top_gainers_error"] = "skipped_optional"
    dimension_status["top_gainers"] = _build_dimension_receipt(
        "top_gainers", "skipped_optional", trace_token=trace_token,
    )
    results["_dimension_status"] = dimension_status
    # Path B 收敛到 Path A 的 QC-consumable 形状：让 _qc_auction 直接消费，
    # 使 golden-pit 复用与 /api/analyze auction 分支完全相同的授权阶梯。
    results["_meta"] = {
        "as_of": requested_at.isoformat(timespec="seconds"),
        "market_phase": auction_data.market_phase(requested_at),
        "auction_results_ready": auction_data.market_phase(requested_at) not in {
            "pre_open", "auction_in_progress", "non_trading_day",
        },
        "trace_token": trace_token,
    }
    for name in dimension_status:
        results[f"{name}_status"] = dimension_status[name]
    results["_trace_token"] = trace_token
    return results


async def _get_watchlist_alerts(change_threshold: float):
    """Use watchlist config plus Eastmoney hot rank as lightweight live upstream."""
    def _load_watchlist():
        from backend.app.routers import watchlist as watchlist_router
        watch_data = watchlist_router.wl._load()
        return watch_data.get("stocks", [])

    stocks_task = _run_blocking(_load_watchlist)
    hot_task = _get_hot_stocks()
    stocks, hot_stocks = await asyncio.gather(stocks_task, hot_task)
    watch_codes = {str(item.get("code", "")).strip() for item in stocks}
    watch_names = {str(item.get("name", "")).strip() for item in stocks}
    alerts = []
    for item in hot_stocks:
        change = float(item.get("change", 0) or 0)
        if abs(change) < float(change_threshold or 0):
            continue
        code = str(item.get("code", ""))
        name = str(item.get("name", ""))
        alerts.append({
            "code": code,
            "name": name,
            "price": item.get("price"),
            "change": round(change, 2),
            "threshold": change_threshold,
            "watchlist_match": code in watch_codes or name in watch_names,
            "source": "eastmoney_hot_rank",
        })
    return sorted(alerts, key=lambda x: (not x["watchlist_match"], -abs(x["change"])))


async def _get_research_reports(symbol: str = "", limit: int = 10):
    """Fetch Eastmoney/AkShare research reports without LLM summarization."""
    def _fetch():
        import akshare as ak

        kwargs = {"symbol": symbol} if symbol else {}
        df = ak.stock_research_report_em(**kwargs)
        items = []
        for _, row in df.head(max(1, min(int(limit or 10), 50))).iterrows():
            items.append({
                "code": str(row.get("股票代码", "")),
                "name": str(row.get("股票简称", "")),
                "title": str(row.get("报告名称", "")),
                "rating": str(row.get("东财评级", "")),
                "institution": str(row.get("机构", "")),
                "industry": str(row.get("行业", "")),
                "date": str(row.get("日期", "")),
                "url": str(row.get("报告PDF链接", "")),
                "source": "eastmoney_research_report",
            })
        return items

    return await asyncio.wait_for(_run_blocking(_fetch), timeout=35)


def _industry_themes(auction_data: dict, limit: int = 3) -> list[dict]:
    industries = []
    for key in ("zt_pool", "strong_pool", "previous_zt"):
        for item in auction_data.get(key) or []:
            industry = item.get("所属行业")
            if industry:
                industries.append(str(industry))
    return [
        {"name": name, "count": count, "source": "eastmoney_auction"}
        for name, count in Counter(industries).most_common(limit)
    ]


@router.get("/xueqiu-hot")
async def xueqiu_hot():
    """热门讨论 - 返回市场快讯（东方财富新闻）"""
    try:
        items = await _get_market_news()
        return {
            '_qc': _qc('success' if items else 'partial', ['eastmoney'], 1.0 if items else 0.5),
            'data': items,
            'count': len(items),
        }
    except Exception as e:
        return _intel_failure(e, "xueqiu_hot")


@router.get("/xueqiu-hot-stock")
async def xueqiu_hot_stock():
    """热股榜 - 返回东方财富人气排行"""
    try:
        items = await _get_hot_stocks()
        return {
            '_qc': _qc('success' if items else 'partial', ['eastmoney'], 1.0 if items else 0.5),
            'data': items,
            'count': len(items),
        }
    except Exception as e:
        return _intel_failure(e, "xueqiu_hot_stock")


@router.get("/discussions")
async def intel_discussions(limit: int = 10):
    """Sidebar 热门讨论兼容路由。"""
    result = await xueqiu_hot()
    result["data"] = _limit(result.get("data") or [], limit)
    result["count"] = len(result["data"])
    return result


@router.get("/hot-stocks")
async def intel_hot_stocks(limit: int = 10):
    """Sidebar 热股榜兼容路由。"""
    result = await xueqiu_hot_stock()
    result["data"] = _limit(result.get("data") or [], limit)
    result["count"] = len(result["data"])
    return result


@router.get("/watch-alerts")
async def intel_watch_alerts(change_threshold: float = 3.0):
    """Sidebar 自选股异动：watchlist_json + Eastmoney spot."""
    try:
        items = await _get_watchlist_alerts(change_threshold)
        return {
            "_qc": _qc(
                "success",
                ["watchlist_json", "eastmoney"],
                1.0,
                threshold=change_threshold,
            ),
            "data": items,
            "count": len(items),
        }
    except Exception as e:
        return _intel_failure(e, "watch_alerts")


@router.get("/research", dependencies=[Depends(get_current_user)])
async def intel_research(limit: int = 10, mode: str = "batch", max_llm: int = 0, symbol: str = ""):
    """Sidebar 研报入口：Eastmoney/AkShare research reports, no LLM."""
    del mode, max_llm
    try:
        items = await _get_research_reports(symbol=symbol, limit=limit)
        return {
            "_qc": _qc(
                "success" if items else "partial",
                ["eastmoney_research_report"],
                1.0 if items else 0.5,
            ),
            "data": items,
            "count": len(items),
        }
    except Exception as e:
        return _intel_failure(e, "research")


@router.get("/market-context", dependencies=[Depends(get_current_user)])
async def market_context_layer():
    """今日市场画像：Eastmoney/AkShare live market structure."""
    started = time.monotonic()
    collected = await _collect_market_context_inputs(timeout=10.0)
    results = collected["results"]
    input_status = collected["status"]
    hot_stocks = results.get("hot_stocks") or []
    news = results.get("news") or []
    auction = results.get("auction_data") or {}
    auction_status = auction.get("_dimension_status") or {}

    zt_count = len(auction.get("zt_pool") or [])
    strong_count = len(auction.get("strong_pool") or [])
    broken_count = sum(int(item.get("炸板次数", 0) or 0) for item in (auction.get("zt_pool") or []))
    avg_change = round(sum(item.get("change", 0) for item in hot_stocks[:10]) / max(1, len(hot_stocks[:10])), 2)
    themes = _industry_themes(auction)
    top_sector = themes[0]["name"] if themes else None
    market_status = "偏强" if zt_count >= 50 else ("中性" if zt_count >= 20 else "偏弱")
    generated_at = _now_iso()
    latency_ms = round((time.monotonic() - started) * 1000)
    timed_out = [name for name, item in input_status.items() if item.get("status") == "timeout"]
    provider_errors = [name for name, item in input_status.items() if item.get("reason") == "provider_error"]
    empty_inputs = [name for name, item in input_status.items() if item.get("status") == "empty"]
    auction_timeouts = [name for name, item in auction_status.items() if item.get("outcome") == "timeout"]
    auction_provider_errors = [
        name for name, item in auction_status.items()
        if item.get("outcome") in ("provider_error", "parse_error", "unknown_error")
    ]
    auction_empty = [
        name for name, item in auction_status.items()
        if item.get("outcome") in ("valid_empty", "unavailable")
    ]
    auction_optional_missing = [
        name for name, item in auction_status.items()
        if item.get("outcome") == "skipped_optional"
    ]
    available_dimensions = []
    if hot_stocks:
        available_dimensions.append("hot_rank")
    if news:
        available_dimensions.append("eastmoney_news")
    if zt_count or strong_count or themes:
        available_dimensions.append("auction_market_structure")
    has_any_live_data = bool(available_dimensions)
    market_context_missing = []
    if "auction_data" in timed_out:
        market_context_missing.append("auction_data")
    if "hot_stocks" in timed_out:
        market_context_missing.append("hot_rank")
    if "news" in timed_out:
        market_context_missing.append("news")
    if provider_errors:
        market_context_missing.extend(provider_errors)
    market_context_missing.extend(auction_timeouts)
    market_context_missing.extend(auction_provider_errors)
    for name in ("hot_rank", "hot_up"):
        if name in auction_empty and name not in market_context_missing:
            market_context_missing.append(name)
    market_context_missing.extend(auction_optional_missing)
    if not has_any_live_data:
        market_context_missing.append("market_context")
    if has_any_live_data and not auction.get("top_gainers") and "top_gainers" not in market_context_missing:
        market_context_missing.append("top_gainers")
    market_context_missing = list(dict.fromkeys(market_context_missing))
    incomplete_dimensions = timed_out + provider_errors + empty_inputs + market_context_missing
    overall_status = "partial" if incomplete_dimensions or not has_any_live_data else "success"
    completeness = 1.0 if overall_status == "success" else (0.5 if has_any_live_data else 0)
    realtime_available = [
        name for name in [
            "hot_rank" if hot_stocks else None,
            "auction_market_structure" if (zt_count or strong_count) else None,
        ] if name
    ]
    realtime_missing = []
    if "auction_data" in timed_out:
        realtime_missing.append("auction_data")
    realtime_missing.extend([
        name for name in auction_timeouts + auction_provider_errors + auction_optional_missing
        if name in {"zt_pool", "strong_pool", "previous_zt", "big_buy", "hot_rank", "hot_up", "top_gainers"}
    ])
    realtime_missing = list(dict.fromkeys(realtime_missing))

    data_availability = {
        "market_context": _availability(
            "complete" if overall_status == "success" else ("partial" if has_any_live_data else "unavailable"),
            available_dimensions,
            market_context_missing,
            generated_at if has_any_live_data else None,
            "real" if has_any_live_data else "empty",
            latency_ms,
        ),
        "news": _availability(
            "timeout" if "news" in timed_out else ("complete" if news else "unavailable"),
            ["eastmoney_news"] if news else [],
            [] if news else ["eastmoney_news"],
            news[0].get("time") if news else None,
            "real" if news else ("timeout" if "news" in timed_out else "empty"),
            latency_ms,
        ),
        "capital_flow": _availability(
            "unavailable",
            [],
            ["capital_flow"],
            None,
            "missing",
            latency_ms,
        ),
        "research": _availability(
            "unavailable",
            [],
            ["research"],
            None,
            "missing",
            latency_ms,
        ),
        "realtime": _availability(
            "partial" if realtime_available and realtime_missing else (
                "complete" if realtime_available else ("timeout" if "auction_data" in timed_out else "unavailable")
            ),
            realtime_available,
            realtime_missing or ([] if realtime_available else ["realtime"]),
            generated_at if (hot_stocks or zt_count or strong_count) else None,
            "real" if (hot_stocks or zt_count or strong_count) else ("timeout" if "auction_data" in timed_out else "empty"),
            latency_ms,
        ),
        "valuation": _availability(
            "unavailable",
            [],
            ["valuation"],
            None,
            "missing",
            latency_ms,
        ),
    }

    return {
        "status": overall_status,
        "source": "eastmoney_akshare",
        "title": "今日市场画像",
        "positioning": "市场结构摘要 / Market Context Layer",
        "generated_at": generated_at,
        "date_label": datetime.now().strftime("%Y-%m-%d"),
        "conclusion": (
            f"市场结构{market_status}，涨停池 {zt_count} 只，强势股 {strong_count} 只。"
            if zt_count or strong_count
            else "市场画像部分数据可用，auction/realtime 维度不足。"
        ),
        "metrics": {
            "limit_up_count": zt_count,
            "strong_pool_count": strong_count,
            "broken_board_count": broken_count,
            "hot_stock_avg_change": avg_change,
        },
        "context": {
            "market_preference": market_status if (zt_count or strong_count) else "部分数据可用",
            "theme_concentration": "有主线" if themes else "主线不明显",
            "breadth": f"涨停池 {zt_count} / 强势股 {strong_count}",
            "top_sector": top_sector,
        },
        "themes": themes,
        "monitoring": [item.get("title", "") for item in news[:3]],
        "data_availability": data_availability,
        "disclaimer": "本页面呈现市场结构数据，不含操作建议。仅供参考，不构成投资建议。",
        "_qc": _qc(
            overall_status,
            ["eastmoney", "akshare"] if has_any_live_data else [],
            completeness,
            source_type="real" if has_any_live_data else "empty",
            source="eastmoney_akshare",
            latency_ms=latency_ms,
            missing_dimensions=market_context_missing,
            blocked_fields=market_context_missing,
            timeout_dimensions=list(dict.fromkeys(timed_out + auction_timeouts)),
            provider_errors=list(dict.fromkeys(provider_errors + auction_provider_errors)),
            allowed_use=["基础市场温度", "可用维度速览"] if has_any_live_data else [],
            forbidden_use=["完整市场画像", "短线买卖点", "资金流", "仓位建议"],
        ),
    }


@router.get("/golden-pit", dependencies=[Depends(get_current_user)])
async def golden_pit(realtime: bool = False, limit: int = 10, trace_token: str | None = None):
    """黄金坑候选：从实时涨停/强势/人气数据构造候选，不做交易建议。"""
    del realtime
    import uuid

    trace_token = trace_token or uuid.uuid4().hex[:16]
    try:
        auction = await _get_auction_data(trace_token=trace_token)
        dim_status = auction.get("_dimension_status") or {}

        # (统一到 _qc_auction 阶梯) 复用与 /api/analyze auction 分支完全相同的
        # 授权阶梯：phase + bundle 决定 L1/L2/L3，golden-pit 能力上限 = market_structure_overview。
        from backend.engine.skills import auction_skill as auction_data
        qc = auction_data._qc_auction(auction)
        authz = auction_data.golden_pit_authorization(qc)

        # L1 竞价窗口/盘前/非交易日：只观察，不构造候选。
        if not authz["build_candidates"]:
            return {
                "_qc": _qc(
                    "partial",
                    ["eastmoney_auction"],
                    0.0,
                    source_type="observation",
                    allowed_use=authz["allowed_use"],
                    forbidden_use=authz["forbidden_use"],
                    market_phase=qc["market_phase"],
                    auction_results_ready=qc["auction_results_ready"],
                    blocked_fields=qc["blocked_fields"],
                    minimum_analysis_bundle_satisfied=qc["minimum_analysis_bundle_satisfied"],
                    missing_dimensions=qc["missing_dimensions"],
                ),
                "trace_token": trace_token,
                "receipts": dim_status,
                "algorithm": {
                    "fetch": {
                        "status": "observation_only",
                        "dimensions_total": len(dim_status),
                    },
                    "candidate_filtering": {
                        "status": "blocked",
                        "sources_consumed": [],
                        "sources_skipped": [],
                        "filter_applied": False,
                        "candidate_conclusion": "pre_auction_observation",
                    },
                },
                "data": [],
                "count": 0,
            }

        # 候选构造：只有 outcome ∈ (success_with_data, valid_empty) 的源允许进入候选。
        # provider/mapping failure 的源必须被跳过，不得推出错误的"无候选"结论。
        consumed_sources = []
        skipped_sources = []
        filtered_out = 0
        candidates = []
        for source_key in ("strong_pool", "hot_up", "previous_zt"):
            outcome = (dim_status.get(source_key) or {}).get("outcome")
            if outcome not in ("success_with_data", "valid_empty"):
                skipped_sources.append(source_key)
                continue
            consumed_sources.append(source_key)
            receipt = dim_status.get(source_key) or {}
            for item in auction.get(source_key) or []:
                change = float(item.get("涨跌幅", 0) or 0)
                if source_key == "previous_zt" and change < -3:
                    filtered_out += 1
                    continue
                candidates.append({
                    "code": str(item.get("代码", "")),
                    "name": str(item.get("名称") or item.get("股票名称") or ""),
                    "change": round(change, 2),
                    "reason": str(item.get("入选理由") or item.get("板块") or source_key),
                    "source_bucket": source_key,
                    "source": "eastmoney_auction",
                    # Provenance binding to source dimension receipt —
                    # provider_origin_time is None when the provider does not
                    # stamp rows; fetch_completed_at is an observation boundary
                    # only and must NOT be read as provider data_as_of.
                    "source_receipt_id": receipt.get("receipt_id"),
                    "provider": receipt.get("provider"),
                    "provider_origin_time": receipt.get("provider_origin_time"),
                    "fetch_completed_at": receipt.get("fetch_completed_at"),
                    "timestamp_authority": receipt.get("timestamp_authority"),
                })
        candidates = sorted(candidates, key=lambda x: x["change"], reverse=True)
        items = _limit(candidates, limit)

        # Per-pool health QC: upstream failure must not be scored as complete success.
        core_pools = ("strong_pool", "hot_up", "previous_zt")
        pool_status = {name: (dim_status.get(name) or {}) for name in core_pools}
        success_pools = {n for n, s in pool_status.items() if s.get("outcome") == "success_with_data"}
        empty_pools = {n for n, s in pool_status.items() if s.get("outcome") == "valid_empty"}
        error_pools = {
            n for n, s in pool_status.items()
            if s.get("outcome") in ("timeout", "parse_error", "provider_error", "unknown_error", "unavailable")
        }
        healthy_pools = len(success_pools) + len(empty_pools)
        completeness = round(healthy_pools / len(core_pools), 2) if core_pools else 0.0
        error_detail = {
            n: (pool_status[n].get("error") or pool_status[n].get("outcome"))
            for n in error_pools
        }

        if items:
            candidate_conclusion = "candidates_found"
        elif not error_pools:
            candidate_conclusion = "healthy_inputs_zero_matches"
        else:
            candidate_conclusion = "indeterminate"

        if error_pools:
            status = "partial"
            source_type = "real" if success_pools else "degraded"
        elif completeness == 1.0:
            status = "success" if items else "partial"
            source_type = "real" if success_pools else "empty"
        else:
            status = "partial"
            source_type = "real" if success_pools else "empty"

        return {
            "_qc": _qc(
                status,
                ["eastmoney_auction"],
                completeness,
                source_type=source_type,
                pool_outcomes={n: (s.get("outcome") or "unknown") for n, s in pool_status.items()},
                error_pools=sorted(error_pools),
                error_detail=error_detail,
                missing_dimensions=sorted(error_pools),
                # (统一到 _qc_auction 阶梯) 能力上限 = market_structure_overview；
                # 永不授权 auction_analysis 或黄金坑/量化筛选信号。
                allowed_use=authz["allowed_use"],
                forbidden_use=authz["forbidden_use"],
                market_phase=qc["market_phase"],
                auction_results_ready=qc["auction_results_ready"],
                blocked_fields=qc["blocked_fields"],
                minimum_analysis_bundle_satisfied=qc["minimum_analysis_bundle_satisfied"],
            ),
            "trace_token": trace_token,
            "receipts": dim_status,
            "algorithm": {
                "fetch": {
                    "status": "complete",
                    "dimensions_total": len(dim_status),
                    "core_pools_healthy": healthy_pools,
                },
                "candidate_filtering": {
                    "status": "complete",
                    "sources_consumed": consumed_sources,
                    "sources_skipped": skipped_sources,
                    "filter_applied": filtered_out > 0,
                    "candidate_conclusion": candidate_conclusion,
                },
            },
            "data": items,
            "count": len(items),
        }
    except Exception as e:
        return _intel_failure(e, "golden_pit")


@router.get("/all", dependencies=[Depends(get_current_user)])
async def intel_all(limit: int = 10, modules: str = "discussions,hot-stocks,watch-alerts,research"):
    """Sidebar 聚合兼容路由。未接入模块用 QC 失败契约表达。"""
    market_context, discussions, hot_stocks, watch_alerts, research, golden_pit_panel = await asyncio.gather(
        _run_panel("market_context", market_context_layer(), timeout=12),
        _run_panel("discussions", intel_discussions(limit=limit), timeout=12),
        _run_panel("hot_stocks", intel_hot_stocks(limit=limit), timeout=12),
        _run_panel("watch_alerts", intel_watch_alerts(), timeout=12),
        _run_panel("research", intel_research(limit=limit), timeout=12),
        _run_panel("golden_pit", golden_pit(limit=limit), timeout=12),
    )
    panels = {
        "market_context": market_context,
        "discussions": discussions,
        "hot_stocks": hot_stocks,
        "watch_alerts": watch_alerts,
        "research": research,
        "golden_pit": golden_pit_panel,
    }
    statuses = [panel.get("_qc", {}).get("status") for panel in panels.values()]
    degraded = sum(1 for status in statuses if status != "success")
    completeness = round((len(statuses) - degraded) / max(1, len(statuses)), 2)
    return {
        "panels": panels,
        "_qc": _qc(
            "success" if degraded == 0 else "partial",
            ["eastmoney", "akshare"],
            completeness,
            source_type="real" if degraded == 0 else "fallback",
        ),
        "data_availability": market_context.get("data_availability", _empty_data_availability(None)),
        "meta": {"count": len(panels)},
    }
