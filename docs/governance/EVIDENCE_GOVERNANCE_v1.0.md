# Finance Suite Evidence Governance v1.0

**Document Status:** Architecture Freeze Draft (Phase 2 Absorption Enhanced)
**Evidence Basis:** Derived from production failure case (600439 F-03 Counter-Example) + Phase 1 External Architecture Recon (2026-08-03)
**Phase 1 Input:** [ARCHITECTURE_PATTERN_REVIEW.md](../research/ARCHITECTURE_PATTERN_REVIEW.md), [FINANCIAL_DATA_GOVERNANCE_PATTERN.md](../research/FINANCIAL_DATA_GOVERNANCE_PATTERN.md), [OPEN_SOURCE_GOVERNANCE_SCAN.md](../research/OPEN_SOURCE_GOVERNANCE_SCAN.md), [PHASE1_ABSORPTION_SYNTHESIS.md](../research/PHASE1_ABSORPTION_SYNTHESIS.md)
**Governance Maturity:** SPECIFICATION READY (L0→L1 on Capability Maturity Ladder)
**Runtime Implementation:** NOT STARTED
**Production Capability:** NOT CLAIMED
**Effective date:** 2026-08-03
**Supersedes:** None (new asset; enhanced from Phase 1 absorption)
**Aligns with:** [Capability Claim Governance Framework v1.0](Vera_Capability_Claim_Governance_Framework_v1.md), [Evidence Manifest Protocol v0.1](../evidence/Vera_Evidence_Manifest_Protocol_v0.1.md), [Institutional Provider Architecture v0.1](INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md), [Vera Enterprise Architecture v1.0](../architecture/VERA_ENTERPRISE_ARCHITECTURE_v1.0.md)

---

## 1. Purpose

Finance Suite currently treats data acquisition success as evidence sufficiency. A provider returns data → QC marks it present → Trust Gate returns `success`. The 600439 incident (2026-08-02) proved this is insufficient:

```
Data exists ✅
Acquisition succeeded ✅
QC completeness >= 0.8 ✅
Trust Gate = success ✅
→ Financial data was 16 months stale
```

This document defines an **Evidence Governance Layer** that sits between Provider output and Agent consumption. It governs not whether data exists, but:

> What is this data? Where did it come from? What time period does it represent? What conclusions can it support? What is its trust level?

### 1.1 Governing Principles

```
Principle 1: Data present ≠ Evidence valid
Principle 2: QC passed ≠ Consumer safe
Principle 3: Fetch timestamp ≠ Data period
Principle 4: Code fixed ≠ Root cause proven
Principle 5: Evidence retention is a Runtime contract, not a post-incident supplement
Principle 6: Schema ≠ Data Contract — fields existing does not mean semantics hold
Principle 7: Declared Capability ≠ Effective Capability — what is claimed must be independently verified at runtime
Principle 8: UNKNOWN SHALL NOT ESCALATE PRIVILEGE — the default when uncertain is to restrict, not to permit
```

**Principle 4 (Code fixed ≠ Root cause proven):** A code fix that restores correct behavior proves that the current code path is correct. It does not prove what caused the original failure. The original HTTP status code, Content-Type, response body, request ID, and correlated logs must be preserved to complete a deterministic RCA. Without them, the root cause can only be classified as a candidate hypothesis, never CONFIRMED.

**Principle 5 (Evidence retention is a Runtime contract):** Evidence preservation is not a retrospective action taken after an incident. It is a base capability that the production Runtime MUST provide. A Runtime that cannot answer "which layer produced this error response?" or "was the Provider invoked?" is not trustworthy — regardless of how many successful responses it produces. Pre-Decision Evidence governs whether data can enter a conclusion. Post-Incident Evidence governs whether the system can prove what happened after a failure. Both are required for a Trustworthy Runtime.

**Principle 6 (Schema ≠ Data Contract):** A JSON field named `as_of` that exists in the schema but carries fetch time while implying data currency is a contract violation, not a schema defect. Schema validates structure. Contract validates semantics. A field that passes schema validation has not satisfied its data contract until its meaning, temporal scope, and provenance are independently verified.

**Principle 7 (Declared Capability ≠ Effective Capability):** A configuration file, a registered provider, or a documented integration path proves intent, not runtime capacity. Every capability claim MUST be verified at the runtime boundary — what actually executed, with what evidence, producing what outcome. Audit the spawn snapshot, not the declaration. Aligned with [Capability Claim Governance Framework v1.0](Vera_Capability_Claim_Governance_Framework_v1.md) §2.

**Principle 8 (UNKNOWN SHALL NOT ESCALATE PRIVILEGE):** When freshness, provenance, or confidence cannot be determined, the default judgment MUST restrict downstream use — never expand it. An UNKNOWN freshness is not PASS. An UNKNOWN source confidence is not MEDIUM. An UNKNOWN authorization boundary is not ALLOW. This principle prevents the silent privilege escalation that occurs when governance gaps are filled by optimistic defaults. Aligned with fail-closed semantics from in-toto, SCITT, and OPA/Cedar identified in Phase 1 External Recon. [Origin: External Standards] [Vera Status: Not Implemented]

### 1.2 Architecture Position

```text
                    Vera Evidence Governance
             ┌────────────────────────────┐
             │                            │
             ▼                            ▼
  Pre-Decision Evidence           Post-Incident Evidence
  "答案之前的证据"                  "事故之后的证明"
  - provenance                    - request_id
  - freshness                     - status_code
  - completeness                  - content_type
  - validity                      - response_hash
  - allowed_use                   - trace/log correlation
             │                            │
             └──────────┬─────────────────┘
                        ▼
              Trustworthy Runtime

Provider Layer (Wind / Choice / iFinD / Tushare / AkShare)
        ↓
Provider Normalization (→ Evidence Object)
        ↓
Trust Evaluation (freshness + completeness + confidence + provenance)
        ↓
Authorization Decision (allowed_use / blocked_use / claim_strength)
        ↓
Context Assembly (evidence bundle for consumption)
        ↓
Agent / LLM Consumption
```

**Critical architectural constraint:** Trust Evaluation and Authorization Decision are separate stages. Trust Evaluation answers "is this evidence valid?" Authorization Decision answers "what may this evidence be used for?" A Trust Evaluation PASS MUST NOT automatically authorize all downstream uses. This separation is Vera's core differentiator from existing industry patterns: in-toto proves provenance [Origin: in-toto/v1.0], SCITT proves durability [Origin: IETF RFC 9943], PIT proves temporal correctness [Origin: Bloomberg/FactSet/LSEG] — but none define an authorization boundary between evidence validity and evidence consumption. That boundary is Vera's. [All external standards: Vera Status — Not Implemented. Architecture reference only.]

Provider payloads MUST be normalized to Evidence Objects before Trust Evaluation. Raw provider fields MUST NOT reach the Agent layer ungoverned.

The Pre-Decision branch governs data before it enters a conclusion. The Post-Incident branch governs whether the system can prove what happened after a failure. A Runtime that cannot satisfy both is not trustworthy — regardless of its success rate under normal conditions.

---

## 2. Evidence Object Schema (Normative)

### 2.1 Canonical Evidence Object

Every data point that enters the Trust Gate MUST carry:

```json
{
  "evidence_id": "ev:<uuid>",
  "domain": "financials|announcements|news|valuation|macro",
  "subdomain": "balance_sheet|income_statement|cashflow|earnings_announcement|...",

  "value": "<the data itself — number, string, object, array>",

  "source": {
    "provider": "wind|choice|ifind|tushare|akshare",
    "provider_class": "institutional|retail|public",
    "endpoint": "stock_financial_analysis_indicator",
    "source_type": "structured_api|scraped|derived|cached"
  },

  "time": {
    "data_period_end": "2025-12-31",
    "announced_at": "2026-04-20",
    "fetched_at": "2026-08-03T00:34:00+08:00"
  },

  "quality": {
    "freshness": "PASS|STALE|UNKNOWN",
    "freshness_age_days": 125,
    "completeness": "PASS|PARTIAL|MISSING",
    "source_confidence": "HIGH|MEDIUM|LOW|UNKNOWN"
  },

  "governance": {
    "allowed_use": ["fundamental_analysis", "historical_context"],
    "blocked_use": ["investment_signal", "intraday_decision", "valuation"],
    "block_reason": "financials_stale|source_confidence_low|period_unknown",
    "requires_human_review": false
  }
}
```

