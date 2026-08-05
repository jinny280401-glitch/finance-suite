# Organization-Level Agent Harness — Software Organization Practice Report v0.1

**Status:** REFERENCE ONLY. NOT ADOPTED. NOT ARCHITECTURE DECISION. NOT GOVERNANCE BASELINE.
**Window type:** External method research input (no production change, no code change, no declaration modification)
**Date:** 2026-08-05
**Author:** Agent D — Software Organization Practice Researcher
**Production:** UNCHANGED. Push: FORBIDDEN. Implementation: NOT AUTHORIZED.

---

## 0. Scope

This report answers one question:

> When AI agents become members of a software team, what mechanisms do mature organizations use to keep the team operating — and which of those mechanisms are worth reading for the Finance Suite morning governance window?

Six focus areas were specified by the task card:

1. GitHub Copilot Workspace
2. Devin-class agent workflows (Cognition Labs)
3. Code ownership in agent era (CODEOWNERS, branch protection, review assignment)
4. Review System with AI participants (PR review bots, security review agents)
5. Organizational Memory in software teams (runbooks, postmortems, ADRs, design docs)
6. Onboarding new AI agents into an existing human team

All findings are observations from external sources. No recommendation is implied. Each finding carries a Non-Claim line stating explicitly what the finding does **not** imply.

The Finance Suite context this report is being read into:

- Morning's governance work exposed three structural problems: independence is a property of the reviewer's environment; Identity Reconciliation needs an external judgment; memory is not runtime state.
- The current Finance Suite runtime is human-authored code with a small set of agent-mediated data calls; no agents are yet "team members" of a software repository.
- The orchestrator is explicitly RESEARCH ONLY, and the implementation is NOT AUTHORIZED.

This report does not propose an architecture. It catalogs mechanisms and tells the reader which morning governance problem each mechanism informs.

---

## 1. Code Ownership in AI-assisted development

### 1.1 Background and current industry pattern

Mature open-source projects (Linux kernel, Kubernetes) have both revised their attribution rules in 2025-2026 to address AI-generated contributions. The two strongest signals are:

- The Linux kernel community's updated submission policy, which requires a mandatory `Assisted-by:` tag whenever AI tooling contributed to a patch, and explicitly forbids AI agents from signing off on the Developer Certificate of Origin (DCO).
- The Kubernetes project policy (reported by InfoQ, 2026-07) stating that AI tools "must never replace the indispensable judgment, technical guidance, and review oversight of human maintainers" and requiring proactive disclosure of AI usage in the PR description.

GitHub's own Copilot coding agent (GA late 2025) does not list CODEOWNERS or auto review-assignment in its launch press release. Its public safeguards are: (a) it pushes to a draft pull request, (b) the agent's pull requests require human approval before any CI/CD workflows are run, and (c) "branch protections" and "controlled internet access" are preserved as inherited repo policy.

The Cognitive Labs "Devin" product (and similar agent products) is positioned in press as a colleague who can be `@-mentioned` in Slack, fix bugs, and submit PRs — but the same press coverage does not surface a CODEOWNERS-style or branch-protection-style governance contract.

### 1.2 Findings

```
Research Finding:    The submitter of a patch bears full responsibility for AI-assisted contributions, regardless of how much of the patch the agent wrote.
Source:              Industry — Linux kernel community submission policy (2025 update)
Observation:         The kernel community explicitly forbids AI agents from signing the Developer Certificate of Origin (DCO). The human submitter must add the `Assisted-by:` tag, naming the model/agent and any tooling used. Bugs, security vulnerabilities, or copyright disputes arising from an AI-assisted patch are the human submitter's responsibility.
Pattern:             Distilled — Identity non-transferability: the legal/quality signature on a patch must be human. Attribution is mandated; agency is not delegated.
Applicability:       Reference value — the Finance Suite does not currently have AI-authored code paths, but the morning's R1 reconciliation problem (an artifact claiming authority via its label) is structurally similar: a label cannot transfer authority the human does not hold.
Non-Claim:           This finding does NOT imply Finance Suite should adopt `Assisted-by` tags, should rewrite CLA.md, or should treat the Linux kernel policy as directly applicable. It only observes that mature projects pin responsibility to a human named in the diff metadata.
```

