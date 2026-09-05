"""MCP tool: search

数据访问通过 engine.data_access 层，不直接 import scripts/ 模块。
"""
from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    logger,
)
from engine import data_access


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
        # news 模式使用独立的 v2 多源搜索
        if search_type == "news":
            result = await data_access.fetch_news_search(query)
            formatted = result["formatted"]
            provider_results = result["provider_results"]

            runtime_detail = result["runtime_detail"]
            qc = {
                "search_type": search_type,
                "query": query,
                "sources": [r.provider for r in provider_results],
                "runtime_detail": runtime_detail,
                "unavailable_providers": [
                    r.provider for r in provider_results
                    if r.runtime_state.value == "unavailable"
                ],
                "mock_providers": [
                    r.provider for r in provider_results
                    if r.runtime_state.value == "mock"
                ],
                "result_count": len(result["results"]) if result["results"] else 0,
            }
            return _wrap_response(qc, formatted)

        # 其他模式使用标准搜索
        result = await data_access.fetch_search(query, search_type)
        formatted = result["formatted"]
        providers = result["providers"]

        # 搜索质检
        sources_used = []
        if providers.get("tavily"):
            sources_used.append("tavily")
        if providers.get("brave"):
            sources_used.append("brave")

        result_count = len(result["results"]) if result["results"] else 0
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
