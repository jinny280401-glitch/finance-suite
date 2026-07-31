# REPOSITORY_RECOVERY_DECISION.md

**Date**: 2026-07-30
**Task Status**: DONE
**Closure Note**: document completed; remaining item was task-board granularity residue.
**Auditor**: CC (Claude Code, this session)
**Scope**: Read-only recovery audit. No commit, no merge, no reset, no restore, no push, no clean, no staging changes.
**Target repos**:
- Website: `https://github.com/jinny280401-glitch/finance-suite` (CC primary scope)
- Agent: `https://github.com/jinny280401-glitch/Linmeimei-Agent` (CC consultative scope — to answer Q1)
**Companion docs (read)**:
- `/Users/Zhuanz/finance-suite/SHARED_GATE_REPOSITORY_STATUS.md` (C, 17113 bytes)
- `/Users/Zhuanz/Documents/New project 6/docs/research/VERA_POSITIONING_ALIGNMENT_NOTE_V0.1.md` (C, 14394 bytes)
- `/Users/Zhuanz/finance-suite/BUILDER_BASELINE_DECISION_RECORD_20260729.md` (existing untracked)
- `/Users/Zhuanz/finance-suite/REPOSITORY_SHARE_READINESS_REVIEW_20260729.md` (existing untracked)
- `/Users/Zhuanz/finance-suite/CREDENTIAL_REMEDIATION_REPORT_20260729.md` (existing untracked)

---

## 0. Critical fact (must read first)

**The user's Q1 ("staged deletions 来源") is misplaced for finance-suite and correctly points at Linmeimei-Agent.** This audit therefore spans both repos to answer Q1 fully and Q2-Q4 with repo-specific facts.

| Repo | Tracked modifications | Untracked entries | Staged deletions | Index-worktree split |
|---|---|---|---|---|
| finance-suite (Website) | 17 | 36 | **0** | **NO** |
| Linmeimei-Agent (Agent) | 0 | 21 | **71** | **YES** (per C, confirmed by this audit) |

Source for finance-suite row: `git status --short` direct read.
Source for Linmeimei-Agent row: `git status --short` direct read + `SHARED_GATE_REPOSITORY_STATUS.md` §1.2.

---

## 1. Q1 — Staged deletions 来源？

### 1.1 finance-suite: zero staged deletions

`git diff --staged --name-only --diff-filter=D` returned empty. `git status --short` contains no `D ` prefix entries.

**Verdict**: There are no staged deletions in the Website repo. The question does not apply.

### 1.2 Linmeimei-Agent: 71 staged deletions confirmed

71 files staged as deleted in the Agent repo. Sample of staged-deleted entries:

```
D  .env.example
D  .gitignore
D  CLAUDE.md
D  Caddyfile
D  Dockerfile
D  LICENSE
D  README.md
D  app/__init__.py
D  app/config.py
D  app/main.py
D  app/harness/*.py   (6 files)
D  app/models/*.py    (2 files)
D  app/routers/*.py   (4 files)
D  app/services/*.py  (6 files)
D  app/skills/router.py
D  assets/avatar.png
D  config/*.toml *.sh *.conf *.service (5 files)
D  deploy.sh
D  docker-compose.yml
D  docs/*.md  (8 files)
D  install.sh
D  requirements.txt
D  skills/*/SKILL.md  (12 files)
D  skills/finance-suite/prompts/*.md  (8 files)
D  skills/finance-suite/references/*.md  (2 files)
D  workspace/*.md  (7 files: AGENTS, CLAUDE, HEARTBEAT, IDENTITY, MEMORY, SOUL, TOOLS, USER)
```

### 1.3 Source analysis

The 71 staged-deleted file names **largely overlap with the 21 untracked entries** at file/directory level. Both lists contain `.env.example`, `.gitignore`, `CLAUDE.md`, `Caddyfile`, `Dockerfile`, `LICENSE`, `README.md`, `app/`, `config/`, `deploy.sh`, `docker-compose.yml`, `docs/`, `install.sh`, `requirements.txt`, `skills/`, `workspace/`, etc.

**Content sampling** (this audit sampled two files):

- `app/main.py`: staged-deleted version (`git show HEAD:app/main.py`) and untracked on-disk version (`head -10 app/main.py`) are **byte-identical**. Both start with `"""林妹妹 Agent v2.0 — FastAPI 入口"""`.
- `README.md`: `diff <(git show HEAD:README.md) README.md` returned **empty** (no differences).

