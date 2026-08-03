# GIT_SECURITY_HANDOVER_CHECK.md — finance-suite (网站仓库)

**Date**: 2026-07-30
**Auditor**: CC (Claude Code, this session)
**Scope**: Read-only security check. No credential rotation. No commit. No push. No remediation code change.
**Target repo**: `https://github.com/jinny280401-glitch/finance-suite.git`
**Companion docs**: `REPO_HANDOVER_AUDIT.md`, `CREDENTIAL_REMEDIATION_REPORT_20260729.md`

---

## 0. Boundary applied (no remediation in this audit)

Per the task-card forbidden list:
- ❌ No credential rotation
- ❌ No file deletion
- ❌ No `.gitignore` modification
- ❌ No commit
- ❌ No push

This document reports findings only. Each finding is accompanied by a recommended **owner decision** for the credential-exposure case.

---

## 1. .gitignore coverage (positive control)

`.gitignore` (88 bytes, 11 lines):

```
__pycache__/
*.pyc
.env
.env.save
*.db
logs/*.log
.DS_Store
.claude/
.venv/
venv/
logs/
```

| Path | Gitignored? | Tracked? | Status |
|---|---|---|---|
| `.env` | ✅ line 3 | ❌ (confirmed via `git ls-files .env` → empty; `git check-ignore -v .env` → matched) | CORRECTLY EXCLUDED |
| `.env.save` | ✅ line 4 | ❌ | CORRECTLY EXCLUDED |
| `.env.example` | ❌ not excluded | ✅ tracked (and contains empty placeholder values, not secrets) | INTENDED |
| `__pycache__/` | ✅ | varies | CORRECTLY EXCLUDED |
| `.venv/` | ✅ | varies | CORRECTLY EXCLUDED |
| `logs/` | ✅ | varies | CORRECTLY EXCLUDED |
| `.codex_remote/` | ❌ **NOT** in `.gitignore` | ❌ currently untracked (only contains `routers/__pycache__/api.cpython-312.pyc`) | SHOULD BE EVALUATED |

**Finding S0**: `.codex_remote/` is not gitignored. It currently contains a compiled `.pyc` file but the directory itself may accumulate codex runtime artifacts over time. Recommendation: add `.codex_remote/` to `.gitignore` BEFORE the next commit cycle (this is a hygiene fix, not a credential fix).

---

## 2. Tracked-code credential findings

### 2.1 CONFIRMED — `scripts/tushare_data.py:13`

```python
# Tushare Pro Token
_TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "ac6471c6...<REDACTED>")
```

| Field | Value |
|---|---|
| File | `scripts/tushare_data.py` |
| Line | 13 |
| Token value | `ac6471c6...<REDACTED>` (40 hex chars, redacted for security) |
| Variable name | `_TUSHARE_TOKEN` |
| Pattern | Hardcoded fallback when env var not set |
| Status | **PRESENT IN CURRENT WORKING TREE** (commit `cdac1ca`) |
| gitleaks report | `CREDENTIAL_REMEDIATION_REPORT_20260729.md` flagged this at commit `5b04fa0`, classification `UNKNOWN` |

**Per `CREDENTIAL_REMEDIATION_REPORT_20260729.md`**:
- Issuer/provider: UNKNOWN (needs owner identification)
- Active / ROTATED / UNKNOWN: UNKNOWN
- Required owner decisions: identify issuer, rotate/revoke, authorize history handling

**Confirmed fact**: This token is in the file today, not just in some past commit. The audit re-verified line 13 directly.

**Severity**: HIGH. Tushare Pro tokens control A-share data access. If this token is live (not a placeholder), exposure in public GitHub history = potential data scraping + billing risk.

### 2.2 REPORTED — `docs/MCP_TOOLS_GUIDE.md:571`

Per `CREDENTIAL_REMEDIATION_REPORT_20260729.md`:
- Commit: `aa5f06f`
- Classification: UNKNOWN

