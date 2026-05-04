"""
Finance Suite MCP Server
将 Finance Suite 的 12 个金融数据脚本暴露为 MCP 工具，供 Claude Code / OpenClaw 等 Agent 调用。

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
from datetime import datetime

# 确保 scripts/ 目录在 import 路径中
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "finance-suite",
    instructions=(
        "Finance Suite 金融数据 MCP 服务。"
        "提供 A 股个股分析、宏观经济、盘面数据、多源搜索、视频提取、自选股管理、因子选股、Wind 数据等工具。"
        "数据源架构：Wind API → Tushare Pro → AkShare（三层降级）。"
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
    """盘面数据质检"""
    dims = {
        "zt_pool": "涨停池", "strong_pool": "强势股", "previous_zt": "昨日涨停",
        "big_buy": "大笔买入", "hot_rank": "人气排行", "hot_up": "飙升榜", "top_gainers": "涨幅排行",
    }
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
    数据源：Wind（优先）+ AkShare（降级）。
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
    因子包括：涨停基因、跌破涨停价、横盘筑底、BBIBOLL 反弹、连跌缩量。
    扫描可能需要 1-3 分钟。date 格式 YYYY-MM-DD，留空默认今天。
    返回结构化 _qc 质检 JSON。"""
    try:
        import factor_scan as fs

        data = fs.get_factor_signals(date or None)
        has_error = "error" in data
        has_signals = bool(data.get("signals"))

        qc = {
            "status": "failure" if has_error else ("success" if has_signals else "partial"),
            "completeness": 0 if has_error else (1.0 if has_signals else 0.5),
            "sources": ["trading_system"],
            "fallback_source": None,
            "missing_dimensions": ["扫描结果"] if has_error else [],
            "stale_data": [],
        }
        if has_error:
            qc["error"] = data["error"]

        formatted = fs.format_factor_signals(data)
        return _wrap_response(qc, formatted)

    except Exception as e:
        return _make_error_response(f"factor_scan 异常: {e}")


# ============================================================
# Tool 8: 金融数据查询（三层降级：Wind → Tushare → AkShare）
# ============================================================
@mcp.tool()
def wind_query(action: str, code: str = "", max_peers: int = 10) -> str:
    """查询金融数据（三层降级：Wind → Tushare Pro → AkShare）。

    action 可选值：
    - connect: 检查数据源连接状态
    - stock: 个股快照（价格/市值/PE/PB/ROE）
    - financials: 完整三大报表（近4期）
    - consensus: 卖方一致预期（净利润/EPS/ROE/目标价/评级）
    - peers: 同行业可比公司对比
    - valuation: 历史估值分位（PE/PB 10年百分位）
    - shareholders: 前十大股东及持股变动
    - calendar: 财报披露日期

    数据源优先级：Wind → Tushare Pro（500元/年）→ AkShare（免费）
    返回结构化 _qc 质检 JSON。"""
    try:
        import wind_data
        import tushare_data

        if action == "connect":
            # 检查所有数据源连接状态
            wind_status = wind_data.check_connection()
            tushare_status = tushare_data.check_connection()

            sources = []
            if wind_status.get("connected"):
                sources.append("wind")
            if tushare_status.get("connected"):
                sources.append("tushare")
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
                "akshare": True,
                "priority": "Wind → Tushare → AkShare"
            }
            return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2))

        if not code:
            return _make_error_response(f"action={action} 需要提供 code 参数", fallback_source="tushare/akshare")

        # 三层降级策略
        result = None
        source_used = None

        # 第一层：尝试 Wind
        try:
            actions_map_wind = {
                "stock": lambda: wind_data.get_stock_snapshot(code),
                "financials": lambda: wind_data.get_financials(code),
                "consensus": lambda: wind_data.get_consensus_estimates(code),
                "peers": lambda: wind_data.get_industry_peers(code, max_peers),
                "valuation": lambda: wind_data.get_valuation_history(code),
                "shareholders": lambda: wind_data.get_major_shareholders(code),
                "calendar": lambda: wind_data.get_earnings_calendar(code),
            }
            fn = actions_map_wind.get(action)
            if fn:
                result = fn()
                if result:
                    source_used = "wind"
        except Exception:
            pass

        # 第二层：降级到 Tushare
        if not result:
            try:
                actions_map_tushare = {
                    "stock": lambda: tushare_data.get_stock_snapshot(code),
                    "financials": lambda: tushare_data.get_financials(code, "income"),
                    "consensus": lambda: tushare_data.get_consensus_estimates(code),
                    "peers": lambda: tushare_data.get_industry_peers(code, max_peers),
                }
                fn = actions_map_tushare.get(action)
                if fn:
                    result = fn()
                    if result:
                        source_used = "tushare"
            except Exception:
                pass

        # 第三层：降级到 AkShare（通过 stock_analysis）
        if not result:
            qc = {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "fallback_source": "akshare",
                "missing_dimensions": [f"{action}"],
                "stale_data": [],
                "error": f"Wind 和 Tushare 均不可用，建议使用 stock_analysis 工具（自动走 AkShare）",
            }
            return _wrap_response(qc, "")

        # 成功获取数据
        qc = {
            "status": "success",
            "completeness": 1.0,
            "sources": [source_used],
            "fallback_source": "tushare" if source_used == "wind" else "akshare",
            "missing_dimensions": [],
            "stale_data": [],
        }
        formatted = json.dumps({
            "source": source_used, "code": code, "data": result,
        }, ensure_ascii=False, indent=2, default=str)
        return _wrap_response(qc, formatted)

    except Exception as e:
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

        return _wrap_response(qc, json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        return _make_error_response(f"research_reports 异常: {e}")


# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")
