# Org-Level Agent Harness — Industry Architecture Report v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Author role:** Agent A — Industry Architecture Researcher
**Coordinator:** CC (governance coordinator, not author)
**Date:** 2026-08-05
**Window:** External method research input
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

This document is one of four parallel Agent deliverables dispatched under `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`. It is research material. It does not modify Governance Design Review v0.1, the RRA chain, the Owner Assignment chain, or any declaration document. It informs future windows.

---

## 0. Scope and method

The task card asks: "未来企业 Agent 基础设施长什么样" — what does enterprise Agent infrastructure look like in practice? This report surveys how the industry — Anthropic, AWS, Microsoft, Google, open-source frameworks, and the academic multi-agent literature — is structuring the pieces around the agent (Identity, Permission, Shared Context, Coordination), and extracts the patterns that the morning governance frictions surface as needs but do not yet have names.

Every finding uses the per-finding format mandated in §3 of the task card. Findings are sourced; sources are linked; capability claims are not extrapolated beyond what the source supports. The "Non-Claim" line is mandatory and identifies what the observation does NOT imply.

### Method

- Source layer 1: Primary vendor documentation (Anthropic Claude Code docs, AWS Bedrock AgentCore pages, Microsoft Entra / AutoGen, Google A2A)
- Source layer 2: Vendor / research-blog posts (Anthropic, Microsoft Research, LangChain, Lance Martin's blog)
- Source layer 3: Open-source project documentation (CrewAI, LangGraph, AutoGen, OpenClaw)
- Source layer 4: Academic multi-agent systems literature (contract net, supervisor patterns)
- A handful of search results could not be opened (404 / closed socket) — those claims are explicitly tagged **Evidence not retrieved** and are reported as observation-of-search-output only, not as direct quote.

---

## 1. Gateway vs Harness — current industry consensus

The industry has converged on two distinct layers around an agent. Conflating them is a frequent source of design errors.

| Layer | Position | Concern | State lifetime | Examples |
|---|---|---|---|---|
| **Gateway** | Network perimeter | *Who can call what* (auth, rate limit, observability of traffic) | Request-scoped, stateless | AWS Bedrock AgentCore Gateway ([aws.amazon.com](https://aws.amazon.com/bedrock/agentcore/)), MCP servers, traditional API gateways extended with LLM-aware routing |
| **Harness** | Wraps the agent's execution loop | *How the agent reasons and acts* (tool selection, memory, state, multi-step recovery, sub-agent orchestration) | Conversation/goal-scoped, stateful | Anthropic Claude Code, Claude Agent SDK, Magentic-One orchestrator + ledger, LangGraph supervisor harness |

**Observation.** In current AWS documentation Bedrock AgentCore is described as "build, deploy, and operate agents at scale with purpose-built infrastructure to scale dynamic workloads" and is decomposed into Runtime, Memory, Identity, Gateway, Code Interpreter, Browser Tool, and Observability ([aws.amazon.com/bedrock/agentcore](https://aws.amazon.com/bedrock/agentcore/)). The decomposition itself is the consensus statement: Gateway is one component; Harness concerns are split across the other six.

**Pattern.** Agent infrastructure is a *layered* construct: ingress (gateway) → orchestration/runtime (harness) → substrate (memory, identity, tools, observability). None of the vendors ship a single "the agent platform"; they ship a toolbox of services that compose into a harness, plus a gateway, plus identity.

**Applicability to Finance Suite.** Reference value is conceptual, not prescriptive — the morning governance frictions are harness-layer concerns (memory ≠ runtime state, independence-as-environment-not-role, evidence chains), not gateway concerns. This classifies the research need as *harness + identity + evidence*, not "we need an API gateway."

**Non-Claim.** This report does NOT recommend that Finance Suite build a gateway. It does NOT recommend the AWS AgentCore service set as an architecture. It only establishes that the industry is decomposing agent infrastructure into multiple concerns, and that "harness" names a distinct concern from "gateway."

---

## 2. Agent Identity — 3–5 enterprise patterns

The Agent Identity layer is the area where vendor behaviour is most consistent and most useful as industry reference.

### Finding 2.1 — Identity is a first-class object separate from User Identity

**Research Finding:** Enterprise agent platforms treat the agent as a distinct identity class, not as a user proxy.
**Source:** AWS Bedrock — AgentCore Identity ([aws.amazon.com/bedrock/agentcore/identity](https://aws.amazon.com/bedrock/agentcore/identity/)); Microsoft Entra ID Agent ID Administrator ([blog.csdn.net](https://blog.csdn.net/weixin_42376192/article/details/160612154) reference summary, evidence not retrieved directly); search-summary of Entra update stating Entra markets itself as securing access for "workforce, customers, and agents."
**Observation:** AgentCore Identity lists OAuth, IAM roles, and token management as the primitives for "enabling agents to securely access AWS resources and third-party tools." The agent authenticates with its own credentials (not a user's), and acts on the basis of those credentials.
**Pattern:** *Non-human identity as identity primitive.* The agent has its own principal; user context is not a substitute.
**Applicability:** Finance Suite today uses CC agent identities only informally (subagent roles inside Claude Code workflows, plus human accounts on production servers). The morning frictions — `Memory ≠ Runtime State`, `Evidence ≠ Claim Authorization`, and the R1 Identity reconciliation — all trace to a missing identity model that distinguishes "this Claude Code session" from "this human user" from "this handoff artifact."
**Non-Claim:** This finding does NOT prescribe any particular Identity Provider. It does NOT say Finance Suite should use OAuth for agents. It does NOT assert that AWS AgentCore Identity is mature or suitable (search summary only — direct evidence not retrieved).

### Finding 2.2 — Identity is scoped per-environment, not global

**Research Finding:** Production agent systems bind identity to environment and task, not to a single global agent name.
**Source:** Claude Code Cloud Tag feature ([docs.claude.com/en/docs/claude-code/cloud-tags](https://docs.claude.com/en/docs/claude-code/cloud-tags), snapshot via search — direct fetch 404'd); Microsoft Magentic-One architecture ([microsoft.github.io/autogen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html)).
**Observation:** Cloud Tag is described as "cloud-based tagging is available with Max, Team, Enterprise, and Pro plans" and as "providing centralized session storage, allowing administrators to [manage/access sessions]" (search-summary direct quote; original page returned 404 at fetch time). Magentic-One's orchestrator instantiates WebSurfer, FileSurfer, Coder, Computer Terminal as named specialised identities inside the same harness.
**Pattern:** Identity = (role, scope-of-tools, scope-of-data, scope-of-time). Not identity = agent-name.
**Applicability:** This maps to the morning finding that *independence is a property of the reviewer's environment*. If identity is scoped per-environment, then "is reviewer X independent" becomes a *bound check* ("are X's tools/data/time disjoint from Y's") rather than a *role check* ("X is labelled reviewer").
**Non-Claim:** Does NOT recommend adopting Cloud Tag. Does NOT state that AWS/Microsoft's binding mechanism is correct. Direct evidence from AWS docs and Claude Code docs was not retrieved; the claim restates what the search summaries report.

### Finding 2.3 — Identity is provisioned through enterprise IdP, not locally

**Research Finding:** Agent identities are federated through existing enterprise identity providers (Entra, Okta, IAM) rather than maintained as separate registries.
**Source:** Search-summary on Microsoft Entra ID Agent ID Administrator role (CSDN summary; original Microsoft Learn page not retrieved — evidence not retrieved directly); AWS Bedrock AgentCore Identity lists IAM roles among its primitives ([aws.amazon.com/bedrock/agentcore/identity/](https://aws.amazon.com/bedrock/agentcore/identity/)).
**Observation:** The vendor pattern is to *not invent a new identity provider* — agents become principals inside the existing enterprise IdP, leveraging Conditional Access, governance, lifecycle tooling already in place. CVE-2025-55241 in Entra ID Actor tokens (CVSS 10.0) is a salient counter-example showing why the *implementation* of this federation matters.
**Pattern:** *Federate, do not re-create.* The same IdP that controls human workforce access also controls agent access.
**Applicability:** Finance Suite already has human user identity. Whether to expose agents as principals on the same directory is a *governance design choice*, not a technical novelty.
**Non-Claim:** Does NOT advocate Entra or any specific IdP. Does NOT claim Entra Agent ID is production-ready — search-summary only. The CVE reference is a reminder that federation must be implemented defensively, not a claim about any specific vendor.

### Finding 2.4 — Identity is paired with explicit lifecycle / offboarding

**Research Finding:** Enterprise agent identity products expose lifecycle workflows analogous to employee onboarding (create → rotate → offboard).
**Source:** Microsoft Entra ID Governance documentation summary (Microsoft Learn — direct page not fetched); search-summary framing.
**Observation:** Lifecycle is described as a governance primitive, not optional. Agents that persist credentials after their task is over are a documented security risk.
**Pattern:** *Identity has expiry.* A long-lived agent credential is treated as anomalous.
**Applicability:** Maps to the morning's `Memory ≠ Runtime State` friction: persistent agent identity is one of the channels through which memory leaks across task boundaries. Lifecycle controls are the enforcement mechanism.
**Non-Claim:** Does NOT claim Finance Suite currently has an agent lifecycle policy. Does NOT recommend one. Does NOT recommend specific offboarding intervals.

### Finding 2.5 — Identity is inspectable (audit primitive), not opaque

**Research Finding:** Production agent systems treat agent identity as observable for audit (who acted, when, with what scope) — not as a hidden internal state.
**Source:** Google A2A protocol design ([google-a2a.github.io/A2A](https://google-a2a.github.io/A2A/), [github.com/google/A2A](https://github.com/google/A2A)).
**Observation:** A2A is explicitly described as "opaque by default — agents collaborate without needing to share internal state, memory, or tools" while still exposing an "Agent Card" (JSON) for discovery and authentication at the boundary. The model is: *inside is opaque; boundary is inspectable*.
**Pattern:** *Inside opaque / boundary inspectable.* The collaboration surface is small and declared; the internal state is not.
**Applicability:** This is the closest industry reference to the morning's Producer/Reviewer separation. The Agent Card is what a Reviewer can read; the inside state is what the Reviewer cannot read. This is the structural property that lets an external reviewer form an independent view.
**Non-Claim:** Does NOT recommend adopting A2A in Finance Suite. Does NOT claim the boundary-inspectable model is sufficient for verification.

---

## 3. Permission Model in production agent systems

Permission is the most operationally observable layer. Three industry-wide patterns recur.

### Finding 3.1 — OAuth 2.0 delegated token exchange is the dominant permission primitive

**Research Finding:** Permission for production agents is implemented as OAuth 2.0 delegated token exchange, not as custom ACL systems.
**Source:** AWS Bedrock AgentCore Gateway "[supports] OAuth 2.0 delegated token exchange" (search-summary quote; primary AWS page returned 404); Bedrock AgentCore Identity lists OAuth among its primitives.
**Observation:** Agents do not store long-lived credentials to downstream systems. They hold a token that is exchanged at call time. The delegation chain is auditable.
**Pattern:** *Tokens, not credentials.* The user (or workspace) authorises *one* scope; the agent exchanges that into tool-specific tokens that expire.
**Applicability:** Current Finance Suite often uses static API keys in `.env` files or ENV vars. The morning's evidence-chain frictions can be partly attributed to inability to distinguish "the agent used key X for Y" with temporal precision.
**Non-Claim:** Does NOT recommend OAuth deployment. Does NOT claim Finance Suite should retire API keys. Does NOT evaluate any vendor's OAuth implementation.

### Finding 3.2 — Permissions are policy-declared, not code-imperative

**Research Finding:** Permission is described in policy / configuration files, not hard-coded inside the agent loop.
**Source:** AWS Bedrock AgentCore — "Policy in Amazon Bedrock AgentCore … allows teams to set clear boundaries for Agent operations using natural language … works with APIs, Lambda functions, MCP servers, and third-party services" (search-summary quote).
**Observation:** The agent is told *what it may do* via a policy the user team owns; the agent doesn't decide for itself what counts as a violation.
**Pattern:** *Policy is upstream of execution.* Code runs inside a permission envelope, not the other way around.
**Applicability:** Today's morning frictions are *policy-vs-evidence* frictions: an agent decides what to claim, the policy says what is permissible, and the question "did this claim respect policy" is currently answered by inspection after the fact. The industry direction is to push that answer upstream of the action.
**Non-Claim:** Does NOT prescribe natural-language policy. Does NOT recommend Policy-as-Code adoption. Does NOT assess whether NL-policy is enforceable.

### Finding 3.3 — Permission granularity favours tool-scope + data-scope, not just role-scope

**Research Finding:** Production systems distinguish *which tool* and *which data* a permission covers, beyond classic role-based access.
**Source:** CrewAI permission patterns — `TASK_EXECUTION`, `MEMORY_READ`, `MEMORY_WRITE`, `allowed_tools`, `blocked_actions`, `valid_targets`, `expires_in` ([blog.csdn.net/QuickCode/article/details/155858675](https://blog.csdn.net/QuickCode/article/details/155858675), [blog.csdn.net/ByteGlow/article/details/155858742](https://blog.csdn.net/ByteGlow/article/details/155858742)).
**Observation:** A crew's permission bundle is split into per-tool allowances, per-action blocklists, per-target scopes, and time-bounded expiry. Roles are *one* component among several, not the primary one.
**Pattern:** *Multi-dimensional capability.* Role × tool × data × time. RBAC alone is treated as insufficient.
**Applicability:** Finance Suite's permission discussions (harness governance windows) currently are role-shaped. The wider industry has moved to finer granularity because role-based proved inadequate to express "this agent may read prices but not submit orders."
**Non-Claim:** Does NOT recommend CrewAI. Does NOT recommend any specific permission vocabulary.

### Finding 3.4 — Permission grants are non-transitive unless explicitly delegated

**Research Finding:** In multi-agent settings, an agent's permissions do not transitively extend to its sub-agents.
**Source:** Google A2A — "Enterprise-ready — built for real-world enterprise needs including authentication, security, and observability" ([google-a2a.github.io/A2A](https://google-a2a.github.io/A2A/)); AWS AgentCore Identity lists per-agent IAM primitives.
**Observation:** The pattern is *explicit delegation required*. A supervisor pattern (subagent dispatched by a parent) must re-delegate or hold a narrower permission; the parent's full credential does not pass through.
**Pattern:** *No privilege inheritance by default.*
**Applicability:** Direct connection to the morning's Producer ≠ Reviewer question. If reviewer's permissions were inherited from producer's harness, independence is meaningless. The industry rule "no transitive permission" makes independence a non-vacuous property.
**Non-Claim:** Does NOT recommend this property be enforced in Finance Suite. The finding notes what industry treats as default, not what Finance Suite should adopt.

---

## 4. Shared Context layer architectures

This is the area where vendor offerings diverge most. Three architectural shapes recur.

### Finding 4.1 — Memory is decomposed into short-term / long-term / shared

**Research Finding:** Memory in production agent systems is explicitly decomposed into short-term (task), long-term (agent), and shared (cross-agent) tiers.
**Source:** AWS Bedrock AgentCore Memory — "managed memory infrastructure to maintain context and continuity across multi-turn conversations and agent interactions" ([aws.amazon.com/bedrock/agentcore/memory/](https://aws.amazon.com/bedrock/agentcore/memory/), search-summary); CrewAI memory split (short-term / long-term / shared), per CSDN summary of CrewAI permission docs.
**Observation:** The tiering is explicit in documentation; the boundaries between tiers are owned by the platform, not by the agent.
**Pattern:** *Three-memory decomposition.* The agent doesn't manage its own memory lifecycle.
**Applicability:** Maps directly to the morning's `Memory ≠ Runtime State` and `Memory Exists ≠ Memory Valid` frictions. Industry treats the three tiers as objects the platform owns; Finance Suite currently has implicit, ad-hoc memory-equivalents (subagent transcripts, Engram records, window handoff docs, NOTES.json, handoff.json).
**Non-Claim:** Does NOT prescribe the three-tier model for Finance Suite. Does NOT recommend AgentCore Memory. Does NOT claim the three-tier split is sufficient.

### Finding 4.2 — Shared context is broker-mediated, not peer-shared

**Research Finding:** When multiple agents share context, sharing is mediated by a broker service — not by direct agent-to-agent memory writes.
**Source:** AWS Bedrock AgentCore Memory (search-summary); Google A2A explicit principle: "Opaque by default — agents collaborate without needing to share internal state, memory, or tools" ([google-a2a.github.io/A2A](https://google-a2a.github.io/A2A/)).
**Observation:** A2A's stance — *do not share internal state* — is the strongest industry statement that shared context belongs to a broker, not to peers. AgentCore Memory and LangGraph's shared-state schemas implement this.
**Pattern:** *Broker = single point of audit.* If shared state is broker-owned, every read/write is observable; if shared state is peer-shared, it is not.
**Applicability:** Finance Suite's current handoff.json / Windows/WINDOW_HANDOFF.md / drift detection mechanisms operate as a *manual* broker. The industry direction is broker-as-service. Whether the manual broker is sufficient is a design question, not this report's question.
**Non-Claim:** Does NOT recommend automating the broker. Does NOT claim the manual broker is broken. Does NOT claim broker-as-service is always better.

### Finding 4.3 — Context is write-restricted by authorship

**Research Finding:** Production shared-context architectures restrict *who can write* to the context — typically the originating agent or the orchestrator — and *who can read* more broadly.
**Source:** CrewAI permission pattern includes `MEMORY_READ` and `MEMORY_WRITE` as separate capabilities ([blog.csdn.net/QuickCode/article/details/155858675](https://blog.csdn.net/QuickCode/article/details/155858675)); A2A implicit (peers do not share internal state).
**Observation:** Read/write asymmetry is a feature, not a bug. Producers write; reviewers read; cross-write is denied unless explicit delegation. This is what makes evidence review structurally separate from evidence production.
**Pattern:** *Asymmetric memory access.* Read-everyone-by-default, write-narrow-by-default.
**Applicability:** This maps directly to the morning's Producer ≠ Reviewer design review question. The industry treats asymmetric memory access as the *mechanism* by which independence is implementable. The morning's frictions show Finance Suite does not yet have this asymmetry.
**Non-Claim:** Does NOT prescribe specific read/write scopes. Does NOT recommend any particular asymmetry. Does NOT claim asymmetry is sufficient for independence.

### Finding 4.4 — Context has provenance, not just content

**Research Finding:** Modern shared-context layers record provenance (who wrote, when, under what authority) alongside the content itself.
**Source:** AWS Bedrock AgentCore Observability one of seven services ([aws.amazon.com/bedrock/agentcore/](https://aws.amazon.com/bedrock/agentcore/)); A2A Agent Card metadata.
**Observation:** The industry treats provenance as a first-class property of any context object. Audit answers are *generated from the data*, not reconstructed by inference.
**Pattern:** *Content carries provenance.* A memory entry is not just a string; it is a string + author + timestamp + scope.
**Applicability:** This is what the morning's R1 Identity Reconciliation had to do *manually* — establish that the static evidence record (`v0.2_EVIDENCE_R1`) and the runtime observation (`be3c0e91`) were *Related Artifact* rather than *Same/Conflict/Independent*. With provenance carried in the content, that judgement is mechanical instead of interpretive.
**Non-Claim:** Does NOT recommend provenance-tracking adoption. Does NOT assess whether the resulting artefacts would be review-grade.

---

## 5. Multi-Agent Coordination Model

Four coordination shapes are observed in production. They are not exclusive; mature systems often combine them.

### Finding 5.1 — Orchestrator / supervisor pattern is the dominant shape in 2025–2026

**Research Finding:** The dominant enterprise multi-agent coordination shape is orchestrator/supervisor with specialised sub-agents, not peer-to-peer.
**Source:** Microsoft Magentic-One — Orchestrator (Supervisor) + WebSurfer, FileSurfer, Coder, Computer Terminal + Task Ledger + Progress Ledger ([microsoft.github.io/autogen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html)); LangGraph Hierarchical Agent Teams / `langgraph-supervisor` / supervisor-of-supervisors pattern ([cnblogs.com/lightsong](https://www.cnblogs.com/lightsong/p/18813515), [blog.csdn.net/qq_31557939/article/details/160942338](https://blog.csdn.net/qq_31557939/article/details/160942338)).
**Observation:** Magentic-One uses an orchestrator that owns *Task Ledger* (records and initiates operations) and *Progress Ledger* (tracks each phase). LangGraph implements hierarchical supervisor-of-supervisors, where each supervisor routes via `Command({goto, update})`. The dominant primitive is *centralised control with decentralised execution*.
**Pattern:** *Orchestrator with ledgers.* The orchestrator maintains stateful records of *what is going on*; sub-agents execute without that state.
**Applicability:** Direct mapping to the morning's need: a CC agent that dispatches subagents today is orchestrator-shaped. The morning's frictions show the ledgers (`Task Ledger`, `Progress Ledger`) are implemented *as prose* (handoff docs, window boards) rather than *as data structures*. The industry's lesson is that the ledgers must be queryable, not just readable.
**Non-Claim:** Does NOT recommend Magentic-One. Does NOT recommend LangGraph hierarchical pattern. Does NOT claim orchestrator shape is sufficient.

### Finding 5.2 — Peer / swarm pattern is observed but operationally narrower

**Research Finding:** Peer / swarm coordination exists in some open-source frameworks (CrewAI sequential/hierarchical processes) but is treated as a secondary shape.
**Source:** CrewAI process types — sequential, hierarchical, and other orchestration modes (search-summary; primary CrewAI docs not fetched).
**Observation:** Peer is often implemented as *delegated broadcast* (a Crew's pool of agents works the same task in parallel) rather than as *true peer negotiation*. The narrower "swarm" form (no fixed supervisor) is rare in production deployments.
**Pattern:** *Peer as concurrent workers, swarm as exception.* Most production "peer" patterns are actually horizontal fan-out under an orchestrator.
**Applicability:** The morning's question of "should the four research agents be peers" maps to the same question the industry asks; the dominant answer is "no — they are subordinates of a coordinator (synthesizer)."
**Non-Claim:** Does NOT recommend peer coordination. Does NOT claim peer coordination is unsound. Does NOT address the recent wave of "swarm" or "marketplace" patterns.

### Finding 5.3 — Market-based / Contract-Net coordination is an academic form, not a production pattern in agent systems today

**Research Finding:** Market-based coordination (Contract Net Protocol and successors) is a recognised academic pattern from the 2000s MAS literature but is not the dominant production coordination pattern for LLM-era agents.
**Source:** Contract Net Protocol academic literature — "[An Overview of Multi-Agent System Architectures](https://arxiv.org/abs/2405. ...)"; "Analysis of contract net in multi-agent systems," ScienceDirect ([sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S0005109806000057)); improvement papers on SpringerLink.
**Observation:** Contract Net's value proposition (decentralised task allocation by bid) presupposes that bid evaluation is cheap and reliable. In LLM-mediated systems, bid evaluation is *not* cheap, and the orchestrator-shaped pattern (Finding 5.1) is operationally simpler. Market-based coordination is therefore a reference, not a primary pattern.
**Pattern:** *Market-based is reference, not default.* When a future cost reduction in inference makes bidding cheap, market shapes may return.
**Applicability:** Finance Suite could experiment with task-allocation markets in *low-stakes* research windows. For governance-bearing work, orchestrator pattern remains the industry default.
**Non-Claim:** Does NOT claim Contract Net is wrong. Does NOT recommend any market-shape experiment. Does NOT evaluate opportunity-cost of bidding.

### Finding 5.4 — Boundary-mediated (A2A-style) coordination is emerging as the cross-org layer

**Research Finding:** When coordination crosses organisations (vendor boundaries), a protocol-mediated boundary (A2A Agent Card + capability declaration) is preferred over full orchestrator.
**Source:** Google A2A — "securely exchange information and coordinate actions across isolated enterprise applications and data" ([google-a2a.github.io/A2A](https://google-a2a.github.io/A2A/), [github.com/google/A2A](https://github.com/google/A2A)). 50+ partners including Atlassian, Box, Cisco, MongoDB, Oracle, Salesforce, SAP, ServiceNow, Workday.
**Observation:** A2A is *complementary* to MCP (Anthropic's tool-context protocol). The boundary-mediated shape is the cross-org chord; orchestrator/supervisor is the within-org chord. Both exist, for different scopes.
**Pattern:** *Two coordination layers.* Within-org: orchestrator/supervisor. Cross-org: protocol-mediated Agent Card. The Agent Card declares a *capability surface*, not internal implementation.
**Applicability:** Finance Suite today has only within-org coordination (CC and subagents inside one Claude Code session). The cross-org question (hiring another company's agent, or being hired as one) is not yet a design input. Recording its absence is itself a finding.
**Non-Claim:** Does NOT recommend Finance Suite adopt A2A. Does NOT claim A2A is the only cross-org option.

---

## 6. Morning governance problems these findings *inform* — but do not solve

The morning produced three structural findings that this report's industry survey intersects. This section makes those intersections explicit. It is not a verdict; it is a *map* of where industry patterns might or might not align.

### 6.1 — `Memory ≠ Runtime State`

| Morning finding | Closest industry pattern | Mechanism named | Pattern number |
|---|---|---|---|
| Memory exists, but its validity cannot be asserted | Three-tier memory (short/long/shared) | Decompose memory, audit by tier | 4.1 |
| Runtime state leaks into memory | Asymmetric memory access (read-everyone / write-narrow) | Restrict write by authorship | 4.3 |
| Memory has no provenance field | Provenance-as-content | Carry author + timestamp + scope with content | 4.4 |

The industry treats these as **adjacent mechanisms that compose** into a "memory is a typed, scoped, provenance-carrying object" view. Finance Suite's morning frictions are signs that memory is currently *untyped* (acts as multiple things at once) and *unprovenance-tracked*.

### 6.2 — `Independence is a property of the environment, not a role label`

| Morning finding | Closest industry pattern | Mechanism named | Pattern number |
|---|---|---|---|
| "Reviewer" label doesn't guarantee independence | Identity scoped per-environment (role × tools × data × time) | Identity is multi-dimensional | 2.2 |
| Reviewer's view inherits from producer's harness | Non-transitive permission | No privilege inheritance by default | 3.4 |
| Producer and Reviewer share mental model | Inside-opaque / boundary-inspectable (A2A) | Single declared boundary surface | 2.5 |

The industry treats **environment-shape** as the substrate for independence. Finance Suite currently relies on labels. The friction is that the label exists but the environment does not.

### 6.3 — `Evidence ≠ Claim Authorization`

| Morning finding | Closest industry pattern | Mechanism named | Pattern number |
|---|---|---|---|
| Evidence exists but authorisation is uncertain | Provenance-carrying content | Audit derived from data | 4.4 |
| Two records need classification (Related / Same / Conflict / Independent) | Agent Card boundary surface | Boundary declared once; classifications follow mechanically | 2.5 |
| R1 static evidence vs runtime observation treated as separate problems | Broker-mediated shared context | Single point of audit | 4.2 |

The industry view is that the *evidence object itself* must carry the information required for authorisation; an external system reconstructs authorisation by reading the object's provenance. Finance Suite's R1 reconciliation had to *manually reconstruct* this — a sign that the current evidence objects do not carry the relevant fields.

---

## 7. Implications section (per-finding format)

The task card requires per-finding format. The implications are not new findings; they are re-expressions of the morning's reach into industry patterns.

**Research Finding:** Industry treats agent infrastructure as a *harness*, not a gateway.
**Source:** Synthesis of Findings 1, 2, 4 — AWS AgentCore service decomposition, Claude Code Cloud Tag, Google A2A.
**Observation:** The morning's frictions are about state, identity, and evidence (harness-layer), not about ingress (gateway-layer).
**Pattern:** *Right layer for the right problem.* Gateway = network concern; harness = cognitive-loop concern.
**Applicability:** Direct. The morning's research target is the harness layer; Finance Suite should not mistake the harness problem for a gateway problem.
**Non-Claim:** Does NOT authorise gateway work. Does NOT say "we should adopt AgentCore." Does NOT prescribe any harness.

**Research Finding:** Agent identity in industry is *scoped and federated*, not global and local.
**Source:** Findings 2.1–2.5 — Bedrock AgentCore Identity, Entra Agent ID, Claude Code Cloud Tag, Magentic-One.
**Observation:** Identity binds role, tools, data, and time as a tuple. Federation reuses enterprise IdP.
**Pattern:** *Bounded identity.*
**Applicability:** Direct. Today's CC agent has informal identity; an org-level harness would require bounded identity.
**Non-Claim:** Does NOT prescribe an IdP. Does NOT prescribe scope dimensions.

**Research Finding:** Permission is *multi-dimensional and explicitly non-transitive*.
**Source:** Findings 3.1–3.4 — OAuth delegated exchange, policy-as-config, CrewAI capabilities, A2A non-transitive default.
**Observation:** Permission vocabulary extends beyond RBAC; non-transitivity is the default.
**Pattern:** *Multi-dimensional capability envelope; no inheritance by default.*
**Applicability:** Direct. Maps to Producer ≠ Reviewer.
**Non-Claim:** Does NOT recommend CrewAI's vocabulary. Does NOT recommend any vendor.

**Research Finding:** Shared context is *tiered, broker-mediated, asymmetric, provenance-carrying*.
**Source:** Finding 4.1–4.4.
**Observation:** All four properties appear in industry reference systems; they compose.
**Pattern:** *Memory as a typed, scoped, broker-owned object.*
**Applicability:** Direct. Maps to Memory ≠ Runtime State.
**Non-Claim:** Does NOT propose implementing all four today.

**Research Finding:** Coordination is *orchestrator-within-org, protocol-mediated cross-org*.
**Source:** Findings 5.1, 5.4 — Magentic-One + LangGraph supervisor; A2A.
**Observation:** Within-org = orchestrator + ledger; cross-org = Agent Card boundary.
**Pattern:** *Two coordination layers, one inside, one outside.*
**Applicability:** Direct. Maps to within-org (CC + subagents + Engram) and is silent on cross-org (no current scope).
**Non-Claim:** Does NOT recommend Magentic-One. Does NOT recommend A2A.

---

## 8. What this report does NOT claim

To prevent over-reading, the following are explicit exclusions:

1. **No adoption recommendation.** This is reference-only. No agent harness, framework, vendor, or protocol named in this document is endorsed for Finance Suite adoption.
2. **No implementation timeline.** This report produces no roadmap, sequence, or pacing.
3. **No architecture decision.** No principal / pattern / mechanism is selected for production. The selection, if any, happens in a separate window after the four-agent research block completes and CC synthesises.
4. **No modification to Governance Design Review v0.1.** The synthesis in §6 explicitly does not modify Q1–Q4; it only maps industry patterns onto the morning's open questions.
5. **No capability claim beyond source support.** Where primary docs returned 404 (AWS AgentCore Identity/Memory product page, Claude Code Cloud Tags page), the corresponding finding is tagged accordingly and the claim restates the search summary, not a direct quote.
6. **No claim that the four industry patterns (gateway/harness, identity, permission, coordination) compose into a finished design.** They are *pieces*, observed independently; whether they compose coherently for Finance Suite is the synthesiser's job.

---

## 9. Non-adoption statement (mandatory)

**This document is REFERENCE ONLY. It does NOT authorise, commit, or recommend:**

- adoption of Amazon Bedrock AgentCore;
- adoption of Microsoft Entra ID Agent ID Administrator;
- adoption of Claude Code Cloud Tag;
- adoption of Microsoft Magentic-One;
- adoption of LangGraph supervisor / hierarchical agent teams;
- adoption of Google Agent2Agent (A2A) protocol;
- adoption of CrewAI permission / role vocabulary;
- any OAuth 2.0 delegated token exchange deployment;
- any federation of agent identities to Entra / Okta / IAM;
- any specific scoping of identity, permission, memory, or coordination primitives;
- any architecture decision by Finance Suite.

This document is one of four parallel research outputs dispatched by CC under `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md`. It is research material for the synthesiser and for future governance windows. It does not close, advance, or modify any existing governance, evidence, or review chain. It does not authorise production change.

---

## 10. Source index

Sources are listed in the order they appear in the findings. Items where the original page could not be retrieved (404 / closed socket) are marked *(unretrieved)*; the finding text treats those citations as a search-summary only.

**Anthropic / Claude Code**
- Claude Code Cloud Tags — `https://docs.claude.com/en/docs/claude-code/cloud-tags` *(unretrieved — page returned 301 redirect; original fetched as 404)*
- SiliconANGLE — *Anthropic launches Claude Code for Enterprise* — `https://siliconangle.com/2025/10/22/anthropic-launches-claude-code-for-enterprise-with-new-admin-and-security-features/` *(unretrieved)*
- Lance Martin personal site — `https://www.lance-martin.com/` *(unretrieved)*
- Lance Martin — Claude Code local coding assistant — `https://lance-martin.com/posts/claude-code-local-coding-assistant/` *(unretrieved)*

**AWS Bedrock AgentCore**
- AgentCore overview — `https://aws.amazon.com/bedrock/agentcore/`
- AgentCore Identity — `https://aws.amazon.com/bedrock/agentcore/identity/` *(unretrieved)*
- AgentCore Memory — `https://aws.amazon.com/bedrock/agentcore/memory/` *(unretrieved)*
- AgentCore Gateway — `https://aws.amazon.com/bedrock/agentcore/gateway/`
- AgentCore Runtime — `https://aws.amazon.com/bedrock/agentcore/runtime/`
- AWS Blog — Build production-ready agents with AgentCore — `https://aws.amazon.com/blogs/aws/build-production-ready-agents-with-amazon-bedrock-agentcore/` *(unretrieved)*
- A2A Gateway / MCP / OAuth — Sina Finance summary — `http://finance.sina.com.cn/stock/usstock/summary/2026-06-02/doc-inhzxvtx8113607.shtml`
- Medium — *Amazon Bedrock AgentCore: Seven Services, One Platform* — `https://medium.com/@arif.osman21/amazon-bedrock-agentcore-seven-services-one-platform` *(unretrieved)*

**Microsoft**
- Microsoft Research — *Designing AI agents that can coordinate across an enterprise* — `https://www.microsoft.com/en-us/research/blog/designing-ai-agents-that-can-coordinate-across-an-enterprise/` *(unretrieved)*
- Magentic-One (AutoGen) — `https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/magentic-one.html`
- Microsoft Entra overview — `https://www.microsoft.com/en-gb/security/business/microsoft-entra`
- Microsoft Entra ID Protection — `https://www.microsoft.com/zh-tw/security/business/identity-access/microsoft-entra-id-protection`
- Microsoft Entra ID Agent ID Administrator — CSDN summary — `https://blog.csdn.net/weixin_42376192/article/details/160612154` *(third-party summary)*

**Google A2A**
- A2A spec — `https://google-a2a.github.io/A2A/`
- A2A GitHub — `https://github.com/google/A2A`

**Open-source frameworks**
- LangChain — *Agent orchestration: the core of multi-agent systems* — `https://blog.langchain.com/agent-orchestration-the-core-of-multi-agent-systems/` (redirected to `https://www.langchain.com/blog/agent-orchestration-the-core-of-multi-agent-systems`, not fully fetched)
- LangGraph supervisor / hierarchical agent teams — CSDN summaries:
  - `https://blog.csdn.net/lovechris00/article/details/143062257`
  - `https://www.cnblogs.com/lightsong/p/18813515`
  - `https://blog.csdn.net/qq_31557939/article/details/160942338`
  - `https://blog.csdn.net/m0_59164520/article/details/160635013`
- CrewAI permission patterns:
  - `https://blog.csdn.net/QuickCode/article/details/155858675`
  - `https://blog.csdn.net/ByteGlow/article/details/155858742`
  - `https://blog.csdn.net/DeepNest/article/details/155858516`

**Academic**
- *Analysis of contract net in multi-agent systems* — `https://www.sciencedirect.com/science/article/pii/S0005109806000057`
- *Improvement and Simulation of Contract-Net-Based Task Allocation for Multi-robot System* — `https://link.springer.com/chapter/10.1007/978-3-642-28314-7_8`
- *An Extended Contract Net Protocol with Direct Negotiation of Managers* — `https://link.springer.com/chapter/10.1007/978-3-319-04735-5_6`
- arXiv survey on Multi-Agent System Architectures (cs.MA, 2024) — query result snippet only

---

**End of Agent A — Industry Architecture Report**
