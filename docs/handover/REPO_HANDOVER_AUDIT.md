# REPO_HANDOVER_AUDIT.md — finance-suite (网站仓库)

**Audit date**: 2026-07-30
**Auditor**: CC (Claude Code, this session)
**Scope**: Read-only audit. No code change. No merge. No rebase. No push. No integration.
**Target repo**: `https://github.com/jinny280401-glitch/finance-suite.git`
**Target repo role**: Website repository (per user direction 2026-07-30). Out of scope for this audit: `Linmeimei-Agent` (Agent repo).

---

## 0. Cross-references (existing 2026-07-29 baseline artifacts)

This audit does NOT duplicate the following documents, which already exist in the working tree (all untracked):

- `BUILDER_BASELINE_DECISION_RECORD_20260729.md` — current branch / commit / untracked state
- `CREDENTIAL_REMEDIATION_REPORT_20260729.md` — gitleaks findings in public history
- `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md` — public-safe classification of governance assets
- `REPOSITORY_SHARE_READINESS_REPORT.md` — readiness scan output
- `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md` — gate matrix review
- `docs/governance/Repository_Share_Gate_Status_20260729.md` — gate status LOCKED/BLOCKED

These should be read together with this audit. This document adds the **CC governance audit layer** on top.

---

## 1. Repository Inventory

### 1.1 Identity

| Field | Value |
|---|---|
| Origin URL | `https://github.com/jinny280401-glitch/finance-suite.git` |
| Role | Website repo (per user direction 2026-07-30) |
| Repo size | ~1.4 GB on disk |
| Local HEAD | `cdac1ca docs(memory): record fusion audit freeze` |
| Current branch | `feature/session-1-validation-outcomes` |
| `origin/main` HEAD (per `git log main -1`) | `d352b85 fix(deploy): add Sidebar P0 6 new assets to deploy curl list` |
| `origin/main` HEAD (per BUILDER_BASELINE) | `9e39065` (note: pre-`d352b85`; BUILDER_BASELINE record is dated 2026-07-29) |
| Tracking remote HEAD (per BUILDER_BASELINE) | `7eddfc9` |
| Ahead of tracking | 7 commits (per BUILDER_BASELINE) |
| Modified tracked files | **17** |
| Untracked entries | **34** |

### 1.2 Branch topology

```
Local branches:
  codex/auction-time-gate-qc-20260717
  codex/choice-provider-shadow-step4
  codex/day15-market-context-safety
  codex/hero-path-a-clean
  codex/sidebar-market-temperature-fallback
  feature/ifind-emquant-integration
  feature/p4-phase-a-skeleton
* feature/session-1-validation-outcomes   ← current
  feature/trust-gate-runtime
  main
  release/sidebar-workbench-20260623

Remote-tracking branches (origin/...):
  origin/codex/auction-time-gate-qc-20260717
  origin/codex/hero-path-a-clean
  origin/codex/sidebar-market-temperature-fallback
  origin/feature/ifind-emquant-integration
  origin/feature/p4-phase-a-skeleton
  origin/feature/session-1-validation-outcomes
  origin/main
  origin/release/sidebar-workbench-20260623
```

Branches with NO remote tracking (orphan candidates):
- `codex/choice-provider-shadow-step4`
- `codex/day15-market-context-safety`
- `feature/trust-gate-runtime`

Per `LOOP.md` ("Worktrees: One worktree per fix attempt; discard after verifier REJECT"), some codex branches are expected to be local-only and discardable. Confirmation of intent per branch is required before handover.

### 1.3 Local-only candidate commits (per BUILDER_BASELINE)

The 7 commits ahead of tracking branch `7eddfc9` (none approved as share baseline):

```text
6d5cba7 docs(findings): record BF-JQ-01 phantom provider governance finding
32dc50b feat(vera-v4): 16-page roadshow deck finalized — from AI tool to trusted research infra
47ba08c fix(vera-v4): add missing deck runtime assets
fcafa4d feat(vera-v4): Trust Gate frontend integration + 天玑 brand upgrade + roadshow assets
6fb2deb refactor(roadshow): 路演页面从工程语言切换到评委语言
324f3b5 feat: D26 收口 — 金融数智杯提交版 v1 + Runtime Trust Next Window v0.1
cdac1ca docs(memory): record fusion audit freeze
```

