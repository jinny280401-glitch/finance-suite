# Release Readiness Adversarial Review v0.1

**observed_at:** `2026-08-04T09:07:58Z`  
**Reviewer:** C  
**Target:** `docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md`  
**Baseline:** `12649ca874a987094e7b4665bdc4a8907db519a4`  
**Current governance marker:** `b7b0fed947982a44cb1a038b262ac144dbb3ec82` (reference evidence only)

---

## 1. Baseline Integrity Findings

### 1.1 Evaluated tree matches declared scope

**Claim reviewed:** Freeze point `12649ca` is the evaluated tree (215 tracked paths).

**Evidence:**
- `git rev-parse 12649ca` → `12649ca874a987094e7b4665bdc4a8907db519a4`
- `git ls-tree -r 12649ca | wc -l` → `215`
- Current HEAD `b7b0fed` is not evaluated; the assessment correctly states this.

**Finding:** PASS

### 1.2 Untracked directories are absent from the baseline

**Claim reviewed:** `aws-idea-to-frontier/`, `docs/operations/`, `opc-competition/`, `scripts/alice_poc/` are excluded.

**Evidence:**
- `git ls-tree -r 12649ca -- aws-idea-to-frontier/` → empty
- `git ls-tree -r 12649ca -- docs/operations/` → empty
- `git ls-tree -r 12649ca -- opc-competition/` → empty
- `git ls-tree -r 12649ca -- scripts/alice_poc/` → empty

**Finding:** PASS

### 1.3 Working-tree modification is excluded

**Claim reviewed:** Uncommitted changes to `docs/governance/RUNTIME_REMEDIATION_PLAN_v0.1.md` are excluded from the baseline.

**Evidence:**
- `git ls-tree 12649ca -- docs/governance/RUNTIME_REMEDIATION_PLAN_v0.1.md` → `blob 8f4988fb2725a22777ad3d04c9886f9c9c0bcdaa`
- `git status` shows the same file as modified in working tree (`M`).
- `git diff --stat` on the file shows `+26 / −7`.

The committed blob at `12649ca` is not the working-tree version. Exclusion is correct.

**Finding:** PASS

### 1.4 Main reconstruction method is not a single committed runbook

**Claim reviewed:** "main reconstruction is executable with documented method."

**Evidence:**
- The reconstruction method is recorded in project memory and `REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md`.
- There is no single committed file titled "Canonical Main Reconstruction Runbook" with copy-pasteable commands.

**Finding:** NEEDS EVIDENCE — the documentation exists but is distributed. For a human developer handoff, this should either be accepted as-is or a dedicated runbook window should be added.

---

## 2. Claim Boundary Findings

### 2.1 No release-readiness escalation

**Claim reviewed:** The assessment concludes "It is **not release-ready today**."

**Evidence:** Target file `RELEASE_READINESS_ASSESSMENT_v0.1.md:118`.

**Finding:** PASS — the assessment does not overstate readiness.

### 2.2 Preparation wording may be misread

**Claim reviewed:** "`README Reconciliation v0.1` is scheduled and must close before release."

**Evidence:** Target file `RELEASE_READINESS_ASSESSMENT_v0.1.md:113`.

**Finding:** OVERSTATED — CC cannot schedule owner windows. The statement implies a schedule already exists. Correction: "`README Reconciliation v0.1` **must be scheduled by the owner** and must close before release."

### 2.3 Credential window wording

**Claim reviewed:** "`Credential History Purge v0.1` / Tushare token rotation is scheduled and must close before release."

**Evidence:** Target file `RELEASE_READINESS_ASSESSMENT_v0.1.md:114`.

**Finding:** OVERSTATED — same reason as 2.2. Correction: "`Credential History Purge v0.1` / Tushare token rotation **must be scheduled by the owner** and must close before release."

### 2.4 Conditional vs release verdict is clear

**Claim reviewed:** The overall verdict table distinguishes "for Release Preparation" from "for Release."