### 2.2 Field Definitions

| Field | Type | Required | Definition |
|---|---|---|---|
| `evidence_id` | string | Yes | Stable unique identifier for this evidence unit |
| `domain` | enum | Yes | One of: `financials`, `announcements`, `news`, `valuation`, `macro` |
| `subdomain` | string | No | Finer-grained classification within domain |
| `value` | any | Yes | The governed data payload |
| `source.provider` | string | Yes | Provider identifier from Capability Claim Matrix |
| `source.provider_class` | enum | Yes | `institutional` (Wind, Choice, iFinD) / `retail` (Tushare) / `public` (AkShare) |
| `source.endpoint` | string | Yes | Specific API endpoint or function name |
| `source.source_type` | enum | Yes | `structured_api` / `scraped` / `derived` / `cached` |
| `time.data_period_end` | date | Conditional | The date through which the data is effective. Required for `financials`, `valuation`, `macro`. |
| `time.announced_at` | date | Conditional | When the data was officially disclosed. Required for `financials`, `announcements`. |
| `time.fetched_at` | datetime | Yes | When the system retrieved this data |
| `quality.freshness` | enum | Yes | `PASS` (within policy) / `STALE` (exceeds policy) / `UNKNOWN` (cannot determine) |
| `quality.freshness_age_days` | integer | No | Days since `data_period_end` (or `announced_at` if period unavailable) |
| `quality.completeness` | enum | Yes | `PASS` (all expected fields present) / `PARTIAL` (some missing) / `MISSING` (none) |
| `quality.source_confidence` | enum | Yes | `HIGH` (institutional, direct exchange) / `MEDIUM` (licensed retail) / `LOW` (public, scraped) / `UNKNOWN` |
| `governance.allowed_use` | string[] | Yes | What downstream conclusions this evidence may support |
| `governance.blocked_use` | string[] | Yes | What downstream conclusions this evidence MUST NOT support |
| `governance.block_reason` | string | Conditional | Why blocked. Required when `blocked_use` is non-empty. |
| `governance.requires_human_review` | boolean | Yes | Whether Agent may consume without human review |

### 2.3 Time Semantics — The Bitemporal Contract (MUST)

The 600439 incident's root schema defect was conflating fetch time with data period. Phase 1 External Recon confirmed that the financial data industry standard is **bitemporal governance**: every fact carries two independent time axes. The Evidence Object enforces this as a normative requirement.

```text
valid_time          "What period does this fact describe?"
                    → 2026 Q1 financials: valid_time = 2026-01-01 ~ 2026-03-31

knowledge_time      "When did the market/system first know this fact?"
                    → 2026 Q1 report published: knowledge_time = 2026-04-28 15:00

fetched_at          "When did our system retrieve it?"
                    → 2026-08-03T00:34:00+08:00
```

**Upgrade from v0 (three-date) to v1.0 (bitemporal):**

The v0 draft used `data_period_end`, `announced_at`, and `fetched_at` as three independent fields. Phase 1 absorption of Bloomberg/FactSet Point-in-Time (PIT) semantics and the bitemporal model requires upgrading this to a formal two-axis contract:

| Axis | v0 field | v1.0 field | Governance function |
|---|---|---|---|
| **Validity axis** | `data_period_end` | `valid_time` (MUST) | "What time period does this fact describe?" Drives freshness. |
| **Knowledge axis** | `announced_at` | `knowledge_time` (MUST) | "When did the market/system first know this?" Drives availability expectation and temporal leakage detection. |
| **Observation axis** | `fetched_at` | `fetched_at` (MUST) | "When did our system retrieve it?" Drives latency and cache invalidation. |

**Temporal Leakage Gate:**

If an Agent answers "As of 2026-04-01, the company's financial position is…" using evidence with `knowledge_time = 2026-04-28`, the Trust Gate MUST detect and BLOCK the temporal leakage:

```text
query_time <= knowledge_time → LEAKAGE → BLOCK
knowledge_time < query_time  → ALLOWED (if freshness also PASS)
```

This gate is Vera-defined. While Bloomberg, FactSet, and LSEG all provide PIT products that prevent look-ahead bias in backtesting, the automatic detection of temporal leakage at Agent query time — mapping the gap between `knowledge_time` and the Agent's stated `as_of` claim — is not a standardized industry feature. It is Vera's GAP to define. [PIT: Origin — Bloomberg/FactSet/LSEG (external). Vera temporal leakage enforcement: Not Implemented — Specified GAP only.]

**Freshness policy per data class:**

The temporal contract applies differently by data class, as identified in Phase 1 Financial Data Governance Scout:

| Data Class | valid_time meaning | knowledge_time meaning | Max age |
|---|---|---|---|
| Financial statements | `period_end` of reporting period | Filing/publication date | Latest filing cycle + 90 days |
| Market data | Trade/quote timestamp | Exchange receipt time | 1 trading day (intraday: 15 min) |
| Announcements | Event effective date | Disclosure timestamp | Event-driven (superseded by newer) |
| Estimates | Horizon period end | Analyst publication date | `as_of` + revision age |
| Macro indicators | Measurement period end | Official release date | Expected release + 30 days |

A single `as_of` field that carries `fetched_at` while implying `valid_time` is a **schema contract violation**. Consumers reasonably interpret `as_of` as data currency, producing false freshness conclusions.

### 2.4 Source Confidence Model

| Confidence | Provider Class | Examples | Default Block |
|---|---|---|---|
| `HIGH` | Institutional, direct exchange feed | Wind, Choice, iFinD, SSE/SZSE official | None (full evidential weight) |
| `MEDIUM` | Licensed retail, regulated aggregator | Tushare Pro, JoinQuant | `investment_signal` (requires corroboration) |
| `LOW` | Public, scraped, unregulated | AkShare free tier, web scraping | `investment_signal`, `valuation`, `risk_assessment` |
| `UNKNOWN` | Cannot determine provenance | Fallback, cache-only, derived without lineage | ALL downstream conclusions |

Confidence degrades at each fallback step. A data point retrieved from AkShare after Wind + Tushare both failed carries `LOW` confidence regardless of the data's factual accuracy.

### 2.5 Cross-Source Confidence Formula (Vera-Defined GAP)

Phase 1 External Recon confirmed that no public vendor standard defines a unified cross-source confidence model. This formula is **Vera-defined**, not industry-standard. It MUST NOT be presented as a Bloomberg, FactSet, or LSEG specification.

```text
confidence = authority
           × authenticity
           × transformation_quality
           × corroboration
           × temporal_validity
```

| Factor | Definition | Degradation trigger |
|---|---|---|
| `authority` | Source's legal/institutional standing | Fallback to lower-tier provider |
| `authenticity` | Cryptographic or procedural proof of origin | Unsigned, unverifiable, or relayed through untrusted intermediary |
| `transformation_quality` | Correctness of mapping, normalization, computation | Manual mapping, unversioned transform, known data-type mismatch |
| `corroboration` | Independent confirmation from separate source | Single-source, uncorroborated, or contradicted |
| `temporal_validity` | Data is within its valid time window | Stale, expired, or missing `valid_time` |

Each factor is evaluated independently. A HIGH-authority source (Wind) with expired temporal validity produces UNKNOWN overall confidence — not HIGH. Authority cannot compensate for staleness.

### 2.6 Evidence Object Envelope (Phase 1 Absorption)

The Evidence Object structure defined in §2.1 is the **operational data contract**. The **envelope** that wraps it for exchange and verification draws from:

| Source | Absorbed concept | Vera mapping | Origin |
|---|---|---|---|
| in-toto Statement v1 | `subject + digest + predicateType + predicate` | `evidence_id` = subject, `raw_response_sha256` = digest | [in-toto/v1.0] |
| W3C PROV | `Entity—Activity—Agent` with `wasGeneratedBy/used/wasAttributedTo` | Evidence Object = Entity, Provider invocation = Activity | [W3C PROV-O] |
| SCITT RFC 9943 | Signed Statement + Transparency Receipt | Provider signs Evidence Object → SCITT-compatible receipt | [IETF RFC 9943] |

**External Standard Attribution:** All standards referenced in this section are external. Vera Status: Not Implemented. Architecture reference only. No cryptographic evidence chain is operational in the Vera Runtime.

