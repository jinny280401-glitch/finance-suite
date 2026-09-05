"""
集合竞价排行榜 + 量化选股信号
数据源：东方财富（通过AkShare）

独立CLI脚本，无内部依赖
用法: python3 auction_data.py --query "集合竞价"
"""

import asyncio
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import akshare as ak
import requests

# ── Layer 1: Timeout enforcement for AkShare HTTP calls ──────────────────
# AkShare stock_zt_pool_em / stock_zt_pool_strong_em / stock_changes_em /
# stock_hot_rank_em / stock_hot_up_em all call requests.get/post() WITHOUT
# a timeout= parameter. In Python requests, this defaults to blocking
# indefinitely (socket.settimeout(None)), which means one slow eastmoney
# endpoint can permanently occupy a ThreadPoolExecutor thread.
#
# We patch requests.get and requests.post to inject a default timeout of
# (connect=3s, read=15s) when the caller omits the timeout argument.
# Calls that already pass an explicit timeout= are unaffected.
#
# This is Layer 1 (root cause). Layer 2 (safety net) is the
# asyncio.wait_for in get_auction_data() — see there for the two-layer
# design rationale.

_DEFAULT_AKSHARE_TIMEOUT = (3, 15)  # (connect_timeout, read_timeout)

_original_requests_get = requests.get
_original_requests_post = requests.post


def _requests_get_with_timeout(url, **kwargs):
    kwargs.setdefault("timeout", _DEFAULT_AKSHARE_TIMEOUT)
    return _original_requests_get(url, **kwargs)


def _requests_post_with_timeout(url, **kwargs):
    kwargs.setdefault("timeout", _DEFAULT_AKSHARE_TIMEOUT)
    return _original_requests_post(url, **kwargs)


requests.get = _requests_get_with_timeout
requests.post = _requests_post_with_timeout

_executor = ThreadPoolExecutor(max_workers=4)
_TOP_GAINERS_TIMEOUT_SECONDS = float(os.getenv("MARKET_CONTEXT_TOP_GAINERS_TIMEOUT", "3"))
_SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def market_phase(at: datetime | None = None) -> str:
    """Return the A-share phase relevant to auction-result readiness."""
    now = at or datetime.now(_SHANGHAI_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_SHANGHAI_TZ)
    else:
        now = now.astimezone(_SHANGHAI_TZ)
    if now.weekday() >= 5:
        return "non_trading_day"

    hhmmss = now.hour * 10000 + now.minute * 100 + now.second

    if hhmmss < 91500:
        return "pre_open"
    elif hhmmss < 92500:
        return "auction_in_progress"
    elif hhmmss < 93000:
        return "auction_complete"
    elif hhmmss < 113000:
        return "morning_session"
    elif hhmmss < 130000:
        return "lunch_break"
    elif hhmmss < 150000:
        return "afternoon_session"
    elif hhmmss < 153000:
        return "closing_auction"
    else:
        return "post_market"


def _fetch_zt_pool(date: str = None) -> list[dict] | None:
    """涨停池（含封板资金、首次封板时间、连板数等）"""
    try:
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zt_pool_em(date=date)
        if df is not None and len(df) > 0:
            return df.to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_strong_pool(date: str = None) -> list[dict] | None:
    """强势股池（涨停但未封死）"""
    try:
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zt_pool_strong_em(date=date)
        if df is not None and len(df) > 0:
            return df.to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_previous_zt(date: str = None) -> list[dict] | None:
    """昨日涨停今日表现"""
    try:
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zt_pool_previous_em(date=date)
        if df is not None and len(df) > 0:
            return df.to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_changes(symbol: str = "大笔买入") -> list[dict] | None:
    """盘中异动（大笔买入/大笔卖出/封涨停板/打开涨停板等）"""
    try:
        df = ak.stock_changes_em(symbol=symbol)
        if df is not None and len(df) > 0:
            return df.head(30).to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_hot_rank() -> list[dict] | None:
    """东方财富人气排行榜"""
    df = ak.stock_hot_rank_em()
    if df is not None and len(df) > 0:
        return df.head(30).to_dict(orient="records")
    return None


def _fetch_hot_up() -> list[dict] | None:
    """飙升榜（人气飙升最快的股票）"""
    df = ak.stock_hot_up_em()
    if df is not None and len(df) > 0:
        return df.head(20).to_dict(orient="records")
    return None


