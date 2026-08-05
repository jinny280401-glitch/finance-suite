# Organization-Level Agent Harness Research Task v0.1

**Status:** OPEN — REFERENCE RESEARCH
**Status semantics:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Date:** 2026-08-05
**Coordinator:** CC (governance coordinator, not author of research outputs)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED
**Window type:** External method research input (no production change, no code change, no declaration modification)

---

## 1. Why this research exists

Morning's governance work exposed structural questions that no individual document can answer:

- C Independent Verification revealed that **independence is a property of the reviewer's environment**, not a role label.
- R1 Identity Reconciliation showed that two R1 records (`v0.2_EVIDENCE_R1` static evidence vs `be3c0e91` runtime observation) required an independent judgment to be classified as **Related Artifact** rather than Same / Conflict / Independent.
- Memory boundary work established **Memory ≠ Runtime State** and **Reference ≠ Adopted State**.
- Governance Design Review v0.1 (Q1–Q4) established Independent Verification Boundary, Claim Impact Model, Authority Boundary, Automation Boundary.

These are not bugs. They are symptoms of an unfinished problem: **how should an organization structure its agents when agent count grows beyond two?**

This task card dispatches four parallel research agents to study industry patterns, then synthesizes a design-input document. The output is research material, not architecture decision. It does not modify Governance Design Review v0.1; it informs future windows.

### 1.1 C's Phase 1 method contribution

C issued a Phase 1 method contribution (`docs/research/C_PHASE1_METHOD_NOTE_v0.1.md`, separate file). Key constraints added by C:

- **Source-audited project shortlist** before any Finance Suite architecture proposal. GitHub repositories as starting point; primary specifications, official documentation, and relevant standards supplement when a repo alone cannot prove identity/authorization/audit behavior.
- **Per-claim audit**: every substantive claim records source URL, exact artifact examined, what it proves, what remains unproven, Finance Suite applicability, and confidence level.
- **Required comparison fields**: identity, memory, permission, workflow, governance, evidence/auditability, plus whether the capability is implemented or merely documented.
- **Starting candidates** (not assumed solutions): LangGraph, CrewAI, AutoGen, MCP, OpenFGA, Mem0, OpenClaw, gbrain, Understand Anything.
- **Required reports (renamed by C)**:
  - `ORG_LEVEL_AGENT_HARNESS_RESEARCH.md`
  - `MULTI_AGENT_GOVERNANCE_PATTERN.md`
  - `AGENT_ORGANIZATIONAL_MEMORY_ARCHITECTURE.md`
  - `OPEN_SOURCE_AGENT_HARNESS_COMPARISON.md`
  - `FINANCE_SUITE_AGENT_ORGANIZATION_DESIGN.md` (constrained to questions + prerequisites in this phase)
  - `SOURCE_MATRIX.md` (consolidates citations, capability verdicts, evidence gaps)
- **Finance Suite baseline and decision boundaries**:
  - Analyze current CC/C/Builder model as **single-organization baseline**; do not design multi-institution tenancy in this phase.
  - Preserve distinction between **static evidence and runtime observation** through explicit provenance/relationship metadata, not by collapsing them into one record.
  - **Role separation**: executor ≠ sole verifier or approver for the same governed action; human remains final authority for high-impact actions.
  - **No selection** of workflow framework / knowledge graph / authorization engine / database until Phase 2.
- **Acceptance checks**:
  - Every report answers the "two sessions both correct" scenario and identifies missing identity/reconciliation data.
  - Comparison contains at least one verified candidate for each of workflow orchestration, authorization, memory, audit/evidence; unsupported projects marked accordingly.
  - No claim of operational capability based solely on README / HTTP response / schema / credential / local artifact.
  - Phase 1 ends with ranked source shortlist + explicit unanswered decisions, ready for separate approved v0.1 implementation/design phase.
- **Assumptions**:
  - Research sources may extend beyond GitHub only to validate primary technical claims.
  - First delivery is project-and-evidence shortlist, NOT the final `FINANCE_SUITE_ORGANIZATION_AGENT_HARNESS_DESIGN_v0.1.md`.
  - Current local working tree preserved; this planning phase makes no repository changes.

These constraints apply to all four Agent outputs and to the Synthesizer. C's contribution is preserved as a separate file `C_PHASE1_METHOD_NOTE_v0.1.md`.

---

## 2. Scope and constraints

All agents share these constraints:

- Research only — no production change, no code change, no declaration modification, no push
- Forbidden: only write concepts / only list products / only talk about LLM capability
- Required: each finding must answer (1) what morning governance problem it informs, (2) which mechanisms are worth introducing, (3) which are not appropriate for Finance Suite, (4) what is the minimum viable architecture
- Output: committed to `docs/research/` with **REFERENCE ONLY** status (NOT adopted, NOT architecture decision)
- Final output does not authorize any implementation, adoption, or roadmap commitment

---

## 3. Per-finding output format

Every Agent output must follow this format for each finding:

```
Research Finding:    <one-line statement>
Source:              <Anthropic / OpenAI / GitHub / Academic / Industry>
Observation:         <what was observed in the source>
Pattern:             <what mechanism is distilled>
Applicability:       <whether it has reference value for Finance Suite>
Non-Claim:           <what this finding does NOT imply>
```

The "Non-Claim" line is mandatory. It states explicitly that the finding is observation, not adoption.

---

## 4. Agent A — Industry Architecture

**Output:** `docs/research/ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md`