The audit attempted to read line 571 of `docs/MCP_TOOLS_GUIDE.md` and found content about "K线" / "last_date" — i.e., not an obvious credential. The gitleaks finding may have been a false positive (e.g., a placeholder or example) or may have been redacted. **The audit does NOT have a confirmation that this line currently contains a credential.** Owner confirmation required.

### 2.3 Patterns searched (clean across other tracked files)

The audit searched tracked files (excluding `.venv`, `__pycache__`, `/docs/`-prefixed docs where gitleaks already reports) for:
- `AK=...`
- `SECRET=...`
- `PASSWORD=...`
- `TOKEN=...`
- `api_key=...`

Result: **no other tracked-code credential matches found**.

---

## 3. Working-tree (untracked) credential exposure — `.env`

### 3.1 What's in `.env` (file size 921 bytes, mtime 2026-07-22)

**Note: Actual credential values have been redacted for security. Original audit contained real values.**

```
JQ_USERNAME=<REDACTED>
JQ_PASSWORD=<REDACTED>

JQDATA_USERNAME=<REDACTED>
JQDATA_PASSWORD=<REDACTED>

THS_USERNAME=<REDACTED>
THS_PASSWORD=<REDACTED>
THS_TOKEN=<REDACTED>

EM_USERNAME=<REDACTED>
EM_PASSWORD=<REDACTED>

OPENROUTER_API_KEY=sk-or-v1-<REDACTED>
THS_REFRESH_TOKEN=<REDACTED>
```

**Coverage**:
- JQ / JQData / 聚宽 — credentials present
- THS / 同花顺 iFinD — username, password, token, refresh_token all present
- EM / 东方财富 Choice — username + password present
- OPENROUTER — LLM API key present

### 3.2 Git exposure assessment

- ✅ `.env` is **NOT tracked** (`git check-ignore -v .env` → matched)
- ✅ `.env` IS **NOT in git history** (file added to gitignore; gitignore existed before this `.env` was created on disk)
- ⚠️ `.env` exists in working tree only — local-only exposure

**Risk surface for handover**:
- ✅ A git push would NOT include `.env` (gitignored)
- ⚠️ If `.env` is ever committed (e.g., via `git add -f .env` or by removing `.gitignore` entry), ALL credentials leak
- ⚠️ If the working tree is shared (e.g., tarballed, zipped, uploaded to cloud without filtering), `.env` could leak

### 3.3 `.env.save` (141 bytes, mtime 2026-05-05)

Contains:
```
JQ_USERNAME=你的真实聚宽用户名
JQ_PASSWORD=你的真实聚宽密码
JQ_USERNAME=你的聚宽用户名
JQ_PASSWORD=你的聚宽密码
```

- All values are placeholder comments (Chinese text)
- NOT tracked (gitignored)
- **Not a credential exposure** — documentation only
- ⚠️ File naming `.env.save` is misleading (could be confused with a backup); recommend deletion after handover audit review

### 3.4 `.env.example` (693 bytes, tracked, intended)

Contains **empty values** for all listed credentials + comments documenting each variable:
- `JQDATA_USERNAME=`, `JQDATA_PASSWORD=`
- `TUSHARE_TOKEN=`
- `TAVILY_KEYS=`, `BRAVE_KEYS=`
- `SUPADATA_API_KEY=`
- `THS_USERNAME=`, `THS_PASSWORD=`, `THS_TOKEN=`, `THS_REFRESH_TOKEN=`
- `EM_USERNAME=`, `EM_PASSWORD=`
- `LOG_LEVEL=INFO`, `CACHE_DIR=/tmp/finance-suite-cache`

**Status**: INTENTIONAL template, no secrets. Safe to track.

---

## 4. Other exposure surfaces reviewed

### 4.1 `.codex_remote/` (root)

```
.codex_remote/routers/__pycache__/api.cpython-312.pyc (compiled bytecode)
```

- Not gitignored (see Finding S0)
- Contains compiled Python bytecode only — not source
- Reverse-engineering a `.pyc` back to source is possible but requires effort
- **Risk**: low (no obvious secrets); should be gitignored as a hygiene measure

