# C Task Card — REPOSITORY_HANDOFF_REVIEW_v0.1 (resend)

**Role:** Independent Reviewer
**Mode:** READ-ONLY — write your output as the reply body; do not commit or modify any file
**Window:** Repository Handoff Cleanup v0.1
**Author of card:** CC

---

## Resend rationale

First send was BLOCKED because the baseline required a commit (`5fa917f`) that was never pushed, and the requested scope (commit-level attestation) does not apply to untracked workspace directories. Card has been redesigned to match what the evidence can actually support.

---

## Baseline (corrected)

```
Repository:        ~/finance-suite
Remote canonical:  origin/main
Reference commit:  cefc660fd7c97f372e300773b32b83d4a9f374a4
Tag:               v0.1-main-consolidation
Scope semantics:   filesystem + repository boundary, NOT commit ancestry attestation
```

Attestation rule for this review:

```
For every claim about a tracked path:
    verify against `git ls-tree -r --name-only cefc660`
For every claim about an untracked path:
    verify against the working tree filesystem only
For every claim about file content:
    verify by reading the file (no need to checkout anything)
```

There is no commit-attestation requirement. The three target directories (`docs/operations/`, `opc-competition/`, `scripts/alice_poc/`) are untracked workspace assets — they live in the filesystem, not in any commit object.

---

## Scope 1 — Asset Classification

For each of the three untracked directories, output:

```
Path:
Purpose:           (what is actually in it, not what CC assumes)
Owner:             (if discernible from file content / naming)
Lifecycle:         Active / Stale / POC / Archive
Recommendation:    KEEP / MOVE / ARCHIVE / REMOVE
Risk:              (what could go wrong if left as-is)
Evidence:          (specific file names + line refs you actually read)
```

Specific points to verify (do not trust CC's framing — check independently):

1. `docs/operations/` — files are `CC_SWITCH_CODEX_PROVIDER_SETUP_TUTORIAL.md` and `XIANYU_CLAUDE_CODEX_PROVISION_LISTING.md`. Confirm whether they reference finance-suite code paths or external tooling only. The listing filename suggests commercial resale intent — confirm or refute from file content.
2. `opc-competition/` — files are `创业规划书_v2_模板对齐.md` and `报名表_填表参考.md`. Note: `feature/session-1-validation-outcomes` carries an older `_DRAFT_v1` of the same asset, explicitly excluded from `cefc660`. The current `v2` is untracked. Verify whether the v2 content references any current production code (it should not — competition materials are by definition non-runtime).
3. `scripts/alice_poc/` — files include `run_alice_poc.RECOVERED.py` (the `.RECOVERED` suffix indicates a prior recovery event), `wind_focus/`, `data/`, `__pycache__/`. Verify whether `__pycache__/` contains a recent mtime that proves prior execution. Also: `scripts/` is in the production import path (`server_scripts/intel_api.py:26-27` inserts `SCRIPTS_PATH` into `sys.path`). Determine whether `alice_poc` is reachable from any inbound code reference, not merely whether it lives in a path-on-sys-path. If reachable, the boundary is at risk even if no inbound reference exists today.
4. New untracked as of 2026-08-04 13:13: `aws-idea-to-frontier/`. Was in `feature/session-1-validation-outcomes`, excluded from `cefc660`, has now reappeared in the workspace. Treat as a fourth Scope 1 item.

---

## Scope 2 — Drift Detection

Drift means: `document says X, repository contains Y`. Focus on the canonical main tree (`cefc660`).

Items CC has already self-flagged — verify scope and severity independently, do not just endorse:

1. README env-var mismatch: README lists `OPENAI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`, `WIND_API_USER/PASSWORD`, `CHOICE_USERNAME/PASSWORD`, `IFIND_USERNAME/PASSWORD`, `AKSHARE_NO_TOKEN`, `MCP_PORT`, `FRONTEND_PORT`; `.env.example` has none of those and instead contains `BRAVE_KEYS`, `CACHE_DIR`, `EM_USERNAME/PASSWORD`, `SUPADATA_API_KEY`, `THS_TOKEN`. README also writes `TAVILY_API_KEY` while the file uses `TAVILY_KEYS`.
2. README `npm install` and Node 18+ requirement, but no `package.json` exists in `cefc660` tree.
3. README tree listing includes `backend/`, which does not exist as a directory.

Determine for each: does the discrepancy make the README's "Local Reproduction" section **non-executable**? If yes, this is a material drift. If the section is illustrative only, it is a cosmetic drift. State which.

Additional drift items from the v0.1 validation report — verify, do not assume:

4. `server_scripts/intel_api.py:230` does `import market_context`, but `market_context.py` is absent from the `cefc660` tree (`git ls-tree -r cefc660 | grep market_context` returns empty). Production endpoint `/api/intel/market-context` therefore has no committed module behind it.
5. `deploy.sh` only `curl`s `app/*.html`. No backend deployment artifact in the script. Confirm by reading the file end-to-end.

Surface any additional drift you find. Do not stop at the list above.

---

## Scope 3 — Independent Verdict

Use only one of these per scope:

```
PASS
PASS WITH CONDITIONS
UNKNOWN
BLOCKED
```

Verdicts required:

- Repository Boundary verdict
- README credibility verdict (can a new developer actually follow "Local Reproduction"?)
- `docs/operations/` verdict
- `opc-competition/` verdict
- `scripts/alice_poc/` verdict
- `aws-idea-to-frontier/` verdict
- `server_scripts/intel_api.py:230` import resolution verdict
- `deploy.sh` backend coverage verdict

For each `PASS WITH CONDITIONS` or `UNKNOWN` verdict, the conditions / unknowns must be enumerated. For `BLOCKED`, the blocker must be named concretely.

---

## Constraints

```
❌ No file modification
❌ No commits
❌ No pushes
❌ No merge
❌ No directory moves
```

Output is the **reply body only**. CC will collect the verdict and reconcile with its own audit. Order is C → CC reconcile → Final Report → Boundary Rules v0.1 → window close. Do not skip ahead.

---

## Acceptance Criteria

```
Baseline attestation:            STATED (in reply header)
Untracked directory coverage:    4/4 (the three plus aws-idea-to-frontier)
Drift detection:                 CC's 5 items independently verified + any new items
Verdict set:                     per scope, from the allowed set only
File modification:               NONE
```
