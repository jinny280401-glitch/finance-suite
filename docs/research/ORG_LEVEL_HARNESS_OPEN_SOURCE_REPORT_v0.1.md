# Organization-Level Agent Harness — Open Source Systems Report v0.1

**Topic:** 开源 Agent 协作框架研究 — how do open-source projects implement multi-agent organization?
**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Window type:** External method research input (no production change, no code change, no declaration modification)
**Date:** 2026-08-05
**Coordinator:** CC (governance coordinator, not author of research outputs)
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

> **Output target (per task card §5):** "多 Agent 协作环境如何实现"
> **Required sections:** (1) Project inventory; (2) Comparison table; (3) Patterns that recur across multiple projects; (4) Patterns that appear in only one project; (5) Implications for Finance Suite (per-finding format); (6) Non-adoption statement.

---

## 1. Project inventory

The following open-source projects were reviewed. Each is described as observed on its public repository page or documentation snapshot at 2026-08-05; project status (stars / last commit / license) is reported as visible on the page at fetch time and is **not a maturity claim**.

### 1.1 `garrytan/gbrain` (GBrain)
- **Stars / license:** 27.8k / MIT
- **Maintainer:** Garry Tan (YC); 863 commits on `master`
- **Problem claimed to solve:** "Search gives you raw pages. GBrain gives you the answer." Adds persistent memory + citation to agents that otherwise lack it; self-wires a knowledge graph with typed edges (`attended`, `works_at`, `invested_in`) and zero LLM calls on writes.
- **Mechanism:** Two-tier memory (PGLite WASM or Postgres + pgvector) with hybrid vector+BM25+RRF search; BullMQ-shaped Postgres-native job queue ("Minions") for durable subagent execution; cron-driven "dream cycle" enrichment; 43 routing skills; MCP server exposing "30+ tools"; OAuth 2.1 with scope-gated `read`/`write`/`admin`; per-user scoping in company-brain mode.

### 1.2 `Lum1104/Understand-Anything` (UA)
- **Stars / license:** 77.5k / MIT
- **Problem claimed to solve:** Onboarding to large codebases (200k-line "where do I even start?" problem). Renders an interactive knowledge graph that "quietly teaches you how every piece fits together."
- **Mechanism:** `/understand` command orchestrates seven specialized agents (`project-scanner`, `file-analyzer`, `architecture-analyzer`, `tour-builder`, `graph-reviewer`, `domain-analyzer`, `article-analyzer`). Splits deterministic parsing (Tree-sitter) from semantic understanding (LLM). File analyzers run in parallel (5 concurrent, 20–30 files per batch) with fingerprint-based incremental re-analysis. Output: `.ua/knowledge-graph.json`.

### 1.3 OpenClaw (multi-agent extension context)
- **Surface:** Referenced in `gaaiyun/TradingAgents-OpenClaw-Skill` (MIT, 6 commits) and `lanyasheng/openclaw-multiagent-framework` (TEMPLATES.md) and `hyperlist/feishu-multi-agent`.
- **Problem claimed to solve:** "Microservice-ization of LLM reasoning." Agent = LLM (brain) + Skill (capability) + Tool permissions, persisted at `~/.openclaw/agents/<agentId>`.
- **Mechanism:** Skill discovery via `SKILL.md` + `_meta.json`; standardized Request/ACK/Final messaging protocol between agents; per-agent credential/permission boundary; routing across single-agent and multi-agent modes; LLM engine / signals engine / mock engine router for graceful degradation in tests.

### 1.4 `langchain-ai/langgraph` (LangGraph)
- **Stars / license:** 38.9k / MIT
- **Problem claimed to solve:** "Low-level orchestration framework for building stateful agents." Inspired by Pregel and Apache Beam; public interface draws from NetworkX.
- **Mechanism:** Nodes-and-edges graphs with durable execution, branching, subgraphs, checkpointing. Short-term working memory + long-term persistent memory. Human-in-the-loop via state inspection/modification ("interrupts"). Higher-level `deepagents` package; LangSmith for observability.