def _fetch_spot_sorted() -> list[dict] | None:
    """全市场实时行情（按涨幅排序前50）"""
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and len(df) > 0:
            items = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                if code and name:
                    items.append({
                        "name": name,
                        "code": code,
                        "price": row.get("最新价"),
                        "change": row.get("涨跌幅"),
                        "pe": row.get("市盈率-动态"),
                        "mv": row.get("总市值"),
                    })
            by_change = sorted(items, key=lambda x: float(x.get("change") or 0), reverse=True)[:50]
            return by_change
    except Exception:
        pass
    return None


# ── Layer 2: asyncio-level safety net ──────────────────────────────
# Layer 1 (requests monkey-patch above) prevents threads from blocking
# forever by injecting timeout=(3,15) into every AkShare HTTP call.
# Layer 2 bounds the COROUTINE's total wait time. Under normal operation
# Layer 1 fires first and Layer 2 never triggers — this is a safety net
# for any edge case where Layer 1 is somehow bypassed.
#
# Per-task timeout: read_timeout(15s) + connect_timeout(3s) + buffer(7s) = 25s.
# With 7 tasks running concurrently on 4 threads, worst-case wall time =
# ceil(7/4) x 25s = 50s — well within nginx proxy_read_timeout (120s).
_TASK_TIMEOUT = 25


# ── Outcome receipts (2026-08-13) ─────────────────────────────────────────
# Structured per-dimension outcome taxonomy. None (provider returned nothing)
# and [] (provider succeeded with zero rows) MUST NOT be conflated:
# the former is unavailable, the latter is valid_empty.
#
# Temporal provenance (2026-08-13):
# - provider_origin_time: timestamp from provider's response field (may be None)
# - fetch_completed_at: local observation boundary when fetch completed
# - timestamp_authority: "provider_stamped" | "fetch_boundary"
# - provider_freshness: "unknown" when provider_origin_time is None
#
# SEMANTIC BOUNDARY: fetch_completed_at is NOT provider data_as_of. It proves
# "we observed this at T" not "provider generated this at T".
_RECEIPT_VERSION = "1.1"

_ORIGIN_TIME_KEYS = ("时间", "成交时间", "更新时间", "发布时间", "时间戳")


def _extract_row_metadata(rows) -> dict:
    """Best-effort extraction of provider-origin time and auction-field presence.

    If rows carry no timestamp field, provider_origin_time stays None — the
    receipt then honestly records that origin time is unprovable.
    """
    if not isinstance(rows, list) or not rows:
        return {"provider_origin_time": None, "has_auction_fields": None}
    dict_rows = [row for row in rows if isinstance(row, dict)]
    if not dict_rows:
        return {"provider_origin_time": None, "has_auction_fields": None}

    has_auction_fields = any("竞价" in str(key) for key in dict_rows[0].keys())

    origin = None
    for key in _ORIGIN_TIME_KEYS:
        values = [str(row.get(key)) for row in dict_rows if row.get(key) not in (None, "")]
        if values:
            origin = values[-1]  # last row = latest observed time
            break
    return {"provider_origin_time": origin, "has_auction_fields": has_auction_fields}


def _build_dimension_receipt(
    name: str,
    outcome: str,
    *,
    value=None,
    elapsed_s=None,
    completed_at=None,
    error=None,
    trace_token=None,
) -> dict:
    """Build dimension receipt with dual temporal provenance:

    - provider_origin_time: from provider response (None if absent)
    - fetch_completed_at: local observation boundary
    - timestamp_authority: distinguishes the two
    - provider_freshness: "unknown" when origin time unavailable
    """
    meta = _extract_row_metadata(value)
    provider_origin = meta["provider_origin_time"]

    return {
        "receipt_version": _RECEIPT_VERSION,
        "receipt_id": f"{name}:{trace_token}" if trace_token else name,
        "dimension": name,
        "provider": "eastmoney_akshare",
        "trace_token": trace_token,
        "outcome": outcome,
        "count": len(value) if isinstance(value, list) else None,
        "elapsed_s": round(elapsed_s, 3) if elapsed_s is not None else None,
        "fetch_completed_at": completed_at,
        "provider_origin_time": provider_origin,
        "timestamp_authority": "provider_stamped" if provider_origin else "fetch_boundary",
        "provider_freshness": "unknown" if provider_origin is None else "provider_stamped",
        "has_auction_fields": meta["has_auction_fields"],
        "error": error,
    }


