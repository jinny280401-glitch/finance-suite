"""
集合竞价排行榜 + 量化选股信号
数据源：东方财富（通过AkShare）

独立CLI脚本，无内部依赖
用法: python3 auction_data.py --query "集合竞价"
"""

import asyncio
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import akshare as ak

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
    try:
        df = ak.stock_hot_rank_em()
        if df is not None and len(df) > 0:
            return df.head(30).to_dict(orient="records")
    except Exception:
        pass
    return None


def _fetch_hot_up() -> list[dict] | None:
    """飙升榜（人气飙升最快的股票）"""
    try:
        df = ak.stock_hot_up_em()
        if df is not None and len(df) > 0:
            return df.head(20).to_dict(orient="records")
    except Exception:
        pass
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


async def get_auction_data(include_top_gainers: bool = True) -> dict:
    """并发获取集合竞价相关全部数据"""
    requested_at = datetime.now(_SHANGHAI_TZ)
    loop = asyncio.get_event_loop()

    tasks = {
        "zt_pool": loop.run_in_executor(_executor, _fetch_zt_pool, None),
        "strong_pool": loop.run_in_executor(_executor, _fetch_strong_pool, None),
        "previous_zt": loop.run_in_executor(_executor, _fetch_previous_zt, None),
        "big_buy": loop.run_in_executor(_executor, _fetch_changes, "大笔买入"),
        "hot_rank": loop.run_in_executor(_executor, _fetch_hot_rank),
        "hot_up": loop.run_in_executor(_executor, _fetch_hot_up),
    }

    results = {}
    for key, task in tasks.items():
        try:
            results[key] = await task
        except Exception:
            results[key] = None

    if not include_top_gainers:
        results["top_gainers"] = None
        results["top_gainers_error"] = "skipped_optional"
    else:
        try:
            top_gainers_task = loop.run_in_executor(_executor, _fetch_spot_sorted)
            results["top_gainers"] = await asyncio.wait_for(
                top_gainers_task,
                timeout=_TOP_GAINERS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            results["top_gainers"] = None
            results["top_gainers_error"] = f"timeout_{_TOP_GAINERS_TIMEOUT_SECONDS:g}s"
        except Exception as e:
            results["top_gainers"] = None
            results["top_gainers_error"] = f"{type(e).__name__}: {e}"

    results["_meta"] = {
        "as_of": requested_at.isoformat(timespec="seconds"),
        "market_phase": market_phase(requested_at),
        "auction_results_ready": market_phase(requested_at) not in {
            "pre_open",
            "auction_in_progress",
            "non_trading_day",
        },
    }

    return results


# ── QC ─────────────────────────────────────────────────────────────────

def _qc_auction(data: dict) -> dict:
    """盘面数据质检 — 时间闸门 + 全零成交检测 + 维度有效性。

    返回 _qc dict，调用方根据 qc['status'] 和 qc['auction_results_ready']
    决定是否允许原始数据进入 LLM。
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
    critical_keys = {"zt_pool", "hot_rank", "top_gainers"}
    meta = data.get("_meta") or {}
    phase = meta.get("market_phase") or "unknown"
    auction_results_ready = meta.get("auction_results_ready") is True

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
    missing_critical = [key for key in critical_keys if not _present(key)]

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
    if not auction_results_ready:
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
        "missing_dimensions": missing,
        "missing_critical_dimensions": missing_critical,
        "invalid_dimensions": invalid_dimensions,
        "market_phase": phase,
        "as_of": meta.get("as_of"),
        "auction_results_ready": auction_results_ready,
        "gate_reason": gate_reason,
        "allowed_use": ["pre_auction_observation"] if not auction_results_ready else ["auction_analysis"],
        "blocked_fields": sorted(set(blocked_fields)),
        "stale_data": [],
    }


class AuctionDataQualityError(Exception):
    """Raised when auction data fails QC and should not be fed to LLM."""
    def __init__(self, qc: dict):
        self.qc = qc
        super().__init__(f"auction QC failed: status={qc['status']}, gate_reason={qc.get('gate_reason')}")


async def get_validated_auction_data(include_top_gainers: bool = True) -> dict:
    """获取数据后执行 QC，不合格抛出 AuctionDataQualityError。"""
    data = await get_auction_data(include_top_gainers=include_top_gainers)
    qc = _qc_auction(data)
    if qc["status"] == "failure" or not qc["auction_results_ready"] or qc["invalid_dimensions"]:
        raise AuctionDataQualityError(qc)
    data["_qc"] = qc
    return data


# ── Formatting ──────────────────────────────────────────────────────────

def format_auction_data(data: dict) -> str:
    """格式化为LLM可读文本（含时间门阻断）。"""
    invalid = set(data.get("_qc", {}).get("invalid_dimensions", []))
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

    # 涨停池
    zt = None if "zt_pool" in invalid else data.get("zt_pool")
    if zt:
        parts.append(f"【今日涨停池】共{len(zt)}只")
        for s in zt[:15]:
            parts.append(f"  {s.get('名称','')}({s.get('代码','')}) "
                        f"涨幅{s.get('涨跌幅','')}% 成交额{s.get('成交额','')} "
                        f"封板资金{s.get('封板资金','')} "
                        f"首封{s.get('首次封板时间','')} 连板{s.get('连板数','')}")
        parts.append("")

    # 强势股
    strong = None if "strong_pool" in invalid else data.get("strong_pool")
    if strong:
        parts.append(f"【强势股池】共{len(strong)}只")
        for s in strong[:10]:
            parts.append(f"  {s}")
        parts.append("")

    # 昨日涨停今日表现
    prev = None if "previous_zt" in invalid else data.get("previous_zt")
    if prev:
        parts.append(f"【昨日涨停今日表现】共{len(prev)}只")
        for s in prev[:10]:
            parts.append(f"  {s}")
        parts.append("")

    # 大笔买入异动
    bb = data.get("big_buy")
    if bb:
        parts.append(f"【盘中大笔买入异动】共{len(bb)}条")
        for s in bb[:15]:
            parts.append(f"  {s.get('时间','')} {s.get('名称','')}({s.get('代码','')}) "
                        f"板块:{s.get('板块','')} {s.get('相关信息','')}")
        parts.append("")

    # 热门排行
    hot = data.get("hot_rank")
    if hot:
        parts.append(f"【东方财富人气排行Top20】")
        for i, s in enumerate(hot[:20], 1):
            parts.append(f"  {i}. {s}")
        parts.append("")

    # 飙升榜
    up = data.get("hot_up")
    if up:
        parts.append(f"【人气飙升榜Top10】")
        for i, s in enumerate(up[:10], 1):
            parts.append(f"  {i}. {s}")
        parts.append("")

    # 涨幅排行
    gainers = data.get("top_gainers")
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