### 1.4 Untracked entry inventory (34 entries)

| Category | Files |
|---|---|
| Governance decision records | `BUILDER_BASELINE_DECISION_RECORD_20260729.md`, `CREDENTIAL_REMEDIATION_REPORT_20260729.md`, `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md`, `REPOSITORY_SHARE_READINESS_REPORT.md`, `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md`, `REVIEW_REQUEST_D23.md`, `REVIEW_REQUEST_D23_FOLLOWUP.md` |
| Directories | `aws-idea-to-frontier/`, `opc-competition/`, `docs/evidence/`, `docs/governance/`, `docs/incidents/`, `docs/signal-validation-v0.1/` |
| Governance findings | `docs/findings/DAY23_RUNTIME_TRUST_GAP_FINDING.md`, `docs/findings/Presentation_Truth_Guard_RCA_20260727.md`, `docs/joinquant-integration-audit-20260722.md` |
| Roadshow extras | `roadshow-2026-06/FINAL_DEMO_CHECKLIST.md`, `roadshow-2026-06/ROADSHOW_DEMO_SPEAKER_CUE_CARD.md`, `roadshow-2026-06/VERA_TRUST_GATE_SOURCE_SYSTEM_ROADSHOW.md`, `roadshow-2026-06/html/ROADSHOW_FINAL_MANIFEST.md`, `roadshow-2026-06/html/fig-*.html`, etc. |

### 1.5 Modified tracked files (17)

| Path | Likely cause |
|---|---|
| `app/deep-research.html` | Demo-day prep |
| `app/stock.html` | Demo-day prep |
| `data/morning_brief/latest.html`, `latest.json`, `loop_state.json` | Loop run output drift |
| `deploy.sh` | Deploy script edit |
| `roadshow-2026-06/html/*.css`, `roadshow-2026-06/html/fig*.html`, `roadshow-2026-06/html/index.html` (11 files) | Roadshow deck refinements |

**11 of 17 modified files are roadshow deck assets**. This indicates the active work stream at HEAD is roadshow-finalization, not runtime / production code.

---

## 2. Architecture Boundary Check

### 2.1 Actual directory layout

| Directory | Observable role | Files |
|---|---|---|
| `app/` | Frontend HTML pages | 25 files (.html, .js, .css) |
| `server_scripts/` | Backend API routes (NOT `server/` per task card) | 5 files (auth.py, intel_api.py, manage_users.py, watchlist_api.py, import_accounts.sh) |
| `scripts/` | Data providers + utility scripts | 29 files |
| `data/` | Generated data | 2 sub-areas: `morning_brief/`, `research_reports.json` |
| `tests/` | Tests (thin) | 3 files |
| `docs/` | Documentation + governance | Multiple subdirs |
| `prompts/` | Analysis prompt templates | ~10 .md files |
| `references/` | Reference materials | 4 files |
| `reports/` | (empty) | 0 |
| `research_runtime/` | Runtime code (events, evidence_bundle, session, workflow) | 5 .py files |
| `ops/` | Operations | 2 (monitor_sources.py, production/) |
| `handoff/` | (empty) | 0 |
| `deploy/` | Deploy configs | nginx/ |
| `roadshow-2026-06/` | Roadshow materials | many |
| `vera-v4-launch/` | Vera v4 launch | exists |
| `aws-idea-to-frontier/` | AWS application (untracked) | exists |
| `opc-competition/` | OPC competition (untracked) | exists |
| `mcp_server.py` (root) | **MCP server entry point** | 1 file at root, NOT in scripts/ |

### 2.2 Architecture observations

