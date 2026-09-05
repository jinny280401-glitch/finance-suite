"""MCP tool: video_extract

数据访问通过 engine.data_access 层，不直接 import scripts/ 模块。
"""
import json

from backend.mcp_tools.server import (
    mcp, _wrap_response, _make_error_response,
    logger,
)
from engine import data_access


# Tool 5: 视频内容提取
# ============================================================
@mcp.tool()
async def video_extract(url: str) -> str:
    """从 YouTube 或 B站 视频提取字幕/内容。
    支持格式：youtube.com、youtu.be、bilibili.com 链接。
    YouTube 使用 Supadata API，B站使用官方 API。
    返回结构化 _qc 质检 JSON。"""
    try:
        result = await data_access.fetch_video_content(url)
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
