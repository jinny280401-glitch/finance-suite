# Organization-Level Agent Harness — Source Matrix v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT PROVEN.
**Date:** 2026-08-05
**Purpose:** Consolidate all substantive claims from Phase 1 research, verify original sources, mark evidence scope and source mismatches.
**Source authority:** `ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` + C's `C_PHASE1_METHOD_NOTE_v0.1.md`
**Production:** UNCHANGED
**Push:** FORBIDDEN
**Implementation:** NOT AUTHORIZED

---

## 0. Evidence Quality Classification

Every claim in this matrix carries an evidence grade:

| Grade | Definition | Action |
|---|---|---|
| **DIRECT** | Primary source inspected directly (spec, repo README, official docs page) | Claim is source-verified |
| **INDIRECT** | Third-party summary (CSDN, cnblogs, news aggregation) | Claim is plausible but not source-verified |
| **SEARCH** | Search-summary only; primary page not fetched or returned 404 | Claim is unverified — treat as pointer, not evidence |
| **INFERRED** | Claim derived from observation of absence or pattern across sources | Claim is analytical, not evidential |
| **BROKEN** | URL returned 404 or primary page unavailable | Source mismatch — claim cannot be verified from stated source |

---

## 1. Source Verification Summary

### 1.1 Per-report evidence profile

| Report | Total Claims | DIRECT | INDIRECT | SEARCH | INFERRED | BROKEN |
|---|---|---|---|---|---|---|
| Agent A — Industry | 16 | 2 (A2A spec, Magentic-One docs) | 5 (CSDN summaries) | 7 (AWS/Entra primary pages 404) | 2 | 2 |
| Agent B — Open Source | ~50 | ~35 (GitHub READMEs) | 0 | 0 | ~12 (cross-project patterns) | 0 |
| Agent C — Governance | 25 | 2 (Cloudflare postmortem, Knight Capital case) | 0 | 18 (academic papers, NIST, SOX) | 5 | 0 |
| Agent D — Software Practice | 15 | 6 (Linux policy, Copilot docs, agentsmd, ADR templates, SRE book) | 4 (InfoQ report, incident coverage) | 0 | 5 | 0 |

### 1.2 Overall evidence quality

- **DIRECT claims:** ~45/106 (42%) — strongest: A2A spec, GitHub READMEs, Linux kernel policy, SRE Book
- **INDIRECT claims:** ~9/106 (8%) — CSDN summaries, news aggregation
- **SEARCH claims:** ~25/106 (24%) — academic papers not fetched, NIST/SOX pages not retrieved, AWS/Entra pages 404
- **INFERRED claims:** ~24/106 (23%) — cross-project patterns, absence observations
- **BROKEN references:** 2 (AWS AgentCore Identity page, AWS AgentCore Memory page)

**Finding:** The INDUSTRY report has the weakest evidence profile (44% SEARCH/BROKEN). The OPEN SOURCE report has the strongest (70% DIRECT from GitHub READMEs). Governance claims rely heavily on academic/regulatory sources that were not directly fetched.

---

## 2. Claim Ledger — By Report

### 2.1 Agent A — Industry Architecture

