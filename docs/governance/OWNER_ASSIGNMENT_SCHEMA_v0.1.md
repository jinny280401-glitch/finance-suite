# Owner Assignment Schema v0.1

**Status:** DRAFT — defines field requirements per protocol; does NOT assign identities
**Date:** 2026-08-05
**Source authority:** Decision Matrix `a0d1249`, Classification Decision `45f6306`, B-03 Supplement Decision (this commit)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## 1. Why this exists

Governance Design Review Q2 (Claim Impact Model) and Q3 (Authority Boundary) require that protocol weight determines the responsibility schema. The four blockers have been classified:

| Blocker | Total | Protocol |
|---|---|---|
| B-01 Backend Deployment Chain | 15/16 | Full Closure Protocol |
| B-02 `market_context` module | 14/16 | Full Closure Protocol |
| B-03 Developer Handoff | 10/16 | Automated Closure Protocol |
| B-04 Remote reproducibility | 10/16 | Automated Closure Protocol |

B-01 and B-02 require a heavier responsibility schema than B-03 and B-04. This document defines what each protocol demands from a closure record. The Owner Assignment Declaration will then enumerate concrete identities against these schemas.

---

## 2. Full Closure Protocol — required fields

Required fields on the closure record for B-01 and B-02:

```
blocker_id:           B-0X
owner:                <named human, NOT CC, NOT C>
verifier:             <named human, distinct from owner, NOT CC>
changed_artifact:     <path + commit SHA>
evidence_reference:   <runtime observation / commit / file / test result>
verification_result:  PASS / FAIL
final_verdict:        BLOCKER CLOSED / BLOCKER REMAINS OPEN
observed_at:          <ISO-8601 timestamp>
producer_reviewer_separation: CONFIRMED (verifier ≠ owner)
```

Mandatory constraints:

- Owner ≠ Verifier (Producer ≠ Reviewer; CC and C excluded from owner role)
- Owner and Verifier each must be a named human, not a role placeholder
- Evidence must be reproducible from the listed commit or runtime observation
- Final verdict must match verification_result semantics (PASS → CLOSED; FAIL → REMAINS OPEN)

---

## 3. Automated Closure Protocol — required fields

Required fields on the closure record for B-03 and B-04:

```
blocker_id:           B-0X
executor:             <named human or named automation, NOT CC>
verifier:             <named human, distinct from executor, sign-off only>
changed_artifact:     <path + commit SHA>
automated_evidence:   <script name + commit SHA + output reference>
verification_result:  AUTOMATED PASS / AUTOMATED FAIL
final_verdict:        BLOCKER CLOSED / BLOCKER REMAINS OPEN
observed_at:          <ISO-8601 timestamp>
executor_verifier_separation: CONFIRMED
```

Mandatory constraints:

- Executor ≠ Verifier
- Executor may be a named automation if the executor role produces only mechanical evidence (hash, diff, `git ls-remote`, fresh clone hash compare)
- Verifier is a named human performing sign-off, not re-running the automation
- Final verdict must match verification_result semantics

The "lighter" weight of Automated Closure is in the *evidence type* (mechanical facts, not human reproduction), not in the *responsibility separation*. Owner ≠ Verifier / Executor ≠ Verifier still applies.

---

## 4. Lightweight Closure Protocol — reserved

Per the Decision Matrix mapping rule, scores 11–13 map to Lightweight Closure. **No current blocker is in this range.** The schema is reserved:

```
blocker_id:           B-0X
owner:                <named human, NOT CC>
verifier:             <optional; spot-check by any non-CC human accepted>
changed_artifact:     <path + commit SHA>
evidence_reference:   <diff + referenced docs>
verification_result:  LIGHTWEIGHT PASS / LIGHTWEIGHT FAIL
final_verdict:        BLOCKER CLOSED / BLOCKER REMAINS OPEN
observed_at:          <ISO-8601 timestamp>
```

When a blocker enters this range, the schema activates. For now, it is reserved, not applied.

---

## 5. Cross-cutting constraints (apply to all protocols)

- CC and C cannot serve as Owner, Verifier, or Executor for any blocker
- Owner / Executor cannot also be Verifier
- Implementation remains NOT AUTHORIZED until the corresponding Declaration moves from DRAFT to AUTHORIZED
- Push, merge, deploy, credential handling, untracked asset moves remain forbidden in all protocols
- Each closure record must reference a baseline SHA; closure evidence must be reproducible from that SHA

---

## 6. What this document does NOT do

- It does NOT assign identities to any Owner, Verifier, or Executor
- It does NOT move any Declaration to AUTHORIZED
- It does NOT authorize any implementation
- It does NOT change the protocol mapping rule

The next step (when ready) is to apply this schema to `RRA_v0.1_OWNER_ASSIGNMENT_DECLARATION.md` §3 by filling in concrete identities per the per-protocol field requirements.

---

## 7. Cross-references

- `docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md` (a0d1249)
- `docs/governance/BLOCKER_RISK_CLASSIFICATION_DECISION_v0.1.md` (45f6306)
- `docs/governance/B03_CLASSIFICATION_SUPPLEMENT_DECISION_v0.1.md` (this commit)
- `docs/governance/C_RECORD_INCONSISTENCY_NOTE_v0.1.md`
- `docs/reviews/RRA_v0.1_CLOSURE_PLAN.md` (b5428cd) §3 process rules
- `docs/reviews/RRA_v0.1_OWNER_ASSIGNMENT_DECLARATION.md` (PAUSED)

---

**End of schema**