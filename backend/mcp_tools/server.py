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
  python mcp_tools/mcp_server.py

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

import functools
import json
import sys
import os
import time
import logging
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# scripts/ 已迁移至 engine/skills/ 和 engine/providers/，不再需要 sys.path hack

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("finance-suite.mcp")

# Trust Gate Phase 1a — wind_query enforcement (fail-closed)
# If the trust_gate module cannot be imported, wind_query returns a hard BLOCK,
# not raw provider data. There is no fail-open path.
try:
    from trust_gate.enforcer import enforce_wind_query, format_trust_gate_envelope
    _TRUST_GATE_AVAILABLE = True
except ImportError:
    _TRUST_GATE_AVAILABLE = False
    logger.critical("trust_gate module not available — wind_query will return BLOCK for all requests")


def _enforce_trust_gate_or_block(
    action: str,
    code: str,
    result: dict | None,
    source_used: str,
    raw_response: str,
) -> str:
    """Apply Trust Gate enforcement to a wind_query response.

    If the Trust Gate module is unavailable, returns an explicit BLOCK
    with a GATE_UNAVAILABLE reason code. Provider data never reaches
    the caller without enforcement.

    This is the SINGLE enforcement choke-point for wind_query.
    There is no code path that returns raw_response unfiltered.
    """
    if not _TRUST_GATE_AVAILABLE:
        import uuid
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        now_us = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        decision_id = f"tg-wind_query-{now_us}-{uuid.uuid4().hex[:6]}-GATE_UNAVAILABLE"
        block_envelope = {
            "_qc": {
                "status": "failure",
                "completeness": 0,
                "sources": [],
                "source_chain": {"primary": None, "attempted": [], "failed": [], "winner": None},
                "source_type": "none",
                "fallback_source": None,
                "missing_dimensions": [action] if action else [],
                "stale_data": [],
                "error": "Trust Gate module unavailable — enforcement cannot run",
            },
            "_trust_gate": {
                "gate_version": "v0.1-phase1a",
                "decision_id": decision_id,
                "decided_at": now_ts,
                "tool": "wind_query",
                "action": action,
                "code": code,
                "source_used": "",
                "retrieved_at": now_ts,
                "overall_verdict": "BLOCK",
                "blocked_boundaries": ["GATE"],
                "boundaries": [{
                    "boundary_id": "GATE",
                    "boundary_label": "Trust Gate Enforcement",
                    "verdict": "BLOCK",
                    "reason_code": "GATE_UNAVAILABLE",
                    "detail": "Trust Gate module failed to import — all wind_query requests blocked",
                    "evidence": {
                        "action": action,
                        "code": code,
                        "gate_module": "trust_gate.enforcer",
                        "import_error": "module not found or failed to load",
                    },
                    "evaluated_at": now_ts,
                }],
            },
        }
        return json.dumps(block_envelope, ensure_ascii=False) + "\n\n数据不可用 (Trust Gate module unavailable)"

    tg = enforce_wind_query(action=action, code=code, result=result, source_used=source_used)
    return format_trust_gate_envelope(tg, raw_response)

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
        "valuation": "估值指标",
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
        elif key == "financials" and isinstance(val, list) and val:
            # 检查最新报告期是否超过6个月（两个季报周期）
            # 假设 financials 已按报告期降序排列，val[0] 是最新一期
            latest = val[0] if val else {}
            report_date_str = str(
                latest.get("报告期") or latest.get("日期") or latest.get("date") or latest.get("report_date") or ""
            )
            if report_date_str:
                try:
                    report_date = datetime.strptime(report_date_str[:10], "%Y-%m-%d")
                    age_days = (datetime.now() - report_date).days
                    if age_days > 180:
                        stale.append({
                            "field": label,
                            "issue": f"最新报告期 {report_date_str[:10]}，距今 {age_days} 天（超过6个月）",
                            "latest_period": report_date_str[:10],
                            "age_days": age_days,
                        })
                except ValueError:
                    pass

    # P3 — QC Claim Boundary: detect derived-source dimensions.
    # A dimension whose source_type is "derived" (e.g. valuation calculated from EPS/Price)
    # is recorded separately and MUST NOT enable a status upgrade to "success".
    # This prevents: derived evidence → QC success → capability claim upgrade.
    derived = []
    val_data = data.get("valuation")
    if isinstance(val_data, dict):
        val_source = val_data.get("valuation_source") or {}
        if val_source.get("type") == "derived":
            if "估值指标" in missing:
                missing.remove("估值指标")
            derived.append("估值指标")
    for key, label in list(dimensions.items()):
        if key == "valuation":
            continue
        val = data.get(key)
        if isinstance(val, dict):
            vs = val.get("valuation_source") or {}
            if vs.get("type") == "derived" and label not in missing and label not in derived:
                derived.append(label)

    total = len(dimensions)
    present = total - len(missing)
    completeness = round(present / total, 2) if total else 0
    realtime_availability = data.get("realtime_availability") or {}
    realtime_blocked_fields = list(realtime_availability.get("blocked_fields") or [])
    realtime_allowed_use = list(realtime_availability.get("allowed_use") or [])
    data_availability = {
        "realtime": realtime_availability or {
            "status": "unavailable",
            "source": None,
            "source_type": "not_connected",
            "as_of": None,
            "available": [],
            "missing": ["realtime"],
            "allowed_use": [],
            "blocked_fields": ["all_realtime_fields"],
        }
    }

    # Trust Gate: completeness + freshness 双重校验
    # freshness_ok: stale 条目 <= 1（允许至多1个维度不新鲜）
    freshness_ok = len(stale) <= 1

    if completeness >= 0.8 and freshness_ok:
        status = "success"
    elif completeness > 0.5 or (completeness > 0 and not freshness_ok):
        status = "partial"
    else:
        status = "failure"

    # P3 cap: derived dimensions NEVER allow status=success.
    # derived evidence ≠ REAL_PROVIDER evidence; claiming "success"
    # on derived-only data would be a capability claim upgrade.
    if derived and status == "success":
        status = "partial"

    return {
        "status": status,
        "completeness": completeness,
        "sources": [source],
        "fallback_source": "akshare" if source == "wind" else None,
        "missing_dimensions": missing,
        "derived_dimensions": derived,
        "stale_data": stale,
        "data_availability": data_availability,
        "allowed_use": {
            "realtime": realtime_allowed_use,
        },
        "blocked_fields": {
            "realtime": realtime_blocked_fields,
        },
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


# ============================================================
# Trust Gate enforcement: see trust_gate/ module (Phase 1a — wind_query pilot)
# Imported at top of file: enforce_wind_query, format_trust_gate_envelope


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
        from backend.engine.skills import watchlist
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

# ============================================================
# 工具模块注册 — 导入即注册 @mcp.tool()
# ============================================================
from backend.mcp_tools.tools import analysis, search, video, watchlist, factor  # noqa: F401
from backend.mcp_tools.tools import wind, social, barchart, research  # noqa: F401
from backend.mcp_tools.tools import market_intel, jqdata, ths, emquant  # noqa: F401


# ============================================================
# 启动入口
# ============================================================
if __name__ == "__main__":
    mcp.run(transport="stdio")
