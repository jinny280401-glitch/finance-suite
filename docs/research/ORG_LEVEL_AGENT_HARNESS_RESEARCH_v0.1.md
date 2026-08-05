# Organization-Level Agent Harness Research Task v0.1

**Status:** OPEN — 4-agent parallel research + synthesizer
**Date:** 2026-08-05
**Coordinator:** CC (governance coordinator, not author of research outputs)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED
**Window type:** Design research (no production change, no code change)

---

## 1. Why this research exists

Morning's governance work exposed structural questions that no individual document can answer:

- C Independent Verification revealed that **independence is a property of the reviewer's environment**, not a role label.
- R1 Identity Reconciliation showed that two R1 records (`v0.2_EVIDENCE_R1` static evidence vs `be3c0e91` runtime observation) required an independent judgment to be classified as **Related Artifact** rather than Same / Conflict / Independent.
- Memory boundary work established **Memory ≠ Runtime State** and **Reference ≠ Adopted State**.
- Governance Design Review v0.1 (Q1–Q4) established Independent Verification Boundary, Claim Impact Model, Authority Boundary, Automation Boundary.

These are not bugs. They are symptoms of an unfinished problem: **how should an organization structure its agents when agent count grows beyond two?**

This task card dispatches four parallel research agents to study industry patterns, then synthesizes a Finance-Suite-specific design document. The output informs, but does not modify, the current Governance Design Review v0.1 window.

---

## 2. Scope and constraints

All agents share these constraints:

- Research only — no production change, no code change, no declaration modification, no push
- Forbidden: only write concepts / only list products / only talk about LLM capability
- Required: each finding must answer (1) what morning governance problem it informs, (2) which mechanisms are worth introducing, (3) which are not appropriate for Finance Suite, (4) what is the minimum viable architecture
- Output: Markdown report committed to `docs/research/` (not pushed)

---

## 3. Agent A — Enterprise AI Architect

**Output:** `docs/research/ORG_AGENT_HARNESS_ARCHITECTURE_REPORT.md`

Research questions:

- What is the **Gateway vs Harness** distinction? Why does an organization need Harness, not just a Gateway?
- How do leading agent systems handle **Agent Identity** (independent of human identity)?
- How do they handle **Permission** (what an agent may do vs what a human may do)?
- How is **Shared Context** constructed and maintained across agents and sessions?
- How is **Organizational Memory** distinguished from personal memory and runtime state?
- What is the **Multi-Agent Coordination Model** used in practice (orchestrator / peer / hierarchical / market-based)?

Sections required:

1. Gateway vs Harness
2. Agent Identity
3. Agent Permission
4. Shared Context
5. Organizational Memory
6. Multi-Agent Coordination Model
7. Implications for Finance Suite

---

## 4. Agent B — AI Governance Researcher

**Output:** `docs/research/MULTI_AGENT_GOVERNANCE_PATTERN_REPORT.md`

Research questions:

- How do organizations design **Role Separation** when agents are producers AND reviewers?
- What is the **Approval Chain** pattern when an agent produces evidence and another agent must verify?
- How is the **Evidence Chain** maintained so that "Evidence ≠ Claim Authorization" is enforced by design?
- What are the known **Failure Modes** (e.g., agent self-certifying completion, owner = verifier collapse, claim escalation through language drift)?
- What is the **Recommended Model** for separating Owner / Executor / Verifier / Authority across agents and humans?

Sections required:

1. Role Separation
2. Approval Chain
3. Evidence Chain
4. Failure Modes (with concrete examples from production)
5. Recommended Model

---

## 5. Agent C — AI Infrastructure Architect

**Output:** `docs/research/AGENT_MEMORY_CONTEXT_ARCHITECTURE_REPORT.md`

Research questions:

- How are **Personal Memory**, **Project Memory**, and **Organizational Memory** distinguished in practice?
- How is **Session Continuity** handled when an agent's lifetime is shorter than the project's lifetime?
- How is **Runtime State** kept out of long-term memory stores?
- What is an **Evidence Identity**? How is it attached to provenance rather than to claims?
- How is **Context Reconciliation** performed when two records cover the same root-cause domain with different evidence scopes (the Related Artifact pattern from morning's R1 work)?

Sections required:

1. Personal Memory
2. Project Memory
3. Organizational Memory
4. Runtime State
5. Evidence Identity
6. Context Reconciliation
7. Implications for Finance Suite's memory architecture

---

## 6. Agent D — Open Source Intelligence Researcher

**Output:** `docs/research/OPEN_SOURCE_AGENT_HARNESS_COMPARISON.md`

Focus projects (minimum):

- `garrytan/gbrain` (per user-provided link, MIT)
- Open-source agent frameworks with organizational claims (LangGraph, CrewAI, AutoGen, OpenClaw)
- Any project that claims to address multi-agent organization rather than single-agent orchestration

Comparison dimensions (one row per project):

| Dimension | Question |
|---|---|
| Identity | Does the project define an Agent Identity distinct from User Identity? |
| Memory | How is Organizational Memory represented? |
| Permission | How is agent-level permission enforced? |
| Workflow | How are multi-agent workflows composed? |
| Governance | Does the project include audit / approval / verification primitives? |

Sections required:

1. Project inventory (one paragraph each)
2. Comparison table
3. Patterns that recur across multiple projects
4. Patterns that appear in only one project (assess maturity)
5. Recommendations for Finance Suite

---

## 7. Synthesizer — CC

**Output:** `docs/research/FINANCE_SUITE_ORGANIZATION_AGENT_HARNESS_DESIGN_v0.1.md`

After Agents A–D complete, the synthesizer produces one document that:

- Does not copy any industry pattern wholesale
- Answers the question: if Finance Suite grows to 10 agents / 100 users / institutional clients, what must be in place?
- Cross-references each agent's report with the morning's specific governance findings
- Identifies which industry mechanisms are worth introducing, which are not, and why
- Specifies a minimum viable architecture (MVA) for Finance Suite's organizational layer
- Marks recommendations as DESIGN ONLY (no implementation authorization implied)

---

## 8. State board

```text
Governance Design Review v0.1:    OPEN (research phase only)
Org-level Agent Harness Research: OPEN (4 agents + synthesizer)
RRA v0.1 Blocker Closure:         PAUSED (unaffected)
Owner Assignment:                 WAITING (unaffected)
Implementation:                   NOT AUTHORIZED
Push:                             FORBIDDEN
```

Research does NOT advance the RRA / Owner Assignment / Closure chain. It produces design material for future Governance Review v0.2.

---

## 9. Cross-references

- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` (current window)
- `docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md` (Q1–Q4 decisions)
- `docs/research/R1_IDENTITY_DECISION.md` (morning's Related Artifact reconciliation)
- `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md` (morning's environment boundary finding)

---

**End of task card**