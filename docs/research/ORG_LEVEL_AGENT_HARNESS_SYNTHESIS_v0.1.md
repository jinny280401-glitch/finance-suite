# Organization-Level Agent Harness — Synthesis v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Author role:** Synthesizer (CC, governance coordinator)
**Date:** 2026-08-05
**Window:** External method research input (no production change, no code change, no declaration modification)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED
**Decision:** NOT DECIDED

> **Output target:** Synthesize the four parallel research reports dispatched under `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`.
> **Required answer:** Are the morning's governance frictions PROCESS DESIGN PROBLEMS that better procedures can solve, OR are they EVIDENCE that future Agent systems require an organizational-level Harness as native infrastructure?
> **Required sections:** (1) Common patterns across 3+ reports; (2) Patterns unique to one report; (3) Morning frictions re-examined; (4) Candidate architecture principles; (5) Open questions; (6) Non-decision statement.

This document synthesises four REFERENCE ONLY research outputs:

1. `ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md` — Industry Architecture (Agent A)
2. `ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md` — Open Source Systems (Agent B)
3. `ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md` — Governance & Safety (Agent C)
4. `ORG_LEVEL_HARNESS_SOFTWARE_PRACTICE_REPORT_v0.1.md` — Software Organization Practice (Agent D)

It does not modify Governance Design Review v0.1, the R1 reconciliation, C Independent Verification, or any declaration document. It informs future windows.

---

## 0. The synthesised answer

> **Are the morning's governance frictions PROCESS DESIGN PROBLEMS that better procedures can solve, OR are they EVIDENCE that future Agent systems require an organizational-level Harness as native infrastructure?**

**Research suggests potential runtime governance gaps that require further validation before any architecture decision.** The four reports observe patterns that intersect with the morning's frictions:

- The *symptoms* look procedural (a missing label, a missing approval gate, a missing sign-off) and can be partly addressed by better procedure. Procedure may be sufficient for some frictions; the reports do not collectively establish that procedure alone is insufficient.
- The *hypothesized* root causes point toward substrate-level questions: whether the runtime conflates identity with user-identity, memory with state, evidence with claim, or authority with context. These are observations from external references, not verified findings about the current Finance Suite runtime. The research reports describe patterns in other systems; they do not directly inspect the Finance Suite substrate.
- Industry references describe substrate separation as **infrastructure in some production systems**, not as a universal necessity or a proven requirement for Finance Suite. The morning's frictions are *consistent with* patterns that other systems address at the substrate level, but this consistency is observation, not causation. Whether Finance Suite's answer is improved process discipline, a substrate-level change, narrowing scope, or some combination is a *future-window decision* with evidence not yet collected.

This is a design-input statement, not an adoption statement. The synthesis does not authorise building, adopting, or avoiding a harness. It records the convergence.

---

## 1. Common patterns across all four reports

Patterns observed in **three or four of the four reports** are listed below. Each pattern carries: (a) which reports observe it, (b) the convergent observation, and (c) the structural implication.

### 1.1 Independence is a property of the environment, not a label

**Observed by:** A (Findings 2.2, 2.5), B (Producer ≠ Reviewer analysis), C (Findings 1.1, 1.4), D (Two-stage review).

**Convergent observation:** Across vendor reference, OSS review, governance literature, and software-org practice, the same primitive recurs: a "Reviewer" label confers no independence unless the reviewer's tools, data, time, and prompt are *disjoint* from the producer's. Independence is environmental.

**Structural implication:** When independence is a label and not an environment, verification is a sub-routine of production. The morning's C Independent Verification finding is consistent with this primitive.

### 1.2 Evidence carries provenance as content, not as commentary

**Observed by:** A (Finding 4.4), B (provenance fields), C (Finding 3.1), D (Identity at the source, not at the format).

**Convergent observation:** Production evidence objects carry (author, time, scope, method, target) as fields on the object itself. Comment-after-the-fact is treated as a known weakness. An audit answer is *generated from the data*, not reconstructed by inference.