### 4.2 `deploy.sh`

The deploy script pulls from public raw GitHub URLs (`raw.githubusercontent.com/jinny280401-glitch/finance-suite/main/...`). No secrets in the file. Server-side deployment target is `/home/ubuntu/finance-suite-web/static/app/`.

**No credential exposure.**

### 4.3 `docs/` directory

The docs/ directory contains many `.md` files including governance materials. The 2026-07-29 reports document 2 gitleaks findings here. The audit confirmed `docs/MCP_TOOLS_GUIDE.md:571` does not appear to currently contain a credential (likely false positive from a prior commit, or content has since changed).

### 4.4 `mcp_server.py` (root)

Not searched in this audit (out of strict scope). If credential patterns are present, the gitleaks tool already covers them in its broader scan.

---

## 5. Risk summary

| Finding | Severity | Status | Action required |
|---|---|---|---|
| `scripts/tushare_data.py:13` hardcoded Tushare token | **HIGH** | Present today, in public history per `CREDENTIAL_REMEDIATION_REPORT_20260729.md` | Owner identify issuer + rotate + revoke + authorize history rewrite |
| `docs/MCP_TOOLS_GUIDE.md:571` (gitleaks 2026-07-29) | UNKNOWN | Cannot confirm at current HEAD | Owner confirm whether content remains sensitive |
| `.env` plaintext credentials in working tree | MEDIUM (local-only) | Gitignored, not in history | Continue gitignore enforcement; never commit; never share tree without filter |
| `.env.save` placeholder file | LOW | Gitignored, no real values | Consider deletion post-handover (misleading name) |
| `.codex_remote/` not gitignored | LOW | Not tracked today; future risk | Add to `.gitignore` |
| README / SKILL.md overclaim (Wind 优先; 6/7 技能; deployed) | MEDIUM (claim hygiene) | Documented in `REPO_HANDOVER_AUDIT.md` §3 | Owner author claim corrections |

---

## 6. Required owner decisions (handed back, NOT made by this audit)

Per `CREDENTIAL_REMEDIATION_REPORT_20260729.md` and this audit:

For `scripts/tushare_data.py:13` Tushare token:

1. **Issuer/provider**: confirm whether `ac6471c6...<REDACTED>` is a real Tushare Pro token or a placeholder/example
2. **Status**: `ROTATED`, `ACTIVE`, or `UNKNOWN`
3. **Revocation**: required / not required
4. **History remediation**: required / not required
5. **Authorization for history rewrite** (if required): owner must explicitly authorize before any `git filter-repo` / `git filter-branch` is run

For `docs/MCP_TOOLS_GUIDE.md:571` (gitleaks 2026-07-29):

1. Confirm whether content is sensitive at current HEAD
2. If false positive, document the false positive in the remediation report
3. If true positive, classify and treat as above

For `.env` working-tree presence:

1. Confirm local-only risk tolerance is acceptable for handover
2. Confirm `.env` will not be pushed or shared before handover closes
3. Confirm `.env.save` cleanup intent

---

## 7. Boundary applied (echoed)

- ❌ No credential rotation performed
- ❌ No file deletion
- ❌ No `.gitignore` modification (despite S0 recommendation)
- ❌ No commit
- ❌ No push
- ❌ No rebase
- ❌ No merge

This audit only READS and REPORTS. All remediation decisions await owner authorization.

---

## 8. Sign-off

| Aspect | Statement |
|---|---|
| Scope | Read-only security check. No remediation. |
| Source | `.gitignore`, `.env`, `.env.example`, `.env.save`, `scripts/tushare_data.py` (direct read), `CREDENTIAL_REMEDIATION_REPORT_20260729.md` (cross-reference), `git ls-files`, `git check-ignore` |
| Companion | This document is intended to be read alongside `REPO_HANDOVER_AUDIT.md` and the existing `CREDENTIAL_REMEDIATION_REPORT_20260729.md` |
| Boundary | D27-A1 / D28 trust governance self-audit respected. No claim promoted. No remediation applied. |