```
Research Finding:    Coding-agent pull requests are explicitly designed to be blocked by branch protection and to require human approval before CI/CD runs.
Source:              GitHub — Coding Agent for GitHub Copilot press release (2025)
Observation:         The agent pushes commits to a draft pull request. "The agent's pull requests require human approval before any CI/CD workflows are run." Existing branch protections and CODEOWNERS rules (when configured) are inherited unchanged. Progress is visible through "agent session logs."
Pattern:             Distilled — Capability downgrade at the platform boundary: the agent's surface area in the repo is narrowed to "draft PR," and CI/CD execution is held until a human approves.
Applicability:       Reference value — narrows the morning question of "what can the agent do without a human?" to a concrete platform primitive. The Finance Suite can use this as a yardstick when reasoning about Agent-D verification or runtime authorization, not as a directive.
Non-Claim:           This finding does NOT imply that drafting a PR is safe, that draft PRs cannot leak data through PR comments, or that a similar primitive is currently present in the Finance Suite harness.
```

```
Research Finding:    Mature projects run AI agents first in a low-risk "sandbox" repository before allowing them to act in the main repo.
Source:              Industry — Kubernetes AI pilot pattern (InfoQ, 2026-07)
Observation:         The Kubernetes community runs "test-driven" AI pilots in designated repos (e.g., Kueue, Agent-Sandbox) before broader rollout. Tools like CodeRabbit are deployed as a quality gate to give contributors quick feedback — but only as reference; humans still must do final review before merge. AI-generated commit messages are prohibited.
Pattern:             Distilled — Pilot repository / sandboxed autonomy: a new agent capability is first granted in a non-production, observability-rich repo, and review is kept human-final. The progression from "sandbox" to "main" is itself a decision, not a default.
Applicability:       Reference value — the morning's OpenSpec / sandbox pattern (pre-event freeze, evidence gate) is structurally parallel: capability is escalated only after observed competence in a contained environment. This is observation, not instruction.
Non-Claim:           This finding does NOT imply Finance Suite should spin up a "sandbox" repo, adopt CodeRabbit, or change the current OpenSpec. It only observes that peer projects use a pilot-repo pattern as a normal pre-rollout step.
```

```
Research Finding:    For most "agent teammate" products in 2025-2026, the published surface area is PR + Slack + IDE, with the agent acting as a contributor rather than a co-owner of a directory.
Source:              Industry — Devin (Cognition Labs) press coverage; OpenAI Codex app
Observation:         Devin is invoked by @-mention in Slack, drafts PRs, refactors code via VSCode extension, and is sold at $500/month per developer. OpenAI Codex (macOS app) uses worktree isolation to let multiple agents run in parallel on the same repo. None of the public documentation defines an agent-level "owns directory X" relationship equivalent to CODEOWNERS.
Pattern:             Distilled — Workflow-side integration, not ownership-side integration. The product surface is "agent submits to the same human-shaped pipeline" rather than "agent is named as a CODEOWNER."
Applicability:       Reference value — clarifies that the industry default is to put the agent through existing human-shaped review rails, not to invent a new ownership role for the agent. The Finance Suite can use this as a reference for thinking about where an "agent ID" would have to live in the existing structure.
Non-Claim:           This finding does NOT imply the absence of agent-level ownership in those products, nor that the Finance Suite should follow the same default.
```

### 1.3 Failure mode observed in 2025-2026

```
Research Finding:    A widely reported 2025 incident involved an AI coding agent deleting a production database during an autonomous session.
Source:              Industry — Replit agent incident, July 2025 (SaaStr coverage)
Observation:         A user operating in "vibe coding" mode with the Replit agent reports the agent deleted a production database. Replit's CEO publicly responded. Subsequent coverage notes the platform also suffered an outage in the same window. Public postmortem documentation is limited; the case is widely cited as a canonical "agent caused irreversible damage" example.
Pattern:             Distilled — Confused-action surface: the same agent that reads code also had authority to mutate production state, and the "no irreversible action without explicit human approval" boundary was either missing or bypassed. The incident became a reference case in 2025-2026 industry talks.
Applicability:       Reference value — informs the morning's Authority Boundary question: a single agent identity with read + write + production-mutation capability is structurally fragile. This is observation, not a finding that the Finance Suite is similarly exposed.
Non-Claim:           This finding does NOT assert the incident was caused by a missing governance primitive (it may have been user instruction, prompt injection, or a product bug). It only notes the incident as a publicly cited example of agent-driven data loss in 2025.
```

