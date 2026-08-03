# News Evidence Provider Boundary v0.1

**Document Status:** DESIGN ONLY  
**Runtime Implementation:** NOT IMPLEMENTED  
**Production Capability:** NOT CLAIMED  
**Effective date:** 2026-08-03  
**Scope:** News and information content as Evidence within Vera Trust Runtime  
**Aligns with:** [Evidence Governance v1.0](EVIDENCE_GOVERNANCE_v1.0.md), [Capability Claim Governance Framework v1.0](Vera_Capability_Claim_Governance_Framework_v1.md), [Institutional Provider Architecture v0.1](INSTITUTIONAL_PROVIDER_ARCHITECTURE_v0.1.md)

---

## 1. Purpose

This document establishes governance boundaries for news and information content as Evidence within Finance Suite's Trust Runtime. It converts a production failure case ("news extraction failed") into a normative Provider Capability boundary definition.

**Governing Question:**
> When a news article is fetched, what evidence is required before it may be used in research or investment conclusions?

**Key Principle:**
```
Source exists
  != Source accessible
  != Content extractable
  != Evidence validated
  != Research usage authorized
```

Each layer is independent and must be governed separately.

---

## 2. Provider Capability Boundary

### 2.1 Five-Layer Separation

News providers must progress through five distinct capability boundaries:

| Layer | Capability | Evidence Required | What This DOES NOT Prove |
|---:|---|---|---|
| **L0** | `SOURCE_EXISTS` | URL, source identifier, or reference exists | Source is accessible |
| **L1** | `SOURCE_ACCESSIBLE` | HTTP 200, or equivalent reachability proof | Content is extractable |
| **L2** | `CONTENT_EXTRACTABLE` | Text body retrieved, encoding confirmed | Content is valid evidence |
| **L3** | `EVIDENCE_VALIDATED` | Publication time, author, source identity verified | Usage is authorized |
| **L4** | `RESEARCH_AUTHORIZED` | Trust Gate decision: allowed_use boundary | May be cited in conclusions |

**Critical invariant:** Each layer MUST be proven independently. A later layer MUST NOT be claimed based on an earlier layer alone.

### 2.2 Prohibited Claim Escalations

The following capability escalations are PROHIBITED:

```text
PROHIBITED:
  "We can open the webpage"
    -> "News integration is complete"

PROHIBITED:
  "We extracted text from the article"
    -> "This is trusted research input"

PROHIBITED:
  "The scraper returned 200 OK"
    -> "News evidence is available for agent consumption"

PROHIBITED:
  "The provider config lists news sources"
    -> "News capability is production-ready"
```

**Rationale:** Each escalation skips one or more governance layers defined in §2.1. A capability claim MUST NOT exceed the lowest verified layer of its dependency chain.

---

## 3. Evidence Object Schema for News

### 3.1 Canonical News Evidence Object

When a news article enters the Trust Gate, it MUST carry:

```json
{
  "content": {
    "body": "<extracted text>",
    "title": "<article title>",
    "summary": "<optional summary>"
  },
  "provenance": {
    "source_url": "<original URL>",
    "source_domain": "<domain>",
    "source_identity": "<publisher name>",
    "extraction_method": "api|scraper|rss|manual",
    "extraction_timestamp": "<ISO 8601>"
  },
  "temporal": {
    "publication_time": "<ISO 8601>",
    "last_updated_time": "<ISO 8601 or null>",
    "data_period_start": "<ISO 8601 or null>",
    "data_period_end": "<ISO 8601 or null>"
  },
  "validity": {
    "content_completeness": 0.0-1.0,
    "extraction_confidence": 0.0-1.0,
    "source_verification_status": "verified|unverified|unknown"
  },
  "metadata": {
    "author": "<author name or null>",
    "content_type": "news|research|opinion|press_release",
    "language": "<ISO 639-1>",
    "character_count": 0
  }
}
```

### 3.2 Field Semantics

#### 3.2.1 Provenance Fields

