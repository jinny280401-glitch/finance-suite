"""
Finance Suite MCP Server — 瘦入口，实际逻辑在 mcp_tools/ 包中。

启动方式（stdio 模式）：
  python mcp_tools/mcp_server.py

或：
  python -m mcp_tools.server
"""
from backend.mcp_tools.server import mcp  # noqa: F401

if __name__ == "__main__":
    mcp.run(transport="stdio")
