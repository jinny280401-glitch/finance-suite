# BRANCH_TRACKING_AUDIT_v0.1

**Date:** 2026-08-04
**Detected during:** Repository Handoff Cleanup v0.1
**Status:** OPEN — local-tracking changes only; no push performed

---

## Finding

Three local branches have `upstream` pointing at `origin/main` instead of the branch's own remote counterpart:

| Branch | Current upstream | Intended upstream | Local SHA | Remote SHA | Ahead/Behind vs origin/main |
|---|---|---|---|---|---|
| `codex/sidebar-market-temperature-fallback` | `origin/main` | `origin/codex/sidebar-market-temperature-fallback` | `52e6c6e` | `52e6c6e` (same) | behind 5 |
| `release/sidebar-workbench-20260623` | `origin/main` | `origin/release/sidebar-workbench-20260623` | `fe78035` | `fe78035` (same) | behind 5 |
| `feature/trust-gate-runtime` | `origin/main` | (no remote branch exists) | `f372613` | — (no remote) | behind 6 |

## Risk

If a developer commits to any of these three branches and runs `git push` without an explicit refspec, the push target becomes `origin/main` — not the branch's own remote. For the two branches whose local and remote SHAs are identical, the push is currently a no-op (Git rejects as "up to date"). For `feature/trust-gate-runtime` (no remote) the push would either fail with "no upstream" or, depending on git version and config, push to `main` if someone re-set `--set-upstream origin main` at any point.

The trigger is "someone makes a new commit on this branch" — not the current state. So the fix is to align the tracking now, before any new commits land.

## Action

For the two branches with a remote counterpart:

```
git branch --set-upstream-to=origin/<branch>
```

For `feature/trust-gate-runtime` (no remote):

```
git branch --unset-upstream
```

If the team later wants to publish this branch, an explicit push with refspec (`git push origin feature/trust-gate-runtime:refs/heads/feature/trust-gate-runtime`) is the correct step. Do not rely on upstream defaults to decide where a branch lands.

## Execution

Performed by CC on 2026-08-04, working tree only, no push:

```
git branch --set-upstream-to=origin/codex/sidebar-market-temperature-fallback codex/sidebar-market-temperature-fallback
git branch --set-upstream-to=origin/release/sidebar-workbench-20260623 release/sidebar-workbench-20260623
git branch --unset-upstream feature/trust-gate-runtime
```

Verification:

```
git for-each-ref --format='%(refname:short) | up=%(upstream:short)' refs/heads
```

## Constraint

- No push performed.
- No branches deleted.
- No commits created.
