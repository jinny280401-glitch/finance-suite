# Vera Enterprise Architecture v1.0 — Team Agent Critique

> **Status**: CRITIQUE / READ-ONLY / No capability promoted
> **Date**: 2026-07-31
> **Target document**: `docs/architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md`
> **Purpose**: Multi-voice critique for campaign use; not a governance document.

## 1. Critic Summaries

**Retail Voice (炒股股民)** concludes that v1.0 is not usable for a retail investor today. The document contains no actionable buy/sell/hold guidance; the only immediately useful content is the negative boundary statement that Vera does not provide target prices, positions, or trading signals. Layers like Institution Security, Desensitization Gateway, Evidence Manifest, and the Research Runtime state machine read as engineering or legal artifacts rather than investor-facing content. The smallest fix is a one-page retail reader map plus moving maturity disclaimers to an appendix.

**Institutional CIO (券商 CIO)** finds v1.0 conceptually sound but not procurement-ready. The security ownership boundary is explicit and passes, but the document cannot answer practical enterprise questions: deployment sizing, SLA, vendor, cost, or runtime proof. The Desensitization Gateway is honest but remains a placeholder without code, algorithm, or certification. Alpha/Matt integration is correctly framed as co-pilot rather than clone, yet lacks an end-to-end runtime trace. The LIVE VERIFIED gate is credible in concept but vapor today because no component has been promoted and audited.

**Architecture Rigor (Governance enforcer)** judges that v1.0 largely preserves governance discipline, with one weak section: §6 Valuation Evidence Module. The module lists sub-components but does not compute a module-level MIN() maturity. §6 also slips into implementation language with active verbs like "Replaces" and "the upgrade," which should be rewritten as architecture language. The Capability Boundary Table in §8 is load-bearing but not atomized enough to expose the weakest component, and the §9 Review Checklist lacks MIN() verification and active-verb review items.

**Competition Narrative (Campaign coordinator)** identifies contradictions between v1.0 and downstream campaign documents. cup-v1 claims production validation while v1.0 states Production NOT CLAIMED; OPC claims "Trust Gate v1 上线" plus retail SaaS while v1.0 is institutional and NOT CLAIMED. v1.0 itself is internally consistent in marking capabilities as Design/RESERVED/PENDING, but its dense governance language risks confusing retail judges if attached directly. The verdict: v1.0 is the source of truth; cup-v1 and OPC must be harmonized downstream, and v1.0 should remain invisible to retail-facing submissions.

**Advisor Bridge (投顾)** states that v1.0 plus apps cannot produce a 7月资产配置观察-style advisory output. The gap is at the Trust Gate layer and above; regulated client advisory output requires a separate advisory product or v2.0 governance. In the 6-layer stack, this would sit above Institution Security as a 7th layer or as a separate product, because it cannot sit below Trust Gate. The recommendation is to create a new document defining the advisory voice boundary, not to patch v1.0.

## 2. Convergent Findings

| Finding | Voices | Severity | Why it matters |
|---|---|---|---|
| v1.0 is not actionable for any external audience today (retail, CIO, campaign) | Retail, CIO, Campaign | High | The architecture spec correctly refuses production claims, but that refusal leaves all consumer-facing documents without a usable bridge. |
| Desensitization Gateway / Institution Security Layer are placeholders without runtime proof | Retail, CIO | Medium | Enterprise buyers need evidence; retail readers are alienated; both audiences agree the layer is not yet real. |
| §6 Valuation Evidence Module lacks rigor: missing MIN(), slips into implementation language | Rigor, Advisor | Medium | This is the weakest technical section and the one most likely to be cited as evidence capability. |
| Downstream campaign documents (cup-v1, OPC) contradict v1.0's NOT CLAIMED status | Campaign, Rigor | High | Submitting inconsistent claims damages trust and risks silent capability promotion. |
| Advisory output requires a separate governance layer, not a v1.0 addendum | Advisor, Campaign, Retail | High | Mixing advisory voice into v1.0 would silently promote retail advisory capability. |

## 3. Disagreement Map

| Topic | Voice A stance | Voice B stance | Synthesis |
|---|---|---|---|
| Institution Security Layer value | Retail: remove from external view | CIO: pass, keep explicit | Keep in v1.0 as enterprise source of truth; hide or summarize in retail/campaign-facing derivatives. |
| Dense governance language | Retail/Campaign: confusing, move to appendix | Rigor/CIO: necessary for trust | Governance language stays in v1.0; downstream docs add reader-specific maps. |
| Smallest fix for usability | Retail: one-page reader map | Advisor: new advisory voice document | Both are needed for different audiences; do not choose one over the other. |
| OPC retail SaaS claim | Campaign: contradicts v1.0, must rewrite | Advisor: requires separate product entirely | OPC should be reframed or explicitly scoped as a future product line, not current capability. |

## 4. Missing Middle Layer Recommendation

**Choice**: (b) New document `finance-suite/docs/advisory/VERA_ADVISORY_VOICE_BOUNDARY_v0.1.md`

**Rationale**: A retail reader map alone (option a) would not solve the regulated advisory-output gap, and a runtime feature (option c) would silently promote production capability. A new architecture document is the smallest artifact that (1) defines the 投顾/advisory voice as a distinct product layer, (2) preserves v1.0's NOT CLAIMED boundary, and (3) gives campaign documents a consistent downstream reference without contradictions.

**1-line scope**: Define the product, compliance, and evidence boundary for a client-specific 投顾 output that consumes Vera evidence but operates under separate advisory governance.

## 5. What v1.0 Should NOT Do

- Do not state or imply that Vera currently serves retail investors.
- Do not claim or imply that Vera provides investment advice, target prices, position sizing, or buy/sell/hold signals.
- Do not promote any component to RUNTIME or PRODUCTION status.
- Do not allow downstream documents (cup-v1, OPC) to silently upgrade DESIGN/RESERVED/PENDING items to verified or live.
- Do not merge the advisory/投顾 voice into v1.0; keep it as a separate governed layer.
- Do not replace `7月资产配置观察.md`-style outputs with architecture language; the two serve different purposes.

## 6. Top 5 Action Items

| Priority | Action | Owner | Why |
|---|---|---|---|
| P0 | Rewrite/harmonize cup-v1 and OPC claims so they do not contradict v1.0's Production NOT CLAIMED boundary. | Human + CC | Prevents silent capability promotion before any campaign submission. |
| P0 | Create `finance-suite/docs/advisory/VERA_ADVISORY_VOICE_BOUNDARY_v0.1.md` with scope, compliance boundary, and explicit NOT CLAIMED status. | CC / C-pending-window | Closes the 投顾 gap without polluting v1.0. |
| P1 | Harden §6 Valuation Evidence Module: add module-level MIN(), remove active implementation verbs, add sub-rows/footnote for weakest component. | CC | Addresses the weakest technical section per Rigor review. |
| P1 | Add a one-page retail reader map to v1.0 as an appendix or derivative doc, summarizing what v1.0 is, what it is not, and where actionable outputs live. | CC | Makes the architecture accessible without changing its scope. |
| P2 | Draft a deployment worksheet for institutional readers (sizing, SLA, vendor, cost placeholders) marked as FUTURE/NOT CLAIMED. | Human | CIO feedback showed procurement readiness gap; worksheet is planning-only, not a commitment. |
