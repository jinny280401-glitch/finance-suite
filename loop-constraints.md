# Loop Constraints — Finance Suite

## Denylist (绝对不可自动修改的路径)

### Production servers
- `119.28.156.125` (Seoul Lighthouse) — 真实生产环境
- `/home/ubuntu/finance-suite-web/*` — 生产 webroot
- `/home/ubuntu/finance-suite-backend/*` — 生产后端

### Authentication & Security
- `*.env` files
- `config/secrets.yaml`
- SSH keys (`~/.ssh/*`)
- API tokens

### State files (只读或需人工审批)
- `~/.claude/projects/-Users-Zhuanz/memory/*.md` — Memory 系统
- `handoff.json` — 状态跟转文件（如存在）
- `~/.finance-suite/user_context.json` — 用户上下文（如存在）

## Auto-merge allowlist

**完全禁止 auto-merge** — Finance Suite 不允许任何自动合并到 main 分支。

理由：
- 金融数据准确性要求人工验证
- Provider 切换需要证据链审查（6 项证据）
- UI 变更需要浏览器实测

**唯一例外**：文档更新（`docs/*.md`, `README.md`）可以在满足以下条件时自动合并：
- CI 全绿
- 无代码变更
- PR 描述包含完整 diff summary

## Human gates (必须人工介入的场景)

### 1. 部署声明门控（6 项证据链）

任何"已上线/已接通/生产可用"声明必须同时给出：

1. **实际 upstream 来源** — 具体调用哪个函数
2. **实际生产文件路径** — 完整路径 + 行号
3. **实际 router 挂载位置** — main.py 挂载位置
4. **curl 返回 body** — 不仅是 HTTP code，必须包含 `_qc.status`
5. **smoke check 结果** — 完整输出
6. **实际用户可见证据** — UI 元素 + 前端调用 + 浏览器行为

**缺一项都不能宣称"已上线"**。

**来源**: [[feedback_deployment_evidence_chain]]

### 2. Provider 切换门控

任何 Provider 变更（AkShare ↔ Wind ↔ Choice）必须：
- Provider 分层验证通过（Contract / Interface / Data 三层）
- Evidence Manifest v1 审查通过（9 字段 schema）
- 6-card 验证框架完成
- Provider provenance boundary 清晰（`provider_mode` 由调用路径决定）

**来源**: [[feedback_provider_layered_verification]], [[project_evidence_manifest_v1]]

### 3. Freeze 窗口门控

Freeze 期间任何操作（即使看起来"安全"）必须：
- 检查是否在已开启的编号窗口内（如"窗口 #1"）
- 不在窗口内 = 破例，计入破例次数
- ≥2 次破例 → 立即重置 freeze

**来源**: [[feedback_freeze_erosion]]

### 4. Automation 对齐门控

新增或修改 automation（cron/launchd）必须：
- DRIFT 检查：automation 脚本 vs 模板 vs 人工流程三方一致
- TIMING 检查：触发时间符合业务逻辑（如 Morning Brief 在开盘前）
- 无 DRIFT-XX 或 TIMING-XX open items

**来源**: [[project_d20_automation_alignment_audit]]

## MCP / Connector scope

### finance-suite MCP
- **Allowed**: Read-only queries (stock_analysis, market_pulse, watchlist_manage:list)
- **Restricted**: Write operations (watchlist_manage:add/remove) — L2+ only
- **Forbidden**: Provider config changes, cache invalidation

### Engram MCP
- **Allowed**: POST /lessons (lesson write)
- **Restricted**: During freeze — must check freeze status first
- **Forbidden**: Batch writes (>5 lessons in 1 hour)

### Wind API (if available)
- **Allowed**: Read-only data queries
- **Restricted**: Credential changes — manual only
- **Forbidden**: Automated subscription management

## Worktree isolation

**Required for**:
- L2+ fix attempts (one worktree per fix)
- Parallel feature development (avoid branch conflicts)
- Risky refactoring (discard after verifier REJECT)

**Not required for**:
- L1 report-only loops (no code changes)
- Documentation updates
- Read-only analysis

## Stall detection & escalation

**No-progress detection**:
- Same error message ≥3 times in a row → escalate to human
- Retry same approach ≥2 times → stop and report root cause
- Loop runtime >30 min without STATE.md update → circuit breaker

**Escalation path**:
1. Update Memory MEMORY.md "High Priority" section
2. If Engram available: POST lesson with `domain: finance-suite`
3. Halt current loop (exit code 2)
4. Await human explicit "continue" or "abandon"

**来源**: 第一性原则 — "追根因，不打补丁"

## Least-privilege tool scope

**Principle**: Each skill/agent only gets the minimal tools needed for its role.

| Role | Allowed tools | Forbidden tools |
|------|--------------|-----------------|
| loop-triage (L1) | Read, Bash (read-only), WebFetch | Write, Edit, git push |
| loop-verifier | Read, Bash (test runners) | Write to src, git push |
| implementer (L2) | Read, Edit, Write, Bash | git push (needs verifier approval) |
| deployer | Bash (ssh, git push), Read | Edit, Write (code changes must be committed first) |

## Related

- Safety checklist: See `docs/safety.md` (if exists)
- Deployment SOP: See Memory [[reference_touziagent_outage_sop]]
- Evidence Map: See Memory [[project_finance_suite_evidence_map_20260705]]
