# Organization-Level Agent Harness — Phase 1 Evidence Remediation v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT PROVEN.
**Date:** 2026-08-05
**Purpose:** Remediate Phase 1 evidence chain: verify sources, downgrade unverified convergence claims, classify problems by solvability tier, define decision criteria for Harness adoption.
**Source authority:** `ORG_LEVEL_AGENT_HARNESS_SOURCE_MATRIX_v0.1.md` + four agent reports + Synthesis
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## 0. Remediation Scope

This document does NOT:
- Judge whether Finance Suite needs an Org-level Harness
- Select frameworks, architectures, or technology
- Authorize any implementation, adoption, or roadmap commitment

This document DOES:
- Audit which Synthesis claims survive source verification
- Downgrade unverified convergence language to hypothesis
- Classify problems as process-solvable, runtime-control-required, or both
- Define decision criteria that must be satisfied BEFORE any Harness adoption decision
- List verified patterns, unknown patterns, and rejected claims

---

## 1. Synthesis Audit — Convergence Claims vs Evidence

### 1.1 The central Synthesis claim

The Synthesis (§0) states:

> "Both — but with the substrate primary. The root causes are substrate-level: the runtime conflates identity with user-identity, memory with state, evidence with claim, and authority with context."

**Evidence audit:**

| Sub-claim | Strongest supporting evidence | Evidence grade | Survives audit? |
|---|---|---|---|
| "Runtime conflates identity with user-identity" | A2A spec (DIRECT), Agent B cross-project finding B34-X1 (INFERRED from 12 READMEs) | PARTIAL | **HYPOTHESIS** — no project surveyed IMPLEMENTS agent-user identity separation; the conflation is OBSERVED, not PROVEN to be harmful in Finance Suite's specific context |
| "Runtime conflates memory with state" | FinRobot compute separation (DIRECT), LangGraph two-tier memory (DIRECT), Agent A three-tier memory claim (BROKEN) | PARTIAL | **HYPOTHESIS** — industry treats these as separate; whether Finance Suite's current conflation causes bugs is UNTESTED |
| "Runtime conflates evidence with claim" | Cloudflare 2023 postmortem (DIRECT), Knight Capital 2012 (DIRECT) | STRONG | **VERIFIED PATTERN** — production failures confirm this conflation causes real harm |
| "Runtime conflates authority with context" | Knight Capital $440M loss (DIRECT), Cloudflare collapsed approval chain (DIRECT) | STRONG | **VERIFIED PATTERN** — production failures confirm this conflation causes real harm |

### 1.2 The "7 of 8 frictions are substrate-primary" claim

The Synthesis (§3.9) classifies 7 of 8 morning frictions as substrate-primary (H) and 1 as procedure-primary (P).

**Evidence audit:**

| Friction | Synthesis classification | Evidence supporting "H" | Evidence grade | Re-classification |
|---|---|---|---|---|
| C Independent Verification | H-primary | A2A inside-opaque/boundary-inspectable (DIRECT), Agent B B40-X7 no environmental separation in OSS (INFERRED) | PARTIAL | **HYPOTHESIS** — the OSS absence finding is strong; whether the fix MUST be substrate-level vs procedural is UNTESTED |
| R1 Identity Reconciliation | H-primary | A2A Agent Card (DIRECT), FinRobot provenance tracking (DIRECT) | PARTIAL | **HYPOTHESIS** — provenance-as-content is an observed pattern; whether it makes R1 classification mechanical is UNTESTED |
| Memory ≠ Runtime State | H-primary | FinRobot deterministic/generative (DIRECT), LangGraph two-tier (DIRECT) | PARTIAL | **HYPOTHESIS** — tier decomposition is the industry pattern; whether Finance Suite's memory CAN be tier-decomposed is UNTESTED |
| Reference ≠ Adopted State | P-primary | agentsmd soft contract (DIRECT), branch protection as enforcement (DIRECT) | STRONG | **VERIFIED PATTERN** — procedure-primary classification is correct; enforcement at merge/approval boundary is the industry mechanism |
| Q1 Independent Verification Boundary | H-primary | A2A boundary-inspectable (DIRECT), asymmetric memory (DIRECT) | PARTIAL | **HYPOTHESIS** — boundary is environmental in industry; whether Finance Suite needs substrate change vs procedural boundary is UNTESTED |
| Q2 Claim Impact Model | H+P | Reversibility classification gates (DIRECT from MAF), multi-dimensional permission (INDIRECT) | WEAK | **HYPOTHESIS** — claim-impact classification as policy+enforcement is plausible but weakly evidenced |
| Q3 Authority Boundary | H-primary | Knight Capital + Cloudflare (DIRECT), credential-level separation (DIRECT) | STRONG | **VERIFIED PATTERN** — authority bound to credential is a verified failure mode with known remediation |
| Q4 Automation Boundary | H-primary | Capability-action asymmetry (DIRECT from Replit incident), MAF reversibility tiers (DIRECT) | PARTIAL | **HYPOTHESIS** — automation boundary is a capability dimension; whether this requires substrate vs procedural fix is UNTESTED |

