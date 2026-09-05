"""MCP tools: stock_analysis, macro_snapshot, market_pulse

数据访问通过 engine.data_access 层，不直接 import scripts/ 模块。
"""
import json as _json

from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _check_incremental,
    logger,
)
from engine import data_access


# Tool 1: 个股全维度数据（自动增量）
# ============================================================
@mcp.tool()
async def stock_analysis(query: str) -> str:
    """获取 A 股个股全维度数据：实时行情、财报指标、资金流向、K线、新闻、分红。
    支持股票名称或代码，如"比亚迪"、"002594"。
    数据源：Wind（优先）+ AkShare（降级）+ JQData（兜底）。
    自动比对自选股历史研究记录，返回增量信息。
    返回结构化 _qc 质检 JSON + 正文数据。"""
    try:
        result = await data_access.fetch_stock_data(query)
        resolved = result["resolved"]

        if not resolved:
            return _make_error_response(f"未找到匹配的股票: {query}")

        code = resolved["code"]
        name = resolved["name"]
        data = result["data"]
        source = result["source"]
        formatted = result["formatted"]

        dispatch_trace = {
            "input_text": query,
            "resolved_name": name,
            "resolved_symbol": code,
            "resolver_source": resolved.get("resolver_source"),
            "matched_text": resolved.get("matched_text"),
            "selected_route": "stock_analysis",
            "backend_endpoint": "mcp://finance-suite/stock_analysis",
            "final_seal_called": True,
            "dispatch_called": True,
            "engine_called": True,
        }

        # 增量判断：自动比对 watchlist
        incremental = _check_incremental(code)

        qc = _qc_stock(data, source, realtime_stale=result["realtime_stale"])
        qc["dispatch_trace"] = dispatch_trace
        qc["final_seal"] = {
            "called": True,
            "selected_route": dispatch_trace["selected_route"],
            "resolved_symbol": code,
            "resolved_name": name,
        }

        # 如果 Wind 失败降级到 AkShare，标注降级
        if source == "akshare" and result.get("data_source_mode") == "auto":
            qc["fallback_source"] = "akshare"
            if qc["status"] == "success":
                qc["note"] = "Wind 不可用，已降级到 AkShare，部分高级数据（一致预期/估值分位）不可用"

        # 如果 AkShare 也失败，尝试 JQData 兜底（行情数据）
        if qc["status"] == "failure":
            try:
                from scripts.jqdata_fetch import main as jqdata_main
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                jq_result = jqdata_main('price', code=code, start_date=start_date, end_date=end_date)
                if jq_result.get('success') and jq_result.get('data'):
                    qc["status"] = "partial"
                    qc["sources"] = ["jqdata"]
                    qc["fallback_source"] = "jqdata"
                    qc["note"] = "Wind/AkShare 不可用，已降级到 JQData，仅提供近期行情数据"
                    qc["missing_dimensions"] = ["财报指标", "资金流向", "个股新闻", "分红记录"]
                    return _wrap_response(qc, _json.dumps(jq_result, ensure_ascii=False, indent=2, default=str), incremental)
            except Exception as jq_err:
                logger.warning("stock_analysis JQData fallback failed: %s", jq_err)

        return _wrap_response(qc, formatted, incremental)

    except Exception as e:
        return _make_error_response(f"stock_analysis 异常: {e}", fallback_source="akshare")


# ============================================================


# Tool 2: 宏观经济数据
# ============================================================
@mcp.tool()
async def macro_snapshot() -> str:
    """获取中国宏观经济结构化数据：GDP、CPI、PMI、M2 货币供应、LPR 利率。
    数据来源：国家统计局/央行（通过 AkShare）。
    返回结构化 _qc 质检 JSON。"""
    try:
        result = await data_access.fetch_macro_data()
        data = result["data"]
        formatted = result["formatted"]
        qc = _qc_macro(data)
        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"macro_snapshot 异常: {e}")


# ============================================================


# Tool 3: 集合竞价与盘面数据
# ============================================================
@mcp.tool()
async def market_pulse() -> str:
    """获取 A 股盘面实时数据：涨停池、强势股、昨日涨停今日表现、盘中异动、人气排行、飙升榜、涨幅排行。
    适合每日盘前/盘中了解市场温度。数据来源：东方财富。
    返回结构化 _qc 质检 JSON。"""
    try:
        result = await data_access.fetch_auction_data()
        data = result["data"]
        formatted = result["formatted"]
        qc = _qc_auction(data)
        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"market_pulse 异常: {e}")


# ============================================================