The Evidence Object MUST carry a `durability` block for high-confidence evidence:

```json
{
  "durability": {
    "receipt_type": "scitt|sigstore|none",
    "receipt_uri": "",
    "signed_at": "",
    "signer_identity": "",
    "content_hash": ""
  }
}
```

`receipt_type = "none"` is valid for LOW-confidence sources (AkShare, web scraping). It MUST NOT be used for HIGH-confidence institutional providers without explicit justification.

---

## 3. Five-Domain Governance Model

### 3.1 Financial Evidence

**Domain key**: `financials`
**Subdomains**: `balance_sheet`, `income_statement`, `cashflow`, `financial_indicators`

**Problem addressed**: 600439 — financial data 16 months stale passed Trust Gate as `success`.

**Governance rules**:

1. **Three-date rule is mandatory.** `data_period_end`, `announced_at`, and `fetched_at` MUST all be present. Missing `data_period_end` → `freshness = UNKNOWN` → BLOCK `fundamental_analysis`.

2. **Freshness policy is per-field, not per-dimension.** All core financial fields (revenue, profit, cashflow, assets, liabilities, ROE) share the same freshness requirement: the latest available reporting period. If the latest period exceeds the expected reporting cycle + grace window, BLOCK.

3. **Reporting cycle awareness.** Chinese A-share companies must file:
   - Annual report: within 4 months of fiscal year end (deadline: April 30)
   - Q1 report: within 1 month of quarter end (deadline: April 30)
   - Semi-annual report: within 2 months of half-year end (deadline: August 31)
   - Q3 report: within 1 month of quarter end (deadline: October 31)

   Freshness threshold should account for this cycle. A missing report within 30 days of the filing deadline is expected. A missing report 90 days past the deadline is STALE.

4. **BLOCK rule.** If `freshness = STALE` for financials:
   ```json
   {
     "allowed_use": ["company_profile"],
     "blocked_use": ["fundamental_analysis", "investment_signal", "valuation", "risk_assessment"],
     "block_reason": "financials_stale",
     "requires_human_review": true
   }
   ```

5. **Provider priority matters for confidence.** Wind → `HIGH`. AkShare fallback → `LOW`. The confidence level MUST be reflected in `allowed_use`, not just noted in metadata.

### 3.2 Announcement Evidence

**Domain key**: `announcements`
**Subdomains**: `earnings_announcement`, `material_contract`, `asset_restructuring`, `regulatory_penalty`, `shareholder_change`, `dividend`

**Problem addressed**: Announcements are the highest-authority data source but carry the strictest timeliness requirements. Currently not modeled as a separate QC domain.

**Governance rules**:

1. **Source authority hierarchy:**
   - Exchange official (SSE/SZSE disclosure platform) → `HIGH`
   - Company IR website → `MEDIUM`
   - News media report of announcement → `LOW` (not primary evidence)

2. **Event classification is mandatory.** An announcement MUST be classified before it enters the evidence stream. Raw text without event type → `UNKNOWN`.

3. **Event lifecycle tracking:**
   ```text
   announced → effective_date → implementation_progress → completed|terminated
   ```
   An announcement from 2023 about a "planned" restructuring carries different evidential weight in 2026 than a completed one. The event status MUST be tracked.

4. **Announcement ≠ verification.** The existence of an announcement proves disclosure, not fact. A company announcing "expected profit growth of 50%" is evidence of the *announcement*, not evidence of the *profit growth*.

### 3.3 News Evidence

**Domain key**: `news`
**Subdomains**: `market_news`, `company_news`, `industry_news`, `macro_news`, `analyst_opinion`

**Problem addressed**: News enters the evidence stream as raw articles. Ten articles about the same event count as ten pieces of evidence. Opinion and fact are not separated.

**Governance rules**:

1. **Deduplication before evidence counting.** Articles referencing the same underlying event MUST be collapsed:
   ```text
   10 articles about "Company X signs major contract"
   → 1 underlying event
   → evidence_count = 1
   → source_count = 10 (for corroboration, not multiplication)
   ```

2. **Source rating:**
   | Source type | Confidence | Allowed use |
   |---|---|---|
   | Official wire (Reuters, Bloomberg) | `HIGH` | All |
   | Regulated financial media (证券时报, 中国证券报) | `MEDIUM` | Context, awareness |
   | Platform aggregation (东方财富, 雪球) | `LOW` | Discovery only |
   | Social media, forums, WeChat | `UNKNOWN` | NOT evidence |

3. **Fact vs. opinion separation.** An article may contain both:
   ```json
   {
     "facts": ["Company X reported Q1 revenue of 5.2B"],
     "opinions": ["Analyst believes revenue growth will accelerate"],
     "evidence_weight": "facts_only"
   }
   ```
   Opinions MUST NOT enter the evidence stream as facts.

4. **Temporal relevance decay.** News freshness decays faster than financials. A news article from 90 days ago about "upcoming earnings" when earnings have since been reported is not evidence — it's noise.

### 3.4 Valuation Evidence

**Domain key**: `valuation`
**Subdomains**: `market_multiples`, `historical_percentile`, `peer_comparison`, `target_price`, `dcf_model`

**Problem addressed**: Valuation data exists on a spectrum from observed fact to analytical opinion. Current QC treats PE/PB as factual market data without distinguishing derivation level.

**Governance rules**:

1. **Three-tier classification (mandatory):**

   **Level 1 — Observed Data:**
   - Current PE, PB, PS, EV/EBITDA (as reported by exchange/provider)
   - Historical prices used in multiples
   - Allowed use: `historical_context`, `screening`
   - Blocked use: none (these are facts)

   **Level 2 — Derived Metrics:**
   - Historical percentile ranking
   - Industry average comparison
   - Sector-relative valuation
   - Allowed use: `context`, `relative_comparison`
   - Blocked use: `absolute_valuation`, `target_price`

   **Level 3 — Analytical Opinion:**
   - Analyst target prices
   - DCF fair value estimates
   - "Undervalued/overvalued" judgments
   - Allowed use: `reference_only`
   - Blocked use: `investment_signal`, `risk_assessment`, `compliance`
   - `requires_human_review: true`

2. **Tier leakage prevention.** A Level 3 target price MUST NOT be presented alongside Level 1 PE data as if they carry equal evidential weight. The presentation layer MUST preserve tier distinction.

3. **Derived metric provenance.** Level 2 metrics MUST declare their derivation method and input data period. "PE percentile: 15th" requires: PE time series source, lookback window, percentile method.

### 3.5 Macro Evidence

**Domain key**: `macro`
**Subdomains**: `gdp`, `cpi`, `pmi`, `money_supply`, `interest_rate`, `employment`, `trade_balance`

**Problem addressed**: Macro indicators have the widest gap between event date and release date. Current `_qc_macro()` uses completeness-only Trust Gate with no freshness check.

**Governance rules**:

1. **Three-date rule for macro:**
   ```text
   event_date      "What period does this indicator measure?"
                   → 2026-Q2 GDP: event_date = 2026-06-30

   release_date    "When was this officially published?"
                   → 2026-Q2 GDP first release: 2026-07-15

   revision_date   "When was this last revised?"
                   → GDP typically revised 2-3 times
   ```
   Macro indicators are revised. The `revision_date` distinguishes "preliminary Q2 GDP" from "final revised Q2 GDP."

2. **Release schedule awareness.** Chinese macro indicators follow fixed release calendars. A missing data point within 5 business days of the expected release date is normal. A missing data point 30 days past expected release is `STALE`.

3. **Revision tracking.** When a previously reported macro value changes due to revision, both values MUST be retained:
   ```json
   {
     "value": 5.2,
     "previous_value": 5.0,
     "revision_date": "2026-07-20",
     "revision_type": "preliminary|revised|final"
   }
   ```
   Evidence based on a preliminary value that was later revised downward is evidence of *what was believed at the time*, not evidence of *what happened*.

---

## 3A. Evidence → Decision Authorization Model

### 3A.1 The Missing Layer

Phase 1 External Recon confirmed that the industry has mature solutions for individual governance dimensions — in-toto for provenance, SCITT for durability, PIT for temporal correctness, OPA/Cedar for authorization. But none of these systems answer the question Vera exists to answer:

> **This evidence is valid. What conclusions may it support, and at what strength?**