### 1.5 `crewAIInc/crewAI` (CrewAI)
- **Stars / license:** 56.6k / MIT
- **Problem claimed to solve:** Role-playing autonomous agents ("Crews" + "Flows"). "Speed, flexibility, and control through Crews of AI agents and event-driven Flows."
- **Mechanism:** Identity = `(role, goal, backstory)` triplet declared in `agents.yaml`; tasks reference agents by key. Process models: `sequential`, `hierarchical` (manager-LLM delegates and validates). `Flows` add `@start` / `@listen` / `@router` / `or_` / `and_` combinators with structured Pydantic state. Memory + checkpointing + MCP/A2A support as agent capabilities. Enterprise control plane (AMP) as a separate commercial offering; OSS is MIT.

### 1.6 `microsoft/autogen` (AutoGen)
- **Stars / license:** 60.2k / CC-BY-4.0 (docs) + MIT (code)
- **Status:** Maintenance mode — Microsoft directs new users to `microsoft/agent-framework`.
- **Problem claimed to solve:** Programming framework for building multi-agent LLM apps.
- **Mechanism:** `AssistantAgent(name, model_client, system_message, description)` — `name` + `description` form the agent's identity and tool-facing self-description. `AgentTool(return_value_as_last_message=True)` exposes one agent's output as a tool to another. No persistent memory layer surfaced in README; cross-agent state passes through message passing in Core. Warning about MCP trust boundary.

### 1.7 `ag2ai/ag2` (AG2 — formerly AutoGen)
- **Stars / license:** 4.8k / Apache-2.0
- **Tagline:** "The Open-Source AgentOS"
- **Problem claimed to solve:** "Build systems, not prompts." AI-Native Organization use cases.
- **Mechanism:** `Hub` (agent registry + write-ahead log + TTL sweeper); typed `Channel`s — `conversation` (free-form two-party), `consulting` (one-question-one-reply), `discussion` (round-robin), `workflow` (declarative `TransitionGraph`). `KnowledgeConfig` wraps `KnowledgeStore` (in-memory or disk); `Compact` / `SummarizeCompact` folds dropped turns into a summary; `WorkingMemoryPolicy` injects `memory/working.md` every turn. `context.input(...)` pauses a run; user-supplied `hitl_hook` returns a `HumanMessage`. Classic codebase split into `ag2ai/ag2-classic` at v1.0.

### 1.8 `microsoft/agent-framework` (MAF)
- **Stars / license:** 12.6k / MIT
- **Positioning:** Successor to AutoGen + Semantic Kernel. "Taking agents from prototype to production."
- **Problem claimed to solve:** Durability, restartability, observability, governance, HITL control; provider lock-in avoidance (Foundry, Azure OpenAI, OpenAI, GitHub Copilot SDK).
- **Mechanism:** Three primitives: **Agents** (individual LLM + tools + MCP), **Harness** (opinionated agent for long multi-step tasks: planning, todo tracking, context compaction, file access, memory, "don't-ask-again" tool approval, observability), **Workflows** (graph-based with sequential / concurrent / handoff / group collaboration; checkpointing; HITL). Session-based state management; middleware; `TRANSPARENCY_FAQ.md` placing responsibility on developer.

### 1.9 `AI4Finance-Foundation/FinRobot`
- **Stars / license:** 7.7k / Apache-2.0
- **Problem claimed to solve:** Automates professional equity research by replacing manual analyst workflows.
- **Mechanism:** Lead Agent orchestrates sub-agents (data, analysis, modeling, synthesis, report) + bull/bear/judge debate agents. **Director Agent** + Agent Registration + Agent Adaptor + Task Manager ("Smart Scheduler") allocate tasks based on agent performance metrics. Deterministic compute separation: "Numbers are code-calculated. Narratives are LLM-assisted. Every output is provenance-tracked."

### 1.10 `agentcommunity/agent-interface-discovery` (AID)
- **Stars / license:** 44 / MIT
- **Problem claimed to solve:** "0-th hop for agent discovery." "DNS for Agents: Type a domain. Connect to its agent. Instantly." Standardizes where an agent interaction begins for a given domain across MCP / A2A / OpenAPI.
- **Mechanism:** Single DNS `TXT` record at `_agent.<domain>` with `.well-known` JSON fallback. v2 normative record: Ed25519 JWK with RFC 7638 JWK thumbprint as `keyid`; HTTP Message Signature (RFC 9421) PKA handshake with nonce + `created` + `expires` + `Cache-Control: no-store`; `AID-Domain` header binds query host. Decentralized — no central registry; authority flows from domain ownership + key control.

