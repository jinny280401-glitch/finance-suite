# C Task Card — B-03 Risk Classification Supplement Review v0.1

**Role:** Independent Reviewer (B-03 only — risk classification supplement)
**Mode:** Independent review — output as `docs/reviews/C_B03_RISK_CLASSIFICATION_SUPPLEMENT_REVIEW_v0.1.md`
**Window:** Governance Design Review v0.1 (B-03 gap closure)
**Author of card:** CC (Closure Coordinator)
**Status:** OPEN — first application of Q1 to B-03 risk classification itself

---

## Why this card exists

C's earlier review (`docs/reviews/C_BLOCKER_RISK_CLASSIFICATION_REVIEW_v0.1.md`, commit `517c79a`) classified B-01 (15/16), B-02 (14/16), and B-04 (10/16). It did **not** contain a B-03 scoring row.

The human principal explicitly chose to:

- Treat the missing B-03 row as a gap, not as an inferred score
- Hold B-03 at **PENDING CLASSIFICATION** in `BLOCKER_RISK_CLASSIFICATION_DECISION_v0.1.md` (commit `45f6306`)
- Avoid any default to Lightweight Closure Protocol (which the mapping rule does not auto-assign anyway)

This task card asks C to score B-03 in a single-blocker supplement. It is the first concrete test of Q1 (Independent Verification Boundary): the risk classification of a blocker is itself a high-risk Claim, so it must be independently assessed.

---

## Required baseline (do not modify)

```
Repository:        /Users/Zhuanz/finance-suite
Freeze point:      12649ca
Closure Plan:      docs/reviews/RRA_v0.1_CLOSURE_PLAN.md (b5428cd) §2 B-03 row
Prior C review:    docs/reviews/C_BLOCKER_RISK_CLASSIFICATION_REVIEW_v0.1.md (517c79a)
Decision Matrix:   docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md (a0d1249)
Classification Decision: docs/governance/BLOCKER_RISK_CLASSIFICATION_DECISION_v0.1.md (45f6306)
Push:              forbidden
Implementation:    not authorized
```

---

## C's role boundary

```
CC:    Closure Coordinator + state recorder
C:     Independent reviewer for B-03 only (this task card)
Human: Authority for approval and protocol mapping
```

C must **not**:

- Re-score B-01, B-02, or B-04 (already accepted; out of scope)
- Define the score-to-protocol mapping rule (Full / Lightweight / Automated thresholds)
- Select Owner or Verifier identities
- Propose fixes or remediation strategies
- Declare any blocker closed or open
- Authorize execution
- Push, merge, deploy, handle credentials, move untracked assets

C **must**:

- Either score B-03 on the four Claim Impact dimensions **OR** explicitly state why B-03 cannot be classified in this review
- For any score given: provide rationale, evidence references, and confidence
- For any skip declared: explain why, identify what evidence is missing, and state whether another window would be needed
- Operate from the established review environment (Setup v0.1 Option A or a fresh clone)

---

## Scoring dimensions (per Q2 decision, unchanged)

| Dimension | Question |
|---|---|
| Runtime Impact | Will remediation affect live system behavior? |
| Capability Impact | Will remediation affect what the system can publicly claim? |
| Evidence Impact | Will remediation affect the system's ability to prove what it claims? |
| User Impact | Will remediation affect user decisions based on system outputs? |

Score scale (unchanged from C's prior review, for consistency):

- 0 = no impact
- 1 = minimal impact (cosmetic / structural change only)
- 2 = moderate impact (affects internal posture but no public surface)
- 3 = high impact (affects public claim or observable behavior)
- 4 = critical impact (production-visible behavior or trust-critical claim)

---

## Blocker to score

**B-03 Developer Handoff (clone → run)** — see `RRA_v0.1_CLOSURE_PLAN.md` §2 for the full description, evidence list, and exit criteria. C's own adversarial review identified:

- HD-01 — commands named but operational meaning not determinable
- HD-02 — required environment variables not determinable from handoff docs
- HD-03 — missing `market_context.py` not discoverable from handoff docs
- HD-04 — `deploy.sh` visibly deploys static content; backend provenance indeterminate
- HD-05 — four untracked directories absent after clone, but clone user cannot know historical boundary status

The Closure Plan's B-03 row also requires:

1. README/env-var consistency
2. supported run path documented
3. no misleading interactive workflow documented as a service-start interface
4. explicit boundary document for intentionally absent directories
5. independent human clone→run reproduction recorded with human, timestamp, and SHA

---

## Required output

Write `docs/reviews/C_B03_RISK_CLASSIFICATION_SUPPLEMENT_REVIEW_v0.1.md`:

```markdown
# B-03 Risk Classification Supplement Review v0.1

**observed_at:** <ISO-8601>
**Reviewer:** C
**Baseline:** 12649ca
**Decision Matrix applied:** a0d1249
**Prior C review reference:** 517c79a
**Scope:** B-03 only (B-01, B-02, B-04 out of scope)
**Mode:** Independent risk classification supplement

## Review Environment Verification
Workspace:           /Users/Zhuanz/finance-suite
Baseline resolvable: <YES / NO>
Closure Plan §2 B-03 row readable: <YES / NO>
Prior C review (517c79a) accessible: <YES / NO>
SHA verification:    <list>

## Path A — Classification Decision (preferred if C can score)

### B-03 — Developer Handoff (clone → run)

| Dimension | Score | Rationale | Evidence |
|---|---:|---|---|
| Runtime Impact | ?/4 | <...> | <file/line> |
| Capability Impact | ?/4 | <...> | <...> |
| Evidence Impact | ?/4 | <...> | <...> |
| User Impact | ?/4 | <...> | <...> |
| **Total** | ?/16 | — | — |

**Confidence:** HIGH / MEDIUM / LOW
**Notes:** <scale amendments, weak evidence, or comparisons to B-01/B-02/B-04 if relevant>

## Path B — Skip Decision (only if Path A is not feasible)

If C concludes B-03 cannot be classified in this review, output:

### Skip justification
<Why this blocker cannot be classified without additional evidence>

### Missing evidence
<What specifically is missing, with file/observation paths if known>

### Recommended next step
<Whether another window is needed, what that window would do>

## What this review does NOT decide

- Protocol mapping (Full / Lightweight / Automated) — Authority decision
- Owner / Verifier assignment
- Closure authorization
- Re-scoring B-01, B-02, or B-04
- Remediation strategies
```

C must choose **Path A or Path B** and complete the corresponding section. Empty or partial output is not accepted.

---

## Constraints

```
✅ Write only docs/reviews/C_B03_RISK_CLASSIFICATION_SUPPLEMENT_REVIEW_v0.1.md
✅ Read-only inspection of all other files
❌ No modification to Closure Plan, Assessment, Adversarial Review, Decision Matrix, Classification Decision
❌ No re-scoring of B-01, B-02, B-04
❌ No Owner / Verifier / Builder activity
❌ No protocol mapping
❌ No push / merge / cherry-pick / reset
❌ No credential handling
❌ No untracked asset moves
```

---

## Acceptance criteria

```
observed_at stated:                  yes
Review Environment Verification:     complete (4 fields)
Path chosen (A or B):                yes
If Path A:
  - All 4 dimensions scored:         yes
  - Each score has rationale:        yes
  - Each score has evidence:         yes
  - Confidence declared:             yes
  - Total computed:                  yes
If Path B:
  - Skip justification provided:     yes
  - Missing evidence listed:         yes
  - Next step recommendation:        yes
File modification outside target:    none
```

---

**End of card**