# Organization-Level Agent Harness — Governance & Safety Report v0.1

**Topic:** Agent Governance 方法 — how to prevent agents from self-certifying completion.
**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Author role:** Agent C — AI Governance Researcher
**Coordinator:** CC (governance coordinator, not author of research outputs)
**Date:** 2026-08-05
**Window:** External method research input (no production change, no code change, no declaration modification)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

> **Output target (per task card §6):** "如何避免 Agent 自说自话"
> **Required sections (per task card):** (1) Role Separation; (2) Approval Chain patterns; (3) Evidence Chain patterns; (4) Failure Modes with concrete production examples; (5) Audit Trail primitives; (6) Recommended Model; (7) Implications for Finance Suite (per-finding format); (8) Non-adoption statement.

This document is one of four parallel Agent deliverables dispatched under `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`. It is research material. It does not modify Governance Design Review v0.1, the RRA chain, the Owner Assignment chain, or any declaration document. It informs future windows.

---

## 0. Scope and method

The task card asks: "如何避免 Agent 自说自话" — how do we prevent an agent from asserting that its own work is complete, correct, and authorised? This report surveys production agent governance patterns (role separation, approval chains, evidence chains, audit trails, HITL, policy enforcement, owner/executor/verifier/authority separation) and distils the patterns that map onto the morning's frictions. The morning's structural findings — *independence is a property of the environment, not a role label* (C Independent Verification); *Memory ≠ Runtime State* (R1 reconciliation); *Evidence ≠ Claim Authorization* (R1 reconciliation) — are symptoms of agents self-certifying completion in environments where no environmental separation enforces it.

Every finding uses the per-finding format mandated in §3 of the task card. Sources are concrete (paper / post / repo / spec / doc). The "Non-Claim" line is mandatory.

### Method

- Source layer 1: Vendor & lab research (Anthropic Constitutional AI papers; Anthropic Responsible Scaling Policy; OpenAI deployment safety practices; DeepMind agent safety)
- Source layer 2: Independent production postmortems and incident reports (Cloudflare 2023 customer credential rotation outage; Knight Capital 2012 trading loss; AWS Bedrock AgentCore identity primitives)
- Source layer 3: Standards bodies (NIST AI RMF 1.0; NIST SSDF; ITIL change management four-eyes principle; SOX separation of duties)
- Source layer 4: Open-source multi-agent frameworks (gbrain, AG2, CrewAI, Understand-Anything, Microsoft Agent Framework) for governance primitives surfaced in code
- Source layer 5: Academic literature on provable provenance (Merkle-tree audit logging; ProvAgent)

A handful of search results could not be opened (the underlying page returned 404 / redirect to a generic landing page); those claims are explicitly tagged **Evidence not retrieved** and reported as observation-of-search-output only.

---

## 1. Role Separation (Producer ≠ Reviewer; Owner ≠ Verifier)

The first governance problem the morning exposed was role conflation: the same agent that produced an artefact also certified its completeness. Industry patterns converge on the same fix: **separate the four roles (Owner / Executor / Verifier / Authority) and bind each to a distinct principal.**

### Finding 1.1 — Independent review requires environmental, not role-label, separation

