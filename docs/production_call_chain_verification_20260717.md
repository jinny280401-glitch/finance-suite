---
name: feedback_production_call_chain_verification
description: 生产 bug 修复前必须先 SSH 探活实际调用链——文件名相同不等于同一份代码，本地修了 A 路径不等于 B 路径也被修了
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d8ff57f8-688a-4270-93d7-729a749e678c
---

# 生产调用链验证（2026-07-17 集合竞价热修复教训）

**触发**: 2026-07-17 集合竞价 PDF 输出"市场冰点/情绪真空"。C 在 worktree 修了 `mcp_server.py` 的 `_qc_auction()`，但 PDF 实际走的是 `api.py → app/auction_data.py`，那条链没有任何 QC。

**根因**: 同一个 auction 功能在生产服务器上有**两条完全独立的代码链**，文件名相同但路径不同，各自维护各自的实现。本地 `scripts/auction_data.py`（MCP 路径）和生产 `app/auction_data.py`（Web API 路径）是两份独立副本。

**为什么容易漏**: 本地开发时 `mcp_server.py` 的 Tool 3 `market_pulse` 是唯一可见的 auction 入口，自然以为修它就是修了"auction 功能"。但实际上生产 `/api/analyze` 的 dispatcher 直接 import `app.auction_data`，绕过了整个 MCP 层。

**How to apply**:
1. 任何生产 bug 修复第一步：SSH 到服务器，确认 bug 路径上到底跑的是哪个文件
2. 不要假设同名文件 = 同一份代码——在服务器上不同目录可能存在独立副本
3. 确认后在本地找对应文件，如果本地没有（如 `app/auction_data.py` 只在服务器存在），就从服务器拉下来
4. 修复完成后验证所有副本内容一致

**关联**: [[project_auction_qc_hotfix_20260717]]
