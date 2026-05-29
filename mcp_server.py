"""
===============================================================================
Finance Suite MCP Server
架构图（数据源顺序）：

Wind API → Tushare Pro → JoinQuant → AkShare
  (专业版)    (500元/年)    (聚宽)      (免费)

说明：
- MCP Server 内部工具均遵循多源降级逻辑
- JoinQuant 仅在 Wind 或 Tushare 不可用时作为第三层降级
- 所有数据源调用均记录 QC 信息（status, source, completeness）
===============================================================================

将 Finance Suite 的 13 个金融工具暴露为 MCP 工具，供 Claude Code / OpenClaw 等 Agent 调用。

启动方式（stdio 模式）：
  /Users/Zhuanz/finance-suite/.venv/bin/python3.12 /Users/Zhuanz/finance-suite/mcp_server.py

工具列表：
  - stock_analysis       个股全维度数据（行情/财报/资金/新闻/分红）
  - macro_snapshot       宏观经济数据（GDP/CPI/PMI/M2/LPR）
  - market_pulse         集合竞价与盘面数据（涨停池/异动/人气排行）
  - search               多源搜索（Tavily+Brave，股票/宏观/行业/新闻/URL提取）
  - video_extract        视频内容提取（YouTube/B站字幕）
  - watchlist_manage      自选股管理（增删改查/监控/研究记录）
  - factor_scan          因子选股信号（量化扫描）
  - wind_query           Wind 数据查询（快照/财报/一致预期/同行/估值/股东/日历）
  - xueqiu_fetch         雪球数据抓取（热门帖子/热门股票/个股行情/自选股/关注动态）
  - zhihu_fetch          知乎数据抓取（热榜/搜索/问题详情）
  - sinafinance_fetch    新浪财经数据抓取（7x24实时快讯）
  - barchart_fetch       Barchart数据抓取（美股行情/期权链/Greeks/异常期权流）
  - research_reports     投行研报管理（高盛/摩根大通等顶级投行研报链接）
  - research_digest      A 股卖方研报批量脱水（东方财富/AkShare + SQLite + LLM fallback）
  - market_intel         市场情报 Sidebar 聚合（热门讨论/热股榜/自选股异动/脱水研报）
  - jqdata_query         JQData 聚宽数据查询（行情/基本信息/基金净值/财务/指数成分）
  - ths_query            同花顺 iFinD 数据查询（行情/财报/一致预期/指数成分）
  - emquant_query        东方财富 Choice 数据查询（行情/财报/一致预期/同行/宏观/估值）

Pipeline 设计：
  取数（自动增量） + 质检（结构化JSON） → LLM 分析 → 报告
  - 质检层嵌入每个工具返回值，不是独立 Agent
  - stock_analysis 自动比对 watchlist 的 last_research_timestamp，决定全量/增量
  - 每个工具返回 status: success/partial/failure + fallback_source
"""

from __future__ import annotations

import json
import sys
import os
import time
import logging
from datetime import datetime

# 确保 scripts/ 目录在 import 路径中
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("finance-suite.mcp")

mcp = FastMCP(
    "finance-suite",
    instructions=(
        "Finance Suite 金融数据 MCP 服务。"
        "提供 A 股个股分析、宏观经济、盘面数据、多源搜索、视频提取、自选股管理、因子选股、Wind 数据等工具。"
        "数据源架构：Wind API → Tushare Pro → JoinQuant → AkShare（多源降级）。"
        "每个工具返回值包含结构化 _qc 质检 JSON：status(success/partial/failure)、completeness(0-1)、"
        "missing_dimensions、stale_data、sources、fallback_source。"
        "分析时必须参考 _qc 字段，缺失维度应显式标注而非编造，降级数据源应提示用户。"
        "数据仅供参考，不构成投资建议。"
    ),
)


# ============================================================
# 质检层 — 结构化 JSON，嵌入每个工具返回值
# ============================================================

def _qc_stock(data: dict, source: str, realtime_stale: bool = False) -> dict:
    """个股数据质检：返回结构化 JSON"""
    dimensions = {
        "realtime": "实时行情",
        "financials": "财报指标",
        "fund_flow": "资金流向",
        "price_history": "K线数据",
        "news": "个股新闻",
        "dividends": "分红记录",
    }
    missing = []
    stale = []

    for key, label in dimensions.items():
        val = data.get(key)
        if val is None or val == [] or val == {}:
            missing.append(label)
        elif key == "realtime" and realtime_stale:
            stale.append({"field": label, "issue": "数据来自缓存，非真正实时（超过15分钟未刷新）"})
        elif key == "price_history" and isinstance(val, list) and val:
            last_item = val[-1]
            # 兼容 "日期" / "date" / "trade_date" 等多种字段名
            last_date_str = str(last_item.get("日期") or last_item.get("date") or last_item.get("trade_date") or "")
            if last_date_str:
                try:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                    delay_days = (datetime.now() - last_date).days
                    if delay_days > 3:
                        stale.append({"field": label, "last_date": last_date_str, "delay_days": delay_days})
                except ValueError:
                    pass

    total = len(dimensions)
    present = total - len(missing)
    completeness = round(present / total, 2) if total else 0

    return {
        "status": "success" if completeness >= 0.8 else ("partial" if completeness > 0 else "failure"),
        "completeness": completeness,
        "sources": [source],
        "fallback_source": "akshare" if source == "wind" else None,
        "missing_dimensions": missing,
        "stale_data": stale,
    }


def _qc_macro(data: dict) -> dict:
    """宏观数据质检"""
    dims = {"gdp": "GDP", "cpi": "CPI", "pmi": "PMI", "money_supply": "M2货币供应", "lpr": "LPR利率"}
    missing = [label for key, label in dims.items() if data.get(key) is None]
    total = len(dims)
    completeness = round((total - len(missing)) / total, 2)
    return {
        "status": "success" if completeness >= 0.8 else ("partial" if completeness > 0 else "failure"),
        "completeness": completeness,
        "sources": ["akshare"],
        "fallback_source": None,
        "missing_dimensions": missing,
        "stale_data": [],
    }