The Authorization Model defines the boundary between "this evidence passes quality checks" and "this evidence may enter this specific conclusion at this specific strength." It is Vera's core architectural differentiator.

### 3A.2 Trust Evaluation → Authorization Decision Separation

```text
Phase 1: Trust Evaluation             Phase 2: Authorization Decision
─────────────────────                 ────────────────────────────
Is the evidence valid?                What may this evidence be used for?
- provenance verified                 - allowed_use
- freshness within policy             - blocked_use  
- completeness >= threshold           - claim_strength
- source_confidence assessed          - consumer scope
- temporal leakage checked            - requires_human_review
```

**Critical invariant:** Trust Evaluation PASS MUST NOT automatically authorize all downstream uses. A `HIGH` confidence financial statement with perfect freshness supports `fundamental_analysis` but does NOT support `predictive_claim`. A `LOW` confidence news article supports `context` but does NOT support `investment_signal`. This separation is normative, not advisory.

### 3A.3 Authorization Decision Object

```json
{
  "decision_id": "dec:<uuid>",
  "evidence_ids": ["ev:...", "ev:..."],
  "policy_version": "evidence-governance-v1.0",
  "verdict": "ALLOW|LIMIT|BLOCK",
  "allowed_use": ["fundamental_analysis", "historical_context"],
  "blocked_use": ["investment_signal", "predictive_claim"],
  "max_claim_strength": "comparative",
  "requires_human_review": false,
  "expires_at": "2026-08-04T01:00:00+08:00",
  "reason": "Financial evidence fresh within policy; confidence HIGH"
}
```

If any required field is UNKNOWN or missing, fail closed: `verdict → BLOCK`, `max_claim_strength → descriptive`. UNKNOWN SHALL NOT ESCALATE PRIVILEGE (Principle 8).

---

## 3B. Claim Strength Contract

### 3B.1 Evidence Tier → Claim Strength Mapping

| Confidence | Freshness | Max Claim Strength | Example |
|---|---|---|---|
| `HIGH` | `PASS` | `directional` | "Revenue grew 15% YoY for 3 consecutive quarters" |
| `HIGH` | `PASS` + human review + validated model | `predictive` | "Based on disclosed assumptions and model, revenue may reach X" |
| `MEDIUM` | `PASS` | `comparative` | "Company A's PE is lower than industry average" |
| `MEDIUM` | `STALE` | `descriptive` | "Company A's last reported PE was 15.2 (as of 2025-12-31)" |
| `LOW` | `PASS` | `descriptive` | "According to public aggregation, Company A reported revenue of X" |
| `LOW` | `STALE` or `UNKNOWN` | `descriptive` (with caveat) | "Historical data suggests… (verify independently)" |
| `UNKNOWN` | Any | `descriptive` (with UNKNOWN marker) | "Retrieved data; provenance and currency unverified" |

### 3B.2 Claim Escalation Gate

```text
Claim tier upgrade = new evidence required
Evidence tier downgrade = claim tier MUST downgrade
```

This prevents **rhetorical escalation without evidential escalation** — the most common failure mode in AI-generated financial analysis.

### 3B.3 Six-Tier Claim Strength Ladder

| Tier | Type | Definition | Minimum Evidence |
|---|---|---|---|
| `descriptive` | "This is what the data says" | Factual restatement | Any confidence, freshness PASS |
| `comparative` | "X vs Y" | Relative comparison | ≥ MEDIUM, both comparands independently verified |
| `directional` | "X is trending" | Observed trend (≥3 points) | ≥ MEDIUM, valid_time for all points |
| `causal` | "X caused Y" | Attribution | HIGH confidence, temporal precedence, confounders addressed |
| `predictive` | "X will happen" | Forward-looking | HIGH confidence + validated model + error bounds + human review |
| `prescriptive` | "You should do X" | Action recommendation | All above + regulatory compliance + human authorization |

---

## 4. Freshness Policy Matrix

### 4.1 Per-Domain Freshness Thresholds

| Domain | Subdomain | Max Age | Basis Date | Failure Mode |
|---|---|---|---|---|
| Financials | Core statements | Latest filing cycle + 90 days | `data_period_end` | BLOCK fundamental_analysis |
| Financials | Financial indicators | Latest filing cycle + 90 days | `data_period_end` | BLOCK fundamental_analysis |
| Announcements | All types | N/A (event-driven) | `announced_at` | Mark STALE if superseded by newer announcement |
| News | Market/company news | 30 days | `fetched_at` | Mark STALE, allow context only |
| News | Industry/macro news | 90 days | `fetched_at` | Mark STALE, allow context only |
| Valuation | Level 1 (observed) | 1 trading day | `fetched_at` | Mark STALE, block investment_signal |
| Valuation | Level 2 (derived) | 30 days | `data_period_end` | Mark STALE, allow reference only |
| Valuation | Level 3 (opinion) | 90 days | `announced_at` | Mark STALE, block all |
| Macro | GDP | Expected release + 30 days | `release_date` | Mark STALE |
| Macro | CPI, PMI | Expected release + 15 days | `release_date` | Mark STALE |
| Macro | M2, LPR | Expected release + 10 days | `release_date` | Mark STALE |

### 4.2 Freshness Evaluation Model

The `len(stale) <= 1` model tested in the 600439 Path B fix is **rejected** for normative use. It fails when a single critical dimension (financials) is stale while all others are fresh:

```
completeness = 0.83
stale = [financials]
len(stale) = 1 → freshness_ok = True
→ status = "success"  ← FAILURE: critical dimension stale
```

**Replacement model: Critical-domain freshness gating.**

```text
For each evidence bundle:
  1. Identify required critical dimensions by use case
  2. If any critical dimension freshness = STALE or UNKNOWN → BLOCK
  3. If any critical dimension completeness ≠ PASS → BLOCK or requires_human_review
  4. Non-critical dimension staleness → mark STALE, allow with warnings
```

**Critical dimension definitions:**

| Use Case | Critical Dimensions | Why |
|---|---|---|
| Fundamental analysis | financials | Core input to any fundamental judgment |
| Intraday decision | realtime price | Stale price = wrong decision |
| Event-driven analysis | announcements | Event timing is the signal |
| Macro context | macro indicators | Core input |
| Company screening | financials, valuation (L1 only) | Comparison basis |
| News monitoring | news | Primary source |

A use case MUST declare its critical dimensions. The Trust Gate MUST NOT infer them.

---

## 5. Trust Gate Upgrade Path

### 5.1 Current State (as of 2026-08-03)

| QC Function | Status Model | Freshness | Allowed Use | Blocked Fields |
|---|---|---|---|---|
| `_qc_stock()` | completeness + `len(stale)<=1` → `success/partial/failure` | financials (180d), price_history (3d), realtime (15min) | realtime only | realtime only |
| `_qc_macro()` | completeness-only → `success/partial/failure` | None | None | None |

**Defect**: Two QC functions in the same codebase use different Trust Gate semantics. `_qc_macro()` can return `success` on 5-year-stale GDP data.

### 5.2 Target State (v2)

| Status | Meaning | Condition | Consumer Impact |
|---|---|---|---|
| `PASS` | All critical dimensions fresh and complete | completeness ≥ threshold AND all critical dimensions `freshness = PASS` AND `source_confidence ≥ MEDIUM` for all critical dims | Full evidential weight. May support investment decisions. |
| `PARTIAL` | Some non-critical dimensions missing or stale | completeness > 0 AND all critical dimensions `freshness = PASS` | Limited evidential weight. Use for context and screening. Block investment signals. |
| `UNKNOWN` | Cannot determine freshness or completeness for ≥1 critical dimension | `data_period_end` missing, `source_confidence = UNKNOWN`, or provider error | No evidential weight. Human review required for any use. |
| `BLOCKED` | ≥1 critical dimension STALE or MISSING | Critical dimension `freshness = STALE` OR critical dimension absent | MUST NOT pass Trust Gate for any use case requiring that dimension. |

### 5.3 Migration Sequence

1. **Phase 1**: Unify `_qc_stock()` and `_qc_macro()` Trust Gate semantics (both use same status model)
2. **Phase 2**: Implement Evidence Object normalization layer (Provider → Evidence Object)
3. **Phase 3**: Replace `len(stale) <= 1` with critical-domain gating
4. **Phase 4**: Extend `allowed_use` / `blocked_use` to all dimensions (currently realtime-only)
5. **Phase 5**: Add source_confidence to Evidence Object and integrate into Trust Gate decision

