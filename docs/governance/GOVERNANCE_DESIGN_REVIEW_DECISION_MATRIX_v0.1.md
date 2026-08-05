# Governance Design Review Decision Matrix v0.1

**Status:** DRAFT — CC does not select; human principal decides
**Date:** 2026-08-05
**Coordinator:** CC (read-only; structures decisions, does not answer them)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## Purpose

The Decision Matrix structures the four questions in `GOVERNANCE_DESIGN_REVIEW_BRIEF_v0.1.md` so that the human principal can make each decision explicitly and traceably. CC provides questions, options, trade-offs, and evidence. The human principal provides the decision.

This is a **draft** for review. CC does not endorse any option.

---

## Q1 — Independent Verification Boundary

**Question:** Which scenarios must require independent workspace, independent artifact source, and independent verifier?

| Option | Description | Trade-off | Evidence |
|---|---|---|---|
| **A. All reviews** | Every claim must be independently verifiable in a separate workspace | Removes false negatives; costs maximum time; blocks CC-internal reviews | C's BLOCKED at Phase 0 demonstrated workspace boundary matters; would have been the safe default |
| **B. High-risk claims only** | Reviewer judgment decides "high-risk"; runtime / capability / release claims qualify by default | Cost proportional to risk; depends on threshold clarity | Auction Runtime Observation was high-risk and warranted independent verification |
| **C. Production-related events only** | Limited to incidents, live deploys, and post-deployment review | Lowest cost; misses pre-production design defects | B-01 (Backend Deployment) would only enter scope if bound to live production |

**Human indication suggested:** B (high-risk only) with explicit threshold criteria.

**Decision needed:**

- Which option (A / B / C)?
- If B: what is the threshold for "high-risk"?
- Where is the threshold documented and who maintains it?

---

## Q2 — Governance Granularity

**Question:** Should governance protocol weight be derived from file type or claim impact?

### Option A — File-type-driven

- Mapping: file extension or directory → protocol weight
- Simpler, deterministic
- Risk: misclassifies when docs change imply new capability claims

### Option B — Claim Impact Model

- Four-dimension score per blocker / change:
  - Runtime Impact
  - Capability Impact
  - Evidence Impact
  - User Impact
- Closer to actual risk
- Risk: scoring is itself a governance activity; CC cannot score honestly without framework input

| Dimension | Question |
|---|---|
| Runtime Impact | Will the change affect live system behavior? |
| Capability Impact | Will the change affect what the system can claim? |
| Evidence Impact | Will the change affect the system's ability to prove what it claims? |
| User Impact | Will the change affect user decisions based on system outputs? |

**Human indication suggested:** B (Claim Impact) with explicit scoring rule.

**Decision needed:**

- Which option (A file-type / B claim-impact)?
- If B: how does the four-dimension score map to protocol weight (Full / Lightweight / Automated)?
- Who performs the scoring — the Owner, the Reviewer, or both independently?

---

## Q3 — Minimum Trust Closure

**Question:** What is the minimum set of properties a release must demonstrate to be trustworthy?

### Candidate four-element closure

```
Evidence exists
+
Claim bounded
+
Runtime observable
+
Independent verification when risk requires
```

### Cross-cutting condition: Authority Boundary

The four elements above address evidence properties. They do not, by themselves, prevent an Agent from self-announcing completion. An Authority Boundary is needed:

- Who can declare a release complete?
- Who can authorize production deployment?
- Who can promote a capability claim up the L0–L6 ladder?

Without an explicit Authority Boundary, "evidence exists" can still be defeated by an unauthorized "done" announcement.

**Suggested minimum closure:**

```
Evidence
+
Claim Boundary
+
Runtime Observation
+
Verification
+
Authority Boundary
```

**Decision needed:**

- Is Authority Boundary in scope of this minimum closure?
- Who holds the Authority Boundary for each artifact type?
- How is Authority Boundary recorded — by role, by named individual, by signature, by token?

---

## Q4 — Automation Boundary

**Question:** Which verification steps are mechanical, and which require human judgment?

### Mechanical candidates

| Step | Tool family |
|---|---|
| File existence | filesystem |
| Git object resolution | git |
| SHA-256 / content hash | hash tool |
| Test runner output | test framework |
| API response status | HTTP client |
| `git ls-remote` output | git |
| Fresh clone hash comparison | git + filesystem |
| Schema validation | schema tool |
| Timestamp consistency | clock + diff |

### Human-required candidates

| Step | Reason |
|---|---|
| Risk acceptance | Subjective |
| Capability claim adjudication | Subjective |
| Production release authorization | Authority |
| Verdict in the presence of UNKNOWN evidence | Subjective |
| Conflict resolution when mechanical checks disagree | Subjective |
| Promotion up the L0–L6 ladder | Authority |

**Principle under consideration:** Mechanical verification proves facts; human approval accepts meaning.

**Decision needed:**

- Which steps are mechanical? (confirm / amend the candidates above)
- Which steps are human? (confirm / amend the candidates above)
- What is the escalation rule when a mechanical check fails — automatic HOLD, automatic BLOCK, or human routing?
- What is the rule when a human verdict contradicts a mechanical check?

---

## Cross-questions

These four questions interact:

- The choice in Q2 (granularity) determines which blockers in RRA v0.1 enter Full / Lightweight / Automated protocol.
- The choice in Q1 (verification boundary) determines which blocker closures require an independent verifier.
- The choice in Q3 (minimum closure) determines the release authorization contract.
- The choice in Q4 (automation) determines which steps in Q3 can be mechanical.

If any of the four is left as default-uniform, the other three degrade in clarity. The decisions should be made together or in dependency order.

---

## What CC will and will not do in this matrix

CC will:

- Maintain this Matrix
- Track decisions once recorded
- Cross-reference related documents
- Apply human decisions to the four RRA blockers once they exist

CC will NOT:

- Select any option
- Score any blocker on any dimension
- Modify the Closure Plan or Assessment
- Push, merge, deploy, or move untracked assets

---

## Decision log (to be filled by human principal)

| Question | Decision | Recorded at | Recorded by |
|---|---|---|---|
| Q1 — Independent Verification Boundary | (pending) | | |
| Q2 — Governance Granularity | (pending) | | |
| Q3 — Minimum Trust Closure | (pending) | | |
| Q4 — Automation Boundary | (pending) | | |

---

## Cross-references

- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` (window status)
- `docs/governance/GOVERNANCE_DESIGN_REVIEW_BRIEF_v0.1.md` (questions and evidence)
- `docs/reviews/RRA_v0.1_OWNER_ASSIGNMENT_DECLARATION.md` (PAUSED, awaiting Q2 decision)
- `docs/reviews/RRA_v0.1_CLOSURE_PLAN.md`
- `docs/reviews/RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md`
- `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md`

---

**End of decision matrix**