- **`source_url`**: MUST be the canonical URL where the content was retrieved. If the source is behind authentication or paywalled, this MUST be marked explicitly.
- **`source_identity`**: MUST identify the publisher or platform (e.g., "新浪财经", "财联社", "Bloomberg").
- **`extraction_method`**: MUST record how content was obtained. `api` implies official API with authorization. `scraper` implies HTML parsing. `manual` implies human input.
- **`extraction_timestamp`**: MUST be the server time when extraction completed, NOT the publication time.

#### 3.2.2 Temporal Fields

- **`publication_time`**: MUST be the time when the article was originally published. If unavailable, this field MUST be `null`.
- **`last_updated_time`**: If the article has been updated since publication, this MUST reflect the most recent update time. Otherwise `null`.
- **`data_period_start` / `data_period_end`**: If the article discusses events or data covering a specific time range (e.g., "Q2 2026 earnings"), these fields SHOULD capture that range.

**Critical constraint:** `extraction_timestamp` MUST NOT be used as a substitute for `publication_time`. Fetching an article today does not mean the article was written today.

#### 3.2.3 Validity Fields

- **`content_completeness`**: Ratio of successfully extracted content to expected content length. If the extraction is incomplete (e.g., "read more" paywall encountered), this MUST be < 1.0.
- **`extraction_confidence`**: Provider's self-assessment of extraction quality. If content structure is ambiguous or extraction heuristics are weak, this MUST be reduced.
- **`source_verification_status`**: 
  - `verified`: Publisher identity independently confirmed (e.g., official domain, verified social media account)
  - `unverified`: Publisher identity claimed but not verified
  - `unknown`: Publisher identity cannot be determined

---

## 4. Trust Gate Decision Logic (Design)

### 4.1 Freshness Evaluation

News evidence MUST be evaluated for freshness based on `publication_time`, NOT `extraction_timestamp`.

**Freshness ladder (illustrative):**

| Publication Age | Freshness Grade | Allowed Use Example |
|---|---|---|
| < 24 hours | `REAL_TIME` | Breaking news, market reaction analysis |
| 24h - 7 days | `RECENT` | Weekly trend analysis, event retrospective |
| 7 - 30 days | `CURRENT` | Monthly review, comparative analysis |
| 30 - 90 days | `HISTORICAL` | Quarterly trend, long-term pattern |
| > 90 days | `ARCHIVAL` | Historical research, regulatory review |

**Governance rule:** If `publication_time` is `null`, freshness MUST be classified as `UNKNOWN`, and Trust Gate MUST restrict usage to non-time-sensitive contexts.

### 4.2 Source Confidence Evaluation

Source confidence depends on:
1. **Source identity verification** (§3.2.3)
2. **Extraction method reliability** (api > rss > scraper > manual)
3. **Content completeness** (§3.2.3)

**Confidence ladder (illustrative):**

| Conditions | Confidence Grade | Allowed Use Example |
|---|---|---|
| Verified source + API extraction + completeness ≥ 0.95 | `HIGH` | Primary research citation |
| Verified source + RSS/scraper + completeness ≥ 0.80 | `MEDIUM` | Supporting evidence |
| Unverified source OR completeness < 0.80 | `LOW` | Contextual reference only |
| Unknown source OR extraction_confidence < 0.50 | `INSUFFICIENT` | Not authorized for research |

### 4.3 Authorization Decision

Trust Gate produces an `allowed_use` boundary:

```json
{
  "allowed_use": [
    "background_research",
    "trend_identification",
    "comparative_analysis"
  ],
  "blocked_use": [
    "primary_citation",
    "quantitative_model_input",
    "regulatory_filing"
  ],
  "claim_strength": "SUPPORTING_EVIDENCE",
  "trust_decision": "CONDITIONAL_PASS",
  "restrictions": [
    "Must be cross-referenced with at least one additional source",
    "Not suitable as sole evidence for investment recommendation"
  ]
}
```

**Critical invariant:** A Trust Gate PASS for completeness and freshness DOES NOT automatically authorize all downstream uses. Authorization is a separate decision layer (aligned with Evidence Governance v1.0 §1.2).

---