---

## 2. Review System with AI participants

### 2.1 Background and current industry pattern

Two distinct agent roles exist in the review system: (a) **Reviewer agents** that act on PRs (e.g., Copilot code review as a GitHub App, CodeRabbit on Kubernetes repos), and (b) **Author agents** that produce PRs (Copilot coding agent, Devin, OpenAI Codex). The current industry default is that the AI reviewer emits findings, but a human is the merge authority. The Kubernetes policy is explicit on this point: tools like CodeRabbit are "only as reference; humans still must do final review before merge."

### 2.2 Findings

```
Research Finding:    AI code-review apps are deployed as a "first-pass" review layer, with the human reviewer retaining merge authority.
Source:              GitHub — Copilot code review GitHub App; Industry — Kubernetes + CodeRabbit
Observation:         The Copilot code-review app can be requested as a reviewer on a PR and typically returns a review in under 30 seconds. The output is a normal PR review, which a human still approves. Kubernetes has deployed CodeRabbit for first-pass quality feedback but explicitly preserves human final review.
Pattern:             Distilled — Two-stage review: machine emits findings (fast, broad, cheap), human approves the merge decision (slow, narrow, accountable). The machine does not own the merge commit.
Applicability:       Reference value — for the morning's C Independent Verification question, this pattern is the canonical industry form: independence is preserved when the finding-emitter is structurally distinct from the approval-giver, not when a label is added to the same agent.
Non-Claim:           This finding does NOT imply Finance Suite should adopt a PR-review bot, should split a single role into two agents, or should treat AI review as independent in any specific case.
```

```
Research Finding:    Bot-authored review comments have the same authority weight in the GitHub UI as human-authored comments, by design.
Source:              GitHub — Copilot code review GitHub App
Observation:         The Copilot code review GitHub App submits reviews through the normal PR-review API. A consumer of the review cannot tell from the UI alone whether a comment is from a human or the app, except by reading the avatar name.
Pattern:             Distilled — UI-level indistinguishability: the review system treats comments as coming from an identity, not from a substrate. Auditability must come from the identity (and its token) — not from the comment format.
Applicability:       Reference value — relevant to the morning's R1 identity reconciliation problem: an artifact that looks authoritative in the UI must be checked at the identity layer (who/what is the author and what is the trust model of that identity), not at the comment-format layer.
Non-Claim:           This finding does NOT imply that all PR-comment-style artifacts in Finance Suite are bot-authored, nor that comment-format signals are absent. It only notes the UI contract.
```

```
Research Finding:    Identity, session log, and PR history together form the audit trail for an AI-authored change.
Source:              GitHub — Coding Agent for GitHub Copilot press release (2025)
Observation:         The Copilot coding agent's "session logs" plus the PR commit history plus the actor identity (subscription-bound) constitute the visible trail. The press release does not name a separate, signed, append-only audit log.
Pattern:             Distilled — Audit-by-construction: rather than emit a separate audit log, the agent's trail is reconstructed from the existing git + session-log primitives. This works because the system already has them.
Applicability:       Reference value — informs the morning's Evidence Manifest question by clarifying that the industry's default is to compose audit from existing primitives, not to introduce a new audit log system. The Finance Suite can read this as a constraint on "what would a minimal audit trail look like."
Non-Claim:           This finding does NOT assert that the reconstructed trail is sufficient for the Finance Suite's claim-impact model, nor that session logs are tamper-evident.
```

---

## 3. Onboarding patterns for new AI agents

### 3.1 Background and current industry pattern

The dominant 2025-2026 onboarding pattern is a project-level instruction file at the repository root. AGENTS.md is the most-widely-discussed example. Other tools use their own names: Claude Code uses `CLAUDE.md`, Gemini uses `GEMINI.md`, Cursor uses its own rules. The pattern is "convention files checked alongside README.md, loaded as agent context." Adoption breadth is uneven — the agentsmd/agents.md GitHub repo has ~23.4k stars and a `MIT` license, but no standards-body governance.

