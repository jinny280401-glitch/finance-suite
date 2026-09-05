"""
AkShare 客户端 — 纯 API 封装层（Provider）

只负责调用 AkShare API，返回原始 DataFrame。
不包含任何业务逻辑、降级策略、格式化。

所有函数都是同步的（AkShare 是同步库），调用方负责线程池/超时包装。
"""
from __future__ import annotations

import logging
from typing import Optional

import akshare as ak

logger = logging.getLogger(__name__)


# ── 全市场快照（用于股票名称缓存） ─

def stock_zh_a_spot_tx():
    """腾讯全市场快照（直连，稳定，有 PE/市值/价格，缺 PB）"""
    return ak.stock_zh_a_spot_tx()


def stock_zh_a_spot_em():
    """东方财富全市场快照（字段最全含 PB，但走代理可能被阻断）"""
    return ak.stock_zh_a_spot_em()


def stock_zh_a_spot():
    """新浪全市场快照（直连，轻量，只有基本价格字段）"""
    return ak.stock_zh_a_spot()


# ── 财报数据 ──

def stock_financial_abstract(symbol: str):
    """财报摘要（按报告期）"""
    return ak.stock_financial_abstract(symbol=symbol)


def stock_financial_analysis_indicator(symbol: str, start_year: str = "2024"):
    """财务分析指标"""
    return ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)


def stock_profit_sheet_by_report_em(symbol: str):
    """利润表（按报告期）"""
    return ak.stock_profit_sheet_by_report_em(symbol=symbol)


def stock_balance_sheet_by_report_em(symbol: str):
    """资产负债表（按报告期）"""
    return ak.stock_balance_sheet_by_report_em(symbol=symbol)


# ─ 行情数据 ──

def stock_zh_a_hist(symbol: str, period: str = "daily",
                    start_date: str = "", end_date: str = "", adjust: str = ""):
    """个股历史行情（K线）"""
    kwargs = {"symbol": symbol, "period": period}
    if start_date:
        kwargs["start_date"] = start_date
    if end_date:
        kwargs["end_date"] = end_date
    if adjust:
        kwargs["adjust"] = adjust
    return ak.stock_zh_a_hist(**kwargs)


def stock_individual_fund_flow(stock: str, market: str = ""):
    """个股资金流向"""
    kwargs = {"stock": stock}
    if market:
        kwargs["market"] = market
    return ak.stock_individual_fund_flow(**kwargs)


# ── 新闻数据 ─

def stock_news_em(symbol: str):
    """个股新闻（东方财富）"""
    return ak.stock_news_em(symbol=symbol)


# ── 分红数据 ──

def stock_history_dividend_detail(symbol: str, indicator: str = "分红"):
    """历史分红"""
    return ak.stock_history_dividend_detail(symbol=symbol, indicator=indicator)


# ── 估值数据 ──

def stock_a_gxl_lg(symbol: str = "上证 A 股"):
    """A 股股息率（乐咕）"""
    return ak.stock_a_gxl_lg(symbol=symbol)