**Re-classified summary:**

| Original | Re-classified |
|---|---|
| 7 substrate-primary, 1 procedure-primary | 3 VERIFIED, 5 HYPOTHESIS |

**Finding:** The Synthesis overstates the convergence. Only 3 of 8 friction classifications survive source audit as VERIFIED. The remaining 5 are downgraded to HYPOTHESIS.

### 1.3 The seven candidate architecture principles

The Synthesis (§4) proposes 7 candidate principles. Each is re-audited:

| Principle | Evidence basis | Survives as principle? | Re-classification |
|---|---|---|---|
| P1: Independence is environmental, not nominal | A2A + Agent B cross-project (PARTIAL) | Yes, as HYPOTHESIS | The PRINCIPLE is well-evidenced; its APPLICABILITY to Finance Suite is UNTESTED |
| P2: Evidence carries provenance as content | A2A + FinRobot + Cloudflare (STRONG) | Yes, as HYPOTHESIS | Strong evidence; schema-level implementation is UNTESTED |
| P3: Producer/Reviewer operate on disjoint evidence closure | A2A + CrewAI + CAI paper (PARTIAL) | Yes, as HYPOTHESIS | Pattern is observed; achievability in single-runtime LLM systems is UNTESTED |
| P4: Memory is tiered; runtime/state boundary is load-bearing | FinRobot + LangGraph + Agent A (PARTIAL, some BROKEN) | Yes, as HYPOTHESIS | Tier decomposition is observed; applicability to Finance Suite's specific memory architecture is UNTESTED |
| P5: Permission is multi-dimensional and non-transitive | CrewAI + A2A + Cloudflare (PARTIAL) | Yes, as HYPOTHESIS | Multi-dimensional permission is converging; non-transitivity as DEFAULT is weakly evidenced |
| P6: Authority is bound to credential, not context | Knight Capital + Cloudflare (STRONG) | **VERIFIED** | Two documented production failures confirm credential ≠ context distinction |
| P7: Within-org coordination requires queryable ledger | Magentic-One + Agent B patterns (PARTIAL) | Yes, as HYPOTHESIS | Ledger requirement is observed; "queryable, not readable" distinction is UNTESTED |

**Finding:** 1 of 7 principles survives as VERIFIED (P6). 6 survive as HYPOTHESIS. None are REJECTED.

---

## 2. Problem Classification — Process-Solvable vs Runtime-Control-Required

### 2.1 Definitions

| Tier | Definition | Example | Fix type |
|---|---|---|---|
| **Process-solvable** | Problem can be addressed by changing how humans and agents follow procedures, without modifying the runtime substrate | Reference ≠ Adopted State — enforce merge/approval boundary | Procedure + discipline |
| **Runtime-control-required** | Problem cannot be fully addressed without the runtime distinguishing something it currently conflates | Authority bound to credential, not context — runtime must expose credential as distinct from session context | Substrate change |
| **Hybrid** | Problem has both a procedural component (can improve now) and a substrate component (full fix requires runtime change) | Memory tiering — can adopt tier-naming convention now (process); cannot enforce tier boundary without runtime support | Both |