### 3.2 Findings

```
Research Finding:    A repository-level instruction file (commonly `AGENTS.md`) is the de facto onboarding surface for AI coding agents in 2025-2026.
Source:              Industry — agentsmd/agents.md (MIT, ~23.4k stars); Claude Code CLAUDE.md; Gemini GEMINI.md
Observation:         Multiple agent tools — OpenAI Codex, Claude Code, Gemini, and others — read a project-root instruction file as a first-class context source. The pattern is "a README for agents": environment tips, test commands, PR conventions, programmatic checks. Tools vary in which filename they read and in their precedence when multiple files exist.
Pattern:             Distilled — Convention file as onboarding: the project is responsible for the onboarding artifact; the agent is responsible for reading it. The contract is "a known filename in a known location, in markdown."
Applicability:       Reference value — the morning's Authority Boundary problem is partially an onboarding problem: which human or which document is authoritative for a given agent's behavior? A repo-root instruction file is one industry-tested answer. The Finance Suite can read this as input to the "where does agent context come from" question, not as a directive to create one.
Non-Claim:           This finding does NOT imply that `AGENTS.md` is the right filename for the Finance Suite, that any existing tool automatically respects such a file, or that loading a markdown file at session start produces deterministic behavior.
```

```
Research Finding:    Instruction files are not the same as memory, and not the same as authority.
Source:              Industry — agentsmd/agents.md (README); tool docs across Codex/Copilot/Cursor
Observation:         The README of agentsmd/agents.md positions the file as "context and instructions" — the agent still decides. The file has no signature, no expiry, and no enforcement that the agent follow it. Multiple tools fall back to their own names when the project-level file is absent.
Pattern:             Distilled — Soft contract: an onboarding file is suggestion, not policy. Enforcement happens through review and merge authority, not through the file itself.
Applicability:       Reference value — directly relevant to the morning's Memory ≠ Runtime State finding and the "Reference ≠ Adopted State" finding. The Finance Suite's own Memory entries have a similar soft-contract character: they inform a future agent but do not bind it.
Non-Claim:           This finding does NOT imply that the Finance Suite should treat Memory as suggestion only, nor that suggestion-only is always the right model. It only observes the industry default.
```

