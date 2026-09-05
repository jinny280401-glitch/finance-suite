"""MCP tools: ths_query"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

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
        from backend.engine.providers import ifind_provider as ths

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


