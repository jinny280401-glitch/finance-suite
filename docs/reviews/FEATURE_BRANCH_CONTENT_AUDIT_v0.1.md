# Feature Branch Content Audit v0.1

**Status:** REVIEW RECORD  
**Purpose:** Document the selective consolidation decision. This file does not define runtime capability.  
**Reviewer role:** External Repository Boundary Auditor  
**Branch reviewed:** `feature/session-1-validation-outcomes`  
**Comparison:** `main...feature/session-1-validation-outcomes`  
**Merge base:** `c9c4b43a46af3ddd58ce882c0ad357365c96a8be`  
**Repository state at audit:** merge in progress on `main`; `deploy.sh` unresolved. No merge action was taken.

## Inventory

The authoritative complete inventory is produced by:

```bash
git diff --name-status main...feature/session-1-validation-outcomes
```

Result: **1,723 paths** — **1,701 added**, **22 modified**, no deletions or renames.

| Inventory group | Paths | Classification |
| --- | ---: | --- |
| `roadshow-2026-06/**` | 1,523 | Exclude from main |
| `docs/**` | 90 | Mixed; classified below |
| `app/**` | 18 | Runtime/deployment candidate; selective review |
| `scripts/**` | 24 | Runtime candidate; selective review |
| `vera-v4-launch/**` | 21 | Exclude from main |
| Remaining root, data, prompts, patches, tests, and support files | 47 | Mixed; classified below |

## A. Approved for Main — Candidate Set

These asset classes fit Repo A's **Runtime + Governance** boundary, but admission still requires ordinary code and security review. This audit does not prove runtime capability.

- Runtime code and tests: `app/**`, `scripts/**`, `research_runtime/workflow.py`, `tests/**`, `smoke_*.py`.
- Governance and architecture: `docs/governance/**`, `docs/architecture/**`, `docs/evidence/**`.
- Runtime evidence and incident records: `AUCTION_RUNTIME_*.md`, `docs/findings/**`, `docs/incidents/**`, `docs/signal-validation-v0.1/**`.
- Provider and operational code candidates: `scripts/auction_data.py`, `scripts/emquant_data.py`, `scripts/ifind_data.py`, `scripts/search.py`, `scripts/stock_data.py`, `scripts/workflow_orchestrator.py`, `scripts/choice_provider.py`, `scripts/jqdata_fetch.py`, and the two `tests/**` files.

**Boundary verdict:** These are eligible *classes*, not a blanket merge approval. The branch combines unrelated changes; each runtime change needs its own implementation and validation evidence.

## B. Exclude from Main

The following are research, presentation, competition, agent-session, or review materials. They belong in Repo B or an archival/presentation repository, not the finance-suite runtime baseline.

- All `roadshow-2026-06/**` (1,523 paths): decks, exports, images, PDFs, videos, embedded agent skills, renders, and temporary/output material.
- All `vera-v4-launch/**` (21 paths): launch composition, render outputs, media, and presentation configuration.
- `aws-idea-to-frontier/**` and `opc-competition/**`.
- `docs/competition/**`.
- `docs/research/**`, including `VERA_DEMO_ADVERSARIAL_REVIEW_v0.1.md`, `VIBE_CODING_PATTERN_SYNTHESIS_v0.1.md`, and `VIBE_CODING_PRODUCT_PATTERN_REPORT_v0.1.md`.
- Agent/session material: `MEMORY.md`, `SKILL.md`, `LOOP.md`, `STATE.md`, `loop-budget.md`, `loop-constraints.md`, `loop-run-log.md`, `docs/CLAUDE.md`, and `docs/skills/**`.
- Review, handover, and repository-process material: `BUILDER_BASELINE_DECISION_RECORD_20260729.md`, `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md`, `REPOSITORY_SHARE_READINESS_*.md`, `REVIEW_REQUEST_D23*.md`, `SHARED_GATE_REPOSITORY_STATUS.md`, `STATE_BOARD_ALIGNMENT_20260731.md`, `docs/handover/**`, and `docs/repository-ssot-map.md`.

**Boundary verdict:** Research and presentation artifacts do not become runtime capability evidence by being merged into Repo A.

## C. Need Human Decision

| Asset group | Decision required | Reason |
| --- | --- | --- |
| `deploy.sh` | Resolve semantic conflict before any merge | Conflicting targets (`static/index.html` vs `templates/index.html`) and conflicting Sidebar/workbench asset deployment scope. |
| `.env.example`, `.gitignore` | Accept/reject configuration changes | Configuration and ignore rules affect deployment and source visibility. |
| `data/morning_brief/**`, `app/weekly-recap-latest.json` | Treat as runtime fixtures or generated outputs | Current-output artifacts can be mistaken for validated evidence. |
| `app/demo-mini-to-snapshot.html`, `app/market-mini-card-20260721.html`, `app/market-snapshot*`, `app/weekly-recap*` | Confirm production runtime surface vs demo | Mixed naming and dated/demo intent. |
| `patches/kan_piao_db_session_20260730/**` | Separate authorized patch from evidence package | Contains deployment authorization material, patch files, and a hotfix test. |
| `mcp_server.py`, `prompts/stock-analyst.md`, `scripts/alice_poc/**` | Assess operational/security scope | These alter agent behavior or introduce a proof-of-concept/tooling surface. |
| Top-level status/RCA files and `docs/incidents/**` | Retain as governance evidence or move to Repo B | Some are runtime evidence; others are review/process records. |

## Recommendation

**HOLD — do not merge the feature branch as a whole.**

Use **selective cherry-pick**, grouped by a human-approved intent and validated independently:

1. governance specification/evidence records;
2. bounded runtime implementation with its tests;
3. deployment changes only after the `deploy.sh` decision;
4. keep research, presentation, competition, and agent-session material outside Repo A.

No code, merge state, conflict marker, deployment script, or existing branch asset was modified by this audit.
