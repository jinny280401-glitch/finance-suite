# Safety — Finance Suite

## Denylist (绝对不可自动修改)

### Production servers
- `119.28.156.125` (Seoul Lighthouse) — 真实生产 webroot
- `/home/ubuntu/finance-suite-web/*`
- `/home/ubuntu/finance-suite-backend/*`

### Auth & Secrets
- `*.env` files
- `config/secrets.yaml`
- SSH keys (`~/.ssh/*`)
- API tokens and credentials

### State files
- `~/.claude/projects/-Users-Zhuanz/memory/*.md` — Memory system
- `handoff.json` — state handoff (if exists)
- `~/.finance-suite/user_context.json` — user context (if exists)

## Auto-merge policy

**Auto-merge is forbidden** for all code changes. Finance Suite requires:
- Financial data accuracy verification
- Provider switch evidence chain review (6 items)
- UI changes require browser verification

**Exception**: Documentation-only PRs (`docs/*.md`, `README.md`) with:
- CI green
- No code changes
- Full diff summary in PR description

## Human gates

### Deployment gate (6-item evidence chain)
Any "deployed/live/production-ready" claim requires all 6:
1. Actual upstream source (which function was called)
2. Actual production file path (full path + line number)
3. Actual router mount location (main.py line)
4. curl response body (not just HTTP code, include `_qc.status`)
5. Smoke check result (full output)
6. User-visible evidence (UI elements + frontend calls + browser behavior)

**Missing any one = cannot claim "deployed"**

### Provider switch gate
Any provider change (AkShare ↔ Wind ↔ Choice) requires:
- Provider layered verification (Contract / Interface / Data)
- Evidence Manifest v1 review (9-field schema)
- 6-card verification framework
- Clear provider provenance boundary

### Freeze gate
During freeze, any operation must:
- Be within an explicitly opened numbered window
- Count as violation otherwise (≥2 violations → immediate freeze reset)

## MCP scopes (least privilege)

| Role | Allowed | Forbidden |
|------|---------|-----------|
| loop-triage (L1) | Read, Bash (ro), WebFetch | Write, Edit, git push |
| loop-verifier | Read, Bash (test) | Write to src, git push |
| implementer (L2) | Read, Edit, Write, Bash | git push (needs verifier OK) |
| deployer | Bash (ssh, git push), Read | Edit, Write |

## Stall / no-progress detection

- Same error ≥3 times in a row → escalate to human
- Retry same approach ≥2 times → stop, report root cause
- Loop runtime >30 min without STATE.md update → circuit breaker

## Escalation path

1. Update Memory MEMORY.md "High Priority" section
2. If Engram available: POST lesson with `domain: finance-suite`
3. Halt current loop (exit code 2)
4. Await human explicit "continue" or "abandon"

## Related

- Full constraints: [loop-constraints.md](../loop-constraints.md)
- Budget & freeze rules: [loop-budget.md](../loop-budget.md)
- State tracking: [STATE.md](../STATE.md)
- Loop config: [LOOP.md](../LOOP.md)
