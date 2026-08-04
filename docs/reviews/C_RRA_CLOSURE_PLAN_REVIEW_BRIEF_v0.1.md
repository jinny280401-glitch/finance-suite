# C Task Card — RRA v0.1 Closure Plan Review v0.1

**Role:** Independent Reviewer
**Mode:** READ-ONLY — output as `docs/reviews/RRA_v0.1_CLOSURE_PLAN_REVIEW_v0.1.md`
**Window:** RRA v0.1 Blocker Closure Planning
**Author of card:** CC

---

## Why this card exists

RRA v0.1 produced a `BLOCKED` verdict. CC has written `RRA_v0.1_CLOSURE_PLAN.md` that turns the four blockers into验收任务 with owner, required evidence, and exit criteria. Before this plan can be treated as the authoritative closure contract, C must independently verify that the plan is complete, the blocker descriptions match what was actually found, and the exit criteria are falsifiable rather than self-verifying.

---

## Required baseline (do not modify)

```
Repository:        ~/finance-suite
Evaluated tree:    12649ca874a987094e7b4665bdc4a8907db519a4
RRA assessment:    docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md
Adversarial review: docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md
Closure plan:      docs/reviews/RRA_v0.1_CLOSURE_PLAN.md
Push:              forbidden
Implementation:    not authorized
```

---

## Scope

Review `RRA_v0.1_CLOSURE_PLAN.md` against the adversarial review's findings and the assessment's exit conditions. Answer:

### Scope 1 — Completeness

Do the four blockers in the closure plan cover every BLOCKING finding from the adversarial review and the assessment?

Verify by comparing:
- `RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md` §1–§5
- `RELEASE_READINESS_ASSESSMENT_v0.1.md` §2.1–§5
- `RRA_v0.1_CLOSURE_PLAN.md` §2

For each blocker, state whether it captures the full finding or omits part of it.

### Scope 2 — Falsifiability

For each blocker's exit criteria ("PASS when…"), determine whether a reasonable reviewer could independently verify the evidence. The exit criterion fails this test if:
- It requires trusting CC's own attestation without independent verification
- It uses passive voice to hide an untestable condition
- It accepts "scheduling a window" as closure

### Scope 3 — Process rules

Verify that:
1. No implementation is authorized by the closure plan.
2. The distinction between "exit criteria" and "owner assignment" is clear.
3. The plan correctly restates that scheduling ≠ evidence.

### Scope 4 — Missing items

Identify any blocker or exit condition that should be present but is absent. Specifically:
- Check whether credential rotation should appear here or remains separate.
- Check whether `deploy.sh` unpinned `main` URLs are covered by any blocker.
- Check whether the README env-var mismatch is covered by the Developer Handoff blocker.

---

## Required output

Write `docs/reviews/RRA_v0.1_CLOSURE_PLAN_REVIEW_v0.1.md`:

```markdown
# RRA v0.1 Closure Plan Review v0.1

**observed_at:** <ISO-8601>
**Reviewer:** C
**Target:** RRA_v0.1_CLOSURE_PLAN.md

## 1. Completeness

## 2. Falsifiability

## 3. Process Rules

## 4. Missing Items

## 5. Overall Verdict

Use exactly one of:
- ACCEPT AS EXIT CONTRACT — the plan is complete and falsifiable as written
- CONDITIONAL — the plan is acceptable with named amendments
- REVISE — the plan requires changes before it can serve as the closure contract

## 6. Required Changes (if any)
```

---

## Constraints

```
✅ Write only docs/reviews/RRA_v0.1_CLOSURE_PLAN_REVIEW_v0.1.md
✅ Read-only inspection of all other files
❌ No modification to any existing file
❌ No implementation
❌ No push / merge / cherry-pick / reset
```

---

**End of card**
