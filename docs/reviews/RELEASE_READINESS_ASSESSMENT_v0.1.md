# Release Readiness Assessment v0.1

**Status:** OPEN  
**Date:** 2026-08-04  
**Mode:** Assessment Only  
**Assessor:** CC (Release Readiness Owner)  
**Baseline:** `12649ca874a987094e7b4665bdc4a8907db519a4`  
**Current governance marker:** `ffa0390` (reference evidence only; not part of evaluated tree)  
**Production:** UNCHANGED  
**Push:** FORBIDDEN

---

## 1. Baseline and scope

This assessment evaluates whether freeze point `12649ca` meets the conditions to enter **Release Preparation**.

It does **not** claim the project is ready to release today.

```
Evaluated tree:        12649ca (215 tracked paths)
Governance markers:    038e030, ffa0390
Marker role:           Audit evidence only
Excluded from input:   ffa0390 tree state, future commits, working tree changes,
                       4 untracked workspace directories
```

All evidence is sourced from the committed tree at `12649ca`, the Baseline Freeze Declaration, and prior review records produced in this governance cycle.

---

## 2. Repository readiness

### 2.1 Main reconstruction

**Evidence:**
- `origin/main` resolves to `cefc660fd7c97f372e300773b32b83d4a9f374a4` with tag `v0.1-main-consolidation`.
- Canonical main reconstruction was performed via selective checkout (recorded in project memory and `REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md`).
- Freeze point `12649ca` is a descendant of `cefc660` on local branch `runtime-validation-v0.1`.

**Assessment:** The canonical main is reproducible from remote. The local validation branch is ahead of `origin/main` by governance commits only; no production code has been modified in the drift from `987fe8b` to `12649ca`.

**Verdict:** PASS — main reconstruction is executable with documented method.

### 2.2 Release scope

**Evidence:**
- `docs/reviews/FEATURE_BRANCH_CONTENT_AUDIT_v0.1.md` classifies 1,723 changed paths into Runtime/Governance candidates vs excluded Research/Roadshow/Competition assets.
- `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md` §Inclusions and §Exclusions enumerate the RRA input boundary.
- `README.md:89-98` states the repository boundary explicitly.

**Assessment:** The runtime repository boundary is defined and excludes roadshow, competition, external reconnaissance, and personal-agent assets.

**Verdict:** PASS — release scope is explicit.

### 2.3 Excluded assets

**Evidence:**
- 4 untracked directories: `aws-idea-to-frontier/`, `docs/operations/`, `opc-competition/`, `scripts/alice_poc/` (recorded in `Baseline Freeze Declaration` Appendix B with `observed_at: 2026-08-04T08:44:56Z`).
- Uncommitted working-tree modification to `docs/governance/RUNTIME_REMEDIATION_PLAN_v0.1.md` (+26 / −7) is explicitly excluded.
- `Baseline Freeze Declaration` §Exclusions states that any commit after `12649ca` is outside RRA input.

**Assessment:** Exclusions are named, time-bounded, and not part of the evaluated tree.

**Verdict:** PASS — excluded assets are clearly identified.

---

## 3. README readiness

**Evidence:**
- `README.md:139-144` lists `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`.
- `.env.example` contains none of those keys; it uses `TAVILY_KEYS` (plural), `BRAVE_KEYS`, `CACHE_DIR`, `EM_USERNAME/PASSWORD`, `SUPADATA_API_KEY`, `THS_TOKEN`.
- `README.md:104, 126` requires Node 18+ and `npm install`; no `package.json` exists at `cefc660`.
- `README.md:64, 170, 173-174` references `deploy-backend.sh`, but `deploy.sh` does not deploy any backend artifact and uses unpinned `main` URLs.

Source: `REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md` §2.1–2.3, §3.

**Assessment:** The Local Reproduction chapter is not executable as written. A new developer cannot follow it without inventing steps or encountering missing files. This is pre-existing drift and is not fixed by this assessment.

**Verdict:** BLOCKING FOR RELEASE — README reconciliation is required before any release. For Release Preparation, acceptable if README Reconciliation v0.1 is scheduled as an exit gate.

---

## 4. Security readiness

**Evidence:**
- `scripts/tushare_data.py:13` contains hardcoded fallback token: `os.getenv("TUSHARE_TOKEN", "ac6471c66535d4aa49516341175ae6d7a7ba763682fad2b4559a05b3")`.
- `docs/MCP_TOOLS_GUIDE.md:596` contains `export TUSHARE_TOKEN="ac6471c66535d4aa49516341175ae6d7a7ba763682fad2b4559a05b3"`.

Source: `docs/security/CREDENTIAL_EXPOSURE_TUSHARE_v0.1.md`.

**Assessment:** A valid provider credential is present in the committed tree. Rotation is pending owner action; source remediation and history rewrite are deferred. CC has not tested token validity and will not.

**Verdict:** BLOCKING FOR RELEASE — credential rotation and source remediation are required before any release. For Release Preparation, acceptable if credential remediation is scheduled as an exit gate.

---

## 5. Overall verdict

| Dimension | Verdict for Release Preparation | Verdict for Release |
|---|---|---|
| Repository readiness | PASS | PASS |
| Release scope | PASS | PASS |
| Excluded assets | PASS | PASS |
| README readiness | CONDITIONAL | BLOCKING |
| Security readiness | CONDITIONAL | BLOCKING |

**Overall assessment:**

Freeze point `12649ca` is a **stable, reproducible, and scope-bounded baseline**. It is suitable as the input to **Release Preparation** under the following conditions:

1. `README Reconciliation v0.1` must be scheduled by the owner and must close before release.
2. `Credential History Purge v0.1` / Tushare token rotation must be scheduled by the owner and must close before release.
3. No release artifact is produced until both conditions are met.
4. No release artifact — including a tagged release candidate — may be produced until the above conditions close.
5. The evaluated tree remains `12649ca`; later governance markers are audit evidence only.

It is **not release-ready today**.

---

## 6. Required next windows before Main Release Preparation

| Window | Owner | Status |
|---|---|---|
| README Reconciliation v0.1 | Human programmer / owner | Required |
| Credential History Purge v0.1 | Owner | Required |
| Workspace Boundary v0.1 | Owner | Recommended |
| Backend Deployment Chain v0.1 | Implementation team | BLOCKED until remediation |

---

## 7. Cross-references

- `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md`
- `docs/reviews/REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md`
- `docs/reviews/FEATURE_BRANCH_CONTENT_AUDIT_v0.1.md`
- `docs/security/CREDENTIAL_EXPOSURE_TUSHARE_v0.1.md`
- `docs/governance/REPOSITORY_BOUNDARY_RULES_v0.1.md`

---

**End of assessment**