### 1.11 `FoundationAgents/MetaGPT`
- **Stars / license:** 69.7k / MIT
- **Problem claimed to solve:** Coordinates multiple LLM agents as a software company. "Code = SOP(Team)." One-line requirement → repo.
- **Mechanism:** Built-in roles (product manager, architect, project manager, engineer, `DataInterpreter`). SOP-driven handoffs; CLI `metagpt "Create a 2048 game"` produces user stories / APIs / docs in `./workspace`. No explicit role-based permissions, message ACLs, or governance primitives documented on the README.

### 1.12 `matrix97317/AgentMesh` (and forks)
- **Stars / license:** 0 (early stage) / unspecified
- **Problem claimed to solve:** Modular layered multi-agent platform; "AgentTeam" handles task allocation, context management, collaboration workflow.
- **Mechanism:** Role definition, task allocation, multi-turn autonomous decision-making; shared `Context` (team details + task content + execution history); planned heterogeneous-agent communication protocol.

---

## 2. Comparison table

| Project | Identity (Agent vs User) | Memory / Organizational State | Permission / Access Boundary | Workflow Composition | Governance Primitives |
|---|---|---|---|---|---|
| **gbrain** | Implicit: agent = persistent identity with OAuth 2.1 scope claims; per-user scoping in company-brain mode | Postgres + pgvector hybrid store; typed edges self-wired on writes; cron-driven "dream cycle" enrichment | OAuth 2.1 `read` / `write` / `admin` scopes; rate limiting; DCR-style client registration; vault-aware secret distribution | BullMQ-shaped Postgres-native "Minions" job queue; durable subagents (pending → done); skill-routed `signal → search → respond → write → auto-link → sync` | Telemetry + audit on writes; provenance per edge; cron-driven enrichment is observable |
| **Understand-Anything** | Distinct agent identities (`project-scanner`, `file-analyzer`, `architecture-analyzer`, `tour-builder`, `graph-reviewer`, `domain-analyzer`, `article-analyzer`) — seven agents with separate role definitions | Single persisted `.ua/knowledge-graph.json` shared across agents; fingerprint-based incremental updates | None surfaced on the README; tool access bounded by what each agent's LLM prompt permits | Parallel file analyzers (5 concurrent, 20–30 files per batch); deterministic Tree-sitter parses before LLM semantic pass; clear handoff: scanner → analyzer → architecture → tour → reviewer | `graph-reviewer` validates completeness + referential integrity (built-in verification primitive) |
| **OpenClaw (multi-agent surface)** | Per-agent directory `~/.openclaw/agents/<agentId>` with own credentials | Skill-defined context per agent; cross-agent state via standardized Request/ACK/Final messaging | Per-agent tool permissions; per-agent credential; engine router (`llm` / `signals` / `mock`) is an isolation boundary | Skill registry (`SKILL.md` + `_meta.json`); Request/ACK/Final protocol; single- vs multi-agent modes | Engine router gives deterministic fallback for CI without API keys |
| **LangGraph** | Not explicit on the README — agent identity is whatever the developer wires into nodes | Short-term working memory + long-term persistent memory; checkpointing; subgraphs as named units | Not addressed on README | Nodes-and-edges graph; durable execution; branching; subgraphs | Interrupts = HITL primitive; **durable execution = audit-friendly state history** |
| **CrewAI** | Explicit: `(role, goal, backstory)` triplet declared in `agents.yaml`; agents are role-bound, not user-bound | Memory, knowledge, checkpointing listed as agent capabilities; no API detail on README | Per-agent `tools=[...]`; `Process.hierarchical` adds manager-LLM validation; `share_crew=True` opt-in telemetry sharing | `Process.sequential` / `Process.hierarchical`; `Flows` event-driven with `@start` / `@listen` / `@router` / `or_` / `and_` | Telemetry anonymous by default; AMP (commercial) adds observability + governance + security; HITL supported |
| **AutoGen** | `AssistantAgent(name, model_client, system_message, description)` — `name` + `description` are the identity + tool-facing self-description | No persistent memory layer in README; cross-agent state via message passing in Core runtime | `AgentTool` exposes one agent as tool to another (explicit invocation); `max_tool_iterations` cap; MCP trust warning | Multi-agent orchestration via `AgentTool`; higher-level patterns in AgentChat docs | Maintenance-mode redirect; explicit disclaimer about MCP trust; contribution scope restricted |
| **AG2** | Explicit `Hub` registry of agents with identity | `KnowledgeConfig` + `KnowledgeStore` (in-memory / disk); `Compact` / `SummarizeCompact` history folding; `WorkingMemoryPolicy` injects `memory/working.md` every turn | `context.input(...)` pauses run; `hitl_hook` (user-supplied function) decides how human input is gathered | Typed `Channel`s (`conversation` / `consulting` / `discussion` / `workflow`); declarative `TransitionGraph` | **Write-ahead log in `Hub`** (replayable audit trail); event subscriptions (`CompactionCompleted`, `CompactionFailed`) |
| **Microsoft Agent Framework** | Explicit `name` and `instructions`; per-provider credentials (e.g., `FoundryChatClient` carries creds per agent) | Session-based state management; workflow checkpointing; time-travel resume | Credential chains (`AzureCliCredential`, `DefaultAzureCredential`); middleware for request/response filtering | Graph-based workflows: sequential / concurrent / handoff / group collaboration; streaming; checkpointing | OpenTelemetry integration; `TRANSPARENCY_FAQ.md`; **Harness** primitive has "don't-ask-again" tool approval + observability; declarative YAML agents for versioning |
| **FinRobot** | Lead Agent + named sub-agents (data / analysis / modeling / synthesis / report) + bull/bear/judge debate agents | Per-output provenance; 13-chapter research output + IC memos + evidence links + numeric provenance | Director Agent allocates tasks based on **performance metrics**; deterministic compute separation | Pipeline: Lead → Data → Analysis → Modeling → Synthesis → Report; Bull ↔ Bear → Judge → Output | "Numbers are code-calculated. Narratives are LLM-assisted. Every output is provenance-tracked"; audit trail implicit in pipeline |
| **AID (Agent Interface Discovery)** | **Cryptographic identity via Ed25519 in DNS TXT; `keyid` = RFC 7638 JWK thumbprint** | None — spec covers record-level metadata only, not agent state | Permissioning = DNS ownership + key control + PKA handshake + domain-binding | Discovery workflow: TXT query → parse → `Accept-Signature` PKA → connect | **Decentralized by design** — no central registry; security contact via `SECURITY.md` |
| **MetaGPT** | Role identities: product manager / architect / project manager / engineer / `DataInterpreter` | Persistent workspace repo per run; not an explicit memory layer | None documented on README | SOP-driven handoffs; CLI produces repo in `./workspace` | None documented on README |
| **AgentMesh** | Role definition as first-class concept | Shared `Context` (team details + task content + execution history) | Not surfaced | `AgentTeam` for task allocation + collaboration workflow | Not surfaced |

