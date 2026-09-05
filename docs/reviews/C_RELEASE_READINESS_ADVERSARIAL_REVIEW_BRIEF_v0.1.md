# C Task Card — Release Readiness Adversarial Review v0.1

**Role:** Independent Reviewer  
**Mode:** Adversarial — challenge every claim in `RELEASE_READINESS_ASSESSMENT_v0.1.md`  
**Window:** Release Readiness Assessment v0.1  
**Author of card:** CC  
**Target output:** `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md`

---

## Why this card exists

CC has produced `RELEASE_READINESS_ASSESSMENT_v0.1.md` evaluating freeze point `12649ca` for Release Preparation. Your job is not to agree but to attack the assessment from three angles:

1. **Baseline Integrity** — does the evaluated tree actually match the declared scope?
2. **Claim Boundary** — does the assessment convert repository state into overstated capability claims?
3. **Human Developer Handoff** — can a new human programmer clone the repo and correctly understand what is runnable, what is verified, and what cannot be claimed?

---

## Required baseline (do not modify)

```
Repository:        ~/finance-suite
Evaluated tree:    12649ca874a987094e7b4665bdc4a8907db519a4
Governance marker: ffa0390 (audit evidence only; do not evaluate its tree)
Remote ref:        origin/main → cefc660fd7c97f372e300773b32b83d4a9f374a4
RRA input status:  OPEN
Push:              forbidden
Implementation:    not authorized
```

Attestation rule:
- For committed paths: `git ls-tree -r 12649ca --name-only` plus direct read.
- For untracked paths: filesystem observation only, with `observed_at`.
- Do not evaluate files introduced after `12649ca`.

---

## Scope 1 — Baseline Integrity

Challenge this statement from the assessment:

> "Freeze point `12649ca` is a stable, reproducible, and scope-bounded baseline."

Verify:
1. Does `git ls-tree -r 12649ca` contain exactly the paths CC claims (215)?
2. Are the 4 untracked directories (`aws-idea-to-frontier/`, `docs/operations/`, `opc-competition/`, `scripts/alice_poc/`) actually absent from the `12649ca` tree?
3. Is the uncommitted modification to `docs/governance/RUNTIME_REMEDIATION_PLAN_v0.1.md` absent from the `12649ca` tree?
4. Are any files in `12649ca` that should have been excluded per the Repository Boundary Rules?

For each item, output:

```
Claim:
Evidence:
Finding:
```

---

## Scope 2 — Claim Boundary

Challenge whether CC's assessment contains any of these claim escalations:

| Repository state | Does NOT imply |
|---|---|
| `deploy-backend.sh` exists | backend deployment works |
| `README.md` exists | Local Reproduction succeeds |
| `mcp_server.py` exists | MCP server runs in production |
| `scripts/auction_data.py` exists | Auction P0 capability is available |
| `server_scripts/intel_api.py` imports `market_context` | `/api/intel/market-context` works |
| Assessment says "PASS for Release Preparation" | project is ready to release |
| Assessment says "CONDITIONAL" | the condition will be met |

Read:
- `RELEASE_READINESS_ASSESSMENT_v0.1.md` §2–§5
- `REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md` §2.1–§2.5
- `docs/governance/REPOSITORY_BOUNDARY_RULES_v0.1.md` Rule C

For each potential escalation, state:

```
Claim reviewed:
CC's wording:
Adversarial finding: PASS / OVERSTATED / NEEDS EVIDENCE / BLOCKING
Suggested correction:
```

---

## Scope 3 — Human Developer Handoff

Imagine a new human programmer clones the repo at `12649ca` and reads only:

1. `README.md`
2. `.env.example`
3. `deploy.sh`
4. `deploy-backend.sh`
5. `mcp_server.py` top-level imports

Answer from their perspective:

1. Can they determine which commands are supposed to run?
2. Can they determine which environment variables are actually required?
3. Can they determine that `market_context.py` is missing without running code?
4. Can they determine that `deploy.sh` does not deploy the backend?
5. Can they determine that the 4 untracked directories are not part of the runtime?
6. What is the single most misleading statement a new developer would encounter?

---

## Required output

Write `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md` with the following sections:

```markdown
# Release Readiness Adversarial Review v0.1

**observed_at:** <ISO-8601 timestamp>
**Reviewer:** C
**Target:** RELEASE_READINESS_ASSESSMENT_v0.1.md
**Baseline:** 12649ca

## 1. Baseline Integrity Findings

## 2. Claim Boundary Findings

## 3. Human Developer Handoff Findings

## 4. Overall Adversarial Verdict

Use exactly one of:
- BLOCKED — assessment cannot be trusted as-is
- CONDITIONAL — assessment is acceptable only with named corrections
- PASS — assessment withstands adversarial review

## 5. Required Corrections (if any)
```

---

## Constraints

```
✅ Write only docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md
✅ Read-only inspection of all other files
❌ No modification to production code
❌ No modification to README.md
❌ No credential handling
❌ No untracked directory moves
❌ No push / merge / cherry-pick / reset
❌ No implementation work
```

---

## Acceptance criteria

```
observed_at stated:                  yes
Baseline 12649ca verified:           yes
Scope 1 findings present:            yes
Scope 2 findings present:            yes
Scope 3 findings present:            yes
Overall verdict from allowed set:    yes
File modification outside target:    none
```

---

**End of card**
