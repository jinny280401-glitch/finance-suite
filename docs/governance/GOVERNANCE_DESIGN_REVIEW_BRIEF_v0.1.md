# Governance Design Review Brief v0.1

**Status:** OPEN — awaiting human architectural decision
**Date:** 2026-08-05
**Coordinator:** CC (read-only; lists questions and evidence, does not select answers)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## 1. Context — three observed incidents that triggered this window

### 1.1 Independent Review revealed environmental boundary

C's BLOCKED on RRA v0.1 Closure Plan Re-review showed that review independence requires **independent workspace, independent artifact source, and independent verifier environment**, not merely a role label. Files committed by CC in the same session, even when reviewed by a prompt role-played as "C", cannot satisfy independence because they share session, worktree, and git object database with the producer.

Evidence: `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md` and `docs/reviews/RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md` (Phase 0 PASS).

### 1.2 RRA Blocker Closure revealed uniform protocol over-spend

The Owner Assignment Declaration assumed a uniform `Owner + Verifier + Evidence Schema + Final Verdict` closure for every blocker. B-01 (Runtime Deployment) and B-03 (README drift) do not carry the same risk weight. Treating them identically risks governance theater without proportional system benefit.

Evidence: `docs/reviews/RRA_v0.1_OWNER_ASSIGNMENT_DECLARATION.md` §2.5 (risk classification suggested, classification deferred).

### 1.3 Runtime observation revealed claim-boundary shortcuts

The Auction Runtime Observation incident established that when runtime source identity cannot be confirmed, the only defensible verdict is `UNKNOWN`. Existing capability claim rules permit weaker shortcuts that should be closed off by design rather than by reviewer discipline.

Evidence: governance memory references the Auction Runtime Observation case.

---

## 2. Decision Question 1 — Independent Verification Boundary

**Question:** Which scenarios must require independent workspace, independent artifact source, and independent verifier?

### Candidates

| Option | Scope | Cost | Risk of false-positive |
|---|---|---|---|
| **A. All reviews** | Maximum certainty; every claim requires independent access | Highest; blocks CC-internal reviews | Slows down low-stakes iteration |
| **B. High-risk claims only** | Reviewer judgment decides "high-risk"; runtime / capability claims qualify by default | Medium | Risk of misclassification |
| **C. Production-related events only** | Limited to incidents and live deploys | Lowest | Misses design defects in development |

### Trade-offs

- A: removes false negatives but creates governance overhead on every cycle.
- B: relies on the reviewer applying the threshold correctly; needs explicit criteria for "high-risk".
- C: lowest cost but excludes pre-production risk; B-01 (Backend Deployment) would only enter this scope if bound to live production.

### Evidence from existing incidents

- C's BLOCKED at Phase 0 was filed even though the review inputs existed in another workspace — confirming the workspace boundary matters.
- Auction Runtime Observation was a production-related event; under (C) it would be in scope, under (A) and (B) it would also be in scope.

**CC does not select.**

---

## 3. Decision Question 2 — Governance Granularity

**Question:** Should governance protocol weight be derived from file type, claim impact, or some other axis?

### Current proposal (paused in §2.5 of Owner Assignment Declaration)

File-type-driven:

| Blocker | File type | Suggested weight |
|---|---|---|
| B-01 | Runtime / Deploy | Full |
| B-02 | Capability code | Full |
| B-03 | README / docs | Lightweight |
| B-04 | Git / remote | Automated |

### Alternative proposal — Claim Impact Model

Score each blocker on four dimensions:

| Dimension | Question |
|---|---|
| Runtime Impact | Will the fix affect live system behavior? |
| Capability Impact | Will the fix affect what the system can claim? |
| Evidence Impact | Will the fix affect the system's ability to prove what it claims? |
| User Impact | Will the fix affect user decisions based on system outputs? |

A high score on any dimension should drive the protocol weight. The mapping rule from score to protocol is itself an open question.

### Trade-offs

- File-type-driven: simple, deterministic, but can misclassify when README change implies a new capability claim.
- Claim-impact-driven: closer to the actual risk, but requires per-blocker scoring that CC cannot perform honestly without framework input.

### Evidence from existing incidents

- A README change that introduces a new capability claim ("supports X") would be classified Lightweight under file-type-driven but Full under claim-impact-driven.
- B-02 (market_context) is a capability boundary issue; under both models it qualifies for Full.

**CC does not select.**

---

## 4. Decision Question 3 — Minimum Trust Closure

**Question:** What is the minimum set of properties a release must demonstrate to be considered trustworthy?

### Candidate minimum

```
Evidence exists
+
Claim bounded
+
Runtime observable
+
Independent verification when risk requires
```

### Open questions

- Does "Runtime observable" require production live verification, or is post-deployment static observation sufficient?
- Does "Claim bounded" require a claim ladder level (L0–L6) annotation on every public-facing output?
- Is "Independent verification when risk requires" a property of the claim, of the artifact, or of the risk class?

### Evidence from existing incidents

- Capability Claim Ladder L0–L6 exists in `Vera_Capability_Claim_Governance_Framework_v1.md`; it has not been formally integrated into the closure protocol.
- Evidence Governance v1.0 has eight governing principles including "Declared Capability ≠ Effective Capability"; integration with closure schema is not formalized.

**CC does not select.**

---

## 5. Decision Question 4 — Automation Boundary

**Question:** Which verification steps can be mechanical, and which must be human?

### Mechanical candidates

- File existence
- Git object resolution
- SHA-256 / content hash
- Test runner output
- API response status codes
- `git ls-remote` output
- Fresh clone hash comparison

### Human-required candidates

- Capability claim adjudication
- Production risk acceptance
- Release authorization signature
- Verdict in the presence of UNKNOWN evidence
- Conflict resolution when mechanical checks disagree

### Trade-offs

- Maximizing automation speeds up low-stakes verification but can hide subjective risk.
- Maximizing human review slows everything and creates reviewer bottleneck.
- The boundary is not just about which side is faster; it is about which side can be trusted at which maturity level.

### Evidence from existing incidents

- B-04 (Remote reproducibility) is largely mechanical: `git ls-remote`, fresh clone, hash compare.
- B-03 (Developer Handoff) is largely human: a developer reading README and trying to run.
- B-01 (Backend Deployment) is mixed: deployment can be mechanical; runtime start/respond may need human spot-check.

**CC does not select.**

---

## 6. What CC will and will not do in this window

CC will:

- Maintain this Brief
- Coordinate with C and the human principal
- Track answers once provided
- Cross-reference governance documents

CC will NOT:

- Select between options
- Score any blocker
- Modify any existing governance document
- Push, merge, deploy, or move untracked assets

---

## 7. Cross-references

- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` (window status)
- `docs/reviews/RRA_v0.1_OWNER_ASSIGNMENT_DECLARATION.md` (PAUSED, classification deferred)
- `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md`
- `docs/reviews/RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md`
- `docs/governance/EVIDENCE_GOVERNANCE_v1.0.md`
- `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`
- `docs/reviews/UNTRACKED_ARTIFACT_ATTRIBUTION_REPORT_v0.1.md`

---

**End of brief**