**Provider layer (per `scripts/`)**:
- `auction_data.py` (AkShare aggregation)
- `choice_provider.py` (Choice EmQuantAPI — exists; D16 status: FAIL_RISK)
- `emquant_data.py` (Choice EmQuantAPI direct)
- `ifind_data.py` (THS iFinD — branch `feature/ifind-emquant-integration` exists)
- `jqdata_fetch.py` (JoinQuant — current shadow/integration under audit per `docs/joinquant-integration-audit-20260722.md`)
- `macro_data.py` (AkShare macro)
- `news_providers.py`
- `stock_data.py` (AkShare Eastmoney)
- `tushare_data.py` (Tushare Pro — has **hardcoded token at line 13**, see security check)
- `video_data.py` (YouTube/B站 via Supadata)
- `wind_data.py` (Wind — STATE.md: Pending local Mac setup)

**Backend layer**:
- `server_scripts/intel_api.py` registers 6+ endpoints (e.g., `/api/intel/market-context`, `/api/intel/golden-pit`, `/api/intel/all`)
- `mcp_server.py` (root, NOT in scripts/) registers MCP tools (market_pulse etc.) — important: MCP server lives at root, separate from server_scripts

**Runtime layer**:
- `research_runtime/` has its own session/events/evidence_bundle/workflow modules — independent of server_scripts and mcp_server
- This suggests THREE execution surfaces, not one

### 2.3 Boundary integrity findings

Per the task card's forbidden actions:
- ❌ Don't infer capability from directory names — followed
- ❌ Don't treat experimental code as production — flagged below
- ❌ Don't pull PoC into canonical runtime — flagged below

**Findings**:

1. **`mcp_server.py` is at the repo root**, not under `scripts/` or `server_scripts/`. The README's project-structure section does NOT mention this file. The actual MCP entry surface is therefore NOT visible to a reader relying solely on README's "scripts/ contains data fetch scripts" framing.

2. **`research_runtime/` is structurally separate** from `server_scripts/`. It is unclear whether research_runtime is invoked by the Web/MCP path, or whether it is an alternative runnable surface. This needs runtime-level confirmation before handover.

3. **`scripts/` mixes data-layer modules (`auction_data.py`, `tushare_data.py`) with utility scripts (`site_smoke_check.py`, `loop-orchestrator.py`) and demos (`research_demo_api.py`)**. The directory name `scripts/` is generic and does not enforce a single-role boundary. Per task-card scope rule "禁止：根据目录名推断能力" — `scripts/` itself should not be treated as a uniform capability surface.

4. **`tests/` only has 3 files** (test_emquant_connection.py, test_wind_query_optional_joinquant.py, plus __pycache__). This is **not test coverage**; these are provider smoke tests. The repository's test surface is essentially absent for app/server_scripts/research_runtime.

5. **`reports/` and `handoff/` are empty** — likely placeholder directories. Handover artifacts should not be deposited there unless explicitly named.

### 2.4 Boundary integrity: NOT ENTERED

This audit makes NO determination of canonical runtime path, NO identification of canonical implementation surface, NO proposal of directory restructuring. Those decisions require Implementation Authorization per the user's task card.

---

## 3. Capability Claim Hygiene

### 3.1 Documentation claim audit

**README.md claims**:

- Line 3: "6大专业分析技能" (six major skills)
- Lines 6–14: skill table listing 6 skills with data sources (e.g., "AkShare + Tavily")
- Line 15: "集合竞价: 涨停排行+量化选股信号 | AkShare"
- Line 34: "Web版：touziagent.com"
- Lines 39–50: project structure section — only mentions `scripts/` (5 named files); **does NOT mention `app/`, `server_scripts/`, `mcp_server.py`, `research_runtime/`**

**SKILL.md claims** (this is the OpenClaw Skill manifest, `metadata.openclaw`):

- Line 4: "7大技能：看票分析、宏观内参、麦肯锡报告、视频拆解、深度研究(行业+公司)、集合竞价、自选股管理"
- Line 4: "数据层：Wind API (优先) + 东方财富实时数据(AkShare降级) + Tavily/Brave双搜索引擎 + YouTube/B站字幕提取(Supadata)"
- Line 5: 触发条件列表 implies these skills are invocable

**STATE.md reality** (per D16 Interface Health Check, recorded 2026-07-16):

- AkShare: FAIL_SAFE (fallback ready, primary unstable)
- Choice: FAIL_RISK (credential issues, not for production)
- Wind: Pending local Mac setup completion