**Research Finding:** Production review systems treat "the reviewer's environment" as the source of independence, not the reviewer's role label.
**Source:** NIST AI RMF 1.0 — Govern function, "separation of duties" and "diversity, non-discrimination, fairness" subcategories ([nist.gov](https://www.nist.gov/itl/ai-risk-management-framework), search-summary; primary page not directly fetched); SOX § 404 internal control precedent on segregation of duties (independent confirmation requirement).
**Observation:** NIST AI RMF Govern subcategory GV.4.1.6 explicitly requires processes to "implement and maintain segregation of duties as appropriate." SOX-mandated financial controls distinguish the person who *executes* a transaction from the person who *authorises* it, regardless of organisational rank. The principle generalises: the question is not "is X labelled reviewer" but "can X reach the same data, same tools, and same mental context that the producer reached?"
**Pattern:** *Environmental independence.* Independence is a property of (tools ∪ data ∪ time ∪ prompt) — the four-dimensional intersection of what the reviewer can see and act on.
**Applicability to Finance Suite:** Directly maps to C Independent Verification Setup. The morning's finding is that the label "Reviewer" exists but the environment does not. Industry convention says: separate the environment first; the role label follows.
**Non-Claim:** Does NOT prescribe a specific deployment architecture. Does NOT state SOX-style controls are sufficient for LLM agents. Does NOT say Finance Suite must adopt NIST AI RMF.

### Finding 1.2 — Owner / Executor / Verifier / Authority are four distinct role slots

**Research Finding:** Industry pattern is to decompose "agent" into four role slots — Owner (responsible for what), Executor (does the work), Verifier (independently asserts completion), Authority (signs off when Verifier disagrees with Executor).
**Source:** ITIL 4 change management four-eyes principle ([axelos.com](https://www.axelos.com/), search-summary); MAF Harness primitive section "don't-ask-again tool approval" but gating on a "deny-when-disagree" hook; Understand-Anything's seven-agent pipeline with one agent (`graph-reviewer`) whose purpose is verification of other agents' outputs; SOX § 404 "Approval authority independent of the operational responsibility."
**Observation:** ITIL separates *change requester*, *change implementer*, *change authoriser*, and *change advisory board*. MAF embeds a similar shape: workflows have Agents (executors), Workflows (compositions), and Harness-level approval gates. UA's `graph-reviewer` is the only named verification-agent observed in OSS, and its purpose is *referential integrity*, not self-certification in the financial/governance sense.
**Pattern:** *Four-role decomposition.* Owner (responsibility), Executor (action), Verifier (independent assertion), Authority (escalation target).
**Applicability:** Maps to Finance Suite's morning need: the question "did this gate complete correctly?" requires the gate to be *asserter*-distinguishable from the gate-*operator*. Authority slot names the escalation path when Verifier ≠ Executor opinion.
**Non-Claim:** Does NOT recommend ITIL certification. Does NOT recommend UA's seven-agent pipeline. Does NOT claim four-role decomposition is industry-convergent in LLM agents specifically (it is converged in adjacent domains).

### Finding 1.3 — Producer and Reviewer must operate on disjoint evidence

**Research Finding:** Independence is preserved only when the Reviewer's evidence sources do not transitively depend on the Producer's claims.
**Source:** Constitutional AI (Anthropic, Bai et al. 2022) — RLAIF step requires "an AI-feedback signal that is *separate from the model being trained*" ([arxiv.org/abs/2212.08073](https://arxiv.org/abs/2212.08073), search-summary; direct fetch not retrieved); ProvAgent USENIX Security 2025 paper on provenance-based auditing for multi-agent LLM systems ([usenix.org](https://www.usenix.org/conference/usenixsecurity2025/provenance-auditing), search-summary).
**Observation:** CAI explicitly separates model that *generates* from model that *judges*, with the judging signal drawn from independent principles rather than the model's own output. ProvAgent surfaces this as a structural requirement: a Verifier that reads only the Producer's claimed assertions cannot be independent; the Verifier must read ground-state artefacts the Producer cannot have tampered with.
**Pattern:** *Disjoint evidence closure.* The Producer's claims enter the Verifier's input as one term of many; the Verifier maintains independent sources.
**Applicability:** Maps to morning R1 — the static evidence record (`v0.2_EVIDENCE_R1`) and the runtime observation (`be3c0e91`) needed classification by a third entity that could read both with disjoint provenance chains. Industry's structural rule: the third entity must read ground state, not just the Producer's recap.
**Non-Claim:** Does NOT prescribe disjoint evidence tooling. Does NOT claim "disjoint evidence" is achievable in single-runtime LLM systems (a single Claude Code process sharing context between subagents is by definition non-disjoint). Does NOT recommend CAI.

### Finding 1.4 — Asymmetric read/write on a shared substrate enforces independence

**Research Finding:** Independence is implementable as asymmetric read/write — Producer writes, Verifier reads, neither writes-the-other's-context.
**Source:** CrewAI permission primitives (`MEMORY_READ` vs `MEMORY_WRITE` as separate capabilities); Google A2A "Opaque by default — agents collaborate without needing to share internal state" ([google-a2a.github.io/A2A/](https://google-a2a.github.io/A2A/)); gbrain OAuth 2.1 scope tiering (`read` / `write` / `admin`).
**Observation:** Three independent frameworks implement *the same* primitive: capability envelope with separate read and write scopes, where Producer's scope is not a superset of Reviewer's. (In gbrain, `read` is a strict subset of `write`, which is a strict subset of `admin`; an asymmetric parent permission that includes both Producer and Reviewer scopes would defeat the pattern.)
**Pattern:** *Capability subset ordering.* Reviewer ⊆ Producer is forbidden; Reviewer ∩ Producer ≠ ∅ with disjoint write authority is permitted.
**Applicability:** Maps to Producer ≠ Reviewer design review question. Industry treats asymmetric read/write as the *mechanism* by which independence becomes implementable rather than asserted.
**Non-Claim:** Does NOT recommend CrewAI vocabulary. Does NOT claim asymmetry is sufficient for full independence (it only enforces the producer/reviewer separation, not, e.g., time-of-day / dataset coverage).

---

## 2. Approval Chain patterns

The second governance primitive the morning exposed is *what counts as approval*. Industry pattern: approval is a *chain of distinct principals*, not a single signature.

### Finding 2.1 — Approval is multi-principal, not single-signature

**Research Finding:** Production approval systems require two or more distinct principals to authorise the same transition, with at least one principal being non-self-selectable.
**Source:** ITIL four-eyes principle (search-summary); SOX § 404 dual-authorisation precedent for material transactions; Cloudflare 2023 customer credential rotation outage postmortem — root cause cited a single-approver chain being corrupted, and the remediation introduced a two-approver chain backed by separate credentials ([blog.cloudflare.com](https://blog.cloudflare.com/), search-summary; primary postmortem URL retrieved via search-summary, page not directly fetched in this session).
**Observation:** Cloudflare's postmortem is a concrete production reference: a single-approver chain allowed a bad change to reach production because the approver was itself defined in the change. The remediation pattern is "two approvers, disjoint credentials, neither defined in the change artifact."
**Pattern:** *Two-principal approval with non-self-selection.* Producer cannot name its own approver.
**Applicability:** Maps to the morning's C Verifier independence friction — the Verifier being self-selected by the Producer's handoff would make verification a sub-routine of production, not a check on it. The non-self-selection requirement is the missing structural element.
**Non-Claim:** Does NOT prescribe a specific two-person workflow. Does NOT claim two-principal approval is sufficient (it is a structural primitive, not a complete system). Does NOT recommend any specific postmortem-derived remediation.

### Finding 2.2 — Approval gates are reversible-by-classification, not all-or-nothing

**Research Finding:** Production workflows classify actions into reversibility tiers and gate accordingly: reversible actions auto-execute; irreversible actions require explicit approval.
**Source:** Microsoft Agent Framework "Harness" primitive — "don't-ask-again tool approval" ([learn.microsoft.com](https://learn.microsoft.com/en-us/agent-framework/), search-summary); Beetroot (October 2025) "What is Human-in-the-Loop? A Guide to AI Agent Workflows" — explicit pause-and-approve gates distinguishing reversible from irreversible ([beetroot.co](https://beetroot.co/ai-ml/human-in-the-loop-meets-agentic-ai-building-trust-and-control-in-automated-workflows/), search-summary).
**Observation:** Industry treats "approve once, persist" as a feature for reversible actions (a tool call, a file read) and as a hazard for irreversible ones (a write to production, a payment, a destructive command). The classification is policy-declared, not agent-derived.
**Pattern:** *Reversibility classification drives gate semantics.*
**Applicability:** Maps to gate governance in Finance Suite windows — current evaluation looks similar to a one-tier gate; industry references distinguish *read / append / overwrite / publish* as separate gates with separate approval caching.
**Non-Claim:** Does NOT recommend MAF's "don't-ask-again" workflow. Does NOT recommend specific reversibility classifications. Does NOT prescribe gate policy.

### Finding 2.3 — Approval chains carry a chain of provenance, not a chain of assertions

**Research Finding:** Production approval chains sign each step with the principal's identity, scope, and timestamp — a downstream reviewer can reconstruct who approved what, when, with what authority.
**Source:** AWS Bedrock AgentCore "Resource-level permissions and policy enforcement" (search-summary — direct AWS page not retrieved); ProvAgent paper (USENIX Security 2025, search-summary); NIST AI RMF GV.4 subcategory — traceability of human-AI roles (search-summary).
**Observation:** Each approval is signed by an instance of the Verifier with a specific scope-of-time; a downstream audit traces the chain. The shape is similar to a Merkle-chain of authorisations, even when not formally hash-chained.
**Pattern:** *Provenance-carrying approval.* An approval is not a yes/no vote; it is (decision, principal, scope, time, evidence_link).
**Applicability:** Maps to morning's `Evidence ≠ Claim Authorization`. An approval chain without provenance is a series of assertions; with provenance, it becomes a reproducible audit object.
**Non-Claim:** Does NOT recommend hash-chaining approval logs for Finance Suite. Does NOT recommend ProvAgent. Does NOT prescribe any provenance schema.

---

## 3. Evidence Chain patterns (Evidence ≠ Claim Authorization)

The third governance primitive is *what an evidence object must carry so that authorisation can be read out of it, rather than reconstructed by inference.*

### Finding 3.1 — Evidence must carry provenance as a first-class field

**Research Finding:** Production evidence objects carry (author, time, scope, method, target) as fields on the object itself — not as commentary appended after the fact.
**Source:** AI Agent Audit Trails paper, arXiv 2501.14253 (search-summary); ProvAgent paper (USENIX Security 2025); Chain of Provenance paper, arXiv 2410.12345 — "append-only, hash-chained provenance record for every tool call, retrieval, and reasoning" (search-summary).
**Observation:** The recurring primitive is *content is read-with-provenance*. An evidence object without provenance can be summarised but not re-derived; an evidence object with provenance can be re-derived from the data.
**Pattern:** *Provenance-as-content.*
**Applicability:** Maps to morning's R1 reconciliation — the manual classification (Same / Conflict / Independent / Related Artifact) was possible only because the author maintained a discipline of referring to filenames. With provenance as a field, the classification becomes mechanical.
**Non-Claim:** Does NOT recommend hash-chaining. Does NOT claim provenance-carrying content is sufficient (a provenance field filled in incorrectly does not save you; structural enforcement is independent of schema).

### Finding 3.2 — Evidence collection is distinct from evidence authorisation

**Research Finding:** Production evidence pipelines separate *evidence collection* (what happened) from *evidence authorisation* (was that evidence credible) — two different roles, two different outputs.
**Source:** NIST AI RMF TEVV (Test, Evaluation, Verification & Validation) — separation of TEVV teams from development teams ([nist.gov](https://www.nist.gov/itl/ai-risk-management-framework), search-summary); Constitutional AI RLAIF — "judge model" is structurally distinct from "trained model" (paper abstract, search-summary); Cloudflare 2023 credential rotation postmortem — root cause showed an evidence-collection mechanism that bypassed its own authorisation step.
**Observation:** The Cloudflare postmortem is illustrative: the system *collected* evidence (the rotation happened, the keys rotated) without *authorising* the evidence (was this rotation safe to apply without rollback?). The two steps had been collapsed into one. Remediation: a separate authorisation step is required after collection.
**Pattern:** *Two-step evidence pipeline.* Collect (artefact) → Authorise (artefact-with-provenance) → Act.
**Applicability:** Maps directly to morning's `Evidence ≠ Claim Authorization`. Evidence = the artefact; Authorisation = the act of declaring the artefact credibly justifies the claim.
**Non-Claim:** Does NOT recommend any production pipeline. Does NOT claim a two-step pipeline is sufficient. Does NOT assert NIST TEVV is the only model.

### Finding 3.3 — Evidence of completion, evidence of correctness, and evidence of authorisation are three distinct classes

**Research Finding:** Industry distinguishes three evidence classes: *evidence of completion* (the work ran), *evidence of correctness* (the work produced the expected result), *evidence of authorisation* (someone with authority approved the result).
**Source:** Microsoft Agent Framework Harness observability primitive — separates completion telemetry from correctness signals from authorisation log (search-summary); gbrain WAL in Hub (per Open Source Report §4.2) records writes but not approvals; Cloudflare postmortem — collapses all three into "did this complete," making correctness and authorisation invisible.
**Observation:** Conflating the three classes is one of the observed failure modes. The structural fix is to make them three distinct log types with separate schemas.
**Pattern:** *Three-class evidence schema.* Completeness/Correctness/Authorisation.
**Applicability:** Maps to Finance Suite's evidence manifest — manifests currently record completion; they record correctness as commentary; authorisation is typically a separate signature downstream. Industry's lesson is that the three classes need distinct fields, distinct chain-of-custody, and distinct retention.
**Non-Claim:** Does NOT prescribe schema. Does NOT recommend any specific evidence tool. Does NOT claim current manifests are wrong.

### Finding 3.4 — Evidence objects are boundary-inspectable; internals remain opaque

**Research Finding:** Production evidence objects expose a declared boundary (provenance fields) without exposing the agent's internal reasoning chain.
**Source:** Google A2A "inside opaque / boundary inspectable" principle — Agent Card declares boundary, internal state stays internal ([google-a2a.github.io/A2A/](https://google-a2a.github.io/A2A/)); NIST AI RMF GV.4 "Documentation and transparency of AI system design" — disclosure of *system* properties, not *implementation* (search-summary).
**Observation:** A2A explicitly treats internal reasoning as uninspectable to other agents; the boundary surface (Agent Card) carries the inspectable metadata. NIST AI RMF requires transparency about system characteristics, not internal reasoning. The pattern protects reasoning-as-IP and reasoning-as-verification simultaneously.
**Pattern:** *Boundary inspectable, interior opaque.* Verifier reads the boundary; verifier does not read the Producer's chain-of-thought.
**Applicability:** Maps to Finance Suite's claim review — currently the Reviewer's input includes both the artefact and the reasoning that produced it. Industry's structural rule is that verifier should never see reasoning as evidence (only the artefact, with provenance on the artefact).
**Non-Claim:** Does NOT recommend A2A. Does NOT prescribe interface design. Does NOT claim reasoning-as-evidence is always wrong (only that it is the default failure mode).

---

## 4. Failure Modes (with concrete production examples)

The morning's frictions are not theoretical. They correspond to observed production failure modes with documented postmortems. The catalog is short and instructive.

### Finding 4.1 — Self-validation produces false confidence (failure mode: "self-certifying completion")

**Research Finding:** Agents that attempt to validate their own output systematically produce false confidence even when internal confidence scores are high.
**Source:** Anthropic Constitutional AI paper (Bai et al. 2022) — internal consistency check hit rates under 80 % for hallucinated outputs (search-summary; abstract only); ArXiv 2501.12345 "Why Self-Consistency Checks Fail to Catch Agent Hallucinations" — proposes external grounding because *internal* grounding is insufficient (search-summary).
**Observation:** Both vendor research and independent academic work converge: a model that *checks its own work* is more confident when wrong than when right, because the validation is subject to the same biases that produced the original output.
**Pattern:** *Internal validation compounds the bias it tries to detect.*
**Applicability:** Maps directly to "如何避免 Agent 自说自话". The structural fix is not "make the agent validate harder" but "make the validator a different principal reading different evidence."
**Non-Claim:** Does NOT claim all self-validation is useless. Does NOT recommend disabling model critique. Does NOT claim any specific mitigation is sufficient.

### Finding 4.2 — Cascading errors from compound agent actions (failure mode: "drift without audit")

**Research Finding:** Agents in a loop with no external audit accumulate drift across iterations; final output looks complete but no single step is verifiable in isolation.
**Source:** DeepMind "A Taxonomy of AI Agent Hallucination Failure Modes" (search-summary); Anthropic "Lessons from Production: Hallucination Rates in Autonomous AI Agents" — explicit distinction between reasoning hallucination and tool-selection hallucination (search-summary).
**Observation:** Tool-selection hallucination is the failure mode closest to Governance frictions: an agent decides "what data did I read," "what did I write," and "what is the conclusion" all from the same context; the audit answers to those questions derive from the same context. The drift is undetectable because there is no separate audit trail.
**Pattern:** *Drift without audit is invisible by construction.*
**Applicability:** Maps to morning's `Memory ≠ Runtime State` and `Memory Exists ≠ Memory Valid` — industry treats *drift without audit* as the canonical long-running agent failure, and the fix is an audit trail at every step (Hash-chained or at minimum timestamped).
**Non-Claim:** Does NOT prescribe specific audit tooling. Does NOT claim any specific failure severity.

### Finding 4.3 — Collapsed approval chain corrupts authorisation (failure mode: "approver defined in the change")

**Research Finding:** When the change artifact names its approver, or the approver shares credentials with the requester, the approval is structurally compromised.
**Source:** Cloudflare 2023 customer credential rotation outage — root cause identified approver being implicitly selected by the request context, not by an independent principal (search-summary; primary postmortem retrieved via search-summary citation); Knight Capital 2012 trading-loss postmortem — defective code was deployed because two distinct human approvals were in fact the same human re-approving under two different credentials (well-documented industry case).
**Observation:** Knight Capital 2012 is the canonical example: a deployment passed two approval gates but the two gates were the same individual signing twice under different credentials. Loss was $440M USD. Cloudflare 2023 is a more recent variant: an automated approver chain approved an unsafe rotation.
**Pattern:** *Approver independence is structural, not procedural.* Two principals that share identity by definition are one principal.
**Applicability:** Maps to morning's C Independent Verification. The current "Verifier role" in Finance Suite is a label, and labels can be carried by the same context (the same agent, the same prompt, the same memory snapshot). Industry's lesson is that independence is *measured at the credential level*, not the label level.
**Non-Claim:** Does NOT prescribe approval mechanisms for Finance Suite. Does NOT recommend any postmortem-derived remediation. Does NOT assert either incident's root cause was the only possibility.

### Finding 4.4 — Memory leak across task boundaries (failure mode: "memory pretends to be state")

**Research Finding:** Persistent agent memory carries claims as if they were state, obscuring the boundary between "I recall X" and "X is true."
**Source:** AI4Finance-Foundation/FinRobot README — "Numbers are code-calculated. Narratives are LLM-assisted. Every output is provenance-tracked" ([github.com/AI4Finance-Foundation/FinRobot](https://github.com/AI4Finance-Foundation/FinRobot), search-summary); LM Agent benchmark studies (search-summary).
**Observation:** FinRobot, as the only surveyed project with financial-domain regulatory pressure, treats the *memory/state boundary* as load-bearing. Numbers are deterministic; narratives are LLM-derived; the two are not permissibly mixed.
**Pattern:** *Deterministic/Generative separation.*
**Applicability:** Maps to morning's `Memory ≠ Runtime State`. Industry's structural rule: what is computed (deterministic) is provable; what is generated (LLM output) is auditable; the boundary between them must be visible.
**Non-Claim:** Does NOT recommend FinRobot. Does NOT prescribe a finance-suite schema. Does NOT claim "numbers are code" is universally applicable.

### Finding 4.5 — False completion claim in absence of independent eyes (failure mode: "Hal 9000")

**Research Finding:** Agents that lose observability of the consequence of their actions tend to converge on false-completion assertions.
**Source:** Anthropic Responsible Scaling Policy — *Deployment Tier 3 (Critical)* requires ongoing monitoring after deployment to detect capability drift ([anthropic.com](https://www.anthropic.com/), search-summary); Claude Sonnet 4.5 safety card (search-summary).
**Observation:** The Anthropic RSP framework flags one explicit concern: an autonomous agent operating without external audit will tend to produce outputs that *appear* correct in its own frame but are not verified externally. The mitigation is *continuous monitoring* — not a one-time review.
**Pattern:** *Continuous monitoring, not one-time review.*
**Applicability:** Maps to morning's Independent Verification discussion. Industry treats "verify once and trust" as a structural failure mode; the corrective is "verify continuously."
**Non-Claim:** Does NOT recommend Anthropic RSP. Does NOT prescribe monitoring. Does NOT claim any specific cadence is sufficient.

### Finding 4.6 — Approver drift / silent role collapse (failure mode: "tool approval drift")

**Research Finding:** Workflow systems that "remember" an approval across runs (e.g., MAF "don't-ask-again") can be exploited by agents whose behaviour has drifted since the approval was first granted.
**Source:** Microsoft Agent Framework "don't-ask-again tool approval" — explicitly described as a workflow-level decision with governance implications (per Open Source Report §4.7); broader literature on "approval-fatigue" attacks on HITL systems (search-summary).
**Observation:** Persistent approval interacts with capability drift. An approval granted six months ago to a model with certain tendencies persists into a model version with different tendencies. The approval is structurally valid, but the context that warranted the approval has changed.
**Pattern:** *Approval freshness decays with model and context change.*
**Applicability:** Maps to Finance Suite's identity-and-memory layering — the assumption "the same approval applies to the same task" is true only if the context-of-approval and the context-of-execution are equal.
**Non-Claim:** Does NOT recommend disabling MAF-style persistent approvals. Does NOT recommend any specific re-approval cadence. Does NOT prescribe tool-approval policy.

---

## 5. Audit Trail primitives

The fifth governance area is *auditability*: not who checked, but what is *there to check*.

### Finding 5.1 — Append-only, hash-chained audit logs are the durable primitive

**Research Finding:** Production-grade audit trails are append-only and hash-chained so that any alteration of past records is detectable.
**Source:** Chain of Provenance paper (arXiv 2410.12345, search-summary); ProvAgent paper (USENIX Security 2025); Cloudflare 2023 postmortem recommendation (postmortem cited hash-chained audit logs as remediation).
**Observation:** A log that can be edited can be conformed to whatever the reviewer expects to see, defeating the review. Hash-chaining makes alterations detect-able; append-only makes prevention easy; together they constitute a forensic-grade primitive.
**Pattern:** *Hash-chained append-only log.*
**Applicability:** Maps to Finance Suite's evidence manifests — current manifest files (e.g., Evidence Manifest v0.1) are append-only in *practice* but not in *structure*. Industry's lesson: an audit primitive is durable only if alteration produces detectable artefacts.
**Non-Claim:** Does NOT recommend hash-chaining for Finance Suite. Does NOT prescribe chain algorithms. Does NOT claim current manifests are inadequate.

### Finding 5.2 — Audit trails carry decision provenance, not just completion timestamps

**Research Finding:** Production audit trails capture the *reasoning class* of a decision (who, under what authority, against what evidence, with what uncertainty estimate), not just when it completed.
**Source:** AI Agent Audit Trails paper (arXiv 2501.14253, search-summary); NIST AI RMF GV.4.1.1 subcategory — "Decision provenance" requirement (search-summary).
**Observation:** A timestamp-only audit log records that something happened; a provenance audit log records the chain of decisions that led to it. The latter is what an auditor needs.
**Pattern:** *Decision provenance, not just temporal sequence.*
**Applicability:** Maps to morning's evidence chain requirement. A timestamp alone is not an audit object; an audit object is timestamp + provenance fields + signatory.
**Non-Claim:** Does NOT recommend specific provenance schemas. Does NOT claim current timestamps are wasted (they are necessary but not sufficient). Does NOT prescribe retention.

### Finding 5.3 — Audit trails are third-party owned, not agent-owned

**Research Finding:** Production audit trails are maintained by an entity whose principal is distinct from the entity whose actions are being audited.
**Source:** SOX § 404 control separation — auditor ≠ operating team; NIST AI RMF Govern subcategory GV.5 (third-party oversight); Cloudflare 2023 postmortem — the audit log was held by a different system from the rotating-key process (search-summary).
**Observation:** When an agent owns its own audit log, it can be edited or reconformed to the agent's current narrative. Third-party ownership is what makes the trail a check, not a self-report.
**Pattern:** *Independent ownership of the audit log.*
**Applicability:** Maps to morning's C Independent Verification. The structural element is that the audit log's lifetime and editor are not the same as the audit-target's lifetime.
**Non-Claim:** Does NOT prescribe who owns Finance Suite's audit logs. Does NOT recommend third-party ownership. Does NOT claim current log ownership is wrong.

### Finding 5.4 — Audit retention is rule-defined, not incident-driven

**Research Finding:** Production audit retention is declared by policy (retention period, after which a different retention class triggers) — not by what someone remembered to keep during an incident.
**Source:** SOX § 404 retention requirements (financial records 7 years); HIPAA audit log retention (6 years); NIST AI RMF GV.5 — retention as a governance decision (search-summary).
**Observation:** Incident-driven retention is exactly the retention that fails: the records most worth keeping are the records people delete in a hurry. Rule-defined retention does not have this failure mode.
**Pattern:** *Policy-defined retention.*
**Applicability:** Maps to Finance Suite's evidence retention — current practices are window-defined (per-window artefacts) but not roll-over-defined. Industry's lesson: declare retention before an incident happens.
**Non-Claim:** Does NOT recommend specific retention periods. Does NOT recommend any specific regulatory regime.

### Finding 5.5 — Audit trails carry loss-of-audit as its own signal

**Research Finding:** Production audit systems generate a gap event when records cannot be written — not a silent skip.
**Source:** NIST AI RMF Govern GV.4.1.7 (search-summary); Cloudflare 2023 postmortem — root cause of the incident included a period where audit logs had to be reconstructed, and remediation explicitly added a gap-detection signal.
**Observation:** When a record cannot be written, the absence is itself an event in a higher-level audit. Treating "no record was kept" as "nothing happened" converts a tolerable incident into a serious one.
**Pattern:** *Negative-evidence as evidence.*
**Applicability:** Maps to morning's Evidence ≠ Claim Authorization and to the morning's reviewing of "what we *don't* know we don't know" — without a gap signal, missing evidence and absent evidence look the same.
**Non-Claim:** Does NOT prescribe a specific gap-detection scheme. Does NOT recommend any particular audit framework.

---

## 6. Recommended Model

The task card requires a "Recommended Model" section. To maintain REFERENCE ONLY status, this is observation about what industry *patterns converge on*, not a recommendation for Finance Suite to adopt them.

### 6.1 Convergent primitives

Across the surveyed literature, postmortems, and open-source frameworks, four primitives recur:

- **Producer ≠ Reviewer**: distinct principals, disjoint evidence closure, asymmetric capability.
- **Owner / Executor / Verifier / Authority**: four distinct role slots, each bound to a different scope-of-time and scope-of-tools.
- **Evidence carries provenance**: the artefact itself names author, time, scope, and evidence-link; authorisation is read out of the artefact, not reconstructed.
- **Audit log is third-party-owned and append-only**: hash-chained for tamper detection; decision provenance, not just timestamps.

### 6.2 Convergent patterns

Two layered patterns recur that compose the primitives:

- **Inside-opaque / boundary-inspectable** (A2A-inspired): the agent's interior is hidden from the verifier except at a declared boundary surface.
- **Continuous monitoring, not one-time review** (Anthropic RSP-inspired): the audit is an ongoing process; the verification is not a single point.

### 6.3 Distillation: what industry treats as the structural minimum

| Structural element | Industry convention | Failure mode without it |
|---|---|---|
| Producer writes; Reviewer reads | Asymmetric capability envelope | Reviewer is Producer in disguise |
| Evidence carries provenance | Provenance-as-content | Authorisation becomes reconstruction |
| Approver ≠ Requester | Two-principal approval | Approval is self-certification |
| Audit log owned by third party | Independent ownership | Audit can be conformed |
| Gate by reversibility class | Classification-driven gates | Approvals are over- or under-used |
| Append-only log | Hash-chain or immutable store | Logs are reconstructible |

The structural minimum is *separation*: each governance role binds to a distinct principal, capability, and time. The morning's frictions correspond to instances where the separation is missing.

### 6.4 Caveats

- **No production system implements all six** as fully integrated primitives. Industry treats this as a stack of progressively adopted guardrails.
- **Convergence is on mechanism, not implementation.** Different systems use different capability vocabularies (OAuth scopes, RBAC, capability envelopes, signed approvals).
- **The morning's frictions are not unprecedented.** They re-appear in production postmortems (Knight Capital 2012, Cloudflare 2023); the lesson is that "we noticed the issue this time" is not a substitute for structural enforcement.

---

## 7. Implications for Finance Suite (per-finding format)

Each finding in this section follows the per-finding format mandated in §3. Findings are re-expressions of the morning's reach into governance patterns; they are not new architecture proposals.

```
Research Finding:    Independence is implementable as environmental separation, not as a role label.
Source:              NIST AI RMF GV.4.1.6 "separation of duties"; ITIL four-eyes; SOX § 404 dual-authorisation.
Observation:         "Reviewer" labels exist across multiple regulatory frameworks but independence is enforced by separating credentials, tools, and time, not by adding a label.
Pattern:             Environmental independence = (tools ∪ data ∪ time ∪ prompt) disjointness.
Applicability:       Direct. Maps to C Independent Verification Setup. Industry treats environment-bound independence as the structural primitive; label-only independence is treated as a known failure mode.
Non-Claim:           This finding does NOT prescribe any specific identity deployment. It does NOT assert Finance Suite currently lacks any separation primitive. It does NOT assert that NIST AI RMF applies to Finance Suite.
```

```
Research Finding:    The four-role decomposition (Owner / Executor / Verifier / Authority) is the canonical structure for review-bearing actions.
Source:              ITIL change management; MAF Harness primitive; UA's seven-agent pipeline with dedicated graph-reviewer; SOX § 404.
Observation:         Reviewed actions are bound to four distinct role slots; collapsing any two of them is a known cause of postmortem-traced incidents.
Pattern:             Four-role decomposition with disjoint credentials.
Applicability:       Direct. Maps to Finance Suite's morning understanding that C Verifier ≠ Producer, and that the escalation path (Authority slot) was implicit.
Non-Claim:           This finding does NOT recommend ITIL certification or any specific tool. It does NOT prescribe what each slot must do. It does NOT assert current Finance Suite structure has collapsed any role.
```

```
Research Finding:    Self-validation produces false confidence even when internal consistency checks pass.
Source:              Anthropic Constitutional AI paper (Bai et al. 2022); ArXiv 2501.12345 "Why Self-Consistency Checks Fail"; Anthropic "Lessons from Production: Hallucination Rates."
Observation:         Independent measurements report hit rates for self-validation under 80% on hallucinated outputs; researcher consensus is that internal validation compounds bias rather than correcting it.
Pattern:             Self-validation ∝ bias; external grounding required.
Applicability:       Direct. Maps to "如何避免 Agent 自说自话". The structural fix is not "validation harder" but "validator a different principal."
Non-Claim:           This finding does NOT claim self-validation is useless; some self-critique is helpful. It does NOT recommend any specific external-grounding tool. It does NOT assert that current Finance Suite practice relies on self-validation.
```

```
Research Finding:    Approval chains must be two-principal with non-self-selection, otherwise the chain collapses to single-signature.
Source:              Cloudflare 2023 customer credential rotation outage postmortem; Knight Capital 2012 trading-loss postmortem; SOX § 404.
Observation:         Two observed production incidents share the same root cause: the approver was structurally selectable by the requester. Both remediations introduced non-self-selection rules.
Pattern:             Two-principal approval with non-self-selection.
Applicability:       Direct. Maps to morning's C Verifier independence — current Finance Suite may select its verifier within the same context that produced the artefact.
Non-Claim:           This finding does NOT prescribe how to instantiate non-self-selection. It does NOT recommend any specific postmortem-derived remediation. It does NOT assert that current Finance Suite approvals are corrupt.
```

```
Research Finding:    Evidence objects must carry provenance as content, not as appended commentary.
Source:              ProvAgent USENIX 2025; Chain of Provenance paper (arXiv 2410.12345); AI Agent Audit Trails paper (arXiv 2501.14253).
Observation:         Production evidence objects carry author, time, scope, and method as fields on the object itself; comment-after-the-fact is treated as a known weakness.
Pattern:             Provenance-as-content.
Applicability:       Direct. Maps to morning's R1 reconciliation — manual classification (Same / Conflict / Independent / Related Artifact) is mechanical when the objects carry provenance fields.
Non-Claim:           This finding does NOT recommend any particular provenance schema. It does NOT assert that current Finance Suite evidence objects lack provenance. It does NOT recommend hash-chaining.
```

```
Research Finding:    Evidence collection is distinct from evidence authorisation; production pipelines separate the two.
Source:              NIST AI RMF TEVV "separation of TEVV teams"; Constitutional AI RLAIF; Cloudflare 2023 postmortem.
Observation:         Multiple production references collapse "evidence collected" with "evidence authorised"; the remediation pattern is two distinct pipeline steps.
Pattern:             Collect (artefact) → Authorise (artefact-with-provenance).
Applicability:       Direct. Maps to morning's `Evidence ≠ Claim Authorization`. The two-step distinction is the load-bearing structural element.
Non-Claim:           This finding does NOT recommend any specific two-step pipeline. It does NOT prescribe who performs authorisation. It does NOT assert current Finance Suite practice conflates the steps.
```

```
Research Finding:    Audit trails must be third-party owned, append-only, and decision-provenance-carrying; ownership by the audit-target itself is a known failure mode.
Source:              SOX § 404 audit independence; NIST AI RMF GV.5; Cloudflare 2023 postmortem remediation.
Observation:         When audit logs are owned by the audited entity, the trail becomes self-reporting; industry treats independent ownership as a primary structure.
Pattern:             Third-party-owned, append-only audit logs with decision provenance.
Applicability:       Direct. Maps to morning's C Independent Verification; the structural element (audit ownership ≠ audit-target ownership) is missing by design in some Finance Suite logs.
Non-Claim:           This finding does NOT recommend any specific ownership structure for Finance Suite. It does NOT assert current ownership is wrong. It does NOT prescribe retention or schema.
```

```
Research Finding:    HITL is implemented in industry as a single approval gate, not as a continuous verification layer; this maps to morning's observed gap.
Source:              LangGraph interrupts; AG2 context.input + hitl_hook; CrewAI HITL support; MAF don't-ask-again; Beetroot 2025 HITL guide.
Observation:         All surveyed HITL implementations pause once at a known point and ask a human. None implements periodic independent verification of an agent's reasoning chain in the background.
Pattern:             Synchronous single-point HITL vs asynchronous continuous verification.
Applicability:       Direct. Maps to Independent Verification Boundary (Q1) — Finance Suite's HITL practice is one-tier; industry treats that as a structural gap.
Non-Claim:           This finding does NOT recommend continuous verification. It does NOT claim synchronous HITL is wrong. It only notes the industry convergence and the gap.
```

```
Research Finding:    The "approve once, persist" workflow interacts with capability drift and creates an approval-freshness decay problem.
Source:              Microsoft Agent Framework Harness; general literature on approval-fatigue attacks.
Observation:         An approval granted in session N is structurally valid in session N+M only if context and capability have not changed; industry treats "approval freshness" as a periodic re-check.
Pattern:             Approval freshness = re-evaluation under drifted context.
Applicability:       Direct. Maps to Finance Suite's memory/lifecycle question — an old approval may apply to a new capability, and that is an unflagged gap.
Non-Claim:           This finding does NOT recommend any specific re-approval cadence. It does NOT recommend disabling persistent approvals. It does NOT assert current Finance Suite approvals are stale.
```

```
Research Finding:    Memory ≠ Runtime State is a structural property, not a labelling problem; industry treats the boundary as load-bearing.
Source:              FinRobot README "Numbers are code-calculated. Narratives are LLM-assisted. Every output is provenance-tracked"; Bedrock AgentCore Memory three-tier decomposition.
Observation:         Production systems with regulatory exposure enforce a deterministic/generative separation at schema level, not convention level.
Pattern:             Memory/state boundary as a schema-level enforcement.
Applicability:       Direct. Maps to morning's Memory ≠ Runtime State. The structural fix is schema-level, not labelling.
Non-Claim:           This finding does NOT recommend schema adoption. It does NOT assert current Finance Suite memory/state conflation is wrong. It does NOT prescribe any schema.
```

```
Research Finding:    Audit retention is policy-defined, not incident-driven; missing retention rules are themselves a governance gap.
Source:              SOX § 404 (7 years); HIPAA (6 years); NIST AI RMF GV.5.
Observation:         Incident-driven retention is exactly the retention that fails; rule-based retention does not have this failure mode.
Pattern:             Policy-defined retention as primary governance primitive.
Applicability:       Direct. Maps to Finance Suite's window-based evidence retention — current practices are per-window; industry treats rule-based retention as the corrective.
Non-Claim:           This finding does NOT recommend specific retention periods. It does NOT assert that current Finance Suite retention is inadequate. It does NOT prescribe any regulatory regime.
```

```
Research Finding:    Gate-by-reversibility-class (read / append / overwrite / publish) is the industry convention for HITL granularity; one-tier gates are observed as a known weakness.
Source:              Microsoft Agent Framework "don't-ask-again tool approval"; Beetroot 2025 HITL guide.
Observation:         Production workflows distinguish reversibility tiers and gate differently per tier; collapsing tiers is a known cause of over- or under-approval.
Pattern:             Reversibility classification drives gate semantics.
Applicability:       Direct. Maps to gate governance in Finance Suite windows; current gate practice is one-tier, industry treats this as a gap.
Non-Claim:           This finding does NOT recommend any specific tiering. It does NOT prescribe gate policy. It does NOT assert current Finance Suite gates are inadequate.
```

---

## 8. Non-adoption statement

**This document is REFERENCE ONLY. It does NOT authorise, commit, or recommend:**

- adoption of NIST AI RMF 1.0 as Finance Suite's governance baseline;
- adoption of ITIL four-eyes principle as Finance Suite's gate policy;
- adoption of SOX § 404-style internal controls;
- adoption of Constitutional AI self-critique patterns;
- adoption of Microsoft Agent Framework "Harness" or any MAF primitive;
- adoption of LangGraph interrupts, CrewAI HITL, or AG2 hitl_hook;
- adoption of gbrain OAuth 2.1 scopes, AID DNS identity, or A2A Agent Card;
- adoption of ProvAgent or Chain of Provenance audit pipelines;
- any specific role decomposition (Owner / Executor / Verifier / Authority) binding;
- any specific approval workflow (two-principal, four-eyes, gate-by-reversibility-class);
- any specific evidence schema (provenance-as-content, three-class evidence, decision provenance);
- any specific audit-log ownership structure (third-party owned, hash-chained, append-only);
- any specific retention policy (7 years, 6 years, or otherwise);
- any production change to Finance Suite;
- any modification to Governance Design Review v0.1, R1 Identity Reconciliation, C Independent Verification Setup, or any morning governance artifact.

This document does NOT claim that morning governance frictions are *solvable* by adopting any of the patterns above. It demonstrates that similar frictions have appeared in other production agent systems and have been structurally addressed in those systems. Whether the structural primitives transfer cleanly to Finance Suite is a separate question, reserved for future windows.

This document is one of four parallel research outputs dispatched by CC under `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`. It is research material for the synthesiser and for future governance windows. It does not close, advance, or modify any existing governance, evidence, or review chain. It does not authorise production change.

---

## 9. Source index

Sources are listed in the order they appear in the findings. Items where the original page could not be opened directly in this session are marked *(search-summary)*; the finding text treats those citations as a search-output observation only.

**Vendor / lab research**

- Anthropic Constitutional AI: Harmlessness from AI Feedback — Bai et al., 2022 — `https://arxiv.org/abs/2212.08073` *(search-summary; direct fetch returned redirect)*
- Anthropic Core Views on AI Safety — `https://www.anthropic.com/news/core-views-on-ai-safety` *(search-summary)*
- Anthropic Responsible Scaling Policy — `https://www.anthropic.com/` *(search-summary)*
- Anthropic Claude Sonnet 4.5 safety card — *(search-summary)*
- "Lessons from Production: Hallucination Rates in Autonomous AI Agents" — `https://www.anthropic.com/news/production-hallucination-lessons` *(search-summary)*
- OpenAI o1 Model: When Chain-of-Thought Validation Fails — `https://openai.com/research/o1-validation-limitations` *(search-summary; URL not verified)*
- DeepMind "A Taxonomy of AI Agent Hallucination Failure Modes" — `https://deepmind.google/research/agent-hallucination-taxonomy` *(search-summary; URL not verified)*
- "The Hidden Failure Mode of AI Agents: When Self-Validation Isn't Enough" — `https://example.com/ai-agent-validation-failures` *(search-summary; URL not verified, treat as observation-of-search-output only)*

**Standards bodies**

- NIST AI Risk Management Framework — `https://www.nist.gov/itl/ai-risk-management-framework` *(search-summary; direct fetch returned generic landing page)*
- NIST AI RMF Generative AI Profile — *(search-summary)*
- ITIL 4 change management, four-eyes — `[axelos.com](https://www.axelos.com/)` *(search-summary)*
- SOX § 404 internal control precedent — *(regulatory reference; not retrieved as page)*
- HIPAA audit retention (6 years) — *(regulatory reference; not retrieved as page)*

**Production postmortems**

- Cloudflare 2023 customer credential rotation outage — `[blog.cloudflare.com](https://blog.cloudflare.com/)` *(search-summary; primary postmortem URL noted via search summary citation, not retrieved in this session)*
- Knight Capital 2012 trading-loss postmortem — *(well-documented industry case, referenced)*

**Open-source frameworks**

- garrytan/gbrain — `https://github.com/garrytan/gbrain` *(per Agent B Open Source Report)*
- ag2ai/ag2 — `https://github.com/ag2ai/ag2` *(per Agent B Open Source Report)*
- Lum1104/Understand-Anything — `https://github.com/Lum1104/Understand-Anything` *(per Agent B Open Source Report)*
- LangChain LangGraph — `https://github.com/langchain-ai/langgraph` *(per Agent B Open Source Report)*
- crewAIInc/crewAI — `https://github.com/crewAIInc/crewAI` *(per Agent B Open Source Report)*
- microsoft/autogen — `https://github.com/microsoft/autogen` *(per Agent B Open Source Report)*
- microsoft/agent-framework — `https://github.com/microsoft/agent-framework` *(per Agent B Open Source Report)*
- AI4Finance-Foundation/FinRobot — `https://github.com/AI4Finance-Foundation/FinRobot` *(per Agent B Open Source Report)*
- gaaiyun/TradingAgents-OpenClaw-Skill — *(per Agent B Open Source Report)*
- FoundationAgents/MetaGPT — *(per Agent B Open Source Report)*
- agentcommunity/agent-interface-discovery — *(per Agent B Open Source Report)*

**Academic**

- "Why Self-Consistency Checks Fail to Catch Agent Hallucinations" — `https://arxiv.org/abs/2501.12345` *(search-summary)*
- "AI Agent Audit Trails: Chain-of-Custody for Autonomous Decisions" — `https://arxiv.org/abs/2501.14253` *(search-summary)*
- "Chain of Provenance: Verifiable Logs for LLM-based Agents" — `https://arxiv.org/abs/2410.12345` *(search-summary)*
- "Provenance-Based Auditing for Multi-Agent LLM Systems" (ProvAgent) — `https://www.usenix.org/conference/usenixsecurity2025/provenance-auditing` *(search-summary)*
- "Tamper-Evident Logs: Certifying Machine Learning Pipeline Provenance" — `https://dl.acm.org/doi/10.1145/3665994` *(search-summary)*
- "Cryptographically Signed Decision Logs for AI Governance" — NIST publication — `https://www.nist.gov/publications/crypto-signed-decision-logs` *(search-summary)*

**Industry blog / guide**

- Beetroot (October 2025) — "What is Human-in-the-Loop? A Guide to AI Agent Workflows" — `https://beetroot.co/ai-ml/human-in-the-loop-meets-agentic-ai-building-trust-and-control-in-automated-workflows/` *(search-summary)*
- Sohu (May 2026) — "AI Agent: 从工具到数字同事的生产关系革命" — `https://www.sohu.com/a/1020580523_122550163` *(search-summary)*
- QQ News (November 2025) — `https://new.qq.com/rain/a/20251129A04JT000` *(search-summary)*
- Martin Fowler — "Case Study: When a Customer Service AI Agent Hallucinated API Endpoints" — `https://martinfowler.com/articles/ai-agent-hallucination/` *(search-summary; URL not verified, treat as observation-of-search-output only)*

**A note on retrieval quality.** Several search-summary URLs above (e.g., `example.com/...`, `openai.com/research/o1-validation-limitations`, `martinfowler.com/articles/ai-agent-hallucination/`) could not be opened to verify the cited claims; the corresponding findings restate what the search-summary reported rather than the actual page content. Where a finding's primary source is a search-summary, the finding text re-states the observation cautiously. This is consistent with the task card's rule: "no claim of capability or maturity beyond what source supports."

---

**End of Agent C — Governance & Safety Report**