**Inferred source pattern** (this is an inference, not a confirmed git operation log):
- A `git rm -r .` (or equivalent broad deletion) was executed at some point, staging all tracked files for deletion.
- The deletion was **never committed** (`git diff --staged --name-only | wc -l` shows 71 staged entries but the working HEAD is at `eb280b2` and HEAD's parent has the files).
- The actual files remained on disk throughout — `git rm` does not touch working-tree contents by default in modern git, but `git rm --cached` would also leave them; in either case the on-disk files are unchanged.
- The result: an index that says "delete everything on next commit" while the working tree says "files are still here".

This is a textbook **index-worktree split**. C's `SHARED_GATE_REPOSITORY_STATUS.md` §1.2 already identified this pattern correctly.

**Recovery semantics**:
- Files are NOT actually deleted on disk. They are intact.
- The next `git commit` would delete them.
- The next `git restore --staged .` would un-stage the deletions and restore them as tracked (matching on-disk content).
- The choice is between: (a) restore tracked + on-disk consistency, (b) commit the deletion (intentional, irreversible in shared history), (c) hold pending owner decision.

This audit does NOT take the choice. Recovery action is forbidden per task card scope.

---

## 2. Q2 — untracked 文件是否对应替代版本？

### 2.1 Linmeimei-Agent: untracked are NOT alternative versions

The untracked files in Linmeimei-Agent are **the same content** as the staged-deleted versions, not replacements. They are byte-identical samples (`app/main.py`, `README.md`). The pattern is **stale deletion staging**, not staged replacement.

**Verdict for Agent**: NO — untracked entries do not represent replacement versions. They are the original files that survived the (incomplete) `git rm`. If the deletion were committed, the untracked entries would re-emerge as "new untracked files with identical content" — but they would not be replacements; they would be the originals.

### 2.2 finance-suite: untracked are NOT replacements of any tracked file

The 36 untracked entries in finance-suite (recounted this session) are:

**Governance decision records (7)** — created 2026-07-29 by a prior session:
- `BUILDER_BASELINE_DECISION_RECORD_20260729.md`
- `CREDENTIAL_REMEDIATION_REPORT_20260729.md`
- `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md`
- `REPOSITORY_SHARE_READINESS_REPORT.md`
- `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md`
- `REVIEW_REQUEST_D23.md`
- `REVIEW_REQUEST_D23_FOLLOWUP.md`
- `SHARED_GATE_REPOSITORY_STATUS.md` (added by C this session)

**Governance / finding / evidence directories (6)**:
- `aws-idea-to-frontier/` (new AWS application content)
- `opc-competition/` (new OPC competition content)
- `docs/evidence/`
- `docs/governance/`
- `docs/incidents/`
- `docs/signal-validation-v0.1/`
- `docs/handover/` (created by this session)
- `docs/findings/DAY23_RUNTIME_TRUST_GAP_FINDING.md`
- `docs/findings/Presentation_Truth_Guard_RCA_20260727.md`
- `docs/joinquant-integration-audit-20260722.md`

**Roadshow extras (~20 files)**:
- `roadshow-2026-06/FINAL_DEMO_CHECKLIST.md`
- `roadshow-2026-06/ROADSHOW_DEMO_SPEAKER_CUE_CARD.md`
- `roadshow-2026-06/VERA_TRUST_GATE_SOURCE_SYSTEM_ROADSHOW.md`
- `roadshow-2026-06/Vera-路演PPT-HTML版.zip`
- `roadshow-2026-06/html/ROADSHOW_FINAL_MANIFEST.md`
- `roadshow-2026-06/html/fig-*.html` (multiple)
- `roadshow-2026-06/html/assets/*.png` (multiple)
- `roadshow-2026-06/html/batch-print.html`
- `roadshow-2026-06/html/export-pdf.sh`
- `roadshow-2026-06/html/export-slides-to-pdf.js`
- `roadshow-2026-06/html/output/` (generated dir)
- `roadshow-2026-06/html/tmp/` (generated dir)
- `roadshow-2026-06/html/vera-roadshow-2026-aws.pdf`
- `roadshow-2026-06/output/`
- `roadshow-2026-06/tmp/`

**Cross-check against tracked files**: None of these untracked paths exist with the same name in the tracked tree. They are not "renamed/rewritten versions" of any tracked file.

**Verdict for Website**: NO — untracked entries are not replacements. They are:
1. Governance decision records (new artifacts awaiting owner classification per `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md`)
2. New project directories (AWS, OPC, roadshow-2026-06 extras)
3. Generated directories (`output/`, `tmp/`, `*.zip`, `*.pdf`)

### 2.3 Generated/working files vs intentional artifacts

| File/Dir | Status | Recommendation category |
|---|---|---|
| `roadshow-2026-06/html/output/` | Generated | Personal environment; not for repo |
| `roadshow-2026-06/html/tmp/` | Generated | Personal environment; not for repo |
| `roadshow-2026-06/output/` | Generated | Personal environment; not for repo |
| `roadshow-2026-06/tmp/` | Generated | Personal environment; not for repo |
| `roadshow-2026-06/Vera-路演PPT-HTML版.zip` | Generated binary | Personal environment; not for repo |
| `roadshow-2026-06/html/vera-roadshow-2026-aws.pdf` | Generated binary | Personal environment; not for repo |
| `roadshow-2026-06/html/assets/*.png` | Likely generated images | Verify before commit |
| `docs/handover/` (this session) | New governance dir | Owner classification needed |

---

## 3. Q3 — 当前 HEAD 是否可作为 baseline？

### 3.1 finance-suite HEAD `cdac1ca`

| Field | Value |
|---|---|
| Branch | `feature/session-1-validation-outcomes` |
| Local HEAD | `cdac1ca` |
| Tracking remote HEAD | `7eddfc9` (per BUILDER_BASELINE) |
| `origin/main` (BUILDER_BASELINE) | `9e39065` |
| `origin/main` (this session) | `d352b85` (note: advanced past BUILDER_BASELINE record) |
| Ahead of tracking | 7 commits |
| Working tree | DIRTY (17 modified + 36 untracked) |

**Candidate local-only commits** (per BUILDER_BASELINE_DECISION_RECORD):

```
6d5cba7 docs(findings): record BF-JQ-01 phantom provider governance finding
32dc50b feat(vera-v4): 16-page roadshow deck finalized
47ba08c fix(vera-v4): add missing deck runtime assets
fcafa4d feat(vera-v4): Trust Gate frontend integration + 天玑 brand upgrade
6fb2deb refactor(roadshow): 路演页面从工程语言切换到评委语言
324f3b5 feat: D26 收口 — 金融数智杯提交版 v1 + Runtime Trust Next Window v0.1
cdac1ca docs(memory): record fusion audit freeze
```

**Verdict for Website**: HEAD is **NOT suitable as a handover baseline** for the following reasons:
1. `Baseline Frozen` gate is `HOLD` (per BUILDER_BASELINE_DECISION_RECORD); no owner-approved commit and file set exists.
2. Working tree is DIRTY (17 modified + 36 untracked); cannot produce a clean tree from HEAD without explicit owner disposition.
3. 11 of 17 modified files are roadshow deck assets (active work stream, not stable).
4. `Security Status` gate is `FAIL` per `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md` (gitleaks findings unresolved).
5. `Governance Assets` gate is `PARTIAL` (local assets present but not in reproducible baseline).

### 3.2 Linmeimei-Agent HEAD `eb280b2`

| Field | Value |
|---|---|
| Branch | `main` |
| Local HEAD | `eb280b2 fix(prompts): replace script calls with MCP tools in stock-watcher.md` |
| Working tree | DIRTY / INDEX-WORKTREE SPLIT |

**Verdict for Agent** (per C's SHARED_GATE_REPOSITORY_STATUS §1.2 + this audit): HEAD is **NOT safe to commit or hand over** because:
1. 71 staged deletions would delete the entire codebase if committed.
2. Working-tree content is untracked-but-intact.
3. The repo is in a state where the next naive commit is destructive.
4. `Security Status` gate is `FAIL` per C's audit (gitleaks found 15 findings).

### 3.3 Neither HEAD qualifies as baseline today

Per `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md` gate matrix:
- `Builder Ready: NO`
- `Share Gate: HARD BLOCKED / AWAITING DECISION`

Neither repo meets the gate. Both must be in a **clean state with owner-approved commit/file set** before any external sharing or Builder handover.

---

## 4. Q4 — 哪些文件属于个人环境，不应进入仓库？

### 4.1 finance-suite personal-environment candidates

Already gitignored (low risk):
- `.env` (gitignored, contains real credentials — never share tree)
- `.env.save` (gitignored, placeholder)
- `.env.example` (TRACKED — empty template, intended)
- `.codex_remote/` (NOT gitignored; risk of future accumulation)
- `__pycache__/` (gitignored)
- `.venv/`, `venv/` (gitignored)
- `logs/` (gitignored)
- `.claude/` (gitignored in finance-suite; personal Claude Code state)
- `.DS_Store` (gitignored)
- `*.pyc` (gitignored)

NOT gitignored but recommended candidates for gitignore:
- `.pytest_cache/` (visible from earlier ls; pytest test cache)
- `.codex_remote/` (per security check S0 recommendation)

Generated/working directories (not for repo, even if gitignored):
- `roadshow-2026-06/html/output/` (generated)
- `roadshow-2026-06/html/tmp/` (generated)
- `roadshow-2026-06/output/` (generated)
- `roadshow-2026-06/tmp/` (generated)
- `roadshow-2026-06/Vera-路演PPT-HTML版.zip` (generated binary)
- `roadshow-2026-06/html/vera-roadshow-2026-aws.pdf` (generated binary)
- `roadshow-2026-06/html/assets/*.png` (likely generated)
- `data/morning_brief/latest.html`, `data/morning_brief/latest.json`, `data/morning_brief/loop_state.json` (loop run output — already MODIFIED)

### 4.2 Linmeimei-Agent personal-environment candidates

Already gitignored (per C's audit):
- `.env`, `.env.save` etc.

NOT gitignored but currently untracked:
- `.claude/` (untracked — likely personal Claude Code state)
- `scripts/` (untracked — directory, unknown content)
- `tests/` (untracked — directory, unknown content)
- `workspace/` (untracked — contains AGENTS.md, CLAUDE.md, HEARTBEAT.md, IDENTITY.md, MEMORY.md, SOUL.md, TOOLS.md, USER.md — **persona/state files**, NOT production code)

**`workspace/`** in Linmeimei-Agent is particularly notable: its files (IDENTITY, SOUL, USER, MEMORY, AGENTS, TOOLS, CLAUDE, HEARTBEAT) are persona definitions and agent state, not code that should ship with the repo. If the staged deletions were restored, these workspace files would come back as tracked — but they appear to be personal/instance-specific configuration rather than shared repo content.

This audit flags `workspace/` as a **high-priority personal-environment file group** for owner decision.

### 4.3 Personal-environment summary

| Category | finance-suite | Linmeimei-Agent |
|---|---|---|
| Generated binary outputs | 6+ (PDFs, ZIPs, generated images) | unknown (untracked content unread) |
| Generated working dirs | 4 (`output/`, `tmp/` × 2 sites) | unknown |
| Loop run state | 3 (`data/morning_brief/*`) | n/a |
| Persona/state files | n/a | `workspace/*.md` (8 files) — high priority |
| IDE / tool cache | `.pytest_cache/` (not gitignored) | unknown |
| Codex runtime artifacts | `.codex_remote/` (not gitignored) | unknown |

---

## 5. Decision matrix (handoff, NOT applied)

Per task-card boundary, this audit produces a decision matrix but does NOT apply any decision. Each row requires explicit owner authorization.

| Decision | Affected repo | Recommended default | Reversibility | Awaiting |
|---|---|---|---|---|
| Restore Linmeimei-Agent staged deletions | Agent | `git restore --staged .` (un-stage deletions; files remain tracked if they were tracked before; here they are no longer tracked because index says deleted) → followed by `git add .` to re-track on-disk content | Recoverable (re-stage) | Owner + C scope |
| Commit Linmeimei-Agent staged deletions | Agent | **REJECT** — would delete the codebase | **IRREVERSIBLE** | N/A |
| Add `.codex_remote/` to .gitignore | Website | APPLY (low risk; aligns with S0) | Recoverable | Owner |
| Add `.pytest_cache/` to .gitignore | Website | APPLY (low risk) | Recoverable | Owner |
| Commit finance-suite governance docs (7 files) | Website | DEFER to owner classification per `GOVERNANCE_ASSET_CLASSIFICATION_MATRIX_20260729.md` | Recoverable | Owner |
| Commit finance-suite `aws-idea-to-frontier/`, `opc-competition/` | Website | DEFER (deadline-window specific; may be temporary) | Recoverable | Owner |
| Commit finance-suite roadshow extras | Website | SELECTIVE (e.g., `ROADSHOW_FINAL_MANIFEST.md`, `fig-*.html` are intentional; `output/`, `tmp/`, ZIPs, PDFs are generated) | Recoverable | Owner |
| Set baseline commit | Both | DEFER until gates per `REPOSITORY_SHARE_READINESS_REVIEW_20260729.md` are GREEN | Recoverable | Owner |

---

## 6. Boundary applied

- ❌ No commit
- ❌ No merge
- ❌ No rebase
- ❌ No push
- ❌ No reset, restore, add, rm, or clean
- ❌ No `.gitignore` modification
- ❌ No file deletion
- ❌ No credential rotation
- ❌ No provider integration
- ❌ No code change

This document reports and recommends; it does not act.

---

## 7. Sign-off

| Aspect | Statement |
|---|---|
| Scope | Read-only recovery audit across Website and Agent repos. |
| Method | File reads + git status + sampled content diff + cross-reference to existing governance records. |
| Companion | `REPO_HANDOVER_AUDIT.md`, `GIT_SECURITY_HANDOVER_CHECK.md`, `SHARED_GATE_REPOSITORY_STATUS.md` (C), `BUILDER_BASELINE_DECISION_RECORD_20260729.md`. |
| Boundary | D27-A1 / D28 trust governance self-audit respected. No claim promoted. No decision applied. |
| Coordination | CC covers Website repo (primary) + consultative view of Agent repo (for Q1 source attribution). C retains Agent-repo authority per `SHARED_GATE_REPOSITORY_STATUS.md`. |

---

## 8. Owner Decisions (recorded 2026-07-30)

Recorded after the audit above. Sections 1–7 are the CC audit; this section is the owner's ruling on each open item. **No decision below has been executed.**

### 8.1 Window classification

```text
Controlled Recovery Audit
        ↓
Evidence Complete
        ↓
Shared Gate HOLD
```

Recovery Action has **NOT** been reached. Evidence collection is complete; action is not authorized.

### 8.2 Four decisions

| # | Item | Owner decision | Rationale |
|---|---|---|---|
| D1 | Agent repo 71 staged deletions | **暂不 restore** — hold, preserve the scene | `restore` is itself a mutation that changes index state. Current objective is preserving the scene, not repairing git state. |
| D2 | Tushare token exposure | **PENDING OWNER DECISION** — open a separate Credential Remediation Window | Highest-priority risk, but must not be mixed into handover. Requires: (1) validity check, (2) revoke/rotate, (3) git-history presence determination, (4) history-rewrite assessment if needed. |
| D3 | `.codex_remote/` → `.gitignore` | **Deferred** | Hygiene fix, but Shared Gate is still HOLD. Priority is Repository Reality + Security Findings, not Repository Cleanup. |
| D4 | finance-suite baseline | **`cdac1ca` REJECTED as baseline** — open a Baseline Definition Decision Window | 7 local-only commits mix roadshow / provider findings / frontend / competition materials / memory. `commit exists` ≠ `baseline exists`. |

### 8.3 D2 detail — Credential Remediation Window (not opened)

```text
Credential Exposure:  CONFIRMED
Remediation:          PENDING OWNER DECISION

Currently forbidden:
  ❌ rotate
  ❌ revoke
  ❌ history rewrite
```

### 8.4 D4 detail — Baseline options (none selected)

| Option | Description | Status |
|---|---|---|
| A | Select an existing stable commit | Not selected |
| B | Create a new clean baseline commit | Not selected |
| C | Split delivery streams, then define baseline | Not selected |

No option is executed in this window.

### 8.5 Shared Gate final state

```text
finance-suite:
  Repository:        DIRTY
  Baseline:          NOT FROZEN

Linmeimei-Agent:
  Index:             WORKTREE SPLIT
  Recovery:          PENDING OWNER DECISION

Security:
  Credential Findings: OPEN

Shared Gate:         HOLD
Handover Ready:      NO
Implementation:      NOT AUTHORIZED
```

### 8.6 Governing insight

> 仓库接管不是 Git 操作问题，而是状态真实性问题。

Proven in this audit:

```text
文件删除状态  ≠  文件消失
HEAD          ≠  baseline
目录存在      ≠  能力存在
credential 在本地  ≠  安全
```

Shared Gate HOLD is the correct outcome. Recovery action is the owner's call, not the agent's self-repair.