### 3.2 Hygiene findings

| # | Claim | Source | Reality | Classification |
|---|---|---|---|---|
| F1 | "6大专业分析技能" | README | SKILL.md says **7** skills; count discrepancy | **INCONSISTENT** |
| F2 | "Wind API (优先)" | SKILL.md line 4 | STATE.md says "Pending local Mac setup completion" — Wind is **NOT actually integrated** | `Credential Exists ≠ Provider Integrated ≠ Production Capability` violated |
| F3 | All 6 (or 7) skills integrated | README / SKILL.md | `scripts/` has 11 provider modules; integration state varies per D16; no single source confirms all skills operational | **OVERCLAIM** |
| F4 | "Web版：touziagent.com" | README | No verification that touziagent.com serves all claimed pages today | UNVERIFIED |
| F5 | README project structure section | README lines 39–50 | Mentions only `scripts/` (5 files); does NOT mention `app/`, `server_scripts/`, `mcp_server.py` (root), `research_runtime/` | **STALE** |
| F6 | Skill manifest `requires.env: [TAVILY_KEYS, BRAVE_KEYS]` | SKILL.md | Runtime `.env` (local) contains both keys but TAVILY is required | PARTIAL |

### 3.3 Per the discipline locked

```
Observation ≠ Decision
Design ≠ Capability
PoC ≠ Production
Credential ≠ Integration
Provider Connected ≠ Research Capability
```

**The README + SKILL.md together present the project as a deployed 6-or-7-skill platform with Wind-primary data layer.** The actual runtime reality (per D16 status, current SOT inspection) is:
- Wind: NOT integrated (pending local setup)
- AkShare: FAIL_SAFE (degraded)
- Choice: FAIL_RISK (credential issues)

Any handover documentation derived from README/SKILL.md alone would inherit these overclaims.

### 3.4 Recommended claim corrections (NOT applied)

Per the user task-card boundary, this audit identifies but does not apply corrections. Recommendations only:

1. README "6大技能" vs SKILL.md "7大技能" → resolve to a single canonical count, with explicit citation of which scripts implement each.
2. SKILL.md "Wind API (优先)" → reclassify to "Wind API (待 Mac 本地部署完成)" or remove from `requires.env` until integrated.
3. README "Web版：touziagent.com" → add a status qualifier (e.g., "Web版 (部分功能可用)") or remove until verified.
4. README project structure → update to reflect actual layout (`app/`, `server_scripts/`, `mcp_server.py`, `research_runtime/`).

These are documentation-level changes. They do NOT enter Implementation Window. They require explicit owner approval per `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md`.

---

## 4. Implementation Authorization Gate (output of CC scope)

This audit produces the **Repository Reality + Architecture Boundary + Capability Claim Hygiene** layer of the gate. The gate requires additional layers:

```
CC scope (this document)  → Repository Reality ✓
                            Architecture Boundary ✓
                            Capability Claim Hygiene ✓
C scope (separate agent)  → Current Provider Map
                            JQData Integration Boundary
                            Credential/Runtime Requirements
                            JQData Integration Design Note
─────────────────────────────────────────
Both layers must be reviewed before any implementation is authorized.
```

The user task card already establishes the gate:
> 没有通过 Gate: 不进入代码实现。

This audit does NOT grant the gate. It documents the CC layer only.

---

## 5. Boundary applied

- ❌ No merge
- ❌ No rebase
- ❌ No push
- ❌ No code modification
- ❌ No integration
- ❌ No provider modification

Working tree at HEAD `cdac1ca` is unchanged except for this audit document and the security check document.

---

## 6. Sign-off

| Aspect | Statement |
|---|---|
| Scope | Read-only audit. No implementation. |
| Source | File reads, grep, git log, BUILDER_BASELINE_DECISION_RECORD_20260729.md, REPOSITORY_SHARE_READINESS_REVIEW_20260729.md |
| Boundary | D27-A1 / D28 trust governance self-audit respected. No claims promoted. |
| Coordination | This is the CC layer; C layer (JQData integration research) is owned by a separate agent and is required for gate completion. |