**Structural implication:** The morning's R1 reconciliation — manual classification of static evidence vs runtime observation — is a sign that the underlying objects do not carry the fields needed for mechanical classification. Provenance-as-content would make the judgement derivable.

### 1.3 Producer and Reviewer operate on disjoint evidence closure

**Observed by:** A (Finding 3.4 non-transitive permission, Finding 1.1 inside-opaque/boundary-inspectable), B (Producer ≠ Reviewer separation), C (Findings 1.3, 1.4), D (Two-stage review).

**Convergent observation:** Independence is preserved only when the Reviewer's evidence sources do not transitively depend on the Producer's claims. Asymmetric read/write (Producer writes, Reviewer reads, neither writes the other's context) is the structural mechanism.

**Structural implication:** A shared-runtime model where the same Claude Code process carries context for both Producer and Reviewer is by definition non-disjoint. Industry treats this as a *system-architecture* property, not a labelling property.

### 1.4 Memory is decomposed into tiers, with the runtime/state boundary load-bearing

**Observed by:** A (Finding 4.1 three-tier decomposition, Finding 4.2 broker-mediated, Finding 4.3 asymmetric write), B (Shared persistent store), C (Findings 3.3 three-class evidence, 4.4 deterministic/generative separation), D (Memory primitives survive actor substitution).

**Convergent observation:** Memory in production systems is decomposed into short-term / long-term / shared tiers (industry), or into deterministic / generative classes (FinRobot), or into completion / correctness / authorisation classes (governance). The boundary between tiers is owned by the platform, not by the agent.

**Structural implication:** The morning's `Memory ≠ Runtime State` friction is a sign that the current runtime does not distinguish tiers. Adopting a tier decomposition in the runtime is the substrate answer; writing better Memory entries is the procedural answer. Both are needed; either alone is insufficient.

### 1.5 Permission is multi-dimensional and explicitly non-transitive

**Observed by:** A (Findings 3.1, 3.2, 3.3, 3.4), B (Tool-level access boundary, code-as-policy gap), C (Findings 1.4, 4.3), D (Capability downgrade at the platform boundary).

**Convergent observation:** Permission vocabulary extends beyond RBAC into (role × tool × data × time). Non-transitivity is the default. Approval chains must be two-principal with non-self-selection; otherwise the chain collapses to single-signature.

**Structural implication:** The morning's "Verifier self-selected by Producer's handoff" friction maps to *approver defined in the change* — the canonical structural failure mode (Knight Capital 2012, Cloudflare 2023). Fixing this requires that the runtime refuse transitive permission grants, not just that humans follow a two-eyes policy.

### 1.6 Authority is bound to credential, not to context

**Observed by:** A (Finding 2.1 distinct identity class, Finding 2.5 boundary inspectable), B (no cryptographic agent identity observed in OSS), C (Findings 1.4, 4.3), D (Identity at the source layer; AGENTS.md soft contract).

**Convergent observation:** Authority follows identity-with-credential, not context-with-label. Two principals that share identity (by token, by subscription, by capability) are structurally one principal regardless of how they are labelled.

**Structural implication:** When the runtime has no agent-identity credential distinct from the human-account credential, "the same agent verifies its own work" is structurally indistinguishable from self-certification. The morning's C Independent Verification finding maps to this primitive.

### 1.7 Onboarding and policy are soft contracts; enforcement lives at the merge/approval boundary

**Observed by:** A (Finding 2.5 boundary-inspectable), B (soft onboarding file), C (Findings 2.2, 4.5), D (AGENTS.md convention; branch protection as the gate).

**Convergent observation:** A repo-root instruction file, an agent memory entry, and an approved-but-stale policy are all *suggestions*. The merge step, the approval gate, the audit-trail entry — these are *enforcement*. Industry treats the boundary as the place where decisions become authoritative.

**Structural implication:** The morning's "Reference ≠ Adopted State" friction maps exactly here: a research status is reference, not a governance decision. The transition is at a boundary (merge, sign-off, audit entry), not in the file content.

### 1.8 Audit trails are third-party owned, append-only, decision-provenance-carrying

**Observed by:** A (Finding 4.4 provenance-as-content), B (OSS WAL pattern), C (Findings 5.1, 5.2, 5.3), D (Identity + session log + PR history as audit trail).

**Convergent observation:** When the audit-target owns its own audit log, the trail becomes self-reporting. Production systems enforce independent ownership. Trails carry *decision provenance* (who, under what authority, against what evidence), not just temporal sequence.

**Structural implication:** The morning's evidence manifest pattern is append-only *in practice*; it is not third-party-owned in structure. Without the structural element, the trail can be conformed.

### 1.9 Capability-action asymmetry is the dominant observed failure mode

**Observed by:** A (Finding 3.2 policy upstream of execution), B (HITL as single approval point), C (Findings 2.2, 4.1, 4.6), D (Replit incident; Replit CEO response).

**Convergent observation:** The recurring failure is *agent has capability for irreversible action without an explicit human gate*. Self-validation compounds bias; drift without audit is invisible by construction; persistent approvals decay with capability change.

**Structural implication:** The morning's Q3 Authority Boundary and Q4 Automation Boundary map to this primitive. Capability-action asymmetry is a substrate property, not a process discipline.

### 1.10 Within-org coordination is orchestrator-with-ledger; cross-org is boundary-mediated

**Observed by:** A (Findings 5.1, 5.4), B (Orchestrator patterns in OSS), C (Verifiable ledger implied), D (Repo-level review rails).

**Convergent observation:** Within-org multi-agent systems converge on orchestrator + ledger (Magentic-One, LangGraph hierarchical, MAF). Cross-org coordination is boundary-mediated (A2A Agent Card). Industry treats the within-org layer as the place where the ledgers must be queryable, not just readable.

**Structural implication:** The morning's CC orchestrator + subagents + Engram pattern is within-org. The ledger is currently implemented as prose (handoff docs, window boards, NOTES.json). The structural lesson is that the ledger must be queryable, not just readable.

---

## 2. Patterns unique to one report

These patterns appear in only one of the four reports. They are noted for completeness; their *uniqueness* is itself a finding about maturity.

### 2.1 Patterns unique to Agent A (Industry Architecture)

- **Contract Net / market-based coordination is academic, not production** — observed in academic MAS literature; LLM-mediated systems have not adopted it because bid evaluation is not cheap. *Maturity:* Reference-only; no production LLM agent system uses this pattern at scale. (A only.)
- **Inside-opaque / boundary-inspectable as a deliberate architectural stance** — A2A's principle that "agents collaborate without needing to share internal state, memory, or tools" while exposing an Agent Card. *Maturity:* Emerging; A2A is the canonical reference but industry has not converged on a unified boundary surface. (A only.)
- **Lifecycle / offboarding as a governance primitive** — agents that persist credentials after their task are a documented security risk; lifecycle is described as governance, not optional. *Maturity:* Documented in Entra / Okta / IAM primitives; not widely adopted in agent-specific products. (A only.)

### 2.2 Patterns unique to Agent B (Open Source Systems)

- **AID's DNS+Ed25519 cryptographic identity for agents** — public-key-anchored identity outside the project. *Maturity:* Experimental; only one project observed. (B only.)
- **AG2's write-ahead log (WAL) in Hub** — append-only ledger as a substrate primitive. *Maturity:* Project-internal; not interoperable across OSS. (B only.)
- **FinRobot's deterministic/generative separation as a finance-domain pattern** — "Numbers are code-calculated. Narratives are LLM-assisted." *Maturity:* Finance-specific; structurally mature within its scope. (B only.)
- **OpenClaw's CI engine router as a tiered capability surface** — different engines for different tasks. *Maturity:* Project-internal. (B only.)
- **Understand-Anything's `graph-reviewer` agent** — a single named verification-agent in a seven-agent pipeline. *Maturity:* Project-internal; not yet generalised. (B only.)
- **Microsoft Agent Framework's "Harness" + "don't-ask-again" approval** — most recent and least verified vocabulary; appears only in MAF. *Maturity:* Recent vocabulary; unverified by other OSS. (B only.)

### 2.3 Patterns unique to Agent C (Governance & Safety)

- **Owner / Executor / Verifier / Authority four-role decomposition** — explicit naming of the four role slots. *Maturity:* Convergent in adjacent regulatory domains (SOX, ITIL); not yet converged in LLM-agent-specific products. (C only.)
- **Two-principal approval with non-self-selection** — Cloudflare 2023 and Knight Capital 2012 as canonical postmortems. *Maturity:* Documented production failures; remediation patterns known but not universally adopted. (C only.)
- **Three-class evidence schema (completion / correctness / authorisation)** — collapse of the three is a known failure mode. *Maturity:* Conceptually mature; structurally rare in practice. (C only.)
- **Loss-of-audit as its own signal** — gap event when records cannot be written. *Maturity:* Rarely implemented; conceptually established. (C only.)

### 2.4 Patterns unique to Agent D (Software Organization Practice)

- **AGENTS.md layered convention (repo / org / personal)** — closest-scope wins. *Maturity:* De facto standard (~23.4k stars); not standardised by any standards body. (D only.)
- **Linux kernel `Assisted-by:` tag + DCO retention** — human submitter retains DCO signature even on AI-assisted patches. *Maturity:* Project-specific; no industry convergence. (D only.)
- **GitHub Copilot coding-agent "draft PR + branch protection" pattern** — capability downgrade at the platform boundary. *Maturity:* Product-internal; widely replicated as a pattern. (D only.)
- **Blameless postmortem culture as the actor-agnostic memory primitive** — separation of action from actor. *Maturity:* Industry-standard in SRE practice; not specific to agent era. (D only.)

**Assessment of uniqueness.** The patterns unique to one report are not necessarily weaker — some (e.g., AID's PKA identity, MAF's Harness vocabulary) are more ambitious than the cross-report patterns. Their uniqueness is a *coverage* finding: the cross-report patterns have broader industry recognition, while the unique patterns are either newer (MAF), domain-specific (FinRobot), or experimental (AID). Future windows may promote unique patterns to common patterns as industry convergence progresses.

---

## 3. The morning's frictions re-examined

For each morning friction, this section states whether each report's findings illuminate a **process design** solution (P), a **native harness** requirement (H), or both (P+H). The classification is per friction; the convergence is at the bottom.

### 3.1 C Independent Verification revealed environment-bound independence

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Identity scoped per-environment (role × tools × data × time); non-transitive permission default (Findings 2.2, 3.4) |
| B | Layered onboarding; review-assignment rules | No OSS defines environment-bound agent identity; Producer ≠ Reviewer is role-based, not environment-based |
| C | Blameless postmortem culture; Owner/Executor/Verifier/Authority role slots | Environmental independence as (tools ∪ data ∪ time ∪ prompt) disjointness (Finding 1.1) |
| D | Two-stage review (machine findings, human approval); branch protection | Capability downgrade at the platform boundary; submitter bears responsibility |

**Classification: P+H.** Procedure alone cannot enforce environmental disjointness when the runtime does not distinguish environments. Industry treats environment-bound independence as a substrate primitive. The morning's finding is a substrate finding, not a procedure gap.

### 3.2 R1 Identity Reconciliation required manual Related Artifact judgement

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Provenance-as-content; boundary-inspectable Agent Card (Findings 2.5, 4.4) |
| B | Identity + audit log conventions | No cryptographic agent identity in OSS |
| C | Three-class evidence schema; decision provenance audit | Evidence carries provenance as a first-class field (Finding 3.1) |
| D | Identity at the source layer (not format) | Authority lives at the identity layer, not the format layer |

**Classification: H-dominant, P-overlay.** The reconciliation was manual because the underlying objects did not carry the fields needed for mechanical classification. Procedure (write better handoff docs) cannot compensate for missing fields in the substrate. The substrate fix is provenance-as-content and identity-at-source; the procedure overlay is the discipline of reading those fields.

### 3.3 Memory ≠ Runtime State boundary

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | Tiered memory as convention (write rules) | Three-tier decomposition owned by the platform (Finding 4.1); broker-mediated shared state (Finding 4.2); asymmetric write (Finding 4.3) |
| B | Memory as configuration file | Shared persistent store is the closest analogue; no project decomposes memory tiers cleanly |
| C | Deterministic/generative separation as rule | Deterministic/generative separation as schema-level enforcement (Finding 4.4) |
| D | Lifecycle of memory primitives | Memory primitives survive actor substitution; lifecycle owned by platform, not agent |

**Classification: H-primary, P-overlay.** The boundary is load-bearing. Treating it as a labelling problem (write "this is memory, not state") does not enforce the boundary; the runtime must enforce the boundary. Industry treats this as a substrate property.

### 3.4 Reference ≠ Adopted State discipline

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Authority lives at the merge / approval boundary (Finding 1.1: gateway vs harness separation) |
| B | Soft contract for onboarding files | — |
| C | Approval chains with provenance; reversibility-classified gates (Findings 2.2, 2.3) | Provenance-carrying approval (Finding 2.3) |
| D | AGENTS.md soft contract; branch protection as the enforcement layer | — |

**Classification: P-dominant, H-overlay.** Reference vs adopted state is a *transition discipline*. Procedure (declare, sign, merge) is the primary mechanism. The substrate supports by carrying provenance through the transition so the audit can read the result. Both are needed; the procedure is primary.

### 3.5 Q1 Independent Verification Boundary

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Inside-opaque / boundary-inspectable (Finding 2.5) |
| B | — | Asymmetric memory access pattern (Producer writes, Reviewer reads) |
| C | Owner/Verifier role slot | Asymmetric read/write (Finding 1.4); disjoint evidence closure (Finding 1.3) |
| D | Two-stage review | Capability downgrade at the platform boundary |

**Classification: H-primary, P-overlay.** The boundary is environmental. The morning's Q1 is a substrate question. The Industry-A pattern (boundary-inspectable, interior-opaque) is the canonical answer.

### 3.6 Q2 Claim Impact Model

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Reversibility-classification gates (Finding 3.3 multi-dimensional permission) |
| B | HITL as single approval gate | HITL is single-point, not continuous; gap observed |
| C | Reversibility-classification gates (Finding 2.2) | Gate policy upstream of execution; reversibility tiers enforced by platform |
| D | Authority boundary as policy | Capability downgrade at the platform boundary |

**Classification: P+H.** Claim-impact classification is a *policy* decision (process); the policy is *enforced* by the platform (substrate). Industry treats both as load-bearing.

### 3.7 Q3 Authority Boundary

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Authority bound to identity (Finding 2.1); non-transitive permission (Finding 3.4) |
| B | CODEOWNERS-style rules | No cryptographic identity for agents |
| C | Authority slot in Owner/Executor/Verifier/Authority | Approver independence is structural (credential-level), not procedural (Knight Capital 2012) |
| D | Submitter bears responsibility (kernel DCO) | Capability downgrade at the platform boundary |

**Classification: H-primary, P-overlay.** Authority is bound to credential, not to context. The substrate must distinguish credentials; the procedure must enforce that authority is read from the credential, not from the context.

### 3.8 Q4 Automation Boundary

| Report | Process design (P) | Native harness (H) |
|---|---|---|
| A | — | Multi-dimensional permission (role × tool × data × time) (Finding 3.3) |
| B | Tool-level access boundary | Permission is code-as-policy, not file-as-policy |
| C | Reversibility classification (Finding 2.2) | Capability-action asymmetry is the dominant failure mode (Finding 4.1) |
| D | Branch protection; PR + Slack + IDE surface area | Capability downgrade at the platform boundary |

**Classification: H-primary, P-overlay.** The automation boundary is a capability dimension of the runtime, not a labelling choice. Industry treats this as a substrate property; procedure adds discipline.

### 3.9 Friction-by-friction summary

| Friction | Primary | Secondary |
|---|---|---|
| C Independent Verification | H | P |
| R1 Identity Reconciliation | H | P |
| Memory ≠ Runtime State | H | P |
| Reference ≠ Adopted State | P | H |
| Q1 Independent Verification Boundary | H | P |
| Q2 Claim Impact Model | H+P | — |
| Q3 Authority Boundary | H | P |
| Q4 Automation Boundary | H | P |

**Reading.** The four research reports classified seven of eight morning frictions as primarily associated with substrate-level patterns observed in external systems, and one (Reference ≠ Adopted State) as primarily a procedural discipline. This classification is a research observation, not a verified finding about the Finance Suite runtime. The research suggests that substrate-level mechanisms *may* be relevant; it does not establish that substrate separation is necessary or that procedure alone is insufficient. Further validation against the actual Finance Suite runtime is required before any architecture conclusion.

---

## 4. Candidate architecture principles

Seven candidate principles are distilled from the four reports. **One (P6 — Authority bound to credential) is VERIFIED by two documented production failures (Knight Capital 2012, Cloudflare 2023). The remaining six are HYPOTHESIS — consistent with observed patterns but untested against the Finance Suite runtime.** See `ORG_LEVEL_AGENT_HARNESS_PHASE1_EVIDENCE_REMEDIATION_v0.1.md` §1.3 for per-principle evidence audit. Each principle carries a **Non-Claim** line stating what the principle does NOT yet authorise.

### Principle 1 — Independence is environmental, not nominal

**Distilled from:** A (Findings 2.2, 2.5, 3.4), B (Producer ≠ Reviewer analysis), C (Findings 1.1, 1.4), D (Two-stage review).

**Statement:** The independence of a reviewer is a property of (tools ∪ data ∪ time ∪ prompt) disjointness from the producer's, not of a "Reviewer" label. A "Reviewer" label without environmental disjointness is a sub-routine of production.

**Implication for design:** Future windows that introduce a verification role must bind it to an environment, not just to a label.

**Non-Claim:** This principle does NOT authorise building or adopting any verification environment. It does NOT prescribe what environment-bound independence looks like for Finance Suite. It does NOT assert current Finance Suite practice lacks any environmental separation.

### Principle 2 — Evidence carries provenance as content

**Distilled from:** A (Finding 4.4), B (provenance fields), C (Finding 3.1), D (Identity at the source).

**Statement:** Evidence objects carry (author, time, scope, method, target, link) as fields on the object itself. Audit answers are generated from the data, not reconstructed by inference.

**Implication for design:** Future windows that introduce an evidence manifest must declare the provenance schema before the manifest is written, not after.

**Non-Claim:** This principle does NOT authorise any specific provenance schema. It does NOT recommend hash-chaining. It does NOT prescribe what fields are required for which class of evidence.

### Principle 3 — Producer and Reviewer operate on disjoint evidence closure

**Distilled from:** A (Findings 1.1, 3.4), B (Producer ≠ Reviewer), C (Findings 1.3, 1.4), D (Two-stage review).

**Statement:** The Reviewer's evidence sources do not transitively depend on the Producer's claims. Asymmetric read/write — Producer writes, Reviewer reads, neither writes the other's context — is the structural mechanism.

**Implication for design:** Future windows that touch evidence flow must declare the read/write asymmetry before declaring the flow.

**Non-Claim:** This principle does NOT authorise any specific capability vocabulary. It does NOT prescribe asymmetric read/write scope dimensions. It does NOT assert that disjoint evidence closure is achievable in single-runtime LLM systems.

### Principle 4 — Memory is tiered and the runtime/state boundary is load-bearing

**Distilled from:** A (Findings 4.1, 4.2, 4.3), B (Shared persistent store), C (Findings 3.3, 4.4), D (Memory primitives).

**Statement:** Memory is decomposed into tiers (short-term / long-term / shared; or completion / correctness / authorisation; or deterministic / generative). The boundary between tiers is owned by the platform, not by the agent.

**Implication for design:** Future windows that touch memory must declare the tier model and the boundary enforcement before declaring the memory primitives.

**Non-Claim:** This principle does NOT authorise any specific tier model. It does NOT recommend a specific enforcement mechanism. It does NOT assert that current Finance Suite memory conflates tiers.

### Principle 5 — Permission is multi-dimensional and explicitly non-transitive

**Distilled from:** A (Findings 3.1, 3.2, 3.3, 3.4), B (Tool-level access boundary), C (Findings 1.4, 4.3), D (Capability downgrade).

**Statement:** Permission is (role × tool × data × time). Non-transitivity is the default. Approval chains must be two-principal with non-self-selection; otherwise the chain collapses to single-signature.

**Implication for design:** Future windows that touch permission must declare the dimension set and the non-transitivity rule before declaring the permission vocabulary.

**Non-Claim:** This principle does NOT authorise any specific permission vocabulary. It does NOT recommend OAuth 2.0 or any other delegation mechanism. It does NOT prescribe specific dimension sets.

### Principle 6 — Authority is bound to credential, not to context

**Distilled from:** A (Findings 2.1, 2.5), B (no cryptographic agent identity), C (Findings 1.4, 4.3), D (Identity at the source layer).

**Statement:** Two principals that share identity (by token, by subscription, by capability) are one principal regardless of how they are labelled. Authority follows credential, not context.

**Implication for design:** Future windows that introduce a verification or approval role must bind it to a distinct credential, not to a label within the same context.

**Non-Claim:** This principle does NOT authorise any specific identity mechanism. It does NOT recommend Entra / Okta / IAM / PKA. It does NOT prescribe how to construct agent credentials distinct from human credentials.

### Principle 7 — Within-org coordination requires a queryable ledger, not a readable one

**Distilled from:** A (Findings 5.1, 5.4), B (Orchestrator patterns), C (Verifiable ledger implied), D (Repo-level review rails).

**Statement:** Within-org multi-agent coordination converges on orchestrator + ledger. The ledger must be queryable (machine-readable, structurable), not just readable (prose, handoff docs).

**Implication for design:** Future windows that introduce multi-agent coordination must declare the ledger as a queryable object, not as a free-form document.

**Non-Claim:** This principle does NOT authorise any specific orchestrator pattern. It does NOT recommend Magentic-One, LangGraph, or MAF. It does NOT prescribe a ledger schema.

---

## 5. Open questions for future governance windows

The research surfaces questions that this synthesis does NOT answer. Each is recorded as input for a future window.

### 5.1 Identity substrate

- **Q-Identity-1.** What is the minimum credential distinction that constitutes "agent identity distinct from human identity" in a single-runtime Claude Code process? The reports converge that this distinction is necessary; they do not specify the implementation.
- **Q-Identity-2.** Does Finance Suite federate agent identities through an existing IdP (per Agent A Finding 2.3) or maintain a separate agent identity registry? The choice has governance implications not addressed here.

### 5.2 Evidence and audit

- **Q-Evidence-1.** What is the minimum provenance schema that converts R1-class reconciliations from manual to mechanical? The reports converge on provenance-as-content; they do not specify the schema.
- **Q-Evidence-2.** Who owns the audit log? The Industry-C pattern (third-party owned) implies a separate principal; the current Finance Suite evidence manifests are owned by the producer window.

### 5.3 Memory and runtime state

- **Q-Memory-1.** Is the current Finance Suite memory tier-decomposable, or is the runtime/state boundary load-bearing in a way that prevents decomposition without a harness? The reports converge that the boundary is load-bearing; they do not specify whether the current runtime can be retrofitted.
- **Q-Memory-2.** What is the relationship between Engram (lesson store), Memory (Claude Code memory), and the runtime state of a single Claude Code session? The Industry pattern is broker-mediated shared state; Finance Suite's broker is currently manual.

### 5.4 Verification and authority

- **Q-Verification-1.** What is the minimum environmental separation that converts the C Verifier from a label to a structural check? The reports converge that labels are insufficient; they do not specify the separation.
- **Q-Verification-2.** Does Finance Suite introduce a dedicated verification harness, or does it narrow scope to avoid verification-bearing work? Both options are open.

### 5.5 Coordination and onboarding

- **Q-Coordination-1.** What is the minimum queryable ledger that supports CC's within-org coordination without violating the Memory ≠ Runtime State boundary? The reports converge that the ledger must be queryable; they do not specify the ledger.
- **Q-Onboarding-1.** Does Finance Suite adopt a layered onboarding convention (per Agent D AGENTS.md pattern) at repo / org / personal levels? The current CLAUDE.md pattern is project-level only.

### 5.6 Process design vs substrate — the decision question

- **Q-Decision-1.** **Are the morning's frictions best addressed by improving process discipline, by introducing a substrate-level harness, by narrowing scope to avoid harness-shaped work, or by some combination?** This synthesis observes that the substrate is primary for seven of eight frictions; it does NOT decide which option Finance Suite takes.
- **Q-Decision-2.** If a substrate-level harness is the answer, is it built, adopted, or assembled from existing primitives? The reports describe patterns; they do not prescribe Finance Suite's procurement model.

---

## 6. Non-decision statement

**This synthesis does NOT adopt, authorise, or commit.**

- It does NOT authorise the adoption of AWS Bedrock AgentCore, Microsoft Entra ID Agent ID Administrator, Claude Code Cloud Tag, Microsoft Magentic-One, LangGraph supervisor / hierarchical agent teams, Google Agent2Agent (A2A) protocol, CrewAI permission / role vocabulary, or any other vendor product named in the source reports.
- It does NOT authorise any OAuth 2.0 delegated token exchange deployment.
- It does NOT authorise any federation of agent identities to Entra / Okta / IAM.
- It does NOT authorise any specific scoping of identity, permission, memory, or coordination primitives.
- It does NOT authorise any architecture decision by Finance Suite.
- It does NOT authorise any implementation plan, roadmap, sequencing, or production change.
- It does NOT modify Governance Design Review v0.1, R1 Identity Reconciliation, C Independent Verification Setup, or any morning governance artifact.
- It does NOT prescribe whether Finance Suite builds a harness, adopts one, or narrows scope to avoid harness-shaped work.

**This synthesis is REFERENCE ONLY.** It distils patterns observed across four REFERENCE ONLY research outputs. It produces a design-input reading of the morning's frictions (substrate-primary for seven of eight, procedure-primary for one). It does not produce a decision.

**Status:** DECISION: NOT DECIDED.

The decision — whether Finance Suite's answer to the morning's frictions is process discipline, native harness, scope-narrowing, or a combination — is reserved for a future window with explicit authorisation. This synthesis records the convergence; it does not act on it.

---

## 7. Cross-references

- Task card: `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`
- Sister-agent outputs:
  - `docs/research/ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md` (Agent A)
  - `docs/research/ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md` (Agent B)
  - `docs/research/ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md` (Agent C)
  - `docs/research/ORG_LEVEL_HARNESS_SOFTWARE_PRACTICE_REPORT_v0.1.md` (Agent D)
- Morning governance inputs (NOT modified by this synthesis):
  - `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md`
  - `docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md`
  - `docs/research/R1_IDENTITY_DECISION.md`
  - `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md`

---

**End of synthesis** — Status: REFERENCE ONLY. Decision: NOT DECIDED.