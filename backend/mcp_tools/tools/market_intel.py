"""MCP tools: market_intel"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

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


