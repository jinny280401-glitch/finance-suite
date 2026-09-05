# C Phase 1 Method Note v0.1

**Status:** METHOD CONTRIBUTION — preserved as separate file
**Date:** 2026-08-05
**Source:** C's Phase 1 method contribution to Organization-level Agent Harness research
**Integration:** Bound into `ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` §1.1
**Production:** UNCHANGED
**Push:** FORBIDDEN

---

## Why this file exists

C contributed Phase 1 methodology before any research agent produces substantive output. The contribution is preserved as a separate file so that:

1. The method is traceable to its source (C, not CC)
2. The contribution is auditable independently of the task card structure
3. Future revisions to Phase 2 / Phase 3 windows can cite this file directly

---

## C's Phase 1 summary (verbatim)

### Research method

- Create `docs/research/agent-harness/` and deliver the five task-card reports plus a source matrix; do not yet publish the final v0.1 organization design.
- For every substantive claim, record source URL, exact artifact examined, what it proves, what remains unproven, Finance Suite applicability, and confidence.
- Evaluate candidates using the required comparison fields: identity, memory, permission, workflow, governance, evidence/auditability, and whether the capability is implemented or merely documented.
- Treat LangGraph, CrewAI, AutoGen, MCP, OpenFGA, Mem0, OpenClaw, gbrain, and Understand Anything as starting candidates — not assumed solutions. Add stronger candidates only when their source artifacts directly address the governance question.

### Required reports (C's naming)

- `ORG_LEVEL_AGENT_HARNESS_RESEARCH.md` — distinguish gateway from harness; assess identity, permissions, shared context, organizational memory, and human collaboration.
- `MULTI_AGENT_GOVERNANCE_PATTERN.md` — map executor, approver, verifier, evidence retention, and failure tracking; explicitly test how each pattern prevents self-attestation.
- `AGENT_ORGANIZATIONAL_MEMORY_ARCHITECTURE.md` — define the evidence needed to classify artifacts as Same, Related, Independent, Conflict, or Reference, rather than relying on text similarity.
- `OPEN_SOURCE_AGENT_HARNESS_COMPARISON.md` — provide the requested project matrix and identify which projects solve durable organization coordination versus only orchestration.
- `FINANCE_SUITE_AGENT_ORGANIZATION_DESIGN.md` — remain a constrained "questions and prerequisites" document in this phase; no speculative implementation design.
- `SOURCE_MATRIX.md` — consolidate citations, capability verdicts (`PROVEN`, `PARTIAL`, `NOT PROVEN`, `UNKNOWN`), and evidence gaps across all reports.

### Finance Suite baseline and decision boundaries

- Analyze the current CC/C/Builder operating model as a single-organization baseline; do not design multi-institution tenancy in this phase.
- Preserve the distinction between static evidence and runtime observation. The research must explain their relationship through explicit provenance/relationship metadata, not collapse them into one record.
- Require role separation: the executor cannot be the sole verifier or approver for the same governed action; a human remains final authority for high-impact actions.
- Do not select a workflow framework, knowledge graph, authorization engine, or database until Phase 2.

### Acceptance checks

- Every report answers the "two sessions both correct" scenario and identifies the missing identity/reconciliation data.
- The comparison contains at least one verified candidate for each of workflow orchestration, authorization, memory, and audit/evidence; unsupported projects are marked accordingly rather than promoted.
- No claim of operational capability is based solely on a README, HTTP response, schema, credential, or local artifact.
- Phase 1 ends with a ranked source shortlist and explicit unanswered decisions, ready for a separate approved v0.1 implementation/design phase.

### Assumptions

- Research sources may extend beyond GitHub only to validate primary technical claims.
- The first delivery is a project-and-evidence shortlist, not the final `FINANCE_SUITE_ORGANIZATION_AGENT_HARNESS_DESIGN_v0.1.md`.
- The current local working tree is preserved; this planning phase makes no repository changes.

---

## Integration into task card

C's constraints are integrated into the master task card at `ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` §1.1 (commit `04c27eb`). The constraints apply to all four research agents and to the Synthesizer.

---

## Cross-references

- `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` §1.1 (integration)
- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` (current window)
- `docs/governance/REPOSITORY_BOUNDARY_RULES_v0.1.md` (Rule B: per-claim provenance)

---

**End of method note**