def _timed_call(fn, *args):
    """Run fn and return (value, elapsed_s, exception_or_None). Never raises."""
    import time as _time

    started = _time.monotonic()
    try:
        value = fn(*args)
        return value, (_time.monotonic() - started), None
    except Exception as exc:  # noqa: BLE001 — receipt layer must never raise
        return None, (_time.monotonic() - started), exc


async def get_auction_data(include_top_gainers: bool = True, trace_token: str | None = None) -> dict:
    """并发获取集合竞价相关全部数据 — 每个调用受 Layer 1 (HTTP timeout) + Layer 2 (asyncio timeout) 双重保护

    每个维度附带结构化 outcome receipt（见 _build_dimension_receipt）：
    outcome ∈ success_with_data / valid_empty / unavailable / timeout /
    parse_error / provider_error / unknown_error。None 与 [] 不再折叠。
    """
    import uuid

    requested_at = datetime.now(_SHANGHAI_TZ)
    trace_token = trace_token or uuid.uuid4().hex[:16]
    loop = asyncio.get_event_loop()

    tasks = {
        "zt_pool": loop.run_in_executor(_executor, _timed_call, _fetch_zt_pool, None),
        "strong_pool": loop.run_in_executor(_executor, _timed_call, _fetch_strong_pool, None),
        "previous_zt": loop.run_in_executor(_executor, _timed_call, _fetch_previous_zt, None),
        "big_buy": loop.run_in_executor(_executor, _timed_call, _fetch_changes, "大笔买入"),
        "hot_rank": loop.run_in_executor(_executor, _timed_call, _fetch_hot_rank),
        "hot_up": loop.run_in_executor(_executor, _timed_call, _fetch_hot_up),
    }

    # Execute all tasks concurrently, each bounded by timeout.
    # asyncio.gather with return_exceptions=True ensures one task's
    # timeout does not cancel the others.
    task_names = list(tasks.keys())
    task_futures = [
        asyncio.wait_for(tasks[name], timeout=_TASK_TIMEOUT)
        for name in task_names
    ]
    gathered = await asyncio.gather(*task_futures, return_exceptions=True)

    results = {}
    for name, outcome in zip(task_names, gathered):
        completed_at = datetime.now(_SHANGHAI_TZ).isoformat(timespec="seconds")

        if isinstance(outcome, asyncio.TimeoutError):
            results[name] = None
            results[f"{name}_status"] = _build_dimension_receipt(
                name, "timeout", completed_at=completed_at,
                error=str(outcome), trace_token=trace_token,
            )
            continue

        value, elapsed, exc = outcome
        if exc is not None:
            results[name] = None
            if isinstance(exc, json.JSONDecodeError):
                outcome_class = "parse_error"
            elif isinstance(exc, requests.Timeout):
                outcome_class = "timeout"
            elif isinstance(exc, (requests.ConnectionError, requests.HTTPError)):
                outcome_class = "provider_error"
            else:
                outcome_class = "unknown_error"
            results[f"{name}_status"] = _build_dimension_receipt(
                name, outcome_class, elapsed_s=elapsed, completed_at=completed_at,
                error=f"{type(exc).__name__}: {exc}", trace_token=trace_token,
            )
        elif value is None:
            results[name] = None
            results[f"{name}_status"] = _build_dimension_receipt(
                name, "unavailable", elapsed_s=elapsed, completed_at=completed_at,
                trace_token=trace_token,
            )
        elif isinstance(value, list) and len(value) == 0:
            results[name] = value
            results[f"{name}_status"] = _build_dimension_receipt(
                name, "valid_empty", value=value, elapsed_s=elapsed,
                completed_at=completed_at, trace_token=trace_token,
            )
        else:
            results[name] = value
            results[f"{name}_status"] = _build_dimension_receipt(
                name, "success_with_data", value=value, elapsed_s=elapsed,
                completed_at=completed_at, trace_token=trace_token,
            )

    if not include_top_gainers:
        results["top_gainers"] = None
        results["top_gainers_error"] = "skipped_optional"
        results["top_gainers_status"] = _build_dimension_receipt(
            "top_gainers", "skipped_optional", trace_token=trace_token,
        )
    else:
        try:
            top_gainers_task = loop.run_in_executor(_executor, _timed_call, _fetch_spot_sorted)
            top_value, top_elapsed, top_exc = await asyncio.wait_for(
                top_gainers_task,
                timeout=_TOP_GAINERS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            results["top_gainers"] = None
            results["top_gainers_error"] = f"timeout_{_TOP_GAINERS_TIMEOUT_SECONDS:g}s"
            results["top_gainers_status"] = _build_dimension_receipt(
                "top_gainers", "timeout", trace_token=trace_token,
            )
        else:
            results["top_gainers"] = top_value
            if top_exc is not None:
                results["top_gainers_error"] = f"{type(top_exc).__name__}: {top_exc}"
                results["top_gainers_status"] = _build_dimension_receipt(
                    "top_gainers", "unknown_error", elapsed_s=top_elapsed,
                    error=str(top_exc), trace_token=trace_token,
                )
            elif top_value is None:
                results["top_gainers_status"] = _build_dimension_receipt(
                    "top_gainers", "unavailable", elapsed_s=top_elapsed,
                    trace_token=trace_token,
                )
            elif isinstance(top_value, list) and len(top_value) == 0:
                results["top_gainers_status"] = _build_dimension_receipt(
                    "top_gainers", "valid_empty", value=top_value,
                    elapsed_s=top_elapsed, trace_token=trace_token,
                )
            else:
                results["top_gainers_status"] = _build_dimension_receipt(
                    "top_gainers", "success_with_data", value=top_value,
                    elapsed_s=top_elapsed, trace_token=trace_token,
                )

    results["_meta"] = {
        "as_of": requested_at.isoformat(timespec="seconds"),
        "market_phase": market_phase(requested_at),
        "auction_results_ready": market_phase(requested_at) not in {
            "pre_open", "auction_in_progress", "non_trading_day",
        },
        "trace_token": trace_token,
    }

    return results


# ── QC ─────────────────────────────────────────────────────────────────

# Capability-Bundle Fail-Closed（Auction Semantic P0，Design Decision 1）
# minimum_analysis_bundle = 授权 L3 auction_analysis 的最小维度集合。
# 集合竞价强势候选池 = 涨停结构(zt_pool) + 强势股(strong_pool) + 昨日涨停表现(previous_zt)。
# 其余四维(big_buy/hot_rank/hot_up/top_gainers)为增强维度：单一增强维度失败可降级标注，
# 但不得因增强维度缺失而 BLOCK 核心 bundle 已满足的 auction_analysis；反之核心 bundle
# 任一维度失败，不得授权完整 auction_analysis。
MINIMUM_ANALYSIS_BUNDLE = ("zt_pool", "strong_pool", "previous_zt")
_HEALTHY_OUTCOMES = ("success_with_data", "valid_empty")


def _qc_auction(data: dict) -> dict:
    """盘面数据质检 — 时间闸门 + 全零成交检测 + 维度有效性。

    (Design Decision 3C) 三个概念显式解耦，禁止用一个 bool 隐式串起：
      market_phase          — 时间标签（仅描述"现在几点"）
      auction_results_ready — 数据就绪（是否已过 09:25，最终竞价结果可否判读）
      allowed_use           — 授权阶梯（由 phase + bundle 满足度 + 具体哪几维失败共同决定）

    返回 _qc dict。调用方据此决定是否/以何种授权范围让数据进入 LLM。
    """
    dimension_labels = {
        "zt_pool": "涨停池",
        "strong_pool": "强势股",
        "previous_zt": "昨日涨停",
        "big_buy": "大笔买入",
        "hot_rank": "人气排行",
        "hot_up": "飙升榜",
        "top_gainers": "涨幅排行",
    }
    meta = data.get("_meta") or {}
    phase = meta.get("market_phase") or "unknown"
    auction_results_ready = meta.get("auction_results_ready") is True
    # L1 边界：竞价窗口/盘前/非交易日一律只观察，不以 auction_results_ready 单值决定。
    pre_auction_phase = phase in {"pre_open", "auction_in_progress", "non_trading_day"}

    def _number(value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _all_zero_liquidity(rows) -> bool:
        if not isinstance(rows, list) or not rows:
            return False
        records = [row for row in rows if isinstance(row, dict)]
        if not records:
            return False
        return all(
            _number(row.get("成交额")) <= 0 and _number(row.get("换手率")) <= 0
            for row in records
        )

    invalid_dimensions = []
    for key in ("zt_pool", "strong_pool", "previous_zt"):
        if _all_zero_liquidity(data.get(key)):
            invalid_dimensions.append(key)

    def _present(key: str) -> bool:
        return data.get(key) not in (None, [], {}) and key not in invalid_dimensions

    missing = [key for key in dimension_labels if not _present(key)]
    missing_critical = [key for key in MINIMUM_ANALYSIS_BUNDLE if not _present(key)]

    # 结构化 outcome（来自各维度 receipt）— 供 QC/admission 消费，不参与旧 status 词汇
    dimension_outcomes = {}
    for key in dimension_labels:
        receipt = data.get(f"{key}_status")
        dimension_outcomes[key] = receipt.get("outcome") if isinstance(receipt, dict) else None
    unavailable_dimensions = [
        key for key, outcome in dimension_outcomes.items()
        if outcome not in ("success_with_data", "valid_empty", "skipped_optional")
    ]

    # (Decision 1) bundle 满足度：核心维度全部健康(success_with_data/valid_empty)。
    bundle_satisfied = all(
        dimension_outcomes.get(k) in _HEALTHY_OUTCOMES for k in MINIMUM_ANALYSIS_BUNDLE
    )
    bundle_missing = [
        k for k in MINIMUM_ANALYSIS_BUNDLE
        if dimension_outcomes.get(k) not in _HEALTHY_OUTCOMES
    ]

    total = len(dimension_labels)
    completeness = round((total - len(missing)) / total, 2)
    present_keys = [key for key in dimension_labels if _present(key)]

    dimension_sources = {
        key: ("akshare" if _present(key) else None) for key in dimension_labels
    }

    if completeness <= 0:
        status = "failure"
    elif not auction_results_ready or invalid_dimensions:
        status = "partial"
    elif completeness == 1.0:
        status = "success"
    elif missing_critical:
        status = "partial"
    elif completeness >= 0.8:
        status = "success"
    else:
        status = "partial"

    blocked_fields = []
    gate_reason = None
    if pre_auction_phase:
        blocked_fields.extend([
            "auction_result",
            "market_sentiment",
            "limit_up_ranking",
            "quant_signals",
        ])
        gate_reason = "auction_not_complete_before_09_25"
    if invalid_dimensions:
        blocked_fields.extend([
            "market_sentiment",
            "liquidity_assessment",
            "quant_signals",
        ])
        gate_reason = gate_reason or "zero_liquidity_rows"
    # (Decision 3B) 任何不可用维度(timeout/parse_error/provider_error/unknown)必须显式列入
    # blocked_fields — 不得在源头失败时 blocked_fields 为空。
    blocked_fields.extend(unavailable_dimensions)

    # (Decision 2) Allowed Use Ladder：
    #   L1 pre_auction_observation  — 竞价窗口/盘前/非交易日：只观察，不下最终竞价判断。
    #   L2 market_structure_overview — 已过 09:25 但 bundle 未满足/存在无效维度：
    #                                 仅结构速览 + 显式降级标注。
    #   L3 auction_analysis          — 已过 09:25 + bundle 满足 + 无无效维度。
    if pre_auction_phase:
        allowed_use = ["pre_auction_observation"]
    elif not bundle_satisfied or invalid_dimensions:
        allowed_use = ["market_structure_overview"]
    else:
        allowed_use = ["auction_analysis"]

    return {
        "status": status,
        "completeness": completeness,
        "sources": ["akshare"] if present_keys else [],
        "source_used": "akshare",
        "attempted_sources": ["akshare"],
        "supported_sources": ["akshare"],
        "fallback_triggered": False,
        "fallback_source": None,
        "dimension_sources": dimension_sources,
        "dimension_labels": dimension_labels,
        "dimension_outcomes": dimension_outcomes,
        "unavailable_dimensions": unavailable_dimensions,
        "missing_dimensions": missing,
        "missing_critical_dimensions": missing_critical,
        "minimum_analysis_bundle": list(MINIMUM_ANALYSIS_BUNDLE),
        "minimum_analysis_bundle_satisfied": bundle_satisfied,
        "bundle_missing_dimensions": bundle_missing,
        "invalid_dimensions": invalid_dimensions,
        "market_phase": phase,
        "as_of": meta.get("as_of"),
        "auction_results_ready": auction_results_ready,
        "gate_reason": gate_reason,
        "allowed_use": allowed_use,
        "blocked_fields": sorted(set(blocked_fields)),
        "stale_data": [],
    }


def auction_allows_llm(allowed_use) -> bool:
    """(Decision 2 强制) 仅 L3 auction_analysis 授权调用 LLM。

    L1 pre_auction_observation / L2 market_structure_overview 一律不调用 LLM，
    直接返回结构化文本（观察 / 结构速览），从根源上阻断"量化选股 prompt 无条件生成
    竞价结论"的泄漏。此函数是 api.py analyze 分支与测试共用的单一判定来源。
    """
    return "auction_analysis" in (allowed_use or [])


def golden_pit_authorization(qc: dict) -> dict:
    """golden-pit 能力授权映射 — 统一到 _qc_auction 阶梯。

    golden-pit 的能力上限是"市场结构速览(候选池构造)"，永不授权 auction_analysis
    或黄金坑/量化筛选信号。L1(竞价窗口/盘前/非交易日)只观察，不构造候选。
    返回 build_candidates=False 时调用方必须返回空候选 + 观察语义。
    """
    allowed = qc.get("allowed_use") or []
    if "pre_auction_observation" in allowed:
        return {
            "allowed_use": ["pre_auction_observation"],
            "forbidden_use": ["候选池构造", "auction_analysis", "黄金坑/量化筛选信号"],
            "build_candidates": False,
        }
    return {
        "allowed_use": ["market_structure_overview"],
        "forbidden_use": ["auction_analysis", "黄金坑/量化筛选信号"],
        "build_candidates": True,
    }


class AuctionDataQualityError(Exception):
    """Raised when auction data fails QC and should not be fed to LLM."""
    def __init__(self, qc: dict):
        self.qc = qc
        super().__init__(f"auction QC failed: status={qc['status']}, gate_reason={qc.get('gate_reason')}")


async def get_validated_auction_data(include_top_gainers: bool = True, trace_token: str | None = None) -> dict:
    """获取数据后执行 QC，不合格抛出 AuctionDataQualityError。"""
    data = await get_auction_data(include_top_gainers=include_top_gainers, trace_token=trace_token)
    qc = _qc_auction(data)
    if qc["status"] == "failure" or not qc["auction_results_ready"] or qc["invalid_dimensions"]:
        raise AuctionDataQualityError(qc)
    data["_qc"] = qc
    return data


# ── Formatting ──────────────────────────────────────────────────────────

def format_auction_data(data: dict) -> str:
    """格式化为LLM可读文本（含时间门阻断）。"""
    invalid = set(data.get("_qc", {}).get("invalid_dimensions", []))
    # (F7) 不可用维度(timeout/parse_error/provider_error)同样不得把数据送进 prompt。
    blocked_dims = invalid | set(data.get("_qc", {}).get("unavailable_dimensions", []))
    parts = []
    parts.append("=== 集合竞价与盘面数据（东方财富）===")
    meta = data.get("_meta") or {}
    as_of = meta.get("as_of") or datetime.now(_SHANGHAI_TZ).isoformat(timespec="seconds")
    phase = meta.get("market_phase") or "unknown"
    parts.append(f"数据时间：{as_of}")
    parts.append(f"市场阶段：{phase}")
    if meta.get("auction_results_ready") is False:
        parts.append(
            "【时间门阻断】09:25 集合竞价尚未结束。当前数据仅可作为盘前观察，"
            "禁止生成竞价结果、市场情绪或量化选股结论。\n"
        )
        return "\n".join(parts)
    parts.append("")

    # (Decision 2) 授权阶梯 + 不可用维度显式标注：降级状态必须写进给 LLM 的正文，
    # 让"仅结构速览 / 禁止补全缺失维度"在 pre-prompt 内可观察，而非只存在于 _qc。
    qc = data.get("_qc") or {}
    allowed_use = qc.get("allowed_use") or []
    unavailable = qc.get("unavailable_dimensions") or []
    if unavailable or "auction_analysis" not in allowed_use:
        level = allowed_use[0] if allowed_use else "unknown"
        missing_label = "、".join(unavailable) if unavailable else "无"
        parts.append(
            f"【数据降级】授权级别：{level}；不可用维度：{missing_label}。"
            "不可用维度已被阻断，禁止据此推理或补全，请仅基于可用维度给出结论。"
        )
        parts.append("")

    # 涨停池
    zt = None if "zt_pool" in blocked_dims else data.get("zt_pool")
    if zt:
        parts.append(f"【今日涨停池】共{len(zt)}只")
        for s in zt[:15]:
            parts.append(f"  {s.get('名称','')}({s.get('代码','')}) "
                        f"涨幅{s.get('涨跌幅','')}% 成交额{s.get('成交额','')} "
                        f"封板资金{s.get('封板资金','')} "
                        f"首封{s.get('首次封板时间','')} 连板{s.get('连板数','')}")
        parts.append("")

    # 强势股
    strong = None if "strong_pool" in blocked_dims else data.get("strong_pool")
    if strong:
        parts.append(f"【强势股池】共{len(strong)}只")
        for s in strong[:10]:
            parts.append(f"  {s}")
        parts.append("")

    # 昨日涨停今日表现
    prev = None if "previous_zt" in blocked_dims else data.get("previous_zt")
    if prev:
        parts.append(f"【昨日涨停今日表现】共{len(prev)}只")
        for s in prev[:10]:
            parts.append(f"  {s}")
        parts.append("")

    # 大笔买入异动
    bb = None if "big_buy" in blocked_dims else data.get("big_buy")
    if bb:
        parts.append(f"【盘中大笔买入异动】共{len(bb)}条")
        for s in bb[:15]:
            parts.append(f"  {s.get('时间','')} {s.get('名称','')}({s.get('代码','')}) "
                        f"板块:{s.get('板块','')} {s.get('相关信息','')}")
        parts.append("")

    # 热门排行
    hot = None if "hot_rank" in blocked_dims else data.get("hot_rank")
    if hot:
        parts.append(f"【东方财富人气排行Top20】")
        for i, s in enumerate(hot[:20], 1):
            parts.append(f"  {i}. {s}")
        parts.append("")

    # 飙升榜
    up = None if "hot_up" in blocked_dims else data.get("hot_up")
    if up:
        parts.append(f"【人气飙升榜Top10】")
        for i, s in enumerate(up[:10], 1):
            parts.append(f"  {i}. {s}")
        parts.append("")

    # 涨幅排行
    gainers = None if "top_gainers" in blocked_dims else data.get("top_gainers")
    if gainers:
        parts.append(f"【涨幅排行Top20】")
        for i, s in enumerate(gainers[:20], 1):
            parts.append(f"  {i}. {s.get('name','')}({s.get('code','')}) "
                        f"涨幅{s.get('change','')}% 最新价{s.get('price','')} PE{s.get('pe','')}")
        parts.append("")

    if len(parts) <= 3:
        parts.append("当前非交易时段或数据暂不可用。")

    return "\n".join(parts)


def format_auction_qc_failure(qc: dict) -> str:
    """QC 失败时返回降级提示，不把残缺数据送给 LLM。"""
    phase = qc.get("market_phase", "unknown")
    gate = qc.get("gate_reason", "")
    invalid = qc.get("invalid_dimensions", [])
    blocked = qc.get("blocked_fields", [])

    lines = ["=== 集合竞价数据暂不可用 ==="]
    lines.append(f"市场阶段：{phase}")

    if gate == "auction_not_complete_before_09_25":
        lines.append("集合竞价进行中，结果将在 09:25 后可用。")
    elif invalid:
        lines.append(f"以下维度数据无效（全零成交或缺失）：{', '.join(invalid)}")
    else:
        lines.append("数据质量不满足分析要求。")

    if blocked:
        lines.append(f"已阻断结论类型：{', '.join(blocked)}")
    lines.append("请等待 09:25 集合竞价结束后重试。")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="获取集合竞价与盘面数据")
    parser.add_argument("--query", type=str, default="集合竞价", help="查询内容（当前忽略，获取全部盘面数据）")
    args = parser.parse_args()

    print("正在获取集合竞价与盘面数据...", flush=True)

    data = asyncio.run(get_auction_data())
    output = format_auction_data(data)
    print(output)
