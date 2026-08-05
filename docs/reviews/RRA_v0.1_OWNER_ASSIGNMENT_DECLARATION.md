# RRA v0.1 Owner Assignment Declaration

**Status:** **DRAFT** — awaiting human confirmation. Not yet AUTHORIZED.
**Date:** 2026-08-05
**Source authorization:** Independent Verification v0.2 (`3668301`) — PASS WITH CONDITIONS
**Production:** UNCHANGED
**Implementation:** NOT AUTHORIZED
**Push:** FORBIDDEN

---

## 1. Purpose

RRA v0.1 Independent Verification (`RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md`) returned PASS WITH CONDITIONS. The two conditions:

1. Every blocker owner must be assigned before an implementation window opens.
2. The independent verifier must be named in the closure record at acceptance time.

This document is the **DRAFT** Owner Assignment Declaration that closes condition #1. It does **not** authorize any code change, push, merge, or deployment. Once the human principal assigns concrete identities, this document moves to **AUTHORIZED** status, and C will review it per `C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_BRIEF_v0.1.md`.

---

## 2. Blockers

The four blockers from `RRA_v0.1_CLOSURE_PLAN.md` (commit `b5428cd`) §2:

- **B-01 Backend Deployment Chain**
- **B-02 market_context module**
- **B-03 Developer Handoff (clone → run)**
- **B-04 Remote reproducibility**

---

## 2.5 Risk classification (NEW — requires human judgment)

**Status:** Awaiting human classification. This section was added after the initial DRAFT to prevent over-applying the full Owner/Verifier Closure Protocol to every blocker regardless of risk weight.

The four blockers are not the same kind of risk. Full Owner + Independent Verifier + Evidence Schema + Final Verdict protocol may not be appropriate for every blocker.

### Proposed classification (CC suggestion, non-binding)

| Blocker | Risk Class | Reason | Suggested closure weight |
|---|---|---|---|
| B-01 Backend Deployment Chain | **Runtime Critical** | Directly affects whether the system is observably running and which revision is serving | Full Owner + Verifier + Evidence + Verdict |
| B-02 market_context module | **Capability Boundary** | Affects whether a documented endpoint is real or absent; affects claim boundary | Full Owner + Verifier + Evidence + Verdict |
| B-03 Developer Handoff | **Documentation / DX** | Affects how a new human can run locally; no production impact at RRA baseline | Owner + Documentation diff + Spot-check by any human (lighter) |
| B-04 Remote reproducibility | **Repository Integrity** | Affects whether `origin/main` ref is honest; mostly mechanical verification | Owner + automated check (`git ls-remote`, fresh clone hash) + Verifier sign-off |

### Protocol levels under consideration

| Level | Owner | Verifier | Evidence Schema | Final Verdict |
|---|---|---|---|---|
| **Full Closure Protocol** | Required, named | Required, named, ≠ Owner | Full §5 schema | PASS / FAIL recorded |
| **Lightweight Closure** | Required, named | Optional (spot-check by any non-CC human) | Diff + referenced docs | Recorded as Lightweight PASS |
| **Automated Closure** | Required, named | Required (verifier role), but evidence is mechanical | Script output + commit SHA | Recorded as Automated PASS |

**Human decision required:**

For each blocker, indicate:

```
B-01: <Full / Lightweight / Automated> + Verifier required: <YES / NO>
B-02: <Full / Lightweight / Automated> + Verifier required: <YES / NO>
B-03: <Full / Lightweight / Automated> + Verifier required: <YES / NO>
B-04: <Full / Lightweight / Automated> + Verifier required: <YES / NO>
```

The classification decision is itself a governance artifact and should be recorded here once made. CC cannot classify on the human's behalf — this is a judgement call about what the system actually needs.

---

## 3. Assignment table (DRAFT — Owner and Verifier fields empty by design)

| Blocker | Owner | Verifier | Owner ≠ Verifier |
|---|---|---|---|
| B-01 Backend Deployment Chain | TBD — human to assign | TBD — human to assign | (pending) |
| B-02 market_context module | TBD — human to assign | TBD — human to assign | (pending) |
| B-03 Developer Handoff | TBD — human to assign | TBD — human to assign | (pending) |
| B-04 Remote reproducibility | TBD — human to assign | TBD — human to assign | (pending) |

**CC and C are explicitly excluded from any Owner role.** CC is the Closure Coordinator; C is the Independent Verifier Pool.

---

## 4. Suggested role types (non-binding, for human reference)

These are candidate role categories the human principal may use. None are pre-assigned.

| Blocker | Suggested Owner type | Suggested Verifier type |
|---|---|---|
| B-01 Backend Deployment Chain | Runtime / Deploy owner (the person responsible for `server_scripts/`, `mcp_server.py`, deployment) | Independent verifier with no deploy commit history |
| B-02 market_context module | Feature owner of `/api/intel/market-context` (the person who can author or remove the module) | Independent verifier with no `market_context` import commit |
| B-03 Developer Handoff | Documentation / Developer Experience owner (the person who can modify README, `.env.example`, run path) | Independent developer NOT CC who performs clone→run reproduction |
| B-04 Remote reproducibility | Repository / Git operations owner (the person with push authority) | Independent verifier who can attest fresh clone against live remote |

---

## 5. Closure record schema (per blocker)

When a blocker is closed, the closure record must contain:

```
blocker_id:         B-0X
owner:              <name assigned by human>
verifier:           <name, distinct from owner>
changed_artifact:   <path + commit SHA>
evidence_reference: <runtime observation / commit / file / test result>
verification_result: PASS / FAIL
final_verdict:      BLOCKER CLOSED / BLOCKER REMAINS OPEN
observed_at:        <ISO-8601 timestamp>
```

---

## 6. Authorization boundary

This Declaration, once AUTHORIZED, authorizes:

- Each assigned Owner to execute remediation work within their blocker scope.
- Each assigned Verifier to perform independent verification and produce a closure record.

This Declaration does **NOT** authorize:

- Any code change outside the four named blockers.
- Push, merge, cherry-pick, or reset to `main`.
- Production deployment.
- Credential rotation or handling.
- Movement of untracked directories.
- Modification to the Closure Plan, Assessment, Adversarial Review, or Independent Verification artifacts.
- Self-attestation: Owner ≠ Verifier is mandatory for every blocker.

---

## 7. Next steps after human confirmation

1. Human assigns Owner and Verifier identities for each of B-01 to B-04.
2. CC updates §3 to AUTHORIZED status with the concrete identities.
3. C reviews the AUTHORIZED declaration and produces `C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_v0.1.md` with verdict PASS / CONDITIONAL / BLOCKED.
4. If PASS, each blocker enters its assigned Owner-led execution window.
5. Each blocker closure produces a closure record per §5 schema, verified by its assigned Verifier.
6. Only when all four blockers close with PASS does RRA v0.1 move from BLOCKED → CLOSED.

---

## 8. Cross-references

- `docs/reviews/RRA_v0.1_CLOSURE_PLAN.md`
- `docs/reviews/RRA_CLOSURE_PLAN_INDEPENDENT_VERIFICATION_v0.2.md`
- `docs/reviews/C_BLOCKER_CLOSURE_AUTHORIZATION_REVIEW_BRIEF_v0.1.md`
- `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md`
- `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md`

---

**End of declaration**