---

## 3. Patterns that recur across multiple projects

These mechanisms appear in two or more of the reviewed projects. Each is an observation of prevalence, not a recommendation.

### 3.1 Role-as-Identity (CrewAI, AutoGen, MetaGPT, MAF, AG2, gbrain, FinRobot, AgentMesh)
Most projects that explicitly model multi-agent organization treat **role** (and increasingly `(role, goal, backstory)` or `(name, instructions)`) as the agent's identity. **No project surveyed explicitly distinguishes Agent Identity from User Identity at a cryptographic / authentication layer** — the user-vs-agent separation is typically convention, not protocol. The closest is AID (see §4.1).

### 3.2 Shared persistent store as "organizational memory" (gbrain, AG2, UA, FinRobot, LangGraph, CrewAI, MAF)
Where multi-agent organization is supported, the memory model collapses to one of: vector store (gbrain), `KnowledgeStore` (AG2), JSON graph file (UA), provenance-tracked pipeline artifacts (FinRobot), or checkpointed graph state (LangGraph, MAF, CrewAI). **There is no convergence on what an "organizational memory" actually is** — only on the fact that some shared substrate is needed.

### 3.3 Tool-level access boundary (gbrain, OpenClaw, CrewAI, AutoGen, MAF, AG2)
The access boundary is almost always **per-agent tool allow-listing** (gbrain `read`/`write`/`admin` scopes, OpenClaw per-agent tool permissions, CrewAI `tools=[...]`, AutoGen `AgentTool` wrap, MAF middleware). **No project surveyed implements a true role-based access control system with policy files audited separately from code** — enforcement happens in code via tool lists and middleware hooks.