**Evidence:** Target file `RELEASE_READINESS_ASSESSMENT_v0.1.md:101-107`.

**Finding:** PASS — the two-column table prevents the most common readiness escalation.

### 2.5 Capability claims are bounded

**Claim reviewed:** No statement in the assessment implies that any runtime endpoint works in production.

**Evidence:** Scan of §2–§5.

**Finding:** PASS — the assessment stays in repository-state space and does not collapse presence into capability.

---

## 3. Human Developer Handoff Findings

### 3.1 New developer cannot follow README verbatim

**Evidence:**
- `README.md:139-144` requires `DATABASE_URL`, `SECRET_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`.
- `.env.example` contains none of those exact keys. It contains `TAVILY_KEYS` (plural), `BRAVE_KEYS`, `CACHE_DIR`, `EM_USERNAME/PASSWORD`, `SUPADATA_API_KEY`, `THS_TOKEN`.
- `README.md:104, 126` requires Node 18+ and `npm install`.
- `git ls-tree 12649ca -- package.json` returns empty.

**Finding:** CONFIRMED — README Local Reproduction is non-executable. The assessment correctly identifies this.

### 3.2 Backend deployment path is undocumented

**Evidence:**
- `README.md:170, 173-174` says "Start backend / MCP server: `python mcp_server.py`" or "`bash deploy-backend.sh`".
- `deploy.sh:14-38` fetches only static `app/*.html` files from unpinned `main` URLs.
- `deploy.sh` contains no step that deploys `server_scripts/`, `mcp_server.py`, backend dependencies, or invokes `deploy-backend.sh`.
- `deploy-backend.sh` exists but is not integrated into the main deployment script.

**Finding:** CONFIRMED — a new developer cannot determine how the backend reaches production. The assessment notes the missing backend deployment chain.

### 3.3 Missing committed module for documented endpoint

**Evidence:**
- `server_scripts/intel_api.py:230` does `import market_context`.
- `git ls-tree 12649ca -- scripts/market_context.py` returns empty.
- The endpoint `/api/intel/market-context` is named in README but has no committed module behind it.

**Finding:** CONFIRMED — presence of import statement does not imply the endpoint works. The assessment does not claim otherwise.

### 3.4 Most misleading statement for a new developer

> "Copy `.env.example` to `.env` and fill in required values" (`README.md:131-135`)

The table of "Required Environment Variables" (`README.md:139-144`) does not match `.env.example`. A new developer will search for keys that do not exist in the template and will not know which optional keys are actually required by the code.

**Finding:** This is the highest-risk drift for human handoff.

---

## 4. Overall Adversarial Verdict

**CONDITIONAL**

CC's assessment is sound in structure and does not overstate readiness. It correctly separates "Release Preparation" from "release-ready." However, two wording corrections are required before the assessment can be relied upon as governance evidence:

1. Change "is scheduled" to "must be scheduled by the owner" for both README Reconciliation and Credential History Purge windows.
2. Add an explicit statement that no release artifact — including a tagged release candidate — may be produced until both the README drift and the credential exposure are closed.

Additionally, the distributed nature of the main reconstruction documentation (1.4) should be noted as a residual risk for human handoff.

---

## 5. Required Corrections

| # | Location | Current wording | Required correction |
|---|---|---|---|
| 1 | `RELEASE_READINESS_ASSESSMENT_v0.1.md:113` | "`README Reconciliation v0.1` is scheduled" | "`README Reconciliation v0.1` must be scheduled by the owner" |
| 2 | `RELEASE_READINESS_ASSESSMENT_v0.1.md:114` | "`Credential History Purge v0.1` / Tushare token rotation is scheduled" | "`Credential History Purge v0.1` / Tushare token rotation must be scheduled by the owner" |
| 3 | `RELEASE_READINESS_ASSESSMENT_v0.1.md:111-116` | Conditions list | Add: "No release artifact, including a tagged release candidate, may be produced until the above conditions close." |

---

**End of review**