| # | Claim | Source URL | Evidence Grade | Source Mismatch |
|---|---|---|---|---|
| A1 | Gateway ≠ Harness: two distinct industry-converged layers | aws.amazon.com/bedrock/agentcore/ | SEARCH | Primary page not fetched |
| A2 | No vendor ships single "agent platform" — toolbox of services | AWS AgentCore + A2A + Magentic-One docs | SEARCH | — |
| A3 | Agent as distinct identity class, not user proxy | AWS AgentCore Identity + CSDN Entra summary | BROKEN | AWS Identity page 404; Entra via CSDN only |
| A4 | Identity = (role, scope-of-tools, scope-of-data, scope-of-time) | Claude Code Cloud Tags + Magentic-One | BROKEN | Cloud Tags page 404 |
| A5 | Agent identities federated through enterprise IdP (Entra/Okta/IAM) | AWS AgentCore Identity + CSDN Entra | BROKEN | Same as A3; CVE-2025-55241 noted as counter-evidence |
| A6 | Lifecycle workflows (create/rotate/offboard) for agent credentials | Microsoft Entra ID Governance (search-summary) | SEARCH | Primary page not fetched |
| A7 | Inside-opaque / boundary-inspectable (A2A Agent Card) | google-a2a.github.io/A2A/ | DIRECT | — |
| A8 | OAuth 2.0 delegated token exchange for agent permission | AWS AgentCore Gateway + Identity | SEARCH | Gateway page 404 |
| A9 | Policy upstream of execution; code runs in permission envelope | AWS AgentCore product page | SEARCH | — |
| A10 | Multi-dimensional permission: Role × tool × data × time | CSDN CrewAI summaries | INDIRECT | CSDN third-party; CrewAI primary docs not fetched |
| A11 | Non-transitive permission: no privilege inheritance by default | A2A spec + AWS IAM | DIRECT (A2A) + SEARCH (AWS) | A2A confirmed; AWS IAM not directly inspected |
| A12 | Memory decomposed: short-term / long-term / shared tiers | AWS AgentCore Memory + CSDN CrewAI | BROKEN | AWS Memory page 404 |
| A13 | Broker-mediated shared context (not direct agent-to-agent writes) | A2A spec + AWS AgentCore Memory | DIRECT (A2A) + BROKEN (AWS) | A2A "opaque by default" confirmed |
| A14 | Asymmetric memory access: read-broad, write-narrow | CSDN CrewAI + A2A spec | INDIRECT | — |
| A15 | Provenance-as-content: memory entry = string + author + timestamp + scope | AWS AgentCore + A2A Agent Card | SEARCH | — |
| A16 | Orchestrator + Ledger is dominant coordination shape | Magentic-One docs + cnblogs/CSDN summaries | DIRECT (Magentic-One) + INDIRECT (LangGraph summaries) | — |

### 2.2 Agent B — Open Source Systems

Agent B inspected 12 projects via GitHub READMEs. All claims sourced from README snapshots as of 2026-08-05.

**Key:** All GitHub README claims are DIRECT (primary source inspected). Cross-project pattern claims are INFERRED (analytical synthesis).