Phases 1-2 are architectural prerequisites. Phases 3-5 deliver the governance upgrade. No phase claims Production Capability — each must progress through the Capability Maturity Ladder independently.

---

## 6. Provider Contract Alignment

### 6.1 Normalization Requirement

Every Provider MUST normalize its output to the Evidence Object schema before QC evaluation. This is a provider-agnostic contract — Wind, Choice, iFinD, Tushare, and AkShare all produce the same shape.

```text
Wind API output ──────┐
Choice API output ────┤
iFinD API output ─────┤──→ Provider Adapter ──→ Evidence Object ──→ QC
Tushare API output ───┤
AkShare API output ───┘
```

### 6.2 Alignment with Provider State Machine

The [Institutional Provider Architecture v0.1](INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md) defines the Provider lifecycle (`Credential → Transport → Session → Evidence Retrieval → Normalization → Manifest → QC → Consumer → Production Capable`).

Evidence Governance inserts at the **Normalization** stage. A Provider that reaches `EVIDENCE_RETRIEVED` but cannot produce a valid Evidence Object (missing `data_period_end`, unknown `source_confidence`) MUST NOT advance to `NORMALIZED`.

### 6.3 Provider Confidence Defaults

| Provider | Default Confidence | Basis |
|---|---|---|
| Wind | `HIGH` | Institutional terminal, direct exchange feed |
| Choice (EmQuantAPI) | `HIGH` | Institutional data vendor |
| iFinD (THS) | `HIGH` | Institutional data vendor |
| Tushare Pro | `MEDIUM` | Licensed retail, regulated |
| JoinQuant | `MEDIUM` | Licensed retail, community |
| AkShare | `LOW` | Public aggregation, unregulated |
| Web scraping | `LOW` | No license, no SLA |

A Provider MAY earn a higher confidence rating through the Capability Maturity Ladder. Confidence MUST NOT be upgraded without new evidence.

### 6.4 Capability Chain Separation

A Provider capability claim MUST NOT skip layers. Each layer is independently verifiable:

```
Layer 1: Provider exists     ≠ Provider invoked
Layer 2: Provider invoked    ≠ Provider succeeded
Layer 3: Provider succeeded  ≠ Evidence authorized
```

**Layer 1 — Existence vs Invocation:** Configuration present, credentials valid, skill registered — none of these prove the Provider was actually called at runtime. An incident where the frontend receives HTML instead of JSON cannot attribute the failure to the Provider without first proving the Provider was invoked.

**Layer 2 — Invocation vs Success:** HTTP 200 and a non-empty response body prove the Provider returned *something*. They do not prove the returned data satisfies the business requirement. An empty `data` array wrapped in `_qc.status=success` may pass QC while carrying no usable information.

**Layer 3 — Success vs Authorization:** Correct data from a verified Provider does not mean the data may enter an investment conclusion. It must still pass the Quality Evaluation → Authorization Decision chain. Freshness, completeness, provenance, and allowed_use are evaluated independently of whether the Provider "worked."

**Why this matters:** The 2026-08-03 Auction Runtime Error RCA classified its root cause as `UNKNOWN (evidence insufficient)` because no retained evidence could determine which layer failed. The 2026-07-31 Auction P0 classified `Historical Production Success: NOT FOUND` because HTTP 200 (Layer 2) existed but content evidence (Layer 3) did not. Both failures trace to the same gap: the system cannot independently verify which capability layer was reached.

---

## 7. Runtime Evidence Contract

**Principle 5 (Evidence Retention Is Runtime Contract):** Evidence preservation is not a retrospective action taken after an incident. It is a base capability that the production Runtime MUST provide.

A Runtime that cannot answer these questions after a failure is not trustworthy:

1. Which layer produced the error response?
2. Which component failed?
3. Was the Provider invoked?
4. Does the returned content match the declared contract?

### 7.1 Minimum Incident Evidence Set

Every production API response MUST carry or be correlated with:

| Field | Purpose | Example |
|---|---|---|
| `request_id` | Unique identifier for the request | `req_a1b2c3d4` |
| `timestamp` | When the request was received (RFC 3339) | `2026-08-03T09:28:47+08:00` |
| `route` | Which endpoint was called | `/api/intel/market-context` |
| `http_status` | HTTP status code returned | `200`, `504`, `500` |
| `content_type` | Content-Type of the response | `application/json` |
| `response_body_hash` | SHA-256 of the full response body | `72a17651b6...` |
| `nginx_access_log` | Corresponding nginx access log entry | Timestamp + status + upstream |
| `backend_trace_id` | Backend trace/span ID for correlation | `trace_xyz` |
| `provider_execution_state` | Whether a Provider was invoked and its status | `invoked=yes,status=success` |

A missing field is an **Evidence Gap**. RCA with one or more gaps MUST be classified as `Evidence Confidence: LOW` and `Root Cause: UNKNOWN (evidence insufficient)`.

### 7.2 Incident Evidence Preservation Rule

When a production incident occurs, evidence preservation MUST precede any fix:

```
Incident detected
        ↓
Preserve: nginx access log (incident time window)
Preserve: application log (incident time window)
Preserve: at least one complete response example
        ↓
THEN: restart / rollback / deploy fix
```

Evidence collected after restart is not incident evidence — it is post-fix verification evidence. The two serve different purposes and MUST NOT be conflated.

### 7.3 Acceptance Scenario: TC-RUNTIME-EVIDENCE-001

**Scenario:** API returns an unexpected response (wrong Content-Type, error status, empty body).

**Expected:** The Runtime MUST preserve enough evidence to answer:

1. Which layer produced the response? (nginx? backend? upstream Provider?)
2. Which component failed? (timeout? exception? routing error? Provider error?)
3. Was the Provider invoked? If yes, what did it return?
4. Does the returned content match the declared API contract?

**Failure Mode (current):** The 2026-08-03 Auction Runtime Error received `Unexpected token '<'` (HTML where JSON was expected). The original HTTP status code, Content-Type, response body, request ID, and correlated nginx/backend logs were not preserved. Therefore:

```
Original Failure Source:  NOT PROVEN (candidate hypothesis only)
Evidence Confidence:      LOW
Root Cause:               UNKNOWN (evidence insufficient)
```

This scenario is NOT a provider failure, NOT an AkShare failure, and NOT a Wind failure. It is a **Runtime Evidence Preservation Gap** — the system's inability to prove which layer failed.

### 7.4 Relationship to Pre-Decision Evidence

| Dimension | Pre-Decision Evidence (§2-§6) | Post-Incident Evidence (§7) |
|---|---|---|
| **Proves** | "This data is trustworthy enough to enter a conclusion" | "This system can prove what happened during a failure" |
| **Object** | Evidence Object (business facts) | Runtime Evidence (system behavior facts) |
| **Governed by** | Freshness, completeness, provenance, validity, allowed_use | request_id, status_code, content_type, response_hash, trace/log correlation |
| **Failure mode** | Silent acceptance of stale/incomplete data → wrong conclusion | Silent failure → RCA degraded to hypothesis → untrustworthy Runtime |
| **Prototype incident** | 600439 F-03 (16-month stale financials passed QC) | Auction Runtime Error 2026-08-03 (HTML source unattributable) |

Both are required. A system with only Pre-Decision governance produces correct conclusions from bad data. A system with only Post-Incident governance produces perfect incident reports from an untrustworthy decision pipeline.

---

## 8. Relationship to Existing Governance Assets

### 8.1 Capability Claim Governance Framework

Evidence Governance defines the **data contract**. The Capability Framework defines the **claim contract**.

A Provider that reaches `EVIDENCE_RETRIEVED` (L4) in the Capability Framework but cannot produce a conformant Evidence Object has not satisfied the Evidence Governance contract. Both must pass for capability promotion.

### 8.2 Evidence Manifest Protocol

The [Evidence Manifest Protocol v0.1](../evidence/Vera_Evidence_Manifest_Protocol_v0.1.md) governs **end-to-end audit linkage** (request → observation → trust decision → artifact → capability claim).

The Evidence Object is the **operational data contract** that populates the Manifest's `observation` and `trust_decision` blocks:

```text
Evidence Object.source        → Manifest.observation.source
Evidence Object.source.provider → Manifest.observation.provider
Evidence Object.time           → Manifest.observation.source_timestamp / retrieved_at
Evidence Object.quality        → Manifest.trust_decision.qc_status / decision
Evidence Object.governance     → Manifest.trust_decision.allowed_use / blocked_fields
```

### 8.3 Institutional Provider Architecture

The Provider State Machine governs **how** a Provider is onboarded. Evidence Governance governs **what** a Provider must output once onboarded. Both are normative.

---

## 9. Freshness Policy Case Study: 600439 F-03 Counter-Example

### 9.1 Incident Summary

**Date**: 2026-08-02
**Stock**: 600439 (瑞贝卡)
**Symptom**: Report showed all financial data as of 2024-12-31 (16 months stale), with `as_of: 2026-08-02T18:06:34` (fetch time) and Trust Gate `success`.

**Root cause chain**:

```
stock_financial_analysis_indicator() → 9 rows (2024-03-31 to 2026-03-31)
        ↓
df.head(4) on ascending data → selected 4 oldest periods
        ↓
2025/2026 data discarded, 2024 data presented as "latest"
        ↓
QC: financials non-empty → completeness ≥ 0.8 → status = "success"
        ↓
Trust Gate passthrough → LLM trusts stale data → report misleads
```

**Multi-agent verification**: CC diagnosed → Codex independently verified → CC executed Path B fix → Codex re-reviewed → verdict NOT PROVEN due to Trust Gate semantics gap.

### 9.2 The F-03 Counter-Example (Governance Acceptance Test)

Codex re-review Finding F-600439-03 identified the critical failure mode that this Evidence Governance specification is designed to prevent.

**Scenario**:

```text
Input:
  completeness = 0.83       (5 of 6 dimensions present)
  stale_data = [financials]  (latest report period: 2024-12-31, age: 590 days)
  All other dimensions: fresh

Trust Gate evaluation (current code, 2026-08-03):
  freshness_ok = len(stale) <= 1  →  True  (1 ≤ 1)
  completeness >= 0.8              →  True  (0.83 ≥ 0.8)
  → status = "success"

Downstream consumer sees:
  _qc.status = "success"
  → Reasonable inference: "Data is production-ready for financial analysis"
  → Actual: Financial data is 19 months stale
```

**Why this is a governance failure, not a code bug**:

The `len(stale) <= 1` model is semantically wrong for financial evidence. It treats "one stale dimension among six" as acceptable regardless of which dimension is stale. A stale `dividends` field (acceptable) and a stale `financials` field (critical) receive identical treatment.

The correct question is not "how many dimensions are stale?" but "which critical dimensions are stale, and what downstream uses does that block?"

### 9.3 Governance Acceptance Criteria

The following acceptance test MUST pass before Trust Gate v2 can claim `PROVEN`.

**Test Case TC-FRESH-001: Single Critical Dimension Staleness**

```json
{
  "test_id": "TC-FRESH-001",
  "source": "600439 F-03 counter-example (Codex re-review, 2026-08-03)",

  "input": {
    "domain": "stock_analysis",
    "dimensions": {
      "realtime": {"status": "present", "freshness": "PASS"},
      "financials": {
        "status": "present",
        "latest_period": "2024-12-31",
        "age_days": 590,
        "freshness": "STALE"
      },
      "fund_flow": {"status": "missing"},
      "price_history": {"status": "present", "freshness": "PASS"},
      "news": {"status": "present", "freshness": "PASS"},
      "dividends": {"status": "present", "freshness": "PASS"}
    },
    "completeness": 0.83,
    "use_case": "fundamental_analysis"
  },

  "critical_dimensions_for_use_case": ["financials"],

  "expected_trust_gate_decision": {
    "status": "BLOCKED",
    "reason": "Critical dimension financials freshness = STALE (590 days)",
    "allowed_use": ["company_profile", "historical_context"],
    "blocked_use": [
      "fundamental_analysis",
      "investment_signal",
      "valuation",
      "position_recommendation",
      "trading_signal"
    ],
    "requires_human_review": true
  },

  "forbidden_outcomes": [
    "status = success",
    "allowed_use contains fundamental_analysis",
    "blocked_use is empty"
  ]
}
```

**Test Case TC-FRESH-002: Non-Critical Dimension Staleness (Should PASS)**

```json
{
  "test_id": "TC-FRESH-002",
  "source": "Inverse of TC-FRESH-001 — verifies no over-blocking",

  "input": {
    "dimensions": {
      "realtime": {"status": "present", "freshness": "PASS"},
      "financials": {
        "status": "present",
        "latest_period": "2026-03-31",
        "age_days": 125,
        "freshness": "PASS"
      },
      "fund_flow": {"status": "missing"},
      "price_history": {"status": "present", "freshness": "PASS"},
      "news": {"status": "present", "freshness": "PASS"},
      "dividends": {"status": "present", "freshness": "STALE", "age_days": 400}
    },
    "completeness": 0.83,
    "use_case": "fundamental_analysis"
  },

  "critical_dimensions_for_use_case": ["financials"],

  "expected_trust_gate_decision": {
    "status": "PARTIAL",
    "reason": "Non-critical dimension dividends stale; critical dimension financials fresh",
    "allowed_use": ["fundamental_analysis", "company_profile", "screening"],
    "blocked_use": ["investment_signal"],
    "requires_human_review": false
  }
}
```

### 9.4 Defect-to-Governance Mapping

| Observed Defect | Governance Rule Violated | Acceptance Test |
|---|---|---|
| `df.head(4)` on ascending data discarded latest periods | §6.1 Provider Normalization: output selection logic is not contract-governed | Provider contract verification |
| `as_of` carried fetch time, implied data currency | §2.3 Three-Date Rule: `data_period_end` ≠ `fetched_at` | Schema v2 migration |
| QC returned `success` with 16-month-stale financials | §4.2 Critical-domain gating: financials staleness must BLOCK | **TC-FRESH-001** |
| `len(stale) <= 1` allowed single critical dimension staleness | §4.2: scalar stale-count cannot substitute for criticality weighting | **TC-FRESH-001** |
| `_qc_macro()` used different Trust Gate than `_qc_stock()` | §5.1: inconsistent Trust Gate semantics | §5.3 Phase 1 |
| `date_col is None` → silent asc head(4) regression risk | §6.1: normalization failure must be loud, not silent | Provider contract: missing column → UNKNOWN |
| Missing report date → exception swallowed, no stale flag | §4.2: UNKNOWN freshness ≠ PASS | Freshness evaluation: missing date → UNKNOWN |

### 9.5 Resolution Status

| Item | Status |
|---|---|
| Path B fix (acquisition truncation) | COMPLETE — `stock_data.py:310-318` |
| Trust Gate semantics (F-03) | NOT PROVEN — deferred to Trust Gate v2 |
| Schema v2 (`as_of` → `data_period_end` + `fetched_at`) | NOT STARTED — deferred to Schema v2 |
| Evidence Governance v1.0 (this document) | DESIGN / NORMATIVE DRAFT — P0 |
| Acceptance tests TC-FRESH-001, TC-FRESH-002 | SPECIFIED — awaiting Trust Gate v2 implementation |
| Iteration close decision | `/tmp/600439_path_b_verdict_delta_decision.md` |

**This case study is the derivation source for Evidence Governance v1.0. The governance model was not designed in advance of a failure — it was derived from a real failure whose root cause was a governance gap, not a code defect.**

---

## 10. Governance Learning Loop

### 10.1 Purpose and Principle

Evidence Governance is not a static schema. It is a **normative system that evolves through real failure cases**. A fix that repairs code without producing a governance rule has not been absorbed into the system. A governance rule without an acceptance test cannot be verified.

**Governing principle**:

```text
Production Incident
        ↓
RCA Evidence Collection
        ↓
Observed Defect Classification
        ↓
Governance Rule Definition
        ↓
Acceptance Test Creation
        ↓
Runtime Enforcement
```

Each stage produces a required output. A stage without its output is incomplete. A rule that skips stages is not governed.

**Why this loop exists**:

Without a formal absorption mechanism, production incidents produce one-time fixes that do not strengthen the system. The same defect class can recur through a different code path, a different provider, or a different domain — and the system will fail again. The Learning Loop exists to ensure that **every governed failure produces a governed rule**, and that every rule can be tested independently of the incident that created it.