**Role:** Industry Architecture Researcher

**Topic:** 组织级 Agent Harness 行业范式

Focus:

- Anthropic Org-level Harness concept (Claude Code Cloud Tag, Lance Martin definitions)
- Slack / Workspace collaboration model for Agents
- Agent Identity approaches at the enterprise level
- Permission Model in production agent systems
- Shared Context layer architectures
- Multi-Agent Coordination Model (orchestrator / peer / hierarchical / market-based)

Output target: "未来企业 Agent 基础设施长什么样"

Sections required:

1. Gateway vs Harness (current industry consensus)
2. Agent Identity patterns (3–5 concrete examples)
3. Permission models
4. Shared Context architectures
5. Multi-Agent Coordination Model
6. Implications for Finance Suite (per-finding format)
7. Non-adoption statement

---

## 5. Agent B — Open Source Systems

**Output:** `docs/research/ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md`

**Role:** Open Source Intelligence Researcher

**Topic:** 开源 Agent 协作框架研究

Focus projects (minimum coverage):

- `garrytan/gbrain` (per user-provided link, MIT)
- `Lum1104/Understand-Anything` (already reviewed this session)
- OpenClaw
- LangGraph
- CrewAI
- AutoGen
- Any project that addresses multi-agent organization rather than single-agent orchestration

Comparison dimensions (one row per project):

| Dimension | Question |
|---|---|
| Identity | Does the project define an Agent Identity distinct from User Identity? |
| Memory | How is Organizational Memory represented? |
| Permission | How is agent-level permission enforced? |
| Workflow | How are multi-agent workflows composed? |
| Governance | Does the project include audit / approval / verification primitives? |

Output target: "多 Agent 协作环境如何实现"

Sections required:

1. Project inventory (one paragraph each)
2. Comparison table
3. Patterns that recur across multiple projects
4. Patterns that appear in only one project (assess maturity)
5. Implications for Finance Suite (per-finding format)
6. Non-adoption statement

---

## 6. Agent C — Governance & Safety

**Output:** `docs/research/ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md`

**Role:** AI Governance Researcher

**Topic:** Agent Governance 方法

Focus:

- Identity boundary enforcement
- Approval workflow design
- Audit trail primitives
- Human-in-the-loop patterns
- Policy enforcement
- Owner / Executor / Verifier / Authority separation

Output target: "如何避免 Agent 自说自话"

Sections required:

1. Role Separation (Producer ≠ Reviewer; Owner ≠ Verifier)
2. Approval Chain patterns
3. Evidence Chain patterns (Evidence ≠ Claim Authorization)
4. Failure Modes (with concrete examples from production systems)
5. Audit Trail primitives
6. Recommended Model
7. Implications for Finance Suite (per-finding format)
8. Non-adoption statement

---

## 7. Agent D — Software Organization Practice

**Output:** `docs/research/ORG_LEVEL_HARNESS_SOFTWARE_PRACTICE_REPORT_v0.1.md`

**Role:** Software Organization Practice Researcher

**Topic:** 大型软件团队如何管理 AI Agent

Focus:

- GitHub Copilot Workspace
- Devin-class agent workflows
- Code ownership in agent era
- Review system with AI participants
- Organizational memory in software teams
- Onboarding new AI agents into an existing human team

Output target: "Agent 进入真实组织后的运行机制"

Sections required:

1. Code Ownership in AI-assisted development
2. Review System with AI participants
3. Onboarding patterns for new AI agents
4. Organizational Memory in software teams
5. Failure Modes
6. Implications for Finance Suite (per-finding format)
7. Non-adoption statement

---

## 8. Synthesizer — CC

**Output:** `docs/research/ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md`

After Agents A–D complete, the synthesizer produces one document that:

**Status:** DECISION: NOT DECIDED

**Contains:**

- Reusable patterns observed across the four agent reports
- Candidate architecture principles
- Future design inputs for governance windows

**Does NOT contain:**

- Implementation plan
- Adoption decision
- Roadmap commitment
- Production change authorization

The synthesis answers one question:

> Are the morning's governance frictions **process design problems** that better procedures can solve, or are they **evidence that future Agent systems require an organizational-level Harness as native infrastructure**?

This is a design-input question, not a decision question.

---

## 9. Cross-cutting research rules

```
✅ Each finding uses the per-finding format (§3)
✅ Sources are concrete: paper / post / repo / spec / doc
✅ No claim of capability or maturity beyond what source supports
✅ Each finding has Non-Claim line

❌ No adoption recommendation
❌ No implementation timeline
❌ No "we should use X" framing
❌ No modification to existing governance / review / declaration docs
```

---

## 10. State board

```text
Governance Design Review v0.1:    OPEN (research does not modify)
Org-level Agent Harness Research: OPEN (4 agents + synthesizer)
  - Status semantics:              REFERENCE ONLY
RRA v0.1 Blocker Closure:         PAUSED (unaffected)
Owner Assignment:                 WAITING (unaffected)
Implementation:                   NOT AUTHORIZED
Push:                             FORBIDDEN
```

Research does NOT advance the RRA / Owner Assignment / Closure chain.

---

## 11. Cross-references

- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` (current window)
- `docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md` (Q1–Q4 decisions)
- `docs/research/R1_IDENTITY_DECISION.md` (morning's Related Artifact reconciliation)
- `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md` (morning's environment boundary finding)
- `https://github.com/garrytan/gbrain` (Agent B focus project)

---

**End of task card**