## 5. Alignment with Existing Governance

### 5.1 Evidence Governance v1.0

This document extends Evidence Governance v1.0 §2 (Evidence Object Schema) to the news domain. All eight governing principles from Evidence Governance v1.0 §1.1 apply:

- **P-01 Data present ≠ Evidence valid**: Extracting article text does not prove the article is valid evidence.
- **P-02 QC passed ≠ Consumer safe**: Text completeness check does not authorize research usage.
- **P-03 Fetch timestamp ≠ Data period**: `extraction_timestamp` MUST NOT be conflated with `publication_time`.
- **P-06 Schema ≠ Data Contract**: A `publication_time` field that exists but carries extraction time is a contract violation.
- **P-07 Declared Capability ≠ Effective Capability**: A provider config listing news sources does not prove those sources are accessible.
- **P-08 UNKNOWN SHALL NOT ESCALATE PRIVILEGE**: If source identity is unknown, confidence defaults to INSUFFICIENT, not MEDIUM.

### 5.2 Provider Capability Claim (P-01)

News providers follow the same capability maturity ladder as institutional data providers (Capability Claim Governance Framework v1.0 §3):

| Maturity Level | News Provider Example |
|---|---|
| L0: UNKNOWN | No news source registered |
| L1: SHELL VERIFIED | News feed URL exists in config |
| L2: TRANSPORT VERIFIED | HTTP HEAD request returns 200 |
| L3: AUTH BOUNDARY VERIFIED | Paywall or API key authentication fails closed as expected |
| L4: RUNTIME VERIFIED | Article text successfully extracted in scoped test |
| L5: EVIDENCE VERIFIED | Publication time, source identity, and content completeness are independently validated |
| L6: LIVE VERIFIED | Evidence Manifest license authorizes live news capability claim |

**Current status of news capability in Finance Suite:** NOT ASSESSED (this document is design-only).

### 5.3 Claim Strength Ladder

News evidence must be evaluated using the Claim Strength ladder (Evidence Governance v1.0 §4.2):

- **INSUFFICIENT**: Unknown source, incomplete extraction, or no publication time
- **WEAK**: Low confidence, unverified source, or archival (>90 days)
- **SUPPORTING**: Medium confidence, verified source, recent publication
- **STRONG**: High confidence, official API, real-time, verified publisher
- **NORMATIVE**: Reserved for regulatory filings, official announcements

**Design note:** Most news content will fall into SUPPORTING or WEAK categories. STRONG is achievable only with official APIs and verified sources. NORMATIVE is typically not applicable to news content.

---

## 6. Future Acceptance Tests (Design Only)

The following test cases define the EXPECTED behavior of a conformant news evidence provider. These are design specifications, NOT implemented tests.

### TC-NEWS-001: Source Identity Verification

```yaml
Given:
  provider: news_scraper
  source_url: "https://finance.sina.com.cn/stock/relnews/cn/2026-08-03/doc-abc123.shtml"

When:
  extraction completes

Check:
  - source_identity is "新浪财经"
  - source_verification_status is "verified"
  - source_domain is "finance.sina.com.cn"

Expected:
  Trust Gate assigns confidence ≥ MEDIUM
```

### TC-NEWS-002: Publication Time vs Extraction Time

```yaml
Given:
  article published: 2026-08-01 09:30:00
  extraction time: 2026-08-03 15:45:00

When:
  Evidence Object is created

Check:
  - temporal.publication_time == "2026-08-01T09:30:00Z"
  - provenance.extraction_timestamp == "2026-08-03T15:45:00Z"
  - publication_time != extraction_timestamp

Expected:
  Freshness evaluation uses publication_time, not extraction_timestamp
```

### TC-NEWS-003: Incomplete Extraction Handling

```yaml
Given:
  article behind paywall
  extraction stopped at "read more..." link
  extracted 40% of full content

When:
  Evidence Object is created

Check:
  - validity.content_completeness == 0.40
  - validity.extraction_confidence < 0.80

Expected:
  Trust Gate assigns confidence = LOW or INSUFFICIENT
  allowed_use excludes "primary_citation"
```