**What counts as governance input**:

- A production incident where Trust Gate returned `success` on evidence that should have been blocked
- A provider whose output passed QC but whose data period was unknown
- A capability claim that was made without evidence of the claimed maturity level
- A test that passed but should have failed (false negative in verification)

**What does NOT count as governance input**:

- A routine code bug with no governance dimension (e.g., a typo, a missing import)
- A provider outage (unless it exposes a missing fallback contract)
- A performance issue (unless it exposes a timeout-vs-SLA mismatch in the deployment contract)

### 10.2 Learning Loop Lifecycle

Each stage in the loop has a definition and a required output. A stage is complete only when its output is produced, reviewed, and registered in this document.

| Stage | Definition | Required Output | Owner |
|---|---|---|---|
| **Incident** | A production or test anomaly with potential governance dimension | Incident Record (date, symptom, affected domain, initial scope) | Any observer |
| **RCA** | Root cause analysis backed by verifiable evidence | Evidence-backed RCA (root cause chain, not symptom description) | Builder |
| **Observed Defect** | The abstract defect class, separated from the specific code path | Defect Classification (e.g., "scalar stale-count substituted for criticality weighting") | Builder + Reviewer |
| **Governance Rule** | A new or revised normative constraint in this document | Normative Rule (section reference, rule text, scope) | Builder |
| **Acceptance Test** | An executable verification that encodes the counter-example | Test Scenario (test ID, input, expected output, forbidden outcomes) | Builder |
| **Runtime Enforcement** | Trust Gate or equivalent system control that enforces the rule | Enforcement Evidence (code path, configuration, or gate logic that blocks the defect class) | Builder |
| **Verification** | Independent confirmation that the rule is enforced | Reviewer Verdict (verification report, capability verdict delta) | Reviewer |

A governance case is **SPECIFIED** when stages Incident through Acceptance Test are complete. It is **PROVEN** when Runtime Enforcement passes independent Verification.

### 10.3 Case Registry

The Case Registry is the single source of truth for which production failures and governance gaps have been absorbed into the governance model. It consists of two tiers:

**Tier A — Incident-Derived Cases:**

Cases derived from real production incidents. These satisfy the One Incident → One Rule → One Test constraint. Whether a Tier A case counts toward the Architecture Freeze Gate depends on which governance domain it addresses — the Gate requires three specific domains (§10.4); cases in additional domains (e.g., R-01 Runtime Evidence) are tracked at Tier A but do not count toward the Gate.

| Case ID | Domain | Origin | Governance Rule | Acceptance Test | Status |
|---|---|---|---|---|---|
| **F-03** | Freshness | 600439 financial freshness failure (2026-08-02) | §4.2: Critical-domain freshness gating — freshness cannot be inferred from completeness; critical dimension STALE → BLOCK | TC-FRESH-001 (critical stale → BLOCK), TC-FRESH-002 (non-critical stale → PARTIAL) | **SPECIFIED** |
| **R-01** | Runtime Evidence Preservation | Auction Runtime Error 2026-08-03 + Auction P0 2026-07-31 | §7: Production Runtime MUST preserve incident evidence (request_id, status_code, content_type, response_hash, trace/log correlation); missing evidence → RCA confidence downgraded to LOW / Root Cause UNKNOWN | TC-RUNTIME-EVIDENCE-001 (§7.3): API returns unexpected response → evidence preserved → RCA can determine which layer failed | **SPECIFIED** |
| **C-01** | Claim Strength | stock-analyst.md prompt design causing systematic unauthorized claim escalation — prompt structure combined with absence of claim authorization boundary generates L7 prescriptive output (position sizing, strategy selection, buy/sell/hold) from L1-L2 descriptive evidence without authorization gate | Evidence confidence and authorization level SHALL constrain allowed conclusion strength; descriptive ≠ predictive ≠ prescriptive; claim tier escalation requires evidence tier upgrade. Current enforcement: NOT IMPLEMENTED — specification only. Runtime blocking NOT CLAIMED. | TC-CLAIM-001 (no position% in output), TC-CLAIM-002 (no probability without model/methodology/error bounds) | **SPECIFIED** |

**Tier B — Proactive Governance Findings (Tracked, non-blocking):**

Findings identified through proactive audit, architecture review, or governance gap analysis that do not originate from a specific production incident. These are tracked but MUST NOT block the Architecture Freeze Gate. A finding may be promoted to Tier A if a future production incident provides the required evidence chain.

| Finding ID | Domain | Origin | Governance Rule | Status |
|---|---|---|---|---|
| **P-01** | Provider Capability | IMA / Wind Integration Audit (D19/D27) — proactive audit identified credential found, skill assets found, runtime invocation NOT PROVEN, Trust Gate integration NOT PROVEN. Originating incident: NONE (proactive governance gap identification) | Provider existence ≠ capability proven; Provider credential ≠ runtime capability; declared capability MUST NOT exceed verified runtime capability | **TRACKED** |

Tier B findings are not in the Learning Loop because they lack an originating incident. They remain tracked until converted through future incident evidence or validated governance scenarios.

**P-01 Lock Condition**: P-01 is currently a governance finding derived from audit evidence — NOT a production incident. Proactive audit finding ≠ Production incident. Before promotion from `TRACKED` to `SPECIFIED`, P-01 requires: (1) a production incident where a declared provider capability was invoked but failed to produce evidence, OR (2) a runtime attestation test that independently verifies the credential → adapter → invocation → evidence → Trust Gate chain. Until then, it remains TRACKED (Tier B) and MUST NOT block the Architecture Freeze Gate.

**Case promotion criteria (Tier A only)**:

A case graduates from `SPECIFIED` to `PROVEN` when:
1. An acceptance test exists that encodes the counter-example from the originating incident
2. The Trust Gate implementation passes the acceptance test
3. An independent reviewer verifies the implementation against the test and issues a verdict
4. The verdict delta is recorded in the Case Registry

A case at `NOT STARTED` or `IDENTIFYING` MUST have its origin incident identified before it can enter the loop. A case without a real incident is speculative design — it does not belong in the Learning Loop.

### 10.4 Architecture Freeze Gate

**Freeze Rule**:

Vera Evidence Governance MUST NOT enter an Implementation Sprint until the Architecture Freeze Gate is satisfied.

**Gate criteria** — all three conditions must hold:

```text
Three incident-derived governance cases at SPECIFIED or above
        AND
Acceptance Scenario Defined for each case
        AND
Runtime Enforcement Boundary Identified for each case
```

Proactive governance findings without originating production incidents (Tier B) MUST NOT block Architecture Freeze. They remain tracked until converted through future incident evidence or validated governance scenarios.

**Gate domains are explicitly declared, not dynamically selected from the registry.** A new incident in an existing domain replaces its predecessor; a new incident in a new domain requires a Gate amendment, not automatic inclusion.

### 10.4.1 Freeze Gate Domains (incident-derived, counted)

| # | Case | Domain | What It Validates | Current Status |
|---|---|---|---|---|
| **Case 1 — Freshness** | F-03 | Data Quality | Complete data ≠ fresh data. A dimension can be present, non-empty, and pass completeness thresholds while carrying stale values. The Trust Gate must distinguish presence from currency. | **SPECIFIED** |
| **Case 2 — Claim Strength** | C-01 | Conclusion Authorization | Evidence confidence ≠ allowed conclusion strength. Originating incident: stock-analyst.md prompt design causing systematic claim escalation from L1-L2 evidence to L7 prescriptive output (position sizing, strategy selection, buy/sell/hold) without authorization gate. Validation report: C-01_VALIDATION_REPORT.md. | **SPECIFIED** |
| **Case 3 — [Pending]** | — | TBD by next production incident | Reserved for the next incident-derived governance domain. Will be assigned when a production failure exposes a governance gap in a domain not yet covered. | **PENDING INCIDENT** |

**Explicitly excluded from Freeze Gate:**
- **P-01 (Provider Capability)** — Tier B, proactive audit finding, no originating production incident
- **R-01 (Runtime Evidence)** — separate governance track (§7), orthogonal to business evidence governance

Gate count: **2/3 incident-derived cases**. P-01 and R-01 are tracked but MUST NOT satisfy the Gate requirement.

