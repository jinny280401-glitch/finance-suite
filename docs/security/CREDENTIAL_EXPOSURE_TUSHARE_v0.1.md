# CREDENTIAL_EXPOSURE_TUSHARE_v0.1 — Incident Record

**Date detected:** 2026-08-04
**Detector:** CC during Repository Handoff Cleanup v0.1
**Status:** OPEN — rotation required
**Severity:** HIGH
**Push status:** FORBIDDEN until rotation decision

---

## Credential

| Field | Value |
|---|---|
| Type | Tushare Pro API token |
| Value (full) | `<NOT RECORDED IN THIS FILE BY DESIGN — see git history>` |
| Value prefix (verifiable) | `ac6471c6...` (40 hex chars) |
| Owner | UNKNOWN — token is hardcoded as a default in `scripts/tushare_data.py:13` and re-exports in `docs/MCP_TOOLS_GUIDE.md:596` |
| Validity | UNKNOWN — not probed by CC per safety policy |

## Exposure

| Field | Value |
|---|---|
| First introduced | commit `5b04fa0` (`feat: 集成 Tushare Pro 数据源`) |
| Currently in | commit `cefc660` (HEAD = `4fad4ef`, branch `runtime-validation-v0.1`, base = `cefc660`) |
| Pushed to | `origin/main` (`cefc660...` was the last commit pushed to `origin/main` on 2026-08-03) |
| Public visibility | Yes — `origin` is `https://github.com/jinny280401-glitch/finance-suite.git` |
| Distinct files | `scripts/tushare_data.py` line 13 (runtime fallback); `docs/MCP_TOOLS_GUIDE.md` line 596 (export example) |

## Why the prior remediation was incomplete

On 2026-08-03, the credential was first flagged by `docs/handover/GIT_SECURITY_HANDOVER_CHECK.md`. Remediation that same day redacted the token in the audit document (`docs/handover/`) but **did not touch the source files containing the token**. The redaction passed GitHub's `GH013` push protection (which only catches a different secret pattern, OpenRouter) and the source files were pushed to `origin/main` unchanged.

This is a remediation gap: a credential should be neutralized at its source and at any audit copy that quotes it, not only at one of the two locations.

## Action Required

### Immediate (P0)

1. **Token owner: rotate the Tushare Pro token.** Until rotated, the token must be treated as compromised even if it is currently inactive.
2. **Replace hardcoded fallback** in `scripts/tushare_data.py:13` so that no Tushare token is present in the working tree in any form. The new fallback MUST be `os.getenv("TUSHARE_TOKEN")` with no default — a missing env var should raise, not silently fall through to a (now invalid) hardcoded value.
3. **Remove export example** in `docs/MCP_TOOLS_GUIDE.md:596`. Replace with `export TUSHARE_TOKEN="<your-token-from-env>"` and link to `.env.example`.
4. **Do not** push the source-tree changes until after step 1. Until rotation, pushing redacted source to `origin/main` exposes the new fallback (a still-valid token) to the same threat.

### Decision Pending

5. **History rewrite?** Whether to run `git filter-repo` on `5b04fa0..HEAD` and force-push is an organizational decision. CC will not do this autonomously.
6. **Branch scan.** Whether other branches (`feature/*`, `codex/*`, `release/*`) also carry the token. Out of scope for this incident; tracked separately.

## CC Did Not Do

- ❌ Test the token's validity against any external endpoint
- ❌ Run `git filter-repo` / `git filter-branch` / force-push
- ❌ Modify `scripts/tushare_data.py` or `docs/MCP_TOOLS_GUIDE.md` yet
- ❌ Push anything

## Detection Rule (carry forward)

When a secret is identified in an audit document:

```
IF doc contains literal value X
THEN source file containing X must be neutralized in the same change set
     OR explicit hold flag with owner decision must be recorded
```

Carried-forward rule recorded to `feedback_engram_lesson_filter` review queue.
