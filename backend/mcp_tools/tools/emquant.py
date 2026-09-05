"""MCP tools: emquant_query"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

# Tool 18: 东方财富 Choice EmQuantAPI 数据查询
# ============================================================
@mcp.tool()
def emquant_query(action: str, code: str = "", max_peers: int = 10) -> str:
    """东方财富 Choice EmQuantAPI 数据查询工具

    action 可选值：
    - connect: 检查连接状态
    - stock: 个股实时行情快照（OHLCV + 换手率 + 股息率）
    - history: 历史行情序列（日频 OHLCV，默认 250 天）
    - macro: 宏观经济数据（当前账户：CPI_YOY/CPI_MOM/SHIBOR_1M）
    - financials: ⚠️ 财务数据（当前账户基础行情级别，不支持）
    - consensus: ⚠️ 卖方一致预期（当前账户不支持）
    - peers: ⚠️ 同行业对比（当前账户不支持 sector/行业分类）
    - valuation: ⚠️ 历史估值分位（当前账户不支持 PE/PB 指标）

    需要 EmQuantAPI SDK（从 quantapi.eastmoney.com 下载安装）
    环境变量：EM_USERNAME + EM_PASSWORD

    当前账户 hfzq80016 为基础行情级别，已实测验证可用范围见脚本文件头注释。

    返回结构化 _qc 质检 JSON。
    """
    try:
        from backend.engine.providers import emquant_provider as em

        if action == "connect":
            result = em.check_connection()
        elif action == "stock":
            result = em.get_stock_snapshot(code)
        elif action == "history":
            result = em.get_price_history(code)
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
            return _make_error_response(f"未知 action: {action}，支持 connect/stock/history/macro/financials/consensus/peers/valuation")

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




