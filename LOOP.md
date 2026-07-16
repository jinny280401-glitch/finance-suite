# Loop Configuration — Finance Suite (Claude Code)

## Active Loops

| Pattern | Cadence | Status | Command |
|---------|---------|--------|---------|
| Morning Brief | 1d | L1 report-only | launchd scheduled |
| Intelligence Loop v1 | 1d | 🔒 Frozen | Awaiting unfreeze |
| Provider Health Check | 6h | L1 smoke-only | Cron triggered |
| Golden Pit Scan | 1d | ⏸️ Paused | TBD |

## Human Gates

- No auto-fix until L2 checklist complete
- All high-risk paths: human review required (see [docs/safety.md](docs/safety.md) denylist)
- Freeze rules: Pre-Event T-12h + Explicit STOP (see [loop-budget.md](loop-budget.md) § Freeze Rules)
- Deployment requires 6-item evidence chain (see [loop-constraints.md](loop-constraints.md) § Human Gates)

## Worktrees

- Use `isolation: worktree` when spawning implementer sub-agents (L2+)
- One worktree per fix attempt; discard after verifier REJECT
- Already practiced in development workflow

## Connectors (MCP)

- **finance-suite MCP**: Read-only queries, write ops L2+ only
- **Wind API**: Read-only; credential changes manual only
- **Engram**: POST /lessons for run history; check freeze status first
- Full MCP scope: see [loop-constraints.md](loop-constraints.md) § MCP/Connector Scope

## Budget

- See [loop-budget.md](loop-budget.md) for full limits and kill switch
- Max sub-agent spawns per run: 0 (L1 report-only)
- Review [STATE.md](STATE.md) daily

## Project Conventions

- See [docs/CLAUDE.md](docs/CLAUDE.md) for project-specific instructions
- See [.claude/skills/workflow-orchestration.md](.claude/skills/workflow-orchestration.md) for workflow definitions

## Links

- Budget: [loop-budget.md](loop-budget.md)
- Constraints: [loop-constraints.md](loop-constraints.md)
- State: [STATE.md](STATE.md)
- Safety: [docs/safety.md](docs/safety.md)