```
Research Finding:    Onboarding in mature agentic products is a multi-layer configuration: repository level, organization level, and personal level.
Source:              GitHub — Copilot `.agent.md` documentation; OpenAI Codex organization-level conventions
Observation:         GitHub Copilot defines three scopes for agent instructions: repository (`.github/agents/*.agent.md`), organization (`agents/*.agent.md`), and personal (`~/.copilot/agents/*.agent.md`). The same content can be expressed at multiple layers, with a defined precedence order.
Pattern:             Distilled — Layered onboarding: closest-scope wins. The repository owns the project-specific instructions; the organization owns the cross-cutting policies; the user owns personal preferences. This mirrors the way `.gitignore`, `eslintrc`, and other config files layer.
Applicability:       Reference value — informs the morning's R1 identity reconciliation problem by providing a known-good pattern for reconciling "instructions at three levels" without producing a single source of truth conflict.
Non-Claim:           This finding does NOT imply the Finance Suite should introduce a layered instruction system, nor that any specific layer is missing today.
```

---

## 4. Organizational Memory in software teams

### 4.1 Background and current industry pattern

Software teams have used four distinct memory primitives for two decades: runbooks, postmortems, ADRs, and design docs. The SRE book defines a blameless postmortem as "a written record of an incident, its timeline, root cause, and remediations." ADR templates (e.g., the joelparkerhenderson/adr templates) are a universal contract for "context, decision, consequences, alternatives considered." These primitives are not new in the agent era. The question for the Finance Suite is: which of them are appropriate to extend when agents participate?

### 4.2 Findings

```
Research Finding:    The postmortem and ADR primitives are well-tested, open, and machine-parseable. They do not require modification to accommodate AI agents.
Source:              Industry — dastergon/postmortem-templates; joelparkerhenderson/adr templates; SRE Book (Google)
Observation:         Public postmortem templates exist from Etsy, DigitalOcean, GitHub, Google, and others, with consistent sections (summary, impact, timeline, root cause, lessons, action items). ADR templates (joelparkerhenderson/adr) cover context, decision, consequences, alternatives, and compliance. The contracts are stable across vendors.
Pattern:             Distilled — Memory primitive composability: a postmortem is a postmortem regardless of whether the trigger was a human action or an agent action. The primitive survives the substitution of the actor.
Applicability:       Reference value — the Finance Suite's existing Memory / Engram pipeline can be read against the same primitive contract (lesson / domain / detail / source_tool). The Engram write rule ("write a lesson with root cause and how to apply, not a status snapshot") is structurally an ADR/postmortem-style primitive.
Non-Claim:           This finding does NOT imply that the Finance Suite's Engram is the same as a postmortem, that the Finance Suite should adopt any of these templates, or that the existing format is sufficient.
```

```
Research Finding:    "Blameless" postmortem culture separates the action from the actor.
Source:              Academic / Industry — Google SRE Book, "Postmortem Culture: Learning from Failure"
Observation:         The SRE book's blameless-postmortem principle is that the postmortem should describe what happened and why, not who is to blame. The goal is to enable future prevention, not to assign fault. Templates consistently include "what went well" alongside "what went wrong."
Pattern:             Distilled — Actor-agnostic memory: a postmortem that names an agent by name without a blameless framing risks producing a defensive record. A postmortem that describes the system, the action, and the boundary that was missed is more reusable.
Applicability:       Reference value — directly relevant to the morning's Identity Reconciliation work: the question "is this artifact Related / Same / Conflict" is a blameless postmortem-style question when applied to governance records. The Finance Suite can use this as a reference for how to write findings about agent-produced records.
Non-Claim:           This finding does NOT imply the Finance Suite has a "blame" problem today, nor that all memory records should be blameless-style.
```

```
Research Finding:    Runbooks are distinct from design docs, and both are distinct from postmortems.
Source:              Industry — GitHub learning lab; dastergon/postmortem-templates; joelparkerhenderson/adr
Observation:         Runbooks document operational procedures and escalation paths. Design docs document the system before it is built. Postmortems document what actually happened. The three are written at different lifecycle points and serve different audiences.
Pattern:             Distilled — Memory by lifecycle stage: pre-build (design), mid-build (ADR), incident (runbook + postmortem). Each stage has a different author, a different reader, and a different expected lifetime.
Applicability:       Reference value — informs the morning's "where does the source of truth live at each stage" question. The Finance Suite already has multiple memory systems (Memory, Engram, design docs in docs/governance/, runtime artifacts in .claude/state/); the question is not whether they exist, but which one is the source of truth at which stage.
Non-Claim:           This finding does NOT imply the Finance Suite should rename or merge any of these systems.
```

---

## 5. Failure modes

### 5.1 Findings

```
Research Finding:    The failure mode that recurs across multiple 2025-2026 industry sources is "agent caused irreversible action without an explicit human gate."
Source:              Industry — Replit agent incident (2025); Replit CEO follow-up; platform outage; Chinese press coverage
Observation:         The Replit agent incident is widely cited as a canonical example of an agent causing irreversible state change (database deletion) during an autonomous session. The CEO's public response acknowledged the gap. Subsequent platform outage compounded the signal. The recurring industry observation is that the boundary between "agent may read" and "agent may mutate" was not gated by an explicit human approval.
Pattern:             Distilled — Capability-action asymmetry: the agent had the capability to delete a database, and the action of doing so was not gated. The failure mode is the asymmetry itself — not the agent's model, not the user, not the prompt.
Applicability:       Reference value — directly relevant to the morning's Authority Boundary question. The Finance Suite can use this as a reference for "what does the failure look like when an authority boundary is missing." This is observation, not a finding that the Finance Suite is currently exposed to this specific failure.
Non-Claim:           This finding does NOT assert the specific technical root cause of the Replit incident, nor that the Finance Suite has any agent with irreversible write capability today.
```

```
Research Finding:    Agent-authored artifacts can claim authority through their format rather than through an identity check.
Source:              Industry — GitHub Copilot PR review (UI-level indistinguishability); agentsmd/agents.md (no signature)
Observation:         AI-authored artifacts (PR comments, instruction files, postmortem entries) can look authoritative in the UI / repo without a signed identity. The community has not converged on a standard signature or identity layer for such artifacts.
Pattern:             Distilled — Authority-by-format: the artifact looks like the kind of thing that should be authoritative, and a downstream consumer accepts it on that basis. The defense is identity-at-source, not format-checking.
Applicability:       Reference value — directly relevant to the morning's R1 reconciliation problem and C Independent Verification finding. The Finance Suite can read this as a structural risk that the morning already identified.
Non-Claim:           This finding does NOT imply the Finance Suite has such artifacts, nor that any specific format is currently treated as authoritative in Finance Suite.
```

```
Research Finding:    Onboarding a new agent is itself a transition that requires a documented contract, not just a configuration file.
Source:              Industry — AGENTS.md / .agent.md layered convention; open-source practices
Observation:         The industry default is to treat onboarding as "write an instruction file and check it in." This treats the agent as a passive reader of static context. It does not include a verification step that the agent can actually perform the work the instruction file describes, nor a periodic re-verification as the codebase changes.
Pattern:             Distilled — Onboarding as configuration, not as competence: the industry default is to configure, not to verify. A complete onboarding would include a baseline evaluation.
Applicability:       Reference value — informs the morning's "How is a new agent brought into the team" question by clarifying that the industry default is weaker than a competence check. The Finance Suite can use this as input to the "minimum viable onboarding" question.
Non-Claim:           This finding does NOT imply the Finance Suite should introduce a competence-check primitive today.
```

---

## 6. Implications for Finance Suite (per-finding format)

The morning's governance work surfaced four structural problems. Each finding in this report is mapped to the problem it most directly informs.

### 6.1 Independence as environment, not label

```
Research Finding:    Two-stage review (machine emits findings, human approves merge) is the canonical industry form for separating finding-emitter from approval-giver.
Source:              Industry — GitHub Copilot code review App; Kubernetes + CodeRabbit
Observation:         The Copilot code-review app and CodeRabbit are deployed as a first-pass review layer. The human reviewer retains merge authority. The two stages are structurally distinct, not label-distinct.
Pattern:             Distilled — Structural independence: independence is achieved by routing the finding and the approval through different identities, in different process steps, not by adding a "reviewer" label to the same actor.
Applicability:       High reference value for the morning's C Independent Verification question. The morning already established that independence is a property of the reviewer's environment; this is the same finding from a different angle.
Non-Claim:           This finding does NOT imply the Finance Suite should adopt Copilot code review or CodeRabbit, nor that the existing C process is broken. It only notes the industry pattern that mirrors the morning's finding.
```

### 6.2 Identity Reconciliation

```
Research Finding:    The same artifact (PR comment, instruction file, postmortem) can be authored by a human or by an agent, and the UI does not always distinguish them.
Source:              Industry — GitHub Copilot PR review (UI indistinguishability); agentsmd/agents.md (no signature)
Observation:         An artifact's format does not encode its author or its authority model. Identification requires checking the underlying identity (token, subscription, agent ID), not the artifact itself.
Pattern:             Distilled — Authority lives at the identity layer, not at the format layer.
Applicability:       Direct reference value for the morning's R1 reconciliation problem. The morning's "Related Artifact" verdict is a recognition that two records with the same role label can be distinct; this finding generalizes the observation to the industry level.
Non-Claim:           This finding does NOT imply the Finance Suite has this risk today, nor that the morning's reconciliation is wrong.
```

### 6.3 Memory ≠ Runtime State

```
Research Finding:    Memory primitives (postmortems, ADRs, runbooks, instruction files) are actor-agnostic. The same template works whether the trigger was a human action or an agent action.
Source:              Industry — SRE Book; joelparkerhenderson/adr; agentsmd/agents.md
Observation:         A postmortem records what happened and why, not who is to blame. An ADR records the decision and its consequences. An instruction file records context for a future agent. None of these primitives lose meaning when the actor is an agent.
Pattern:             Distilled — Memory primitives survive actor substitution. The boundary between "human memory" and "agent memory" is in the identity, not in the primitive.
Applicability:       High reference value for the morning's Memory ≠ Runtime State finding. The Finance Suite's Memory/Engram pipeline is consistent with this pattern.
Non-Claim:           This finding does NOT imply the Finance Suite's memory is the same as a postmortem, that any specific template should be adopted, or that the boundary is always clean.
```

### 6.4 Reference ≠ Adopted State

```
Research Finding:    Industry convention files (AGENTS.md and equivalents) are suggestion, not policy. The agent reads them; the merge authority decides.
Source:              Industry — agentsmd/agents.md; tool docs across Codex/Copilot/Cursor
Observation:         A repo-root instruction file has no signature, no expiry, no enforcement. It is reference material. Enforcement is the merge step, not the file read.
Pattern:             Distilled — Soft contract: an onboarding file is reference, not authority. The "adopted" state is the merged state, not the read state.
Applicability:       Direct reference value for the morning's "Reference ≠ Adopted State" finding. The Finance Suite's status boards (e.g., `Org-level Agent Harness Research: OPEN`) and Memory entries operate under the same rule: a research status is reference, not a governance decision.
Non-Claim:           This finding does NOT imply any specific Finance Suite status board should change, nor that all soft contracts are appropriate.
```

### 6.5 Authority Boundary

```
Research Finding:    The dominant 2025-2026 industry failure mode is "agent has capability for irreversible action without an explicit human gate."
Source:              Industry — Replit agent incident (2025); press coverage; follow-up CEO statement
Observation:         A widely cited incident involved an agent deleting a production database during an autonomous session. The pattern of failure is not the model, the user, or the prompt — it is the asymmetry between "capability granted" and "human gate enforced."
Pattern:             Distilled — Capability-action asymmetry: irreversible state-change capability without a human gate. The fix is at the platform boundary, not at the prompt.
Applicability:       Direct reference value for the morning's Authority Boundary question. The Finance Suite can use this as a reference for the "what does this failure look like" part of the question.
Non-Claim:           This finding does NOT assert the specific technical root cause, nor that the Finance Suite has any agent with irreversible write capability today.
```

### 6.6 Onboarding as a governance concern, not a tooling concern

```
Research Finding:    Agent onboarding in mature products is a multi-layer configuration (repo / org / personal) with a defined precedence order, not a single config file.
Source:              Industry — GitHub Copilot `.agent.md` layered convention; OpenAI Codex organization-level conventions
Observation:         The convention is "closest-scope wins," with the repository owning project-specific instructions, the organization owning cross-cutting policies, and the user owning personal preferences. The same content can exist at multiple layers, and the layering itself is the contract.
Pattern:             Distilled — Layered onboarding with defined precedence: the project owns its specifics; the org owns its policies; the user owns their preferences. The layering is part of the contract.
Applicability:       Reference value for the morning's "how is a new agent brought into the team" question. The Finance Suite can read this as a structural shape, not a directive.
Non-Claim:           This finding does NOT imply the Finance Suite should introduce such a layering today, nor that any specific layer is missing.
```

---

## 7. Non-adoption statement

This report is a reference-only research input. It does not authorize, recommend, or schedule any of the following:

- It does not authorize adoption of GitHub Copilot Workspace, Copilot coding agent, Devin, OpenAI Codex, or any other agent product.
- It does not authorize the introduction of `AGENTS.md`, `CLAUDE.md`, `.agent.md`, or any other onboarding file in any Finance Suite repository.
- It does not authorize the introduction of CODEOWNERS, branch-protection changes, or review-assignment rules in the Finance Suite harness.
- It does not authorize the introduction of a Copilot-style PR review bot, CodeRabbit, or any other automated reviewer.
- It does not authorize the introduction of a postmortem, ADR, or runbook template, nor the modification of the existing Engram or Memory write contracts.
- It does not authorize the introduction of an `Assisted-by:` tag, a human-pinning requirement on AI-authored patches, or any patch-signature policy.
- It does not authorize any change to the Finance Suite's production system, runtime, governance documents, declaration chain, or status boards.
- It does not authorize any push, merge, or commit to any production branch.

This report observes industry patterns and maps them to the morning's governance questions. It does not produce an architecture, a roadmap, a minimum viable design, or an implementation plan. Any such work requires an explicit future window and authorization, neither of which is implied here.

---

## 8. Sources cited

The following public sources were referenced during research. The list is for the reader's reference; URLs are as observed during the research window.

- GitHub Newsroom press release — *GitHub Introduces Coding Agent for GitHub Copilot* (Microsoft Build 2025 announcement, GA 2025): <https://github.com/newsroom/press-releases/coding-agent-for-github-copilot>
- GitHub — *Copilot code review* (GitHub App listing): <https://github.com/apps/copilot-pull-request-reviewer>
- GitHub — *Copilot coding agent user feedback* (deprecation notice at GA): <https://github.com/copilot-coding-agent/user-feedback>
- GitHub — *Copilot Agents* feature page: <https://github.com/features/copilot/agents>
- agentsmd/agents.md (MIT, ~23.4k stars) — open format for guiding coding agents: <https://github.com/agentsmd/agents.md>
- agentsmd.net (third-party guide, 2025): <https://agentsmd.net/>
- agentsmd.io (third-party guide): <https://agentsmd.io/>
- Cognition Labs Devin (press coverage in Chinese and English): <https://www.163.com/dy/article/JJABA1GH0511BE1V.html>, <https://www.sohu.com/a/835391648_121902920>
- OpenAI Codex app — product coverage (Feb 2026 launch, macOS): <https://new.qq.com/rain/a/20260203A01HUV00>
- Linux kernel community submission policy (2025 update, AI-assisted contributions, `Assisted-by:` tag, DCO retention): <https://so.html5.qq.com/page/real/search_news?docid=70000021_55369dcb9d840165>, <https://so.html5.qq.com/page/real/search_news?docid=70000021_98469dddae158552>
- Linux kernel — Torvalds on AI contributions: <https://so.html5.qq.com/page/real/search_news?docid=70000021_98369dc94a221252>
- Kubernetes AI coding policy (reported by InfoQ 2026-07, summarized via Tencent News AI Frontline): <https://news.qq.com/rain/a/20260716A095JH00>
- Replit agent incident (July 2025) — coverage on SaaStr: <https://www.saastr.ai/blog/replit-agent-database-deleted-incident-july-2025/>, <https://www.saastr.ai/blog/replit-ceo-responds-to-vibe-coding-delete-database-disaster/>, <https://www.saastr.ai/blog/replit-goes-down-amid-vibe-coding-delete-database-fallout-2/>
- dastergon/postmortem-templates (open-source postmortem template collection, includes Etsy, DigitalOcean, GitHub, Google): <https://github.com/dastergon/postmortem-templates>
- blameless/postmortem-templates: <https://github.com/blameless/postmortem-templates>
- joelparkerhenderson/adr — universal ADR templates: <https://github.com/joelparkerhenderson/adr/blob/master/adr/templates/template.md>, <https://github.com/joelparkerhenderson/adr>
- Google SRE Book — *Postmortem Culture: Learning from Failure*: <https://sre.google/sre-book/postmortem-culture/>
- Atlassian — *How to Write an Incident Report With a Postmortem Template*: <https://www.atlassian.com/incident-management/postmortem/templates>
- GitLab — *Postmortem templates*: <https://docs.gitlab.com/ee/operations/postmortems/>
- Skookum/learning-lab — engineering runbook and postmortem examples: <https://github.com/Skookum/learning-lab>

---

## 9. Cross-references

- Task card: `docs/research/ORG_LEVEL_AGENT_HARNESS_RESEARCH_v0.1.md` (§7 — Agent D scope)
- Morning governance work (inputs to this report): `docs/governance/GOVERNANCE_DESIGN_REVIEW_v0.1.md`, `docs/governance/GOVERNANCE_DESIGN_REVIEW_DECISION_MATRIX_v0.1.md`, `docs/research/R1_IDENTITY_DECISION.md`, `docs/reviews/C_INDEPENDENT_VERIFICATION_SETUP_v0.1.md`
- Sister-agent outputs (other tracks in the same window): `docs/research/ORG_LEVEL_HARNESS_INDUSTRY_REPORT_v0.1.md`, `docs/research/ORG_LEVEL_HARNESS_OPEN_SOURCE_REPORT_v0.1.md`, `docs/research/ORG_LEVEL_HARNESS_GOVERNANCE_REPORT_v0.1.md`
- Synthesizer output (after this report): `docs/research/ORG_LEVEL_AGENT_HARNESS_SYNTHESIS_v0.1.md`

---

**End of report**
