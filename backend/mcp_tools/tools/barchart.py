"""MCP tools: barchart_fetch"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

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