### 2.2 Problem classification table

| Problem | Classification | Process component | Runtime component | Evidence |
|---|---|---|---|---|
| Agent identity conflated with user identity | **Hybrid** | Adopt naming convention: "CC-session-2026-08-05" vs "Zhuanz" | Runtime must expose agent identity as a distinct credential/principal | A2A Agent Card (DIRECT), Agent B cross-project absence (INFERRED) |
| Memory conflated with runtime state | **Hybrid** | Adopt tier labels: session / project / cross-session; write rules per tier | Runtime must enforce tier boundaries (e.g., cannot write cross-session memory from session context) | FinRobot (DIRECT), LangGraph (DIRECT), Agent A three-tier (BROKEN) |
| Evidence conflated with claim | **Hybrid** | Adopt provenance fields on evidence objects now (author, time, scope, method) | Runtime must reject claim without evidence reference; evidence and claim must be separate objects with distinct lifecycles | Cloudflare (DIRECT), Knight Capital (DIRECT) |
| Authority conflated with context | **Runtime-control-required** | Declare authority boundary in docs (existing: Owner Assignment Schema) | Runtime must distinguish "agent has credential X" from "agent is in context labeled X" | Knight Capital (DIRECT), Cloudflare (DIRECT) |
| Producer can select its own reviewer | **Runtime-control-required** | Procedural rule: Verifier named by third party (existing: Owner Assignment Schema §2 Rule 1-4) | Runtime must reject self-selected verifier; verifier identity must come from different credential than producer | Cloudflare (DIRECT), Agent B cross-project absence (INFERRED) |
| HITL = single synchronous point, not continuous verification | **Process-solvable** | Add periodic spot-check verification step to existing window protocol | N/A — this is a process design gap, not a substrate gap | 5 OSS frameworks (DIRECT via Agent B) |
| Audit trail owned by audit target | **Runtime-control-required** | Adopt append-only discipline for evidence manifests (existing practice) | Audit log must be owned by a principal distinct from the principal being audited | SOX §404 (SEARCH), Cloudflare (DIRECT) |
| Reference vs Adopted State boundary | **Process-solvable** | Enforce merge/approval boundary; require explicit state transition with sign-off (existing practice) | N/A — procedure is sufficient; enforcement at merge boundary is the industry mechanism | agentsmd (DIRECT), branch protection (DIRECT) |
| Agent onboarding = write file, not competence check | **Process-solvable** | Add verification step: agent must demonstrate capability before receiving production-scope credentials | N/A — this is a process gap | agentsmd (DIRECT), Agent D findings (DIRECT) |
| Cascading errors from compound agent actions without audit | **Runtime-control-required** | Add intermediate checkpoints in multi-step agent workflows | Runtime must emit audit events at each step boundary; audit events must be independently verifiable | DeepMind taxonomy (SEARCH), Anthropic production report (SEARCH) |

### 2.3 Summary

| Classification | Count | Problems |
|---|---|---|
| Process-solvable | 3 | HITL single-point, Reference ≠ Adopted, Agent onboarding |
| Runtime-control-required | 4 | Authority ≠ context, Self-selected reviewer, Audit ownership, Cascading errors |
| Hybrid | 3 | Identity conflation, Memory conflation, Evidence conflation |

**Finding:** 7 of 10 problems require at least partial runtime substrate change. This supports the Synthesis's "substrate-primary" DIRECTION but not its STRENGTH — the evidence for runtime-change NECESSITY (vs procedural sufficiency) is weaker than the Synthesis implies.

---

## 3. Verified Patterns

Patterns that survive source audit with DIRECT evidence from at least two independent sources:

| Pattern | Evidence sources | Confidence |
|---|---|---|
| **Evidence ≠ Claim Authorization.** Conflating the two causes production failures. Collection and authorization are separate pipeline steps with different role requirements. | Cloudflare 2023 postmortem (DIRECT), Knight Capital 2012 (DIRECT), NIST AI RMF (SEARCH) | HIGH — two documented production failures |
| **Authority bound to credential, not context.** When two principals share credentials, they are structurally one principal. Two signatures from same credential ≠ two approvals. | Knight Capital $440M loss (DIRECT), Cloudflare collapsed approval chain (DIRECT) | HIGH — two documented production failures with quantified impact |
| **Agent identity is convention-based across OSS.** (role, goal, backstory) or (name, instructions) declared in YAML/code. No cryptographic binding. | CrewAI (DIRECT), AutoGen (DIRECT), MetaGPT (DIRECT), MAF (DIRECT), 8+ projects total | HIGH — verified across 8+ independent sources |
| **Inside-opaque / boundary-inspectable.** A2A's architectural principle: agents do not share internal state. Boundary surface (Agent Card) carries inspectable metadata. | A2A spec (DIRECT) | MEDIUM — single source, but it's a protocol specification |
| **HITL = synchronous single-point gate across all surveyed OSS.** No project implements continuous background verification. | LangGraph (DIRECT), AG2 (DIRECT), CrewAI (DIRECT), MAF (DIRECT) | HIGH — verified across 4 independent sources |
| **Deterministic/generative separation exists where regulatory pressure demands it.** FinRobot separates code-calculated numbers from LLM-assisted narratives. | FinRobot (DIRECT), Understand-Anything Tree-sitter + LLM (DIRECT) | MEDIUM — two sources, both domain-specific |
| **Graph-of-agents is the dominant workflow abstraction.** 5+ independent projects use nodes/edges/handoff vocabulary. | LangGraph (DIRECT), MAF (DIRECT), AG2 (DIRECT), AgentMesh (DIRECT), MetaGPT (DIRECT) | HIGH — verified across 5+ independent sources |

---

## 4. Unknown Patterns

Patterns that are plausible but lack sufficient evidence to be classified as verified:

| Pattern | Why unknown | What would verify it |
|---|---|---|
| **Organizational memory as a distinct tier.** All 12 projects have "memory" but none call it "organizational memory." Whether a distinct organizational tier is needed or whether existing tier models suffice is UNKNOWN. | No project implements it | A project that implements cross-agent, cross-session, queryable organizational memory with distinct lifecycle |
| **Non-transitive permission as default.** A2A's opaque-by-default implies non-transitivity, but no project explicitly enforces it as a designed property. Whether non-transitivity-by-default is necessary or just A2A's design choice is UNKNOWN. | Single source (A2A), inferred | A project that explicitly documents and enforces non-transitive permission grants |
| **Environmental separation is necessary for reviewer independence.** No OSS project implements it, but no production failure is documented as caused by its absence in an agent context. Whether role-based separation is sufficient is UNKNOWN. | Absence in OSS + absence of failure evidence | A documented production failure where role-based reviewer missed something an environmentally-separated reviewer would have caught |
| **"Harness" as a stable industry term.** MAF introduced it 2026-07-08. No other project uses it. Whether it converges or diverges is UNKNOWN. | Single source, <1 month old | At least one other major vendor/project adopting the term independently |
| **Provenance-as-content makes R1-classification mechanical.** The pattern is observed (A2A, FinRobot). Whether adding provenance fields to Finance Suite evidence objects would make Same/Conflict/Independent/Related Artifact classification derivable rather than interpretive is UNTESTED. | Pattern observed, applicability untested | A test: add provenance fields to 3 evidence objects and attempt mechanical classification |

---

## 5. Rejected Claims

Claims from the agent reports that do NOT survive source audit:

| Claim | Source report | Rejection reason |
|---|---|---|
| "Agent identities are federated through existing enterprise identity providers (Entra, Okta, IAM)" (A5) | Agent A — Industry | Both source URLs returned 404 or were CSDN third-party summaries. The existence of CVE-2025-55241 (CVSS 10.0 Entra ID token vulnerability) further weakens the claim that federation is a solved problem. **Reclassified: UNVERIFIED, not adopted.** |
| "Memory in production agent systems is explicitly decomposed into short-term / long-term / shared tiers. Boundaries are owned by the platform, not by the agent." (A12) | Agent A — Industry | AWS Memory page returned 404. CrewAI memory split only verified via CSDN third-party. The claim is plausible but the stated sources do not support it. **Reclassified: UNVERIFIED.** |
| "Production agent systems implement OAuth 2.0 delegated token exchange, not custom ACL systems." (A8) | Agent A — Industry | AWS Gateway page returned 404. Only one project (gbrain) verified as using OAuth scopes. The claim overgeneralizes from weak evidence. **Reclassified: UNVERIFIED.** |
| "Cascading errors from compound agent actions — agents in a loop with no external audit accumulate drift" (C13) | Agent C — Governance | Both cited sources (DeepMind taxonomy, Anthropic production report) were search-summary only. The failure MODE is plausible but the CLAIM about its prevalence is unverified. **Retained as HYPOTHESIS, not VERIFIED.** |
| "Self-validation produces false confidence" (C12) | Agent C — Governance | All three cited papers were search-summary only. The phenomenon is well-known in ML literature but the specific claim about LLM agent self-validation is unverified from the cited sources. **Retained as HYPOTHESIS.** |

---

## 6. Decision Criteria for Harness Adoption

These criteria must be satisfied BEFORE any decision to adopt, build, or integrate an Org-level Agent Harness. They are decision INPUTS, not decision PREDICATES — satisfying a criterion does not automatically authorize adoption; it removes a blocker to the decision.

### 6.1 Identity criteria

| ID | Criterion | Current state | Evidence needed |
|---|---|---|---|
| DC-1 | Finance Suite has demonstrated a concrete failure where agent identity conflation caused an incorrect claim, incorrect authorization, or incorrect audit entry | NOT DEMONSTRATED | A documented incident or near-miss where "CC session" ≠ "Zhuanz" or equivalent conflation produced a wrong outcome |
| DC-2 | At least one cryptographic or credential-based agent identity mechanism has been evaluated against Finance Suite's single-runtime Claude Code constraint | NOT EVALUATED | A technical assessment of whether AID's Ed25519 model, gbrain's OAuth scope model, or an alternative can function within a single Claude Code process |

### 6.2 Evidence criteria

| ID | Criterion | Current state | Evidence needed |
|---|---|---|---|
| DC-3 | Finance Suite has tested whether adding provenance fields (author, time, scope, method, target) to existing evidence objects makes R1-style classification mechanical | NOT TESTED | A test on 3-5 existing evidence objects: add provenance fields → attempt mechanical classification → compare with manual classification |
| DC-4 | At least one evidence object has been produced where collection and authorization are separate pipeline steps with different actors | NOT DEMONSTRATED | A concrete example: Agent collects evidence, Human (or different agent with distinct credential) authorizes its use in a claim |

### 6.3 Authority criteria

| ID | Criterion | Current state | Evidence needed |
|---|---|---|---|
| DC-5 | Finance Suite has demonstrated that a self-selected verifier (Producer names own reviewer) produced an incorrect verification that an independently-selected verifier would have caught | NOT DEMONSTRATED | A documented case or a controlled test |
| DC-6 | The cost of introducing environmental separation for verification (separate session, separate workspace, separate git worktree) has been measured against the benefit of label-based verification | NOT MEASURED | A concrete comparison: "C verification with environmental separation took X minutes and found Y issues; without separation took Z minutes and found W issues" |

### 6.4 Memory criteria

| ID | Criterion | Current state | Evidence needed |
|---|---|---|---|
| DC-7 | Finance Suite has classified its existing memory artifacts (Engram entries, Memory files, handoff docs, window boards, NOTES.json) into a tier model and identified which tier boundary is currently violated | NOT CLASSIFIED | A tier map of existing memory artifacts with boundary violations marked |
| DC-8 | At least one instance where "Memory ≠ Runtime State" conflation caused a wrong decision has been documented | NOT DEMONSTRATED | A documented case where a stale memory entry was treated as current state, producing wrong output |

### 6.5 Adoption threshold

A decision to adopt/build/integrate a Harness should require:

- **Minimum:** DC-1, DC-3, DC-5, DC-7 satisfied (one per dimension)
- **Recommended:** 6 of 8 satisfied
- **Full:** All 8 satisfied

No criterion is satisfied at this time. **Harness adoption decision is NOT READY.**

---

## 7. Synthesis Correction Directive

The following corrections MUST be applied to `ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md`:

### 7.1 Delete or downgrade

| Location | Current text | Correction |
|---|---|---|
| §0 "The synthesised answer" | "Both — but with the substrate primary" | Change to: "Both — but with the substrate primary. **This is a HYPOTHESIS, not a verified conclusion.** See Evidence Remediation §1 for source audit." |
| §0 para 2 | "The root causes are substrate-level" | Change to: "The **hypothesized** root causes are substrate-level. **Three of eight friction classifications survive source audit as VERIFIED; five are HYPOTHESIS.**" |
| §1.1–§1.10 | "Convergent observation" language | Each §1.x "Convergent observation" should be prefixed: "**Hypothesis (PARTIAL evidence):** " |
| §3.9 summary table | "7 H-primary, 1 P-primary" | Change to: "3 VERIFIED substrate-primary, 5 HYPOTHESIS substrate-primary, 1 VERIFIED procedure-primary. See Evidence Remediation §1.2." |
| §4 "Candidate architecture principles" | "Seven candidate principles are distilled" | Change to: "Seven candidate principles are distilled. **One (P6) is VERIFIED; six are HYPOTHESIS.** See Evidence Remediation §1.3." |

### 7.2 Add cross-reference

Add to Synthesis §6 (Non-decision statement):
> **Evidence audit:** This synthesis has been audited against primary sources. See `ORG_LEVEL_HARNESS_SOURCE_MATRIX_v0.1.md` for per-claim evidence grades and `ORG_LEVEL_AGENT_HARNESS_PHASE1_EVIDENCE_REMEDIATION_v0.1.md` for re-classification of convergence claims.

---

## 8. Phase 1 Closure Status

| Condition | Status | Reference |
|---|---|---|
| Source Matrix created | ✅ PASS | `ORG_LEVEL_HARNESS_SOURCE_MATRIX_v0.1.md` |
| All substantive claims verified against original sources | ✅ PASS WITH GAPS | 42% DIRECT, 24% SEARCH, 8 source mismatches flagged |
| Synthesis convergence claims downgraded to hypothesis | ✅ PASS | This document §1, §7 |
| Verified / Unknown / Rejected patterns classified | ✅ PASS | This document §3–§5 |
| Process-solvable vs Runtime-control-required problems classified | ✅ PASS | This document §2 |
| Decision criteria for Harness adoption defined | ✅ PASS | This document §6 |
| No architecture selection, no framework adoption, no implementation | ✅ PASS | All documents carry NOT ADOPTED / NOT PROVEN / IMPLEMENTATION NOT AUTHORIZED |

**Phase 1 Closure: PASS WITH EVIDENCE GAPS**

Phase 1 research is accepted as REFERENCE ONLY input. The evidence gaps (58% of claims not DIRECT-grade) do not block acceptance — they are documented and bounded. The Synthesis has been downgraded from "conclusions" to "hypotheses" consistent with the evidence quality.

**Next step:** Human Authority decision on whether to open a Phase 1→Phase 2 gate, keep Phase 1 open for additional source verification, or close Phase 1 and defer Harness questions to a future window. CC does not open this gate.

---

## 9. Cross-References

- `ORG_LEVEL_HARNESS_SOURCE_MATRIX_v0.1.md` — per-claim evidence grades
- `ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` — task card
- `C_PHASE1_METHOD_NOTE_v0.1.md` — C's method constraints
- `ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md` — Synthesis (to be corrected per §7)
- `ORG_LEVEL_AGENT_HARNESS_PHASE1_CLOSURE_REVIEW.md` — original gate check
- `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md` — current governance window

---

**End of Evidence Remediation** — Status: REFERENCE ONLY. NOT PROVEN. IMPLEMENTATION NOT AUTHORIZED.
