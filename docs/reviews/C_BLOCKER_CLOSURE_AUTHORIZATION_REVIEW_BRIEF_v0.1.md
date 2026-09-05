# C Task Card — RRA v0.1 Blocker Closure Authorization Review v0.1

**Role:** Independent Verifier Pool (not Owner, not Builder)
**Mode:** Review-only — output as `docs/reviews/C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_v0.1.md`
**Window:** RRA v0.1 Blocker Closure Authorization
**Author of card:** CC (Governance Owner + Closure Coordinator)
**Status:** Standby — human Owner Assignment Declaration expected before any review

---

## Why this card exists

RRA v0.1 Independent Verification returned **PASS WITH CONDITIONS** (`3668301`). The two conditions are:

1. Every blocker owner must be assigned before an implementation window opens.
2. The independent verifier must be named in the closure record at acceptance time.

This card asks C to stand by in their verifier role and to validate the upcoming Owner Assignment Declaration. **It does not authorize C to act as a blocker owner, to perform fixes, or to execute any system.**

---

## Required baseline (do not modify)

```
Repository:        /Users/Zhuanz/finance-suite
Evaluated tree:    12649ca
Closure Plan:      docs/reviews/RRA_v0.1_CLOSURE_PLAN.md (b5428cd)
Independent Verification: docs/reviews/RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md (3668301)
Implementation:    not authorized
Push:              forbidden
```

---

## C's role boundary

```
CC:    Governance Owner + Closure Coordinator (this session)
C:     Independent Verifier Pool (this task card)
Human: Assigns Owners and Verifiers via Owner Assignment Declaration
```

C must **not**:

- Act as a blocker owner
- Execute any system, deploy, or modify production code
- Move untracked directories
- Handle credentials
- Push, merge, cherry-pick, or reset

C **must**:

- Validate the Owner Assignment Declaration when provided
- Reject any assignment where Owner = Verifier
- Reject any assignment where identities are missing or unclear
- Confirm closure records include: changed artifact, evidence reference, verification result, final verdict
- Continue reviewing from `/Users/Zhuanz/finance-suite` (Setup v0.1 Option A) or a fresh clone

---

## Scope

Once the human provides an Owner Assignment Declaration naming four blocker owners and four verifiers, C must:

### Scope 1 — Assignment completeness

Verify for each of the four blockers:

- **B-01 Backend Deployment Chain** — Owner named? Verifier named? Owner ≠ Verifier?
- **B-02 market_context module** — same
- **B-03 Developer Handoff** — same
- **B-04 Remote reproducibility** — same

### Scope 2 — Role separation

- Owner must not be CC (Producer ≠ Reviewer; CC is Closure Coordinator).
- Owner must not be C (Reviewer ≠ Builder; C is Independent Verifier).
- Verifier must be the named independent reviewer for that blocker, not the Owner.

### Scope 3 — Closure record schema

For each blocker, confirm the closure record template includes:

```
changed_artifact:     <path + SHA>
evidence_reference:   <commit / file / runtime observation>
verification_result:  PASS / FAIL
final_verdict:        BLOCKER CLOSED / BLOCKER REMAINS OPEN
owner:                <name>
verifier:             <name, distinct from owner>
observed_at:          <ISO-8601>
```

### Scope 4 — Authorization boundary

Verify that the Owner Assignment Declaration:

- Does not authorize any code change beyond the four named blockers.
- Does not authorize push, merge, or production deployment.
- Does not authorize credential rotation or untracked asset moves.
- Does not collapse any "scheduled window" into evidence.

---

## Required output

Write `docs/reviews/C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_v0.1.md`:

```markdown
# RRA v0.1 Blocker Closure Authorization Review v0.1

**observed_at:** <ISO-8601>
**Reviewer:** C
**Target:** <Owner Assignment Declaration path>

## Review Environment Verification
Workspace:           /Users/Zhuanz/finance-suite
Baseline resolvable: <YES / NO>
Assignment file readable: <YES / NO>
SHA verification:     <list>

## 1. Assignment Completeness

## 2. Role Separation

## 3. Closure Record Schema

## 4. Authorization Boundary

## 5. Overall Verdict

Use exactly one of:
- PASS — assignments are complete and role-separated
- CONDITIONAL — assignments acceptable with named corrections
- BLOCKED — assignments incomplete or violate Producer ≠ Reviewer

## 6. Required Corrections (if any)
```

---

## Constraints

```
✅ Write only docs/reviews/C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_v0.1.md
✅ Read-only inspection
❌ No Owner role for C
❌ No Builder / fix activity
❌ No push / merge / deploy / credential handling
❌ No modification to Closure Plan, Assessment, Adversarial Review
```

---

## Acceptance criteria

```
observed_at stated:               yes
Review Environment Verification:  complete
4/4 blockers reviewed:            yes
Role Separation verified:         yes
Closure Record Schema verified:    yes
Overall verdict from allowed set: yes
File modification outside target: none
```

---

**End of card**