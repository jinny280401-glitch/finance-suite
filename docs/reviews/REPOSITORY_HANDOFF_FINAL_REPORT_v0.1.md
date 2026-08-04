# REPOSITORY_HANDOFF_FINAL_REPORT_v0.1

**Status:** DRAFT
**Date:** 2026-08-04
**Window:** Repository Handoff Cleanup v0.1
**Reviewers:** CC (audit + reconciliation) + C (independent review)
**Capability:** NOT PROVEN
**Production:** UNCHANGED

---

## 0. Reviewer Note (kept verbatim by request)

> Independent review improved confidence not by confirming all findings, but by exposing one incorrect claim and refining the evidence boundary.

C's value in this window was not "finding more problems" — it was demonstrating that the audit process itself can catch the auditor's own errors. That is the more important property of the governance system.

---

## 1. Baseline

```
Repository:        ~/finance-suite
Remote canonical:  origin/main
Reference commit:  cefc660fd7c97f372e300773b32b83d4a9f374a4
Tag:               v0.1-main-consolidation
Branch under audit: runtime-validation-v0.1 (local, unpushed)
```

Attestation rule used throughout this report:

| Asset type | Verification method |
|---|---|
| Committed path | `git ls-tree -r --name-only cefc660` |
| Untracked path | filesystem observation only |
| File content | direct read |
| File mtime | `ls -l` snapshot with `observed_at` |

A previous version of the C task card mixed these and required commit-level attestation for untracked workspace directories. The mistake is recorded in `feedback_engram_lesson_filter` review queue.

---

## 2. Confirmed Findings

### 2.1 MAJOR — drift between README and `.env.example`

`README.md:130-145` requires `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY` (singular). `.env.example` contains none of these, has plural `TAVILY_KEYS` (the code reads plural too), and additionally has `BRAVE_KEYS`, `CACHE_DIR`, `EM_USERNAME/PASSWORD`, `SUPADATA_API_KEY`, `THS_TOKEN`.

Effect: documented configuration route is not executable as written.

### 2.2 MAJOR — README requires Node/npm with no manifest

`README.md:104, 126` requires Node 18+ and instructs `npm install`. No `package.json` exists in `cefc660`. The "if applicable" qualifier gives no criterion for skipping the failing step.

Effect: a new developer cannot pass `Local Reproduction` without inventing a step.

### 2.3 MAJOR — `deploy.sh` fetches from unpinned `main`

`deploy.sh:14-38` curl five `https://raw.githubusercontent.com/.../main/...` URLs (verified `grep -c` returns 5). There is no commit or artifact digest binding the deployed static set to `cefc660`. Reproducibility is by accident of "who pushed last."

This finding was added by C independently and is a stronger statement than CC's original "no backend coverage" — the static deployment itself is not reproducibly bound to the baseline either.

### 2.4 BLOCKING — `market_context` module is absent from the canonical tree

`server_scripts/intel_api.py:230` does `import market_context` after adding `scripts/` to `sys.path` (`intel_api.py:21-27`). `git ls-tree -r --name-only cefc660` returns no `market_context.py`. The exception handler at `intel_api.py:232-263` returns a failure-shaped payload on import failure, so an HTTP response is not evidence of import resolution.

Effect: the `/api/intel/market-context` endpoint named in the README has no committed module behind it. Whether it works in production depends on a non-committed filesystem state.

### 2.5 BLOCKING — backend deployment path is unresolved

`deploy.sh` retrieves only `app/*.html` and reloads nginx. It contains no step that deploys `server_scripts/`, `mcp_server.py`, `research_runtime/`, or any backend dependency. nginx is configured to proxy `/api/` to `http://127.0.0.1:8000` (`deploy.sh:93-100`), but no evidence in the repository attests how that process is started, what revision it runs, or how its code reaches the server.

Effect: the repository does not attest a backend. Any runtime claim about backend services is unevidenced.

---

## 3. Refined Claim (correction to C's wording)

C stated: "README contains no `backend/` tree entry." Verified reading: README has no `backend/` directory in its tree diagram, but the root directory contains `deploy-backend.sh` and README references it four times (`README.md:64, 170, 173, 174`). The substance of the problem is **not** "no backend exists" — it is "README claims a backend can be started but does not explain what the backend artifact is, what runs it, or where it comes from." `deploy-backend.sh` itself is not covered by `deploy.sh`.

Claim strength correction: this is a different drift from what C described, with the same severity (the Local Reproduction chapter is still not executable as written), but a different fix target.

---

## 4. Boundary Findings (carry forward into Boundary Rules v0.1)

