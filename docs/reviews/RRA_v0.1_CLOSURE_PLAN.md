# RRA v0.1 Closure Plan

**Status:** OPEN — blocker closure planning only  
**Date:** 2026-08-04  
**RRA v0.1 final verdict:** BLOCKED  
**Production:** UNCHANGED  
**Implementation:** NOT AUTHORIZED  
**Push:** FORBIDDEN

---

## 1. Why BLOCKED is not a failure

RRA v0.1 produced two complete artifacts:

- `docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md` — CC's readiness assessment
- `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md` — C's independent adversarial review

C returned **BLOCKED** because the release-readiness exit gates are not satisfied. The process worked as designed: the adversarial review caught claim-strength issues that the initial assessment understated.

**BLOCKED means:** the baseline is a valid input tree, but it cannot support a release or Main Release Preparation until the blockers below are closed with evidence.

---

## 2. Blocker closure table

| Blocker | Owner | Required Evidence | Exit Criteria |
|---|---|---|---|
| **Backend Deployment Chain** | TBD | 1. A committed, deterministic deployment contract that identifies how `server_scripts/`, `mcp_server.py`, and backend dependencies reach production.<br>2. `deploy.sh` fetches from a specific SHA, not unpinned `main`. Every source URL in the deployment script must be bound to a committed revision.<br>3. `deploy-backend.sh` is either replaced by a deterministic start contract or removed from the README run path. Its current form is an interactive update workflow, not a service-start interface.<br>4. Evidence that the deployed backend revision matches a specific SHA.<br>5. A runtime check that the backend process starts and responds. | `PASS` when a human can reproduce deployment from the committed contract and runtime check succeeds. |
| **market_context module** | TBD | 1. Either a committed `market_context.py` module or removal of the `/api/intel/market-context` claim from README/API docs.<br>2. If committed, runtime evidence that the endpoint returns the expected payload. | `PASS` when README and committed tree agree and endpoint behavior is independently verified. |
| **Developer Handoff (clone → run)** | TBD | 1. A new human developer can clone at `12649ca` (or a later approved baseline) and follow README verbatim through install, configure, and run without inventing steps.<br>2. `.env.example` matches README required variables.<br>3. A supported run path exists and is documented.<br>4. No README command documents an interactive or non-deterministic workflow as a service-start interface.<br>5. The README or a committed boundary document enables a clone user to identify which directories are intentionally absent from the runtime tree and why. | `PASS` when at least one independent human (NOT CC) completes clone→run reproduction and the result is recorded in a review artifact naming the human, the timestamp, and the SHA tested. |
| **Remote reproducibility** | TBD | 1. A fresh clone from remote `origin/main` reproduces the canonical baseline.<br>2. The local `origin/main` ref is confirmed against the live remote, or the claim is permanently narrowed to local-ref-only. | `PASS` when either (a) a fresh clone from the live remote is independently attested, or (b) the claim is permanently narrowed to local-ref-only AND the narrowing is reviewed and accepted by C or the human principal. |

---

## 3. Process rules

1. **No implementation is authorized by this plan.** This document only turns blockers into验收任务.
2. **Each blocker must close with evidence, not with scheduling.** "Window scheduled" or "fix planned" does not satisfy exit criteria.
3. **Owner assignment is required before any implementation window opens.** TBD owners must be named before work begins.
4. **No release artifact — including a tagged release candidate — may be produced until all blockers are `PASS`.**
5. **RRA v0.1 remains BLOCKED until this closure plan is fully executed and independently reviewed.**
6. **Exit Criteria Validation — Producer ≠ Reviewer.** Self-attestation is not accepted as closure evidence. For each blocker, the implementation owner and the independent verifier must be distinct identities. The verifier must be named in the closure record.

---

## 4. What is not in scope

- Merge to `main`
- Push to GitHub
- README edits (covered under Developer Handoff blocker)
- Credential rotation (covered under separate Credential History Purge window; remains owner-authorized)
- Untracked asset moves
- Production deployment

---

## 5. Next decision point

After owners are assigned and evidence is produced, a new window authorization is required to enter:

> **RRA v0.1 Blocker Closure Verification**

Only then may implementation begin, and only for the explicitly authorized blockers.

---

## 6. Cross-references

- `docs/reviews/RELEASE_READINESS_ASSESSMENT_v0.1.md`
- `docs/reviews/RELEASE_READINESS_ADVERSARIAL_REVIEW_v0.1.md`
- `docs/reviews/RRA_v0.1_CLOSURE_PLAN_REVIEW_v0.1.md`
- `docs/reviews/BASELINE_FREEZE_DECLARATION_v0.1.md`
- `docs/reviews/REPOSITORY_HANDOFF_FINAL_REPORT_v0.1.md`

---

## 7. Revision log

| Version | Date | Author | Change |
|---|---|---|---|
| v0.1 | 2026-08-04 | CC | Initial closure plan from RRA v0.1 BLOCKED verdict |
| v0.2 | 2026-08-04 | CC | Apply C's 5 required corrections (see `RRA_v0.1_CLOSURE_PLAN_REVIEW_v0.1.md` §6) |

---

**End of plan**
