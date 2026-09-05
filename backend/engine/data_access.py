"""
数据访问层 — MCP 工具的统一定义入口

MCP 工具不再直接 import scripts/ 模块，而是通过此层访问数据。
好处：
  1. scripts/ 路径变更不影响 MCP 工具代码
  2. 后续迁移到 engine/providers/ 时只需修改此文件
  3. MCP 工具与 web API 共享同一数据源（app/ 或 scripts/）
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── 股票数据 ─────────────────────────────────────────────────────

async def fetch_stock_data(query: str) -> dict:
    """
    获取个股全维度数据（行情/财报/资金/新闻/分红）。

    Returns:
        {
            "resolved": {"code", "name", "resolver_source", "matched_text"},
            "data": {...},           # 原始数据
            "formatted": str,        # 格式化文本
            "source": str,           # 活跃数据源
            "realtime_stale": bool,
        }
    """
    from backend.engine.skills import stock_skill as stock_data

    stock_data._load_stock_cache()
    if hasattr(stock_data, "resolve_stock_detail"):
        detail = stock_data.resolve_stock_detail(query)
    else:
        legacy = stock_data.resolve_stock(query)
        detail = (
            {
                "code": legacy[0],
                "name": legacy[1],
                "resolver_source": "legacy_resolve_stock",
                "matched_text": legacy[1],
            }
            if legacy
            else None
        )

    if not detail:
        return {"resolved": None, "data": None, "formatted": None, "source": None}

    code = detail["code"]
    name = detail["name"]

    data = await stock_data.get_stock_full_data(code)
    source = stock_data.get_active_source()
    formatted = stock_data.format_stock_data(data, stock_name=name, stock_code=code)

    return {
        "resolved": {
            "code": code,
            "name": name,
            "resolver_source": detail.get("resolver_source"),
            "matched_text": detail.get("matched_text"),
            "input_text": query,
        },
        "data": data,
        "formatted": formatted,
        "source": source,
        "realtime_stale": stock_data._is_realtime_stale(),
        "data_source_mode": getattr(stock_data, "_DATA_SOURCE", "auto"),
    }


# ── 宏观数据 ─────────────────────────────────────────────────────

async def fetch_macro_data() -> dict:
    """
    获取宏观经济数据（GDP/CPI/PMI/M2/LPR）。

    Returns:
        {"data": {...}, "formatted": str}
    """
    from backend.engine.skills import macro_skill as macro_data

    data = await macro_data.get_macro_data()
    formatted = macro_data.format_macro_data(data)
    return {"data": data, "formatted": formatted}


# ── 竞价数据 ─────────────────────────────────────────────────────

async def fetch_auction_data() -> dict:
    """
    获取集合竞价/盘面数据。

    Returns:
        {"data": {...}, "formatted": str}
    """
    from backend.engine.skills import auction_skill as auction_data

    data = await auction_data.get_auction_data()
    formatted = auction_data.format_auction_data(data)
    return {"data": data, "formatted": formatted}


# ── 搜索 ─────────────────────────────────────────────────────────

async def fetch_search(query: str, search_type: str = "stock") -> dict:
    """
    多源搜索。

    Returns:
        {"results": list, "formatted": str, "providers": dict}
    """
    from backend.engine.providers import search_provider as search_mod

    if search_type == "stock":
        results = await search_mod.multi_search_stock(query)
        formatted = search_mod.format_search_results_grouped(results)
    else:
        results = await search_mod.unified_search(query, search_type)
        formatted = search_mod.format_search_results(results)

    return {
        "results": results,
        "formatted": formatted,
        "providers": {"search_module": "engine.providers.search_provider"},
    }


async def fetch_news_search(query: str) -> dict:
    """
    新闻搜索（v2 多源）。

    Returns:
        {"results": list, "formatted": str, "provider_results": list}
    """
    from backend.engine.providers import search_provider as search_mod

    # 使用 engine.providers.search_provider 的统一搜索能力
    results = await search_mod.unified_search(query, "news")
    formatted = search_mod.format_search_results(results)

    return {
        "results": results,
        "formatted": formatted,
        "provider_results": [],
        "runtime_detail": [],
    }


# ── 视频 ─────────────────────────────────────────────────────────

async def fetch_video_content(url: str) -> dict:
    """
    视频字幕/内容提取。

    Returns:
        原始 video_data.get_video_content() 结果
    """
    from backend.engine.skills import video_skill as video_data

    return await video_data.get_video_content(url)