def _qc_auction(data: dict) -> dict:
    """盘面数据质检

    当前 market_pulse 为 AkShare 单源聚合，未做多源降级。
    _qc 字段语义：
      - sources:              本次实际成功使用的数据源
      - source_used:          主数据源标识；若未来维度级多源混用则为 "mixed"
      - attempted_sources:    本次尝试过的数据源
      - fallback_triggered:   是否触发过降级
      - fallback_source:      降级时用到的备源（未降级为 None）
      - dimension_sources:    每个维度实际取数来源，key 为英文维度标识
      - dimension_labels:     英文维度标识到中文显示名的映射
      - missing_dimensions:   本次缺失的维度（英文 key 列表）
      - missing_critical_dimensions: 缺失的"核心维度"（英文 key 列表，会触发 partial）
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

    def _present(key: str) -> bool:
        return data.get(key) not in (None, [], {})

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
    elif completeness == 1.0:
        status = "success"
    elif missing_critical:
        status = "partial"
    elif completeness >= 0.8:
        status = "success"
    else:
        status = "partial"

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
        "stale_data": [],
    }


def _wrap_response(qc: dict, content: str, incremental_info: dict | None = None) -> str:
    """统一封装：_qc JSON + 正文内容"""
    envelope = {"_qc": qc}
    if incremental_info:
        envelope["_incremental"] = incremental_info
    return json.dumps(envelope, ensure_ascii=False) + "\n\n" + content


def _make_error_response(error_msg: str, fallback_source: str | None = None) -> str:
    """工具失败时的标准化返回"""
    qc = {
        "status": "failure",
        "completeness": 0,
        "sources": [],
        "fallback_source": fallback_source,
        "missing_dimensions": ["all"],
        "stale_data": [],
        "error": error_msg,
    }
    return json.dumps({"_qc": qc}, ensure_ascii=False)


def _format_jq_signals(data: dict) -> str:
    """格式化 JoinQuant 基本面因子选股结果"""
    if "error" in data:
        return f"【JoinQuant 因子选股】数据暂不可用: {data['error']}"
    signals = data.get("signals", [])
    parts = [
        "=== 因子选股信号（JoinQuant 基本面筛选）===",
        f"扫描日期：{data.get('scan_date', '未知')}",
        f"筛选条件：PE 10-30 | ROE > 15% | 市值 50-500亿",
        "",
    ]
    if not signals:
        parts.append("今日无命中股票")
    else:
        parts.append(f"【命中股票】共 {len(signals)} 只（按 ROE 降序）")
        for i, s in enumerate(signals, 1):
            parts.append(
                f"  {i}. {s.get('name', '')}({s['code']})  "
                f"PE:{s.get('pe', '-')}  ROE:{s.get('roe', '-')}%  "
                f"市值:{s.get('market_cap', '-')}亿"
            )
    parts.append("\n注：JoinQuant 基本面筛选，非技术因子，trading-system 恢复后自动切回。")
    return "\n".join(parts)


def _joinquant_stale_entries(data: dict) -> list[dict]:
    meta = data.get("_metadata") if isinstance(data.get("_metadata"), dict) else data
    if meta.get("used_fallback_date"):
        return [{
            "source": "joinquant",
            "reason": "trial_account_delay",
            "data_date": meta.get("data_date") or data.get("scan_date"),
            "message": "JoinQuant trial account returned delayed historical data.",
        }]
    return []


# ============================================================
# 增量判断 — 自动比对 watchlist 的 last_research_timestamp
# ============================================================

def _check_incremental(code: str) -> dict | None:
    """查询 watchlist 判断是否有历史研究记录，返回增量信息或 None"""
    try:
        import watchlist
        data = watchlist._load()
        stock = watchlist._find_stock(data, code)
        if not stock:
            return None
        history = stock.get("research_history", [])
        last_date = stock.get("last_research_date")
        if not last_date or not history:
            return None
        # 计算距上次研究的天数
        try:
            last_dt = datetime.strptime(last_date, "%Y-%m-%d")
            days_since = (datetime.now() - last_dt).days
        except ValueError:
            days_since = None
        return {
            "is_incremental": True,
            "last_research_date": last_date,
            "days_since_last": days_since,
            "research_count": len(history),
            "last_findings": history[-1].get("key_findings", "") if history else "",
            "last_promises": history[-1].get("management_promises", []) if history else [],
            "tags": stock.get("tags", []),
        }
    except Exception:
        return None


# ============================================================
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
        import stock_data

        stock_data._load_stock_cache()
        resolved = stock_data.resolve_stock(query)
        if not resolved:
            return _make_error_response(f"未找到匹配的股票: {query}")

        code, name = resolved

        # 增量判断：自动比对 watchlist
        incremental = _check_incremental(code)

        data = await stock_data.get_stock_full_data(code)
        source = stock_data.get_active_source()
        qc = _qc_stock(data, source, realtime_stale=stock_data._is_realtime_stale())

        # 如果 Wind 失败降级到 AkShare，标注降级
        if source == "akshare" and stock_data._DATA_SOURCE == "auto":
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
                    import json as _json
                    return _wrap_response(qc, _json.dumps(jq_result, ensure_ascii=False, indent=2, default=str), incremental)
            except Exception as jq_err:
                logger.warning(f"stock_analysis JQData fallback failed: {jq_err}")

        formatted = stock_data.format_stock_data(data, stock_name=name, stock_code=code)
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
        import macro_data

        data = await macro_data.get_macro_data()
        qc = _qc_macro(data)
        formatted = macro_data.format_macro_data(data)
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
        import auction_data

        data = await auction_data.get_auction_data()
        qc = _qc_auction(data)
        formatted = auction_data.format_auction_data(data)
        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"market_pulse 异常: {e}")


# ============================================================
# Tool 4: 多源搜索
# ============================================================
@mcp.tool()
async def search(query: str, search_type: str = "stock") -> str:
    """多源搜索引擎（Tavily + Brave），支持 5 种模式：
    - stock: 股票多维度搜索（财报/资金/估值/新闻/股东）
    - macro: 宏观经济新闻搜索
    - industry: 行业研究搜索
    - news: 最新新闻搜索
    - extract: URL 内容提取（query 传入 URL）
    自动去重、自动降级备用引擎。
    返回结构化 _qc 质检 JSON。"""
    try:
        import search as search_mod

        if search_type == "stock":
            results = await search_mod.multi_search_stock(query)
            formatted = search_mod.format_search_results_grouped(results)
        else:
            results = await search_mod.unified_search(query, search_type)
            formatted = search_mod.format_search_results(results)

        # 搜索质检
        sources_used = []
        if search_mod._TAVILY_KEYS:
            sources_used.append("tavily")
        if search_mod._BRAVE_KEYS:
            sources_used.append("brave")

        result_count = len(results) if results else 0
        qc = {
            "status": "success" if result_count >= 3 else ("partial" if result_count > 0 else "failure"),
            "completeness": min(1.0, round(result_count / 5, 2)),
            "sources": sources_used,
            "fallback_source": "brave" if "tavily" in sources_used else ("tavily" if "brave" in sources_used else None),
            "missing_dimensions": [] if result_count > 0 else ["搜索结果"],
            "stale_data": [],
            "result_count": result_count,
        }

        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"search 异常: {e}", fallback_source="brave")


# ============================================================
# Tool 5: 视频内容提取
# ============================================================
@mcp.tool()
async def video_extract(url: str) -> str:
    """从 YouTube 或 B站 视频提取字幕/内容。
    支持格式：youtube.com、youtu.be、bilibili.com 链接。
    YouTube 使用 Supadata API，B站使用官方 API。
    返回结构化 _qc 质检 JSON。"""
    try:
        import video_data

        result = await video_data.get_video_content(url)
        success = result.get("success", False)
        is_partial = result.get("partial", False)

        qc = {
            "status": "success" if (success and not is_partial) else ("partial" if success else "failure"),
            "completeness": 1.0 if (success and not is_partial) else (0.3 if is_partial else 0),
            "sources": [result.get("source", "unknown")] if success else [],
            "fallback_source": "noembed" if "supadata" in result.get("source", "") else None,
            "missing_dimensions": [] if success else ["视频字幕"],
            "stale_data": [],
        }
        if not success:
            qc["error"] = result.get("error", "未知错误")

        formatted = json.dumps(result, ensure_ascii=False, indent=2)
        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"video_extract 异常: {e}")


# ============================================================
# Tool 6: 自选股管理
# ============================================================
@mcp.tool()
def watchlist_manage(
    action: str,
    code: str = "",
    name: str = "",
    tags: str = "",
    alert_above: float | None = None,
    alert_below: float | None = None,
    alert_change: float | None = None,
    mode: str = "",
    findings: str = "",
    promises: str = "",
) -> str:
    """管理个人自选股清单。持久化存储到 ~/.finance-suite/watchlist.json。

    action 可选值：
    - add: 添加自选股（需 code，可选 name/tags/alert_above/alert_below/alert_change）
    - remove: 移除自选股（需 code）
    - list: 列出所有自选股
    - monitor: 批量监控自选股实时行情 + 盈亏 + 价格提醒
    - update-research: 更新研究记录（需 code，可选 mode/findings/promises）
    - check-research: 查询历史研究记录（需 code）

    返回结构化 _qc 质检 JSON。"""
    try:
        import watchlist

        # 构造 argparse-like 对象
        class Args:
            pass

        args = Args()
        args.code = code
        args.name = name
        args.tags = tags
        args.alert_above = alert_above
        args.alert_below = alert_below
        args.alert_change = alert_change
        args.mode = mode
        args.findings = findings
        args.promises = promises

        if action in ("add", "remove", "update-research", "check-research") and not code:
            return _make_error_response(f"action={action} 需要提供 code 参数")

        actions_map = {
            "add": watchlist.action_add,
            "remove": watchlist.action_remove,
            "list": watchlist.action_list,
            "monitor": watchlist.action_monitor,
            "update-research": watchlist.action_update_research,
            "check-research": watchlist.action_check_research,
        }

        fn = actions_map.get(action)
        if not fn:
            return _make_error_response(f"未知 action: {action}，支持: {list(actions_map.keys())}")

        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            fn(args)
        output = buf.getvalue()

        qc = {
            "status": "success",
            "completeness": 1.0,
            "sources": ["local_watchlist"],
            "fallback_source": None,
            "missing_dimensions": [],
            "stale_data": [],
        }
        return _wrap_response(qc, output)

    except Exception as e:
        return _make_error_response(f"watchlist_manage 异常: {e}")


# ============================================================
# Tool 7: 因子选股信号
# ============================================================
@mcp.tool()
def factor_scan(date: str = "") -> str:
    """执行量化因子选股扫描，返回命中股票及评分。
    优先级：trading-system → JoinQuant → Wind → Tushare → AkShare。
    扫描可能需要 1-3 分钟。date 格式 YYYY-MM-DD，留空默认今天。
    返回结构化 _qc 质检 JSON。"""
    try:
        import factor_scan as fs
        import joinquant_data
        import wind_data
        import tushare_data

        scan_date = date or None
        data = fs.get_factor_signals(scan_date)
        has_error = "error" in data
        source_used = data.get("source_used", "trading_system")
        logger.info(f"factor_scan start date={scan_date or 'today'} source=trading_system status={'error' if has_error else 'ok'}")

        # 第二层：JoinQuant
        if has_error:
            try:
                jq_data = joinquant_data.get_factor_signals(scan_date)
                if jq_data and "signals" in jq_data and "error" not in jq_data:
                    data = jq_data
                    has_error = False
                    source_used = "joinquant"
                    logger.info("factor_scan fallback success source=joinquant")
                else:
                    logger.warning("factor_scan fallback source=joinquant returned empty/error")
            except Exception as e:
                logger.warning(f"factor_scan fallback source=joinquant failed: {e}")

        # 第三层：Wind（以估值/快照近似筛选信号）
        if has_error:
            try:
                universe = ["600519.SH", "000858.SZ", "600036.SH", "601318.SH", "000333.SZ"]
                signals = []
                for code in universe:
                    snap = wind_data.get_stock_snapshot(code) or {}
                    pe = snap.get("pe") or snap.get("pe_ttm")
                    roe = snap.get("roe")
                    mv = snap.get("market_cap") or snap.get("total_mv")
                    if pe is None or roe is None or mv is None:
                        continue
                    try:
                        pe_f = float(pe)
                        roe_f = float(roe)
                        mv_f = float(mv)
                    except Exception:
                        continue
                    if 10 <= pe_f <= 30 and roe_f > 15 and 50 <= mv_f <= 500:
                        signals.append({"code": code, "name": code, "pe": pe_f, "roe": roe_f, "market_cap": mv_f})
                data = {"signals": signals, "scan_date": datetime.now().strftime("%Y-%m-%d")}
                has_error = False
                source_used = "wind"
                logger.info("factor_scan fallback success source=wind")
            except Exception as e:
                logger.warning(f"factor_scan fallback source=wind failed: {e}")

        # 第四层：Tushare（以快照近似筛选信号）
        if has_error:
            try:
                universe = ["600519.SH", "000858.SZ", "600036.SH", "601318.SH", "000333.SZ"]
                signals = []
                for code in universe:
                    snap = tushare_data.get_stock_snapshot(code) or {}
                    pe = snap.get("pe") or snap.get("pe_ttm")
                    roe = snap.get("roe")
                    mv = snap.get("market_cap") or snap.get("total_mv")
                    if pe is None or roe is None or mv is None:
                        continue
                    try:
                        pe_f = float(pe)
                        roe_f = float(roe)
                        mv_f = float(mv)
                    except Exception:
                        continue
                    if 10 <= pe_f <= 30 and roe_f > 15 and 50 <= mv_f <= 500:
                        signals.append({"code": code, "name": code, "pe": pe_f, "roe": roe_f, "market_cap": mv_f})
                data = {"signals": signals, "scan_date": datetime.now().strftime("%Y-%m-%d")}
                has_error = False
                source_used = "tushare"
                logger.info("factor_scan fallback success source=tushare")
            except Exception as e:
                logger.warning(f"factor_scan fallback source=tushare failed: {e}")

        # 第五层：AkShare（兜底为空结果，不抛错）
        if has_error:
            data = {"signals": [], "scan_date": datetime.now().strftime("%Y-%m-%d"), "note": "AkShare fallback: no factor model"}
            has_error = False
            source_used = "akshare"
            logger.warning("factor_scan fallback source=akshare used")

        has_signals = bool(data.get("signals"))
        market_env = data.get("market_env") or {}
        if isinstance(data, dict) and isinstance(data.get("_qc"), dict):
            qc = data["_qc"]
        else:
            fallback_triggered = source_used != "trading_system"
            attempted_sources = ["trading_system"] if not fallback_triggered else ["trading_system", source_used]
            qc = {
                "status": "success" if has_signals else "partial",
                "completeness": 1.0 if has_signals else (0.5 if market_env else 0.3),
                "sources": attempted_sources,
                "fallback_source": source_used if fallback_triggered else None,
                "missing_dimensions": [] if has_signals else (["候选信号"] if market_env else ["候选信号", "市场环境"]),
                "stale_data": _joinquant_stale_entries(data) if source_used == "joinquant" else [],
            }
            data["_qc"] = qc
        data.setdefault("source_used", source_used)
        data.setdefault("fallback_chain", ["trading_system", "joinquant", "wind", "tushare", "akshare"])
        data.setdefault("fallback_triggered", source_used != "trading_system")
        logger.info(
            f"factor_scan success scan_date={data.get('scan_date', scan_date or 'today')} "
            f"source={data.get('source_used')} fallback_triggered={data.get('fallback_triggered')} "
            f"data_date={(data.get('_metadata') or {}).get('data_date') or data.get('scan_date')}"
        )

        if source_used == "trading_system":
            formatted = fs.format_factor_signals(data)
        elif source_used == "joinquant":
            formatted = (
                f"{_format_jq_signals(data)}\n\n"
                f"{json.dumps(data, ensure_ascii=False, indent=2)}"
            )
        else:
            formatted = json.dumps({"source": source_used, "data": data}, ensure_ascii=False, indent=2)

        return _wrap_response(qc, formatted)

    except Exception as e:
        logger.exception(f"factor_scan fatal error: {e}")
        return _make_error_response(f"factor_scan 异常: {e}")


# ============================================================
# Tool 8: 金融数据查询（三层降级：Wind → Tushare → AkShare）
# ============================================================
@mcp.tool()
def wind_query(action: str, code: str = "", max_peers: int = 10) -> str:
    """Wind 查询工具（支持多源降级）

    数据源优先级：
        - Wind → Tushare Pro → JoinQuant（聚宽）→ AkShare（免费）

    valuation 动作：
        - Wind → JoinQuant → Tushare → AkShare（JoinQuant 历史分位更完整）

    connect action 返回值示例：
        {
            "wind": True,
            "tushare": True,
            "joinquant": jq_status.get("connected", False),
            "akshare": True,
            "priority": "Wind → Tushare → JoinQuant → AkShare"
        }

    action 可选值：
        - connect: 检查数据源连接状态
        - stock: 个股快照（价格/市值/PE/PB/ROE）
        - financials: 完整三大报表（近4期）
        - consensus: 卖方一致预期（净利润/EPS/ROE/目标价/评级）
        - peers: 同行业可比公司对比
        - valuation: 历史估值分位（PE/PB 10年百分位）
        - shareholders: 前十大股东及持股变动
        - calendar: 财报披露日期

    参数：
        action: str, 查询动作类型
        code: str, 股票代码（connect 动作不需要）
        max_peers: int, peers 动作返回的最大同行数量

    返回：
        dict, 包含数据及 _qc 质检信息（status, completeness, sources, fallback_source）
    """
    try:
        import wind_data
        import tushare_data
        import joinquant_data

        if action == "connect":
            # 检查所有数据源连接状态
            wind_status = wind_data.check_connection()
            tushare_status = tushare_data.check_connection()
            jq_status = joinquant_data.check_connection()

            sources = []
            if wind_status.get("connected"):
                sources.append("wind")
            if tushare_status.get("connected"):
                sources.append("tushare")
            if jq_status.get("connected"):
                sources.append("joinquant")
            sources.append("akshare")  # AkShare 总是可用

            qc = {
                "status": "success",
                "completeness": 1.0,
                "sources": sources,
                "fallback_source": None,
                "missing_dimensions": [],
                "stale_data": [],
            }
            result = {
                "wind": wind_status.get("connected", False),
                "tushare": tushare_status.get("connected", False),
                "joinquant": jq_status.get("connected", False),
                "akshare": True,
                "priority": "Wind → Tushare → JoinQuant → AkShare",
                "joinquant_detail": jq_status,
            }
            return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2))

        if not code:
            return _make_error_response(f"action={action} 需要提供 code 参数", fallback_source="tushare/akshare")

        result = None
        source_used = None

        # 按动作定义优先级链
        chains = {
            "stock": ["wind", "tushare", "joinquant"],
            "financials": ["tushare", "joinquant", "akshare"],
            "consensus": ["wind", "tushare"],
            "peers": ["wind", "tushare"],
            "valuation": ["wind", "joinquant", "tushare", "akshare"],
            "shareholders": ["wind"],
            "calendar": ["wind"],
        }
        chain = chains.get(action, ["wind", "tushare", "joinquant"])
        logger.info(f"wind_query start action={action} code={code} chain={' -> '.join(chain)}")

        def _try_wind() -> dict | None:
            actions_map = {
                "stock": lambda: wind_data.get_stock_snapshot(code),
                "financials": lambda: wind_data.get_financials(code),
                "consensus": lambda: wind_data.get_consensus_estimates(code),
                "peers": lambda: wind_data.get_industry_peers(code, max_peers),
                "valuation": lambda: wind_data.get_valuation_history(code),
                "shareholders": lambda: wind_data.get_major_shareholders(code),
                "calendar": lambda: wind_data.get_earnings_calendar(code),
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_tushare() -> dict | None:
            actions_map = {
                "stock": lambda: tushare_data.get_stock_snapshot(code),
                "financials": lambda: tushare_data.get_financials(code, "income"),
                "consensus": lambda: tushare_data.get_consensus_estimates(code),
                "peers": lambda: tushare_data.get_industry_peers(code, max_peers),
                "valuation": lambda: tushare_data.get_valuation_history(code) if hasattr(tushare_data, "get_valuation_history") else None,
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_joinquant() -> dict | None:
            actions_map = {
                "stock": lambda: joinquant_data.get_stock_snapshot(code),
                "valuation": lambda: joinquant_data.get_valuation_history(code),
                "financials": lambda: joinquant_data.get_financials(code) if hasattr(joinquant_data, "get_financials") else None,
            }
            fn = actions_map.get(action)
            return fn() if fn else None

        def _try_akshare() -> dict | None:
            # 仅对 financials / valuation 提供轻量兜底
            if action == "financials":
                try:
                    import akshare as ak
                    bare = code.split(".")[0]
                    df = ak.stock_financial_analysis_indicator(symbol=bare, start_year="2023")
                    if df is not None and len(df) > 0:
                        return {"financials": df.head(4).to_dict(orient="records")}
                except Exception:
                    return None
            if action == "valuation":
                return {"note": "akshare fallback: valuation history unavailable"}
            return None

        runners = {
            "wind": _try_wind,
            "tushare": _try_tushare,
            "joinquant": _try_joinquant,
            "akshare": _try_akshare,
        }

        for source in chain:
            try:
                candidate = runners[source]()
                if candidate:
                    result = candidate
                    source_used = source
                    logger.info(f"wind_query success action={action} code={code} source={source}")
                    break
                logger.warning(f"wind_query empty action={action} code={code} source={source}")
            except Exception as e:
                logger.warning(f"wind_query failed action={action} code={code} source={source} err={e}")

        if not result:
            qc = {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "fallback_source": "akshare",
                "missing_dimensions": [f"{action}"],
                "stale_data": [],
                "error": f"{action} 多源查询失败（Wind/Tushare/JoinQuant/AkShare）",
            }
            return _wrap_response(qc, "")

        fallback_map = {"wind": "tushare", "tushare": "joinquant", "joinquant": "akshare", "akshare": None}
        qc = {
            "status": "success",
            "completeness": 1.0,
            "sources": [source_used],
            "fallback_source": fallback_map.get(source_used),
            "missing_dimensions": [],
            "stale_data": _joinquant_stale_entries(result) if source_used == "joinquant" else [],
        }
        formatted = json.dumps({
            "source": source_used, "code": code, "action": action, "data": result,
        }, ensure_ascii=False, indent=2, default=str)
        return _wrap_response(qc, formatted)

    except Exception as e:
        logger.exception(f"wind_query fatal error action={action} code={code}: {e}")
        return _make_error_response(f"wind_query 异常: {e}", fallback_source="tushare/akshare")


# ============================================================
# Tool 9: 雪球数据抓取（通过 autocli）
# ============================================================
@mcp.tool()
def xueqiu_fetch(command: str, symbol: str = "", limit: int = 10) -> str:
    """通过 autocli 抓取雪球数据（复用 Chrome 登录状态）。

    command 可选值：
    - hot: 雪球热门动态（大V观点、市场讨论）
    - hot-stock: 雪球热门股票榜（人气排行）
    - stock: 个股实时行情（需提供 symbol，如 SH600519）
    - watchlist: 自选股列表（需登录）
    - feed: 关注动态（需登录）
    - search: 搜索股票（需提供 symbol 作为关键词）
    - earnings-date: 财报发布日期（需提供 symbol）

    返回结构化 _qc 质检 JSON + JSON 格式数据。
    """
    try:
        import subprocess

        # 构建 autocli 命令
        autocli_path = os.path.expanduser("~/bin/autocli")
        if not os.path.exists(autocli_path):
            return _make_error_response("autocli 未安装，请先安装: curl -fsSL https://raw.githubusercontent.com/nashsu/AutoCLI/main/scripts/install.sh | sh")

        cmd = [autocli_path, "xueqiu", command]

        # 根据命令类型添加参数
        if command in ("stock", "earnings-date"):
            if not symbol:
                return _make_error_response(f"command={command} 需要提供 symbol 参数（如 SH600519）")
            cmd.append(symbol)
        elif command == "search":
            if not symbol:
                return _make_error_response("command=search 需要提供 symbol 参数作为搜索关键词")
            cmd.extend(["--query", symbol])

        # 添加通用参数
        if command not in ("stock", "earnings-date"):
            cmd.extend(["--limit", str(limit)])
        cmd.extend(["--format", "json"])

        # 设置环境变量（绕过代理）
        env = os.environ.copy()
        env["NO_PROXY"] = "localhost,127.0.0.1"
        env["no_proxy"] = "localhost,127.0.0.1"

        # 执行命令（某些命令如 hot-stock 可能需要更长时间）
        timeout_seconds = 60 if command in ("hot-stock", "feed") else 30
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Not logged in" in error_msg or "HTTP 400" in error_msg:
                return _make_error_response(f"雪球未登录，请在 Chrome 中登录 xueqiu.com 后重试")
            elif "timeout" in error_msg.lower():
                return _make_error_response(f"autocli daemon 超时，请检查 Chrome 扩展是否已加载")
            else:
                return _make_error_response(f"autocli 执行失败: {error_msg}")

        # 解析 JSON 输出
        output = result.stdout.strip()
        if not output:
            return _make_error_response("autocli 返回空数据")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return _make_error_response(f"autocli 返回非 JSON 数据: {output[:200]}")

        # 质检
        has_data = bool(data) and (isinstance(data, list) and len(data) > 0 or isinstance(data, dict))
        qc = {
            "status": "success" if has_data else "partial",
            "completeness": 1.0 if has_data else 0.5,
            "sources": ["xueqiu_autocli"],
            "fallback_source": None,
            "missing_dimensions": [] if has_data else ["数据为空"],
            "stale_data": [],
        }

        return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))

    except subprocess.TimeoutExpired:
        return _make_error_response("autocli 执行超时（30秒），请检查网络或 Chrome 扩展状态")
    except Exception as e:
        return _make_error_response(f"xueqiu_fetch 异常: {e}")


# ============================================================
# Tool 10: 知乎数据抓取（通过 autocli）
# ============================================================
@mcp.tool()
def zhihu_fetch(command: str, query: str = "", question_id: str = "", limit: int = 10) -> str:
    """通过 autocli 抓取知乎数据（复用 Chrome 登录状态）。

    command 可选值：
    - hot: 知乎热榜（热度排名、问题标题、回答数）
    - search: 搜索知乎内容（需提供 query 关键词）
    - question: 问题详情和回答（需提供 question_id，从 URL 中获取）

    示例：
    - zhihu_fetch('hot', limit=10)
    - zhihu_fetch('search', query='人工智能')
    - zhihu_fetch('question', question_id='2031077519936287770', limit=5)

    返回结构化 _qc 质检 JSON + JSON 格式数据。
    """
    try:
        import subprocess

        autocli_path = os.path.expanduser("~/bin/autocli")
        if not os.path.exists(autocli_path):
            return _make_error_response("autocli 未安装")

        cmd = [autocli_path, "zhihu", command]

        if command == "search":
            if not query:
                return _make_error_response("command=search 需要提供 query 参数")
            cmd.append(query)
        elif command == "question":
            if not question_id:
                return _make_error_response("command=question 需要提供 question_id 参数")
            cmd.append(question_id)

        cmd.extend(["--limit", str(limit), "--format", "json"])

        env = os.environ.copy()
        env["NO_PROXY"] = "localhost,127.0.0.1"
        env["no_proxy"] = "localhost,127.0.0.1"

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Not logged in" in error_msg or "HTTP 400" in error_msg:
                return _make_error_response("知乎未登录，请在 Chrome 中登录 zhihu.com 后重试")
            return _make_error_response(f"autocli 执行失败: {error_msg}")

        output = result.stdout.strip()
        if not output:
            return _make_error_response("autocli 返回空数据")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return _make_error_response(f"autocli 返回非 JSON 数据: {output[:200]}")

        has_data = bool(data) and isinstance(data, list) and len(data) > 0
        qc = {
            "status": "success" if has_data else "partial",
            "completeness": 1.0 if has_data else 0.5,
            "sources": ["zhihu_autocli"],
            "fallback_source": None,
            "missing_dimensions": [] if has_data else ["数据为空（可能需要登录）"],
            "stale_data": [],
        }

        return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))

    except subprocess.TimeoutExpired:
        return _make_error_response("autocli 执行超时（30秒）")
    except Exception as e:
        return _make_error_response(f"zhihu_fetch 异常: {e}")


def _autocli_run(platform: str, subcmd: list[str], timeout: int = 30) -> tuple[bool, any, str]:
    """通用 autocli 执行器，返回 (success, data, error_msg)"""
    import subprocess
    autocli_path = os.path.expanduser("~/bin/autocli")
    cmd = [autocli_path, platform] + subcmd + ["--format", "json"]
    env = os.environ.copy()
    env["NO_PROXY"] = "localhost,127.0.0.1"
    env["no_proxy"] = "localhost,127.0.0.1"
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        if result.returncode != 0:
            return False, None, result.stderr.strip() or result.stdout.strip()
        data = json.loads(result.stdout.strip())
        return True, data, ""
    except subprocess.TimeoutExpired:
        return False, None, f"autocli 执行超时（{timeout}秒）"
    except json.JSONDecodeError as e:
        return False, None, f"JSON 解析失败: {e}"


# ============================================================
# Tool 11: 新浪财经实时快讯
# ============================================================
@mcp.tool()
def sinafinance_fetch(limit: int = 20) -> str:
    """抓取新浪财经 7x24 小时实时快讯。无需登录，直接调用 API。
    返回最新财经新闻，包含时间、内容、阅读量。
    返回结构化 _qc 质检 JSON。"""
    ok, data, err = _autocli_run("sinafinance", ["news", "--limit", str(limit)])
    if not ok:
        return _make_error_response(f"sinafinance_fetch 失败: {err}")
    has_data = bool(data)
    qc = {
        "status": "success" if has_data else "partial",
        "completeness": 1.0 if has_data else 0.0,
        "sources": ["sinafinance"],
        "fallback_source": None,
        "missing_dimensions": [] if has_data else ["数据为空"],
        "stale_data": [],
    }
    return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================
# Tool 12: Barchart 期权数据
# ============================================================
@mcp.tool()
def barchart_fetch(command: str, symbol: str = "") -> str:
    """抓取 Barchart 期权和行情数据。需要 Chrome 扩展连接。

    command 可选值：
    - quote: 股票行情（含 PE、EPS、均量）
    - options: 期权链（含 Greeks、IV、成交量、持仓量）
    - greeks: 期权 Greeks 总览（IV、delta、gamma、theta、vega）
    - flow: 异常期权流（大单、异常活动）

    symbol 示例：AAPL、TSLA、NVDA、SPY
    返回结构化 _qc 质检 JSON。"""
    if not symbol:
        return _make_error_response("需要提供 symbol 参数，如 AAPL")
    ok, data, err = _autocli_run("barchart", [command, symbol.upper()], timeout=45)
    if not ok:
        return _make_error_response(f"barchart_fetch 失败: {err}")
    has_data = bool(data)
    qc = {
        "status": "success" if has_data else "failure",
        "completeness": 1.0 if has_data else 0.0,
        "sources": ["barchart"],
        "fallback_source": None,
        "missing_dimensions": [] if has_data else [command],
        "stale_data": [],
    }
    return _wrap_response(qc, json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================
# Tool 13: 投行研报管理
# ============================================================
@mcp.tool()
def research_reports(action: str, code: str = "", industry: str = "", tag: str = "", keyword: str = "", limit: int = 10) -> str:
    """管理顶级投行研报链接（高盛、摩根大通、桥水等）。

    数据来源：
    - 微信公众号"Goldman Sachs"（Huaban1925）- 每日Pitch + 研报汇总
    - IMA知识库 - 2026年八大顶级投行研报，每日更新3+次

    action 可选值：
    - sources: 获取研报来源信息（微信公众号 + IMA知识库入口）
    - list: 获取最新精选研报列表
    - by-stock: 按股票代码查询相关研报（需提供 code）
    - by-industry: 按行业查询相关研报（需提供 industry）
    - by-tag: 按标签查询相关研报（需提供 tag）
    - search: 关键词搜索研报（需提供 keyword）

    返回结构化 _qc 质检 JSON + 研报来源/精选研报列表。

    示例：
    - research_reports("sources")  # 获取研报来源入口
    - research_reports("by-stock", code="600519.SH")
    - research_reports("by-industry", industry="白酒")
    - research_reports("search", keyword="茅台")
    """
    try:
        import research_reports as rr_module

        manager = rr_module.ResearchReportManager()

        if action == "sources":
            sources = manager.get_sources()
            qc = {
                "status": "success",
                "completeness": 1.0,
                "sources": ["research_reports"],
                "fallback_source": None,
                "missing_dimensions": [],
                "stale_data": [],
            }
            result = {
                "action": "sources",
                "sources": sources,
                "note": "研报来源入口，需手动访问获取最新内容"
            }
            return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2))

        elif action == "list":
            reports = manager.get_latest_reports(limit)
        elif action == "by-stock":
            if not code:
                return _make_error_response("action=by-stock 需要提供 code 参数")
            reports = manager.get_reports_by_stock(code)
        elif action == "by-industry":
            if not industry:
                return _make_error_response("action=by-industry 需要提供 industry 参数")
            reports = manager.get_reports_by_industry(industry)
        elif action == "by-tag":
            if not tag:
                return _make_error_response("action=by-tag 需要提供 tag 参数")
            reports = manager.get_reports_by_tag(tag)
        elif action == "search":
            if not keyword:
                return _make_error_response("action=search 需要提供 keyword 参数")
            reports = manager.search_reports(keyword)
        else:
            return _make_error_response(f"未知 action: {action}，可选值: sources/list/by-stock/by-industry/by-tag/search")

        # 对于查询操作，同时返回 sources 和 featured_reports
        sources = manager.get_sources()
        has_data = bool(reports)
        qc = {
            "status": "success" if has_data else "partial",
            "completeness": 1.0 if has_data else 0.5,
            "sources": ["research_reports"],
            "fallback_source": None,
            "missing_dimensions": [] if has_data else ["精选研报数据"],
            "stale_data": [],
        }

        result = {
            "action": action,
            "sources": sources,
            "featured_reports": {
                "count": len(reports),
                "reports": reports
            },
            "note": "精选研报为手动维护，更多研报请访问 sources 中的入口"
        }

        return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"research_reports 异常: {e}")


# ============================================================
# Tool 14: A 股卖方研报批量脱水
# ============================================================
@mcp.tool()
def research_digest(
    action: str = "latest",
    code: str = "",
    industry: str = "",
    keyword: str = "",
    report_id: str = "",
    limit: int = 30,
    mode: str = "batch",
    max_llm: int = 0,
    force_refresh: bool = False,
) -> str:
    """A 股卖方研报批量脱水。

    action 可选值：
    - latest: 全市场最新研报
    - by_stock: 按股票代码查询（code）
    - by_industry: 按行业过滤（industry）
    - by_keyword: 按标题/股票名搜索（keyword）
    - digest_one: 单篇深度脱水（report_id）

    默认 max_llm=0，MCP/HTTP 即时调用优先读缓存；cron 预计算时再打开 LLM。
    返回结构化 _qc + market_intel Sidebar 契约 JSON。
    """
    try:
        import research_digest as rd

        normalized_action = (action or "latest").replace("-", "_")
        if normalized_action == "latest":
            out = rd.latest(limit=limit, digest_mode=mode, max_llm_per_call=max_llm, force_refresh=force_refresh)
        elif normalized_action == "by_stock":
            out = rd.by_stock(code, limit=limit, digest_mode=mode, max_llm_per_call=max_llm)
        elif normalized_action == "by_industry":
            out = rd.by_industry(industry, limit=limit, digest_mode=mode)
        elif normalized_action == "by_keyword":
            out = rd.by_keyword(keyword, limit=limit, digest_mode=mode)
        elif normalized_action == "digest_one":
            out = rd.digest_one(report_id, mode=mode)
        else:
            return _make_error_response("未知 action: " + action + "，支持 latest/by_stock/by_industry/by_keyword/digest_one")

        qc = out.get("_qc", {}) if isinstance(out, dict) else {}
        return _wrap_response(qc, json.dumps(out, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"research_digest 异常: {e}", fallback_source="eastmoney/akshare")


# ============================================================
# Tool 15: 市场情报 Sidebar 聚合
# ============================================================
@mcp.tool()
def market_intel(modules: str = "", limit: int = 10, mode: str = "batch") -> str:
    """聚合市场情报 Sidebar 四板块。

    modules 逗号分隔，可选：
    - discussions
    - hot_stocks
    - watch_alerts
    - research

    留空默认全部。返回 {panels, _qc, meta}，其中每个 panel 都是统一 {items,_qc,meta} 契约。
    """
    try:
        import market_intel as mi

        selected = [m.strip() for m in modules.split(",") if m.strip()] if modules else None
        out = mi.aggregate(modules=selected, limit=limit, digest_mode=mode)
        qc = out.get("_qc", {}) if isinstance(out, dict) else {}
        return _wrap_response(qc, json.dumps(out, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"market_intel 异常: {e}")


@mcp.tool()
def jqdata_query(
    action: str,
    code: str = "",
    start_date: str = "",
    end_date: str = "",
    frequency: str = "daily",
    fields: str = "",
    date: str = "",
    index_code: str = "",
    fund_type: str = "etf",
    limit: int = 20
) -> str:
    """
    通过 JQData（聚宽数据）获取金融数据。

    action 可选值:
    - auth: 测试认证和查询额度
    - price: 获取股票/ETF行情数据（需 code, 可选 start_date/end_date/frequency/fields）
    - info: 获取证券基本信息（股票/ETF/基金均可，需 code）
    - fund_nav: 获取场外基金净值（需 code=6位基金代码如000001, 可选 start_date/end_date/limit）
    - fund_list: 获取基金列表（可选 fund_type=etf/lof/open_fund/money_market_fund）
    - fund_info: 获取场内基金(ETF/LOF)信息+近期行情（需 code）
    - fundamentals: 获取财务数据（需 code, 可选 date）
    - index_stocks: 获取指数成分股（需 index_code, 可选 date）

    示例:
    - jqdata_query('auth')
    - jqdata_query('price', code='000001.XSHE', start_date='2026-01-26', end_date='2026-02-02')
    - jqdata_query('fund_nav', code='000001', limit=10)
    - jqdata_query('fund_nav', code='110022', start_date='2026-01-01')
    - jqdata_query('fund_list', fund_type='etf')
    - jqdata_query('fund_info', code='510300.XSHG')
    - jqdata_query('info', code='510300.XSHG')
    - jqdata_query('index_stocks', index_code='000300.XSHG')

    数据时间范围限制: 2025-01-26 至 2026-02-02（试用账号）
    返回结构化 _qc 质检 JSON。
    """
    try:
        from scripts.jqdata_fetch import main as jqdata_main

        # 按 action 精确分发参数，避免把 price 专用参数传给基金/指数接口。
        kwargs = {}
        if action in {"price", "info", "fund_nav", "fund_info", "fundamentals"} and code:
            kwargs["code"] = code
        if action == "price":
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            if frequency:
                kwargs["frequency"] = frequency
            if fields:
                kwargs["fields"] = fields.split(",")
        elif action == "fund_nav":
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date
            kwargs["limit"] = limit
        elif action == "fund_list":
            kwargs["fund_type"] = fund_type
        elif action == "fundamentals":
            if date:
                kwargs["date"] = date
        elif action == "index_stocks":
            if index_code:
                kwargs["index_code"] = index_code
            if date:
                kwargs["date"] = date

        # 调用 JQData
        result = jqdata_main(action, **kwargs)

        # 质检
        if result.get('success'):
            qc = {
                "status": "success",
                "completeness": 1.0,
                "sources": ["jqdata"],
                "fallback_source": None,
                "missing_dimensions": [],
                "stale_data": [],
                "note": "JQData 数据范围: 2025-01-26 至 2026-02-02"
            }
        else:
            qc = {
                "status": "failure",
                "completeness": 0.0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["JQData 数据"],
                "stale_data": [],
                "error": result.get('error', '未知错误')
            }

        return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"jqdata_query 异常: {e}")


# ============================================================
# Tool 17: 同花顺 iFinD 数据查询
# ============================================================
@mcp.tool()
def ths_query(action: str, code: str = "") -> str:
    """同花顺 iFinD 数据查询工具

    action 可选值：
    - connect: 检查连接状态
    - stock: 个股快照（价格/市值/PE/PB/ROE）
    - financials: 财务数据（营收/净利润/毛利率/ROE，近4期）
    - consensus: 卖方一致预期（净利润预测/EPS/目标价/评级）
    - index: 指数成分股（code 传指数代码）

    接入方式（自动选择）：
    - iFinDPy SDK（THS_USERNAME + THS_PASSWORD）
    - HTTP REST API（THS_TOKEN，从 quantapi.51ifind.com 后台复制）

    返回结构化 _qc 质检 JSON。
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
        import ifind_data as ths

        if action == "connect":
            result = ths.check_connection()
        elif action == "stock":
            result = ths.get_stock_snapshot(code)
        elif action == "financials":
            result = ths.get_financials(code)
        elif action == "consensus":
            result = ths.get_consensus_estimates(code)
        elif action == "index":
            result = ths.get_index_constituents(code)
        else:
            return _make_error_response(f"未知 action: {action}，支持 connect/stock/financials/consensus/index")

        if not result:
            qc = {
                "status": "failure",
                "completeness": 0.0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["iFinD 数据"],
                "stale_data": [],
                "error": "iFinD 连接失败或查询无结果，请确认 THS_TOKEN 或 iFinDPy SDK 已配置",
            }
            return _wrap_response(qc, json.dumps({"success": False}, ensure_ascii=False))

        qc = {
            "status": "success",
            "completeness": 1.0,
            "sources": ["ifind"],
            "fallback_source": None,
            "missing_dimensions": [],
            "stale_data": [],
        }
        return _wrap_response(qc, json.dumps({"success": True, "source": "ifind", "data": result}, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"ths_query 异常: {e}")


# ============================================================
# Tool 18: 东方财富 Choice EmQuantAPI 数据查询
# ============================================================
@mcp.tool()
def emquant_query(action: str, code: str = "", max_peers: int = 10) -> str:
    """东方财富 Choice EmQuantAPI 数据查询工具

    action 可选值：
    - connect: 检查连接状态
    - stock: 个股快照（价格/市值/PE/PB/ROE/股息率）
    - financials: 财务数据（营收/净利润/毛利率/ROE/ROA，近4期）
    - consensus: 卖方一致预期（净利润预测/EPS/目标价/评级）
    - peers: 同行业可比公司对比（max_peers 控制数量）
    - macro: 宏观经济数据（GDP/CPI/PMI/M2）
    - valuation: 历史估值分位（PE/PB 10年百分位）

    需要 EmQuantAPI SDK（从 quantapi.eastmoney.com 下载安装）
    环境变量：EM_USERNAME + EM_PASSWORD

    返回结构化 _qc 质检 JSON。
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
        import emquant_data as em

        if action == "connect":
            result = em.check_connection()
        elif action == "stock":
            result = em.get_stock_snapshot(code)
        elif action == "financials":
            result = em.get_financials(code)
        elif action == "consensus":
            result = em.get_consensus_estimates(code)
        elif action == "peers":
            result = em.get_industry_peers(code, max_peers)
        elif action == "macro":
            result = em.get_macro_data()
        elif action == "valuation":
            result = em.get_valuation_history(code)
        else:
            return _make_error_response(f"未知 action: {action}，支持 connect/stock/financials/consensus/peers/macro/valuation")

        if not result:
            qc = {
                "status": "failure",
                "completeness": 0.0,
                "sources": [],
                "fallback_source": None,
                "missing_dimensions": ["EmQuantAPI 数据"],
                "stale_data": [],
                "error": "EmQuantAPI 连接失败或查询无结果，请确认 EM_USERNAME/EM_PASSWORD 已配置且 SDK 已安装",
            }
            return _wrap_response(qc, json.dumps({"success": False}, ensure_ascii=False))

        qc = {
            "status": "success",
            "completeness": 1.0,
            "sources": ["emquant"],
            "fallback_source": None,
            "missing_dimensions": [],
            "stale_data": [],
        }
        return _wrap_response(qc, json.dumps({"success": True, "source": "emquant", "data": result}, ensure_ascii=False, indent=2, default=str))

    except Exception as e:
        return _make_error_response(f"emquant_query 异常: {e}")


# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")