### TC-NEWS-004: Unknown Publication Time

```yaml
Given:
  scraper cannot locate publication timestamp in HTML
  extraction succeeds but publication_time == null

When:
  Trust Gate evaluates freshness

Check:
  - temporal.publication_time is null
  - freshness classification == UNKNOWN

Expected:
  Trust Gate restricts allowed_use to non-time-sensitive contexts
  blocked_use includes "real_time_analysis", "breaking_news_response"
```

### TC-NEWS-005: Authorization Boundary Separation

```yaml
Given:
  content_completeness == 0.95
  extraction_confidence == 0.90
  source_verification_status == "verified"
  
When:
  Trust Gate evaluates Evidence

Check:
  - trust_decision == "PASS"
  - BUT allowed_use != ["*"]
  - allowed_use is scoped based on source confidence + freshness
  
Expected:
  A PASS on validity does NOT automatically authorize all uses
  Authorization is a separate decision layer
```

---

## 7. Prohibited Actions (Freeze Boundary)

To maintain this document as DESIGN ONLY, the following actions are PROHIBITED:

### 7.1 Implementation Actions

- **PROHIBITED:** Writing news scraper adapters
- **PROHIBITED:** Integrating news APIs (Sina, Cailian, Bloomberg, etc.)
- **PROHIBITED:** Modifying Runtime to consume news Evidence Objects
- **PROHIBITED:** Adding news providers to production config
- **PROHIBITED:** Deploying news extraction infrastructure

### 7.2 Capability Claim Actions

- **PROHIBITED:** Claiming "News integration complete"
- **PROHIBITED:** Adding news capability to Evidence Manifest
- **PROHIBITED:** Promoting news providers beyond DESIGN status
- **PROHIBITED:** Using news content in production research workflows

### 7.3 Governance Expansion

- **PROHIBITED:** Adding news-specific Freeze Gate domains
- **PROHIBITED:** Creating news provider state machines
- **PROHIBITED:** Writing news-specific QC rules

**Rationale:** This document defines governance boundaries for a future capability. Implementation and capability claims are deferred to a later window.

---

## 8. Document Status Summary

**What This Document IS:**
- A governance boundary definition for news evidence
- A P-01 Provider Capability case study
- A design template for future news integration
- An extension of Evidence Governance v1.0 to the news domain

**What This Document IS NOT:**
- An implementation plan
- A production capability claim
- A signal that news integration is underway
- A commitment to deliver news capability in any specific window

**Governance Maturity:**
- **Design Phase:** COMPLETE
- **Specification Phase:** COMPLETE
- **Implementation Phase:** NOT STARTED
- **Verification Phase:** NOT STARTED
- **Production Phase:** NOT CLAIMED

**Next Window Prerequisites (if news capability is prioritized):**
1. Identify target news sources and access methods
2. Establish source verification registry
3. Implement Evidence Object normalization layer
4. Wire Trust Gate decision logic for news domain
5. Create acceptance test suite (TC-NEWS-001 through TC-NEWS-005)
6. Execute verification and claim maturity level

**Current Status:** ARCHITECTURE REFERENCE ONLY

---

## 9. Review Checklist

- [ ] Does this document extend existing governance frameworks without contradicting them?
- [ ] Are the five capability layers (SOURCE_EXISTS → RESEARCH_AUTHORIZED) clearly separated?
- [ ] Are prohibited claim escalations explicitly listed?
- [ ] Is the Evidence Object schema aligned with Evidence Governance v1.0 §2?
- [ ] Are all temporal semantics (publication_time vs extraction_timestamp) clearly distinguished?
- [ ] Is the document clearly marked as DESIGN ONLY / NOT IMPLEMENTED?
- [ ] Are future acceptance tests specified but NOT executed?
- [ ] Does the document avoid making any production capability claims?

**Review Status:** SELF-REVIEW PASS (2026-08-03)  
**Adversarial Review:** NOT REQUESTED (design document, not production claim)  
**Implementation Authorization:** NOT GRANTED

---

**End of Document**