### 3.4 HITL as the canonical "pause and verify" point (LangGraph, AG2, CrewAI, MAF)
Human-in-the-loop is implemented as: a stateful interrupt (LangGraph), a `context.input(...)` call answered by a user-supplied `hitl_hook` (AG2), explicit HITL support (CrewAI), middleware + "don't-ask-again" tool approval (MAF). **HITL is treated as a single point of approval, not a continuous verification layer.**

### 3.5 Graph-of-agents as the dominant workflow abstraction (LangGraph, MAF, AG2, AgentMesh, MetaGPT)
Five projects compose multi-agent workflows as a graph (nodes = agents/functions, edges = handoffs). The vocabulary converges: nodes, edges, handoff, group collaboration, channels, transitions. **The convergence is on the graph metaphor, not on its semantics** — checkpointing, retry, and verification differ.

### 3.6 Tiered engine / engine router (OpenClaw-TradingAgents, gbrain, AG2)
When the project anticipates production-vs-test divergence, it splits engines (OpenClaw `llm` / `signals` / `mock`; gbrain `conservative` / `balanced` / `tokenmax`; AG2's classic-vs-v1 fork). This is a structural response to the same problem: **the same code path must behave differently in test, dev, and prod.**

---

## 4. Patterns that appear in only one project

Each is a candidate "single-source" pattern whose maturity is harder to assess because there is no cross-reference.

### 4.1 Cryptographic Agent Identity via DNS (AID only)
AID is the only project that establishes agent identity at the **DNS + Ed25519 + RFC 9421 PKA** level. No other surveyed project treats the agent's identity as something that can be cryptographically verified by an external party without trusting the agent's host. **Maturity signal:** small (44 stars), but the spec is at v2 and language-agnostic (`protocol/constants.yml` is single source of truth, generated into TypeScript / Python / Go / Rust / .NET / Java).

### 4.2 Write-Ahead Log as Audit Primitive (AG2 only)
AG2's `Hub` owns a write-ahead log that can be replayed. This is the only surveyed project that surfaces **a system-level WAL distinct from application-level memory**. Other projects rely on telemetry / observability (LangSmith, MAF OpenTelemetry, CrewAI AMP, FinRobot provenance) rather than a structured log replay.

### 4.3 Deterministic Compute Separation (FinRobot only)
FinRobot explicitly splits **numbers = code, narratives = LLM** so financial figures cannot be hallucinated by the language model. No other surveyed project imposes this discipline — and no other surveyed project has the same regulatory pressure.

### 4.4 Engine Router as CI/Test Divergence (OpenClaw-TradingAgents only among reviewed)
`llm` / `signals` / `mock` engine router lets CI run 21 pytest cases with no API key. gbrain has a similar idea (`conservative` / `balanced` / `tokenmax`) but oriented to query modes, not test/prod divergence.

### 4.5 Graph-Reviewer as Built-in Verification (UA only)
UA's `graph-reviewer` validates completeness and referential integrity of the produced knowledge graph. No other surveyed project includes a **named agent whose purpose is to verify the output of the other agents**. Most projects either trust the LLM loop or delegate verification to HITL.

### 4.6 "Harness" as a First-Class Primitive (MAF only)
Microsoft Agent Framework is the only project that names **Harness** as a primitive distinct from Agent and Workflow. The Harness is "an opinionated agent with batteries-included capabilities for long, multi-step tasks — planning and todo tracking, context compaction, file access and memory, don't-ask-again tool approval, and observability." The vocabulary choice is recent (the page is dated 2026-07-08) and not yet echoed in OSS siblings.

### 4.7 "Don't-ask-again" Tool Approval (MAF only)
MAF's Harness is the only project that names **persistent tool approval** as a primitive — i.e., once approved, the approval sticks across runs. This is a workflow-level decision that has governance implications (an authorized action stays authorized) but no other surveyed project surfaces it.

---

## 5. Implications for Finance Suite

The findings below follow the per-finding format mandated by task card §3.

---

```
Research Finding:    No surveyed open-source multi-agent framework defines Agent Identity distinct from User Identity at a cryptographic or authentication layer.
Source:              GitHub — agentcommunity/agent-interface-discovery (AID); CrewAI, AutoGen, AG2, MetaGPT, MAF (READMEs)
Observation:         All surveyed frameworks treat agent identity as a `(role, goal, backstory)` or `(name, instructions)` declared in code/config. User identity, where present, is a runtime OAuth scope (gbrain) or credential chain (MAF). No project authenticates "agent X is acting on behalf of user Y" via a verifiable cross-party signature.
Pattern:             Convention-based role-as-identity, not protocol-based identity separation.
Applicability:       Informs morning's C Independent Verification question — independence is a property of the reviewer's environment, not a role label. Industry has no off-the-shelf primitive that would let Finance Suite's Reviewer agent prove "I am an independent runtime, not the same runtime as Producer."
Non-Claim:           This finding does NOT imply Finance Suite should adopt AID, build DNS-based identity, or treat this gap as requiring implementation. It only informs future Identity boundary discussion.
```

---

```
Research Finding:    "Organizational memory" has no converged definition across the surveyed projects — each implements a different substrate.
Source:              GitHub — gbrain (pgvector + graph), AG2 (KnowledgeStore + working.md), UA (knowledge-graph.json), FinRobot (provenance-tracked pipeline artifacts), LangGraph (checkpointed graph state), CrewAI (memory + checkpointing), MAF (session-based state).
Observation:         Substrates range from vector databases to JSON files to per-run workspace directories. None is called "organizational memory" by the maintainers; all are described as memory, knowledge, or state.
Pattern:             Plural substrates without a unifying abstraction.
Applicability:       Informs Morning Memory boundary work (Memory ≠ Runtime State; Reference ≠ Adopted State). Finance Suite's morning discussions about Organizational Memory have no industry template to import directly; the design question remains open.
Non-Claim:           This finding does NOT imply Finance Suite should pick one substrate or treat plurality as a problem. It only describes the landscape.
```

---

```
Research Finding:    Permission enforcement in surveyed frameworks is implemented as per-agent tool allow-listing or middleware — not as audited policy files.
Source:              GitHub — gbrain (OAuth 2.1 scopes), CrewAI (per-agent tools=[...]), OpenClaw (per-agent tool permissions), MAF (middleware + credential chains), AutoGen (AgentTool wrapping).
Observation:         No project publishes a separate policy file that an auditor can review without reading code. Enforcement lives in code that wires tools to agents.
Pattern:             Code-as-policy, not file-as-policy.
Applicability:       Informs morning's governance work where policy files (e.g., Claim Impact Model) are the auditor's primary artifact. Finance Suite's separation of policy from code is not industry default — it is a deliberate choice that may need explicit tooling.
Non-Claim:           This finding does NOT imply Finance Suite should keep code-as-policy or move to file-as-policy. It only describes the contrast.
```

---

```
Research Finding:    HITL is consistently implemented as a single point of approval, not as a continuous verification layer.
Source:              GitHub — LangGraph (interrupts), AG2 (context.input + hitl_hook), CrewAI (HITL support), MAF (middleware + don't-ask-again approval).
Observation:         All surveyed projects pause execution at a known point and ask a human. None implements periodic independent verification of an agent's reasoning chain in the background.
Pattern:             Synchronous approval gate.
Applicability:       Informs the Independent Verification Boundary question raised in Q1. Finance Suite's morning governance established that independence is environmental — industry HITL patterns do not natively address this; any environmental separation would be additive.
Non-Claim:           This finding does NOT imply Finance Suite should add background verification or that HITL is insufficient. It only notes the absence of a pattern.
```

---

```
Research Finding:    Only one surveyed project (MetaGPT) treats multi-agent collaboration as a software-company SOP; only one (UA) embeds a named verification agent; only one (AG2) surfaces a write-ahead log as audit primitive.
Source:              GitHub — FoundationAgents/MetaGPT; Lum1104/Understand-Anything; ag2ai/ag2.
Observation:         The "organization as multi-agent system" metaphor has multiple non-overlapping implementations. Each is a single-source pattern — cross-references do not exist.
Pattern:             Single-source patterns lack maturity triangulation.
Applicability:       Informs future windows where Finance Suite might consider borrowing a specific pattern (e.g., UA's `graph-reviewer`). Single-source patterns should be treated as experimental — their maturity cannot be triangulated.
Non-Claim:           This finding does NOT imply Finance Suite should not borrow single-source patterns. It only notes the maturity signal.
```

---

```
Research Finding:    Engine router as a test/prod divergence boundary appears in OpenClaw-TradingAgents, gbrain, and AG2 — three projects, three different motivations.
Source:              GitHub — gaaiyun/TradingAgents-OpenClaw-Skill; garrytan/gbrain; ag2ai/ag2.
Observation:         The same mechanism (one named entrypoint that dispatches to different backends) appears because of three distinct needs: (1) CI without API keys (TradingAgents), (2) query-mode tradeoffs (gbrain), (3) classic-vs-v1 fork (AG2).
Pattern:             Engine router as a structural response to test/prod divergence.
Applicability:       Informs Finance Suite's distinction between Local Runtime ≠ Production Capability (feedback_local_runtime_not_production_capability.md). An engine-router-shaped primitive would let Finance Suite distinguish "runtime that can produce a research note" from "runtime that can publish to production" — but the design is open.
Non-Claim:           This finding does NOT imply Finance Suite should add an engine router or that the existing dual-runtime model is wrong. It only describes a structural alternative.
```

---

```
Research Finding:    The "Harness" vocabulary introduced by Microsoft Agent Framework (2026-07-08 docs) is not yet echoed in any other surveyed OSS project.
Source:              Microsoft Learn — Microsoft Agent Framework Overview (docs page dated 2026-07-08).
Observation:         MAF names three primitives: Agents (individual), Harness (opinionated agent with planning + memory + tool approval + observability), Workflows (graph-based multi-agent composition). No other surveyed project uses "Harness" as a primitive name.
Pattern:             Recent (and unverified-by-others) vocabulary introduction.
Applicability:       Informs the morning's question of whether morning frictions are "process design problems that better procedures can solve" or "evidence that future Agent systems require an organizational-level Harness as native infrastructure." The vocabulary itself appears to be converging on "Harness" as the name for that infrastructure — but this is a single source and may not stabilize.
Non-Claim:           This finding does NOT imply Finance Suite should adopt "Harness" terminology or treat MAF as the reference architecture. It only notes that the term is recent and unverified.
```

---

```
Research Finding:    No surveyed open-source project includes a separate Producer ≠ Reviewer separation enforced by environment rather than role.
Source:              GitHub — UA (graph-reviewer is a separate agent, but in the same environment), MetaGPT (roles, no separate env), FinRobot (bull/bear/judge same env), CrewAI (manager agent same env).
Observation:         Where a "reviewer" exists, it is typically a peer agent in the same runtime. The closest analogue to environmental separation is AID's PKA handshake — which verifies the endpoint, not the runtime environment.
Pattern:             Role-based separation, not environment-based separation.
Applicability:       Informs morning's C Independent Verification finding — independence is a property of the reviewer's environment. Industry does not have a turnkey primitive for environment-level separation; the gap is real.
Non-Claim:           This finding does NOT imply Finance Suite must build environment-level separation primitives. It only describes the gap.
```

---

## 6. Non-adoption statement

This report is **reference research only**. It does not authorize, recommend, or imply:

- Adoption of any project listed in §1 into Finance Suite's production stack.
- Implementation of any pattern listed in §3 or §4 in Finance Suite's runtime.
- Replacement of any existing Finance Suite mechanism (watchlist, skill registry, MCP server, evidence manifests, governance windows).
- Modification to Governance Design Review v0.1, R1 Identity Reconciliation, C Independent Verification Setup, or any other morning governance artifact.
- Roadmap commitment, timeline, or sequence for any future work.
- A position on whether morning governance frictions are process problems or evidence of an organizational-Harness requirement.

The output is observation of an external landscape as it appeared on 2026-08-05. Project stars, commits, and last-commit dates are **visibility at fetch time**, not maturity claims. Where a project is described as "active" or "in maintenance mode," this reflects the README's own badge or statement, not independent verification by Finance Suite.

This report does not advance the RRA / Owner Assignment / Closure chain. The Org-Level Agent Harness Research window remains OPEN. Implementation is NOT AUTHORIZED. Push is FORBIDDEN.

---

**End of report**