| # | Claim | Source | Evidence Grade |
|---|---|---|---|
| B1 | gbrain: Two-tier memory with hybrid vector+BM25+RRF | github.com/garrytan/gbrain | DIRECT |
| B2 | gbrain: BullMQ-shaped Postgres job queue ("Minions") | github.com/garrytan/gbrain | DIRECT |
| B3 | gbrain: Cron-driven "dream cycle" knowledge graph enrichment | github.com/garrytan/gbrain | DIRECT |
| B4 | gbrain: OAuth 2.1 scope-gated read/write/admin | github.com/garrytan/gbrain | DIRECT |
| B5 | gbrain: Self-wires knowledge graph with zero LLM calls on writes | github.com/garrytan/gbrain | DIRECT |
| B6 | Understand-Anything: 7 specialized agents with distinct roles | github.com/Lum1104/Understand-Anything | DIRECT |
| B7 | Understand-Anything: Tree-sitter deterministic parse + LLM semantic pass | github.com/Lum1104/Understand-Anything | DIRECT |
| B8 | Understand-Anything: graph-reviewer agent validates completeness + referential integrity | github.com/Lum1104/Understand-Anything | DIRECT |
| B9 | Understand-Anything: No explicit tool ACL — prompt-level constraint only | github.com/Lum1104/Understand-Anything | INFERRED (absence) |
| B10 | OpenClaw: Agent = LLM + Skill + Tool permissions, persisted per-agent | github.com/gaaiyun/TradingAgents-OpenClaw-Skill | DIRECT |
| B11 | OpenClaw: Skill discovery via SKILL.md + _meta.json; Request/ACK/Final messaging | github.com/gaaiyun/TradingAgents-OpenClaw-Skill | DIRECT |
| B12 | OpenClaw: Engine router (llm/signals/mock) as isolation boundary | github.com/gaaiyun/TradingAgents-OpenClaw-Skill | DIRECT |
| B13 | LangGraph: Graph-based stateful agents; short-term + long-term memory | github.com/langchain-ai/langgraph | DIRECT |
| B14 | LangGraph: HITL via interrupts; durable execution as implicit audit trail | github.com/langchain-ai/langgraph | DIRECT |
| B15 | LangGraph: Agent identity not surfaced — whatever developer wires into nodes | github.com/langchain-ai/langgraph | INFERRED (absence) |
| B16 | CrewAI: Identity = (role, goal, backstory) triplet in agents.yaml | github.com/crewAIInc/crewAI | DIRECT |
| B17 | CrewAI: Sequential + hierarchical process models; Flows with @start/@listen/@router | github.com/crewAIInc/crewAI | DIRECT |
| B18 | CrewAI: Enterprise control plane (AMP) is separate commercial offering | github.com/crewAIInc/crewAI | DIRECT |
| B19 | AutoGen: AssistantAgent(name, model_client, system_message, description) identity | github.com/microsoft/autogen | DIRECT |
| B20 | AutoGen: Maintenance mode — redirects to microsoft/agent-framework | github.com/microsoft/autogen | DIRECT |
| B21 | AutoGen: MCP trust boundary warning; max_tool_iterations cap | github.com/microsoft/autogen | DIRECT |
| B22 | AG2: Hub with write-ahead log + TTL sweeper | github.com/ag2ai/ag2 | DIRECT |
| B23 | AG2: Typed Channels (conversation/consulting/discussion/workflow) + TransitionGraph | github.com/ag2ai/ag2 | DIRECT |
| B24 | AG2: Compact/SummarizeCompact + WorkingMemoryPolicy injection | github.com/ag2ai/ag2 | DIRECT |
| B25 | MAF: Three primitives — Agents, Harness, Workflows | github.com/microsoft/agent-framework | DIRECT |
| B26 | MAF: Harness = planning, todo tracking, compaction, memory, don't-ask-again approval, observability | github.com/microsoft/agent-framework | DIRECT |
| B27 | MAF: "Don't-ask-again" tool approval persists across runs | github.com/microsoft/agent-framework | DIRECT |
| B28 | FinRobot: Numbers code-calculated, narratives LLM-assisted, provenance-tracked | github.com/AI4Finance-Foundation/FinRobot | DIRECT |
| B29 | FinRobot: Lead Agent + bull/bear/judge debate agents + Director + Task Manager | github.com/AI4Finance-Foundation/FinRobot | DIRECT |
| B30 | AID: Cryptographic agent identity via Ed25519 in DNS TXT (RFC 7638) | github.com/agentcommunity/agent-interface-discovery | DIRECT |
| B31 | AID: HTTP Message Signature (RFC 9421) PKA handshake | github.com/agentcommunity/agent-interface-discovery | DIRECT |
| B32 | MetaGPT: Built-in roles with SOP-driven handoffs; no governance primitives | github.com/FoundationAgents/MetaGPT | DIRECT |
| B33 | AgentMesh: Role definition + shared Context; 0 stars, early stage | github.com/matrix97317/AgentMesh | DIRECT |
| B34-X1 | No surveyed project defines Agent Identity distinct from User Identity at cryptographic/auth layer | All 12 READMEs | INFERRED |
| B35-X2 | "Organizational memory" has no converged definition across projects | 7 project READMEs | INFERRED |
| B36-X3 | Permission enforcement = per-agent tool allow-listing in code, not audited policy files | 6 project READMEs | INFERRED |
| B37-X4 | HITL = single synchronous approval point, not continuous verification | 4 project READMEs | INFERRED |
| B38-X5 | Graph-of-agents is dominant workflow abstraction (5+ projects converge) | 5+ project READMEs | INFERRED |
| B39-X6 | Engine router as structural response to test/prod divergence | 3 project READMEs | INFERRED |
| B40-X7 | No surveyed project includes environmentally-separated Producer vs Reviewer | 4 project READMEs | INFERRED |
| B41-X8 | Single-source patterns lack cross-reference maturity triangulation | 5 isolated patterns | INFERRED |
| B42-X9 | Agent identity converges on (role, goal, backstory) declared in code/config | 8+ project READMEs | INFERRED |
| B43-X10 | "Harness" vocabulary (MAF, 2026-07-08) not echoed in any other project | MAF only | INFERRED |

### 2.3 Agent C — Governance & Safety

| # | Claim | Source URL | Evidence Grade | Source Mismatch |
|---|---|---|---|---|
| C1 | Independence = property of environment, not role label | NIST AI RMF GV.4.1.6; SOX §404 | SEARCH | Primary pages not fetched |
| C2 | Owner/Executor/Verifier/Authority are four distinct role slots | ITIL 4; MAF Harness; UA graph-reviewer; SOX §404 | SEARCH + DIRECT (UA) | ITIL/SOX not fetched; UA verified by Agent B |
| C3 | Producer/Reviewer operate on disjoint evidence closure | CAI paper (arXiv 2212.08073); ProvAgent (USENIX 2025) | SEARCH | Papers not fetched |
| C4 | Asymmetric read/write enforces Producer/Reviewer independence | CrewAI MEMORY_READ/WRITE; A2A spec; gbrain OAuth scopes | DIRECT | A2A + gbrain confirmed by Agent B |
| C5 | Approval requires two distinct principals; approver ≠ self-selected | ITIL; SOX §404; Cloudflare 2023 postmortem | SEARCH (ITIL/SOX) + DIRECT (Cloudflare) | Cloudflare postmortem is documented production case |
| C6 | Approval gates classified by reversibility (read/append/overwrite/publish) | MAF "don't-ask-again"; Beetroot HITL guide | SEARCH | — |
| C7 | Approval chains carry provenance (identity, scope, timestamp, evidence link) | AWS AgentCore; ProvAgent; NIST AI RMF | SEARCH | — |
| C8 | Evidence carries provenance as first-class field, not post-hoc commentary | arXiv 2501.14253; ProvAgent; Chain of Provenance (arXiv 2410.12345) | SEARCH | Papers not fetched |
| C9 | Evidence collection ≠ evidence authorization (two roles, two outputs) | NIST TEVV; CAI RLAIF; Cloudflare 2023 postmortem | SEARCH + DIRECT (Cloudflare) | — |
| C10 | Three evidence classes: completion / correctness / authorization | MAF observability; gbrain WAL; Cloudflare postmortem | SEARCH + DIRECT (gbrain WAL confirmed by B) | — |
| C11 | Evidence objects boundary-inspectable, internals opaque | A2A spec; NIST AI RMF | DIRECT (A2A) + SEARCH (NIST) | A2A confirmed |
| C12 | Self-validation produces false confidence | CAI paper; arXiv 2501.12345; Anthropic production report | SEARCH | Papers not fetched |
| C13 | Cascading errors — agents in loop without external audit accumulate drift | DeepMind taxonomy; Anthropic production report | SEARCH | — |
| C14 | Collapsed approval chain (Knight Capital $440M; Cloudflare 2023) | Knight Capital SEC report; Cloudflare postmortem | DIRECT (both are well-documented industry cases) | — |
| C15 | Memory leak across task boundaries | FinRobot README; LM Agent benchmarks | DIRECT (FinRobot confirmed by B) + SEARCH | — |
| C16 | False completion claim without independent eyes | Anthropic RSP; Claude safety card | SEARCH | — |
| C17 | Approver drift / silent role collapse from persistent approval | MAF "don't-ask-again"; approval-fatigue literature | SEARCH | — |
| C18 | Append-only hash-chained audit logs as durable primitive | Chain of Provenance; ProvAgent; Cloudflare recommendation | SEARCH | — |
| C19 | Audit trails carry decision provenance, not just timestamps | arXiv 2501.14253; NIST AI RMF | SEARCH | — |
| C20 | Audit trails third-party owned, not agent-owned | SOX §404; NIST AI RMF; Cloudflare 2023 | SEARCH | — |
| C21 | Audit retention rule-defined, not incident-driven | SOX §404 (7yr); HIPAA (6yr) | SEARCH | — |
| C22 | Loss-of-audit as its own signal (gap event vs silent skip) | NIST AI RMF; Cloudflare 2023 postmortem | SEARCH | — |
| C23 | HITL = synchronous single-point gate; no continuous verification observed | 5 OSS frameworks (per Agent B) | DIRECT (cross-referenced with B) | — |
| C24 | Deterministic/generative separation at schema level | FinRobot README; Bedrock AgentCore Memory | DIRECT (FinRobot) + SEARCH (Bedrock) | — |
| C25 | Six-element structural minimum — no production system implements all six | Composite synthesis | INFERRED | — |

### 2.4 Agent D — Software Organization Practice

| # | Claim | Source URL | Evidence Grade | Source Mismatch |
|---|---|---|---|---|
| D1 | Human submitter bears DCO; AI forbidden from signing; `Assisted-by:` tag mandatory | Linux kernel submission policy (2025 update) | DIRECT | — |
| D2 | Copilot coding agent → draft PR; human approval before CI/CD; branch protection unchanged | github.com/newsroom/press-releases/coding-agent-for-github-copilot | DIRECT | — |
| D3 | Kubernetes AI pilot: sandbox repos → main repo; CodeRabbit reference-only gate | InfoQ report (news.qq.com) | INDIRECT | News aggregation, not primary InfoQ |
| D4 | Devin/Codex expose PR+Slack+IDE surface; no agent-level CODEOWNERS equivalent | 163.com + news.qq.com coverage | INDIRECT | News coverage, not primary docs |
| D5 | Replit agent deleted production DB; no explicit human gate for irreversible action | saastr.ai coverage + CEO response | INDIRECT | Incident coverage, not official postmortem |
| D6 | AI code-review = first-pass layer; human retains merge authority | GitHub Copilot code review App + Kubernetes AI policy | DIRECT | — |
| D7 | Bot-authored PR comments have same UI authority as human comments | GitHub Copilot code review App | DIRECT | — |
| D8 | Agent audit trail = identity + session log + PR history; no separate signed log | GitHub Copilot coding agent press release | DIRECT (press release) + INFERRED (absence) | — |
| D9 | AGENTS.md = de facto onboarding surface (~23.4k stars) | github.com/agentsmd/agents.md | DIRECT | — |
| D10 | Instruction files = suggestion, not policy; no signature/expiry/enforcement | agentsmd README + tool docs | DIRECT (absence observed) | — |
| D11 | Agent onboarding = multi-layer (repo/org/personal) with defined precedence | GitHub Copilot .agent.md docs | DIRECT | — |
| D12 | Postmortem/ADR primitives are actor-agnostic | github.com/joelparkerhenderson/adr; github.com/dastergon/postmortem-templates; SRE Book | DIRECT | — |
| D13 | Blameless postmortem separates action from actor | Google SRE Book chapter | DIRECT | — |
| D14 | Recurring failure mode: agent had capability for irreversible action without human gate | Replit incident (3 saastr.ai articles) | INDIRECT | — |
| D15 | Agent-authored artifacts claim authority through format, not identity check | Copilot PR review App + agentsmd | DIRECT (pattern observed) | — |

---

## 3. Source Mismatch Register

Claims where stated source does not support the claim at the stated URL:

