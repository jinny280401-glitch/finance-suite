"""MCP tools: research_reports, research_digest"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    _qc_stock, _qc_macro, _qc_auction,
    _format_jq_signals, _joinquant_stale_entries,
    _check_incremental, _enforce_trust_gate_or_block,
    logger,
)

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


