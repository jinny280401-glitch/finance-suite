"""
Market Context Layer / 今日市场画像.

只读聚合层：基于现有 auction_data 取数结果生成市场结构摘要。
不写数据库，不改变登录、集合竞价或前端展示逻辑。
"""

from __future__ import annotations

import asyncio
from collections import Counter
from datetime import datetime
from typing import Any

import auction_data


INSUFFICIENT_TEXT = "数据不足，暂不下结论"
SOURCE_TYPE_REAL = "real"


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip().replace("%", "").replace(",", "")
        if not value or value in {"-", "--", "None", "nan"}:
            return None
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int:
    parsed = _to_float(value)
    return int(parsed) if parsed is not None else 0


def _pick(item: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in item and item.get(key) not in (None, "", "--"):
            return item.get(key)
    return default


def _format_amount(value: Any) -> str:
    parsed = _to_float(value)
    if parsed is None:
        return "--"
    if abs(parsed) >= 100000000:
        return f"{parsed / 100000000:.1f}亿"
    if abs(parsed) >= 10000:
        return f"{parsed / 10000:.1f}万"
    return f"{parsed:.0f}"


def _stock(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(_pick(item, "名称", "股票名称", "name", default="")),
        "code": str(_pick(item, "代码", "code", default="")),
        "change": _to_float(_pick(item, "涨跌幅", "change")),
        "price": _pick(item, "最新价", "price"),
        "amount": _format_amount(_pick(item, "成交额", "amount")),
        "sector": _pick(item, "所属行业", "板块", "sector"),
        "streak": _to_int(_pick(item, "连板数", "streak")),
    }


def _top_sectors(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sectors = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        sector = str(_pick(item, "所属行业", "板块", "sector", default="")).strip()
        if sector:
            sectors[sector] += 1

    total = sum(sectors.values())
    if not total:
        return []
    return [
        {"name": name, "count": count, "share": round(count / total, 3), "source": "eastmoney_auction"}
        for name, count in sectors.most_common(5)
    ]


def _average(values: list[float]) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _availability_entry(
    *,
    status: str,
    available: list[str] | None = None,
    missing: list[str] | None = None,
    source_type: str = SOURCE_TYPE_REAL,
    latency_ms: int | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "available": available or [],
        "missing": missing or [],
        "as_of": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if available else None,
        "source_type": source_type,
        "latency_ms": latency_ms,
    }


def _qc(data: dict[str, Any], payload: dict[str, Any], latency_ms: int) -> dict[str, Any]:
    dimensions = {
        "zt_pool": data.get("zt_pool"),
        "strong_pool": data.get("strong_pool"),
        "previous_zt": data.get("previous_zt"),
        "hot_rank": data.get("hot_rank"),
        "hot_up": data.get("hot_up"),
        "top_gainers": data.get("top_gainers"),
    }
    missing = [key for key, value in dimensions.items() if not value]
    present = len(dimensions) - len(missing)
    completeness = round(present / len(dimensions), 2)

    if present == 0:
        status = "failure"
        sources: list[str] = []
        source_type = "not_connected"
    elif missing:
        status = "partial"
        sources = ["eastmoney", "akshare"]
        source_type = SOURCE_TYPE_REAL
    else:
        status = "success"
        sources = ["eastmoney", "akshare"]
        source_type = SOURCE_TYPE_REAL

    blocked_fields = []
    if "top_gainers" in missing:
        blocked_fields.extend([
            "complete_market_picture",
            "top_gainers_ranking",
            "short_term_trading_points",
            "position_advice",
        ])

    return {
        "status": status,
        "sources": sources,
        "source_type": source_type,
        "completeness": completeness,
        "generated_at": payload.get("generated_at"),
        "latency_ms": latency_ms,
        "missing_dimensions": missing,
        "blocked_fields": blocked_fields,
        "fallback_source": None,
        "stale_data": [],
        "allowed_use": [
            "基础市场温度",
            "涨停池速览",
            "强势股速览",
            "昨日涨停样本观察",
        ],
        "forbidden_use": [
            "短线买卖点",
            "资金流判断",
            "完整市场画像",
            "仓位建议",
            "从缺失 top_gainers 推导主线强度",
        ],
    }


def build_context(data: dict[str, Any] | None) -> dict[str, Any]:
    started = datetime.now()
    data = data or {}

    zt_pool = data.get("zt_pool") or []
    strong_pool = data.get("strong_pool") or []
    previous_zt = data.get("previous_zt") or []
    top_gainers = data.get("top_gainers") or []

    zt_items = [_stock(item) for item in zt_pool if isinstance(item, dict)]
    prev_changes = [
        _to_float(_pick(item, "涨跌幅", "change"))
        for item in previous_zt
        if isinstance(item, dict)
    ]
    prev_changes = [value for value in prev_changes if value is not None]
    large_turnover = [_stock(item) for item in top_gainers[:20] if isinstance(item, dict)]
    sectors = _top_sectors(zt_pool)

    zt_count = len(zt_pool)
    strong_count = len(strong_pool)
    top_sector = sectors[0] if sectors else None
    highest_streak = max([item["streak"] for item in zt_items] or [0])
    continuation_rate = (
        round(len([item for item in zt_items if item["streak"] >= 2]) / zt_count * 100, 1)
        if zt_count
        else None
    )
    open_ratio = (
        round(strong_count / (zt_count + strong_count) * 100, 1)
        if (zt_count + strong_count)
        else None
    )
    prev_avg = _average(prev_changes)
    prev_positive_ratio = (
        round(len([value for value in prev_changes if value > 0]) / len(prev_changes) * 100, 1)
        if prev_changes
        else None
    )

    has_core = bool(zt_pool or strong_pool or previous_zt or data.get("hot_rank") or data.get("hot_up"))
    missing_top_gainers = not bool(top_gainers)

    if not has_core:
        conclusion = INSUFFICIENT_TEXT
        preference = INSUFFICIENT_TEXT
        concentration = INSUFFICIENT_TEXT
        breadth = INSUFFICIENT_TEXT
    else:
        if zt_count >= 80:
            preference = "偏活跃"
        elif zt_count >= 40:
            preference = "中性偏强"
        else:
            preference = "偏弱"

        if top_sector and top_sector["share"] >= 0.25:
            concentration = "集中于主线"
            conclusion = f"{top_sector['name']}集中度较高"
        elif top_sector:
            concentration = "适中"
            conclusion = "市场结构分布相对分散"
        else:
            concentration = "分散"
            conclusion = "市场结构分布相对分散"
        breadth = f"涨停池 {zt_count} / 强势股 {strong_count}"

    monitoring = []
    if not has_core:
        monitoring.append(INSUFFICIENT_TEXT)
    else:
        if open_ratio is not None and open_ratio >= 60:
            monitoring.append("开板比例偏高，说明市场分歧较大")
        if prev_avg is not None and prev_avg < 0:
            monitoring.append("昨日涨停样本平均表现转弱，说明短线承接下降")
        if missing_top_gainers:
            monitoring.append("全市场涨幅排行暂不可用，已降级为基础市场温度")
        if not monitoring:
            monitoring.append("市场结构快项可用，等待更多维度交叉验证")

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latency_ms = int((datetime.now() - started).total_seconds() * 1000)
    available_realtime = ["zt_pool", "strong_pool", "previous_zt", "hot_rank", "hot_up"]
    missing_realtime = []
    if missing_top_gainers:
        missing_realtime.append("top_gainers")
    else:
        available_realtime.append("top_gainers")

    payload = {
        "status": "partial" if has_core and missing_top_gainers else ("success" if has_core else "failure"),
        "source": "eastmoney_akshare" if has_core else None,
        "title": "今日市场画像",
        "positioning": "市场结构摘要 / Market Context Layer",
        "generated_at": generated_at,
        "date_label": datetime.now().strftime("%Y-%m-%d"),
        "conclusion": conclusion,
        "metrics": {
            "limit_up_count": zt_count if zt_pool else None,
            "strong_pool_count": strong_count if strong_pool else None,
            "open_board_ratio": open_ratio,
            "previous_limit_avg_change_pct": prev_avg,
            "previous_limit_positive_ratio": prev_positive_ratio,
            "continuation_rate": continuation_rate,
            "highest_streak": highest_streak or None,
        },
        "context": {
            "market_preference": preference,
            "theme_concentration": concentration,
            "breadth": breadth,
            "top_sector": top_sector["name"] if top_sector else None,
        },
        "themes": sectors,
        "roles": {
            "streak_samples": sorted(
                [item for item in zt_items if item["streak"] >= 2],
                key=lambda item: item["streak"],
                reverse=True,
            )[:5],
            "large_turnover_samples": large_turnover[:5],
            "high_change_samples": large_turnover[:5],
        },
        "monitoring": monitoring,
        "data_availability": {
            "market_context": _availability_entry(
                status="partial" if has_core and missing_top_gainers else ("complete" if has_core else "unavailable"),
                available=["metrics", "themes", "context", "monitoring"] if has_core else [],
                missing=["top_gainers"] if has_core and missing_top_gainers else ([] if has_core else ["market_context"]),
                source_type=SOURCE_TYPE_REAL if has_core else "not_connected",
                latency_ms=latency_ms,
            ),
            "news": _availability_entry(status="unavailable", missing=["news"], source_type="missing", latency_ms=latency_ms),
            "capital_flow": _availability_entry(status="unavailable", missing=["capital_flow"], source_type="missing", latency_ms=latency_ms),
            "research": _availability_entry(status="unavailable", missing=["research"], source_type="missing", latency_ms=latency_ms),
            "realtime": _availability_entry(
                status="partial" if has_core and missing_top_gainers else ("complete" if has_core else "unavailable"),
                available=available_realtime if has_core else [],
                missing=missing_realtime if has_core else ["realtime"],
                source_type=SOURCE_TYPE_REAL if has_core else "not_connected",
                latency_ms=latency_ms,
            ),
            "valuation": _availability_entry(status="unavailable", missing=["valuation"], source_type="missing", latency_ms=latency_ms),
        },
        "allowed_use": [
            "基础市场温度",
            "涨停池速览",
            "强势股速览",
            "昨日涨停样本观察",
        ],
        "forbidden_use": [
            "短线买卖点",
            "资金流判断",
            "完整市场画像",
            "仓位建议",
            "从缺失 top_gainers 推导主线强度",
        ],
        "disclaimer": "本页面呈现市场结构数据，不含操作建议。仅供参考，不构成投资建议。",
    }
    payload["_qc"] = _qc(data, payload, latency_ms)
    payload["_qc"]["latency_ms"] = latency_ms
    return payload


async def snapshot() -> dict[str, Any]:
    started = datetime.now()
    try:
        data = await auction_data.get_auction_data(include_top_gainers=False)
        payload = build_context(data)
        latency_ms = int((datetime.now() - started).total_seconds() * 1000)
        payload["_qc"]["latency_ms"] = latency_ms
        for entry in payload.get("data_availability", {}).values():
            entry["latency_ms"] = latency_ms
        return payload
    except Exception as e:
        latency_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "status": "failure",
            "source": None,
            "title": "今日市场画像",
            "positioning": "市场结构摘要 / Market Context Layer",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_label": datetime.now().strftime("%Y-%m-%d"),
            "conclusion": INSUFFICIENT_TEXT,
            "metrics": {},
            "context": {
                "market_preference": INSUFFICIENT_TEXT,
                "theme_concentration": INSUFFICIENT_TEXT,
                "breadth": INSUFFICIENT_TEXT,
                "top_sector": None,
            },
            "themes": [],
            "roles": {"streak_samples": [], "large_turnover_samples": [], "high_change_samples": []},
            "monitoring": [INSUFFICIENT_TEXT],
            "data_availability": {
                key: _availability_entry(status="unavailable", missing=[key], source_type="not_connected", latency_ms=latency_ms)
                for key in ("market_context", "news", "capital_flow", "research", "realtime", "valuation")
            },
            "allowed_use": [],
            "forbidden_use": [
                "短线买卖点",
                "资金流判断",
                "完整市场画像",
                "仓位建议",
            ],
            "disclaimer": "本页面呈现市场结构数据，不含操作建议。仅供参考，不构成投资建议。",
            "_qc": {
                "status": "failure",
                "sources": [],
                "source_type": "not_connected",
                "completeness": 0,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "latency_ms": latency_ms,
                "missing_dimensions": ["market_context"],
                "blocked_fields": ["market_context"],
                "fallback_source": None,
                "stale_data": [],
                "error": str(e),
            },
        }


def snapshot_sync() -> dict[str, Any]:
    return asyncio.run(snapshot())