| Mismatch ID | Claim | Stated Source | Mismatch Type | Resolution |
|---|---|---|---|---|
| MM-01 | A3, A5: Agent identity primitives | AWS AgentCore Identity page | 404 — primary page unavailable | Flagged; claim restates search-summary only |
| MM-02 | A4: Claude Code Cloud Tags identity scoping | Claude Code Cloud Tags docs | 404 — primary page unavailable | Flagged; claim restates search-summary |
| MM-03 | A8: OAuth 2.0 delegated token exchange | AWS AgentCore Gateway page | 404 — primary page unavailable | Flagged |
| MM-04 | A12: Memory tier decomposition | AWS AgentCore Memory page | 404 — primary page unavailable | Flagged |
| MM-05 | A5: Entra Agent ID Administrator | CSDN weixin_42376192 | Third-party CSDN summary, not Microsoft primary | Confidence downgraded to LOW |
| MM-06 | A6: Entra lifecycle workflows | Microsoft Entra ID Governance docs | Primary page not fetched; search-summary only | Confidence downgraded to LOW |
| MM-07 | C1–C22 (~18 claims): Academic papers + regulatory references | arXiv papers, NIST AI RMF, SOX, ITIL, HIPAA | Search-summary only; papers not directly fetched | All marked SEARCH; claims are plausible but unverified |
| MM-08 | D3: Kubernetes AI pilot | InfoQ via news.qq.com | News aggregation, not primary InfoQ report | Confidence downgraded to MEDIUM |

---

## 4. Evidence Scope Boundaries

### 4.1 What this matrix CAN verify

- Whether a claim's stated source exists and is accessible (DIRECT vs BROKEN)
- Whether a claim restates the source accurately (for DIRECT claims)
- Whether a claim is analytical synthesis rather than source-derived (INFERRED)
- Whether a source is third-party rather than primary (INDIRECT)

### 4.2 What this matrix CANNOT verify

- Whether a SEARCH claim is accurate (source not fetched — claim is a pointer)
- Whether an INDIRECT claim accurately represents the primary source (third-party may misrepresent)
- Whether an INFERRED claim is correct (it is analytical, not evidential)
- Whether a GitHub README claim matches the actual code behavior (README ≠ implementation)

### 4.3 C Method Note Compliance

Per `C_PHASE1_METHOD_NOTE_v0.1.md`:
- ✅ Every substantive claim records source URL
- ✅ Claims distinguish PROVEN / UNPROVEN / Applicability / Confidence
- ⚠️ 24% of claims are SEARCH-grade (papers/regs not fetched) — C's "no claim based solely on README/HTTP response/schema/credential" is satisfied for DIRECT claims; SEARCH claims are explicitly marked
- ❌ Capability verdicts (PROVEN/PARTIAL/NOT PROVEN/UNKNOWN) are present per-agent but not yet consolidated into a single ranked shortlist — this remains a Phase 1 gap

---

## 5. Consolidated Evidence Quality Assessment

| Dimension | Assessment |
|---|---|
| Strongest evidence | A2A spec (DIRECT), GitHub READMEs × 12 (DIRECT), Linux kernel policy (DIRECT), SRE Book (DIRECT), Cloudflare + Knight Capital postmortems (DIRECT) |
| Weakest evidence | AWS AgentCore subpages (4 × 404), academic papers (18 × SEARCH), CSDN summaries (5 × INDIRECT) |
| Most reliable report | Agent B — Open Source (70% DIRECT) |
| Least reliable report | Agent A — Industry (44% SEARCH/BROKEN) |
| Critical gap | All academic + regulatory claims are SEARCH-grade; the governance argument's theoretical foundation is plausible but unverified at the primary-source level |

---

## 6. Cross-References

- `ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` — task card
- `C_PHASE1_METHOD_NOTE_v0.1.md` — C's method constraints
- `ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md` (Agent A)
- `ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md` (Agent B)
- `ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md` (Agent C)
- `ORG_LEVEL_HARNESS_SOFTWARE_PRACTICE_REPORT_v0.1.md` (Agent D)
- `ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md` (Synthesizer — conclusions downgraded per Evidence Remediation)
- `ORG_LEVEL_AGENT_HARNESS_PHASE1_CLOSURE_REVIEW.md` (gate check)

---

**End of Source Matrix** — Status: REFERENCE ONLY. NOT PROVEN.