**Why 2/3, not 3/3**: The third case slot is intentionally held open. It can only be filled by a future production incident that exposes a governance gap in a domain not yet covered by F-03 (Freshness) or C-01 (Claim Strength). Artificial case creation — designing a governance rule first and then searching for an incident to justify it — would reverse the Learning Loop's causal direction from `Incident → Rule` to `Rule → Incident`. This Gate exists to protect that direction. The Architecture Freeze remains ACTIVE until a real failure demands the third domain.

### 10.4.2 Separate Governance Track (not counted toward Freeze Gate)

| ID | Domain | Status | Origin |
|---|---|---|---|
| **R-01** | Runtime Evidence Preservation | **SPECIFIED** | Auction Runtime Error 2026-08-03 + Auction P0 2026-07-31 (two production incidents) |
| **P-01** | Provider Capability | **TRACKED** (Tier B) | IMA/Wind Integration Audit (D19/D27) — proactive audit, no incident |

**Freeze boundary**:

While the Architecture Freeze is in effect:
- Design documents MAY be created or revised
- Acceptance tests MAY be specified
- Case studies MAY be documented
- Production code MUST NOT be modified to implement new governance rules
- Provider integrations MUST NOT be added
- Schema migrations MUST NOT be executed

The Freeze is lifted when all three cases reach `SPECIFIED`. Each case then progresses through the Learning Loop independently — a case at `SPECIFIED` may enter implementation while other cases remain at `SPECIFIED`.

### 10.5 Governance Change Control

**Builder ≠ Reviewer Separation** (Normative):

```text
Builder                       Reviewer
────────                      ────────
Implements fix                Validates governance interpretation
Writes acceptance test        Verifies test against defect class
Produces evidence             Issues capability verdict
PROHIBITED FROM:              PROHIBITED FROM:
  Declaring own PASS            Implementing fixes
  Promoting own capability      Writing production code
  Self-verifying                Self-reviewing
```

This separation is not a process preference. It is a **governance requirement**. The 600439 incident demonstrated its necessity: CC (Builder) implemented a Trust Gate fix that CC believed addressed the defect. Codex (Reviewer) identified that `len(stale) <= 1` did not actually prevent the failure mode. Without the Reviewer, the defect would have been masked, not fixed.

**Prohibited patterns**:

- Builder declares `PASS` on own implementation
- Fix completion is treated as capability upgrade
- Smoke test `PASS` is treated as production readiness
- Acceptance test is written after implementation to match the implemented behavior
- Governance rule is added without an originating incident

**Required evidence for rule promotion**:

A governance rule may be promoted from `SPECIFIED` to `PROVEN` only when:
1. The Builder has produced: implementation diff, acceptance test, runtime evidence
2. The Reviewer has produced: independent verification report, capability verdict delta
3. The Orchestrator has recorded: promotion decision, case registry update

### 10.6 One Incident → One Rule → One Test

**Mandatory constraint**:

```text
One Incident
        ↓
One Governance Rule
        ↓
One Acceptance Test
```

This constraint exists to prevent three failure patterns observed in governance system design:

1. **Scope explosion**: A single incident triggers a comprehensive redesign of the entire governance model. The original defect is lost in architectural ambition. The fix never ships.

2. **Untestable rules**: A governance rule is added without a specific acceptance test. The rule exists in prose but cannot be verified. Future changes may violate it without detection.

3. **Accumulated complexity**: Multiple incidents are batched into a single governance revision. The interaction between rules is untestable. Regression attribution is impossible.

**Application**: The 600439 incident produced exactly one governance rule (§4.2 Critical-domain freshness gating) with exactly two acceptance tests (TC-FRESH-001, TC-FRESH-002). It did NOT attempt to also fix Provider contracts, schema migration, or `_qc_macro()` alignment — those belong to separate cases with separate originating incidents.

**When to split an incident**: If an incident reveals defects in two distinct governance domains (e.g., Freshness AND Provider Capability), create two cases. Each follows the One Incident → One Rule → One Test constraint independently.

---

## 11. Migration Boundary

### 11.1 What This Document Is

- A **normative design** for the Evidence Governance Layer
- A **contract specification** that all future Provider integrations MUST satisfy
- A **reference** for Trust Gate v2 design
- The **governance constitution** for how evidence enters Vera's reasoning pipeline

### 11.2 What This Document Is Not

- An **implementation task** — no code changes are authorized by this document alone
- A **capability claim** — Evidence Governance is DESIGN stage (L0→L1 on the Capability Maturity Ladder)
- A **replacement** for existing QC functions — `_qc_stock()` and `_qc_macro()` continue to operate under current semantics until Trust Gate v2 migration
- A **static specification** — it evolves through the Governance Learning Loop (§10)

### 11.3 Relationship to Active Work

| Item | Status | Governance Relationship |
|---|---|---|
| 600439 Path B fix | COMPLETE (acquisition fix only) | Trust Gate semantics NOT PROVEN; deferred to v2; absorbed as Case F-03 |
| Schema v2 (`as_of` → `data_period_end` + `fetched_at`) | NOT STARTED | Implements §2.3 Three-Date Rule |
| Trust Gate Freshness Policy v2 | NOT STARTED | Implements §4.2 Critical-domain gating; blocked by Architecture Freeze Gate (§10.4) |
| `_qc_macro()` Trust Gate alignment | NOT STARTED | Implements §5.2 Target State |
| Provider confidence integration | NOT STARTED | Implements §2.4 Source Confidence Model; requires Case P-01 |
| Auction API timeout (2026-08-03) | RCA COMPLETE | Absorbed as Case R-01 (Runtime Evidence Preservation); NOT Provider Capability — no provider invocation evidence in incident |

---

## 12. Verification Checklist

Design review of this document should verify:

- [ ] Evidence Object schema covers all five domains (§5.1–§5.5)
- [ ] Bitemporal contract (§2.3) enforces valid_time + knowledge_time as MUST for all time-bearing domains
- [ ] Temporal Leakage Gate (§2.3) prevents `query_time <= knowledge_time` for Agent claims
- [ ] Freshness Policy (§4) replaces `len(stale) <= 1` with per-domain criticality
- [ ] Evidence → Decision separation (§3A.2) is normative: Trust Evaluation PASS != auto-authorize all uses
- [ ] Authorization Decision Object (§3A.3) enforces fail-closed when fields are UNKNOWN
- [ ] Claim Strength Contract (§3B) maps evidence tier to maximum claim strength
- [ ] Claim Escalation Gate (§3B.2) prevents rhetorical escalation without evidential escalation
- [ ] Cross-source confidence formula (§2.5) treats authority and temporal validity as independent factors
- [ ] Durability receipt (§2.6) is required for HIGH-confidence providers
- [ ] All eight Governing Principles (§1.1) have corresponding normative rules
- [ ] Source confidence model (§2.4) distinguishes provider classes and degrades on fallback
- [ ] Provider normalization requirement (§6.1) is testable
- [ ] Alignment with Capability Framework, Manifest Protocol, Provider Architecture, and Enterprise Architecture is explicit (§8)
- [ ] Case Study (§9) maps 600439 defects to governance rules with acceptance tests
- [ ] Governance Learning Loop (§10) defines lifecycle stages, Case Registry, Architecture Freeze Gate, change control, and One Incident → One Rule → One Test
- [ ] Migration boundary (§11) is clear: design only, no implementation claim, freeze gate active

### Phase 2 Acceptance: Five Exit Questions

1. **Why is this evidence trustworthy?** → Provenance + source + valid_time + knowledge_time + provider attestation (§2)
2. **What conclusions can this evidence support?** → allowed_use + claim_strength + consumer scope (§3A, §3B)
3. **Why can't it support stronger conclusions?** → blocked_use + missing evidence + temporal limitation + authorization boundary (§3A.3, §3B.1)
4. **How does the system prevent temporal leakage?** → Bitemporal contract + knowledge_time ≤ query_time gate + per-data-class freshness (§2.3, §4)
5. **How does the system prevent Agent privilege escalation?** → Evidence→Decision separation + Claim Escalation Gate + UNKNOWN fail-closed (§3A.2, §3B.2, Principle 8)

---

*This document governs evidence. The Capability Claim Governance Framework governs claims about evidence. The Governance Learning Loop governs how both evolve. None govern markets.*