| Rule | Summary | Source of evidence |
|---|---|---|
| **A. Evidence Type Matches Asset Type** | Committed asset → git SHA / tree verification. Untracked asset → filesystem observation. Do not mix. | First-send C task card bug |
| **B. Temporal Validity** | All repository evidence carries `observed_at`, reference SHA, and scope. Applies to Git topology, workspace inventory, and runtime state. | `feature/sidebar-market-temperature-fallback` ahead/behind numbers shifted between two reads of the same day |
| **C. Claim Strength** | "Evidence of X exists" does not imply "X works." Specifically: `deploy-backend.sh` exists ≠ backend deployment works; `README.md` exists ≠ Local Reproduction succeeds. | README drift block |
| **D. Workspace Inventory Snapshot** | Each audit session begins with a recorded snapshot of `tracked_files`, `untracked_dirs`, and `excluded_paths`, with `observed_at` and `workspace_root`. The end-of-session snapshot is compared to the start to attribute additions/removals. | `aws-idea-to-frontier/` reappeared 2026-08-04 13:13 and was not caught by CC's review flow until C reported the mtime |
| **E. Independent Review Function** | An independent reviewer's value includes surfacing the auditor's own errors. The review artifact must record both the agreed findings and the corrections, not just the agreed findings. | C's "no backend" claim was wrong, but the underlying risk stands |

---

## 5. Untracked Workspace Asset Inventory

All four directories verified as zero-path in `git ls-tree -r --name-only cefc660`; classification uses filesystem evidence only.

| Path | Recommendation | mtime observed | Risk note |
|---|---|---|---|
| `docs/operations/` | MOVE | 2026-08-03 21:13 / 22:10 | External tooling tutorial + commercial service listing. The listing is commercial copy, not a Finance Suite asset. |
| `opc-competition/` | MOVE | 2026-08-03 23:27 / 23:30 | External application material with public maturity claims. The document itself contains internal claim discipline (`创业规划书_v2_模板对齐.md:155-158`) which acknowledges the boundary problem. |
| `scripts/alice_poc/` | ARCHIVE + separate security review | 2026-06-20 23:23 (source), 2026-06-21 00:30 (binary), 2026-06-21 00:31 (data) | Runnable POC. `scripts/` parent is in `server_scripts/intel_api.py` `sys.path`. No inbound executable reference in `cefc660`, but namespace import remains possible. Binary and capture data have no committed provenance. |
| `aws-idea-to-frontier/` | MOVE | 2026-08-04 13:13 | External application draft. Reappeared after `cefc660` exclusion. Public-facing maturity and infrastructure claims are not runtime evidence. |

This window does **not** move, archive, or delete any of these. Those are owner actions. The table records CC + C agreed classification only.

---

## 6. Credential Exposure (cross-reference)

Independent of the boundary audit, an in-tree credential exposure was found during P0 of this window: a hardcoded Tushare Pro token in `scripts/tushare_data.py:13` and `docs/MCP_TOOLS_GUIDE.md:596`. Full record in `docs/security/CREDENTIAL_EXPOSURE_TUSHARE_v0.1.md`. Status: rotation pending owner action; source remediation on hold; history rewrite DEFERRED. CC did not test token validity and will not.

---

## 7. Verdict Summary

| Scope | Verdict |
|---|---|
| Repository Boundary (commit tree) | PASS WITH CONDITIONS — `cefc660` excludes all four paths, but the live working tree contains them |
| Repository Boundary (workspace) | NOT ESTABLISHED — drift not surveyed continuously; this audit captured one slice |
| README Local Reproduction | UNKNOWN — cannot follow verbatim; runtime execution not performed |
| `docs/operations/` | PASS WITH CONDITIONS — external material; must stay outside runtime worktree |
| `opc-competition/` | PASS WITH CONDITIONS — external application; maturity claims unverified |
| `scripts/alice_poc/` | PASS WITH CONDITIONS — runnable POC in production `sys.path`; no inbound reference but reachable in principle |
| `aws-idea-to-frontier/` | PASS WITH CONDITIONS — external application; runtime claim mismatch risk |
| `server_scripts/intel_api.py:230` import | UNKNOWN — module absent in `cefc660`; runtime environment not inspected |
| `deploy.sh` backend coverage | UNKNOWN — no deploy step; a separate process may exist, no evidence |
| `deploy.sh` reproducibility | UNKNOWN — unpinned `main`; deployed content not bound to `cefc660` |
| Production capability | **NOT PROVEN** |

---

## 8. Next Windows

| Window | Scope | Status |
|---|---|---|
| `README Reconciliation v0.1` | Fix README env-vars, Node/npm step, backend artifact description. Source-modifying window, not audit. | **Required next** |
| `Credential History Purge v0.1` | Decision on `git filter-repo` against `5b04fa0..cefc660`. Requires separate authorization. | DEFERRED |
| `Workspace Boundary v0.1` | Execute MOVE/ARCHIVE on the four untracked directories per the agreed classification. Owner decision on destination. | Pending owner |
| `Backend Deployment Chain v0.1` | Establish how `server_scripts/` reaches production; resolve `market_context` module; bind deploy to a specific SHA. | BLOCKED — requires implementation |

---

## 9. Sign-off

| Role | Verdict |
|---|---|
| CC (audit + reconciliation) | Confirmed 2 BLOCKING + 3 MAJOR findings; corrected C's claim wording; added Rules A–E |
| C (independent review) | 5 items verified; 1 wording corrected; boundary verification improved by surfacing the correction itself |
| Window Status | **OPEN — awaiting Boundary Rules v0.1 then close** |
| Production | **UNCHANGED** |

---

**End of Report**
