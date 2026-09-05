"""MCP tools: watchlist_manage"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

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
        from backend.engine.skills import watchlist

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


