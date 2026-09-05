# Vera Context Admission Coverage Contract v0.1

**状态：** FROZEN DESIGN ASSET
**Mode：** Architecture / Validation Only
**日期：** 2026-08-12
**前置：**
- `CURRENT_STATE_ARCHITECTURE_REBASELINE_v0.1.md` (FROZEN / PARTIALLY VALID)
- [[principle_trust_gate_context_boundary]] — Gate Context Boundary Principle
- [[project_stock_analysis_critical_data_provider_matrix_v01]] — Contract v0.2 (FROZEN)

**约束：** No implementation authorized. 本文件是契约定义，不是实现计划。

---

## 0. Purpose

本 Contract 定义 Finance Suite 所有 context entry 的 admission 契约。目标不是"让 17/17 都有 Gate 代码"，而是：

1. 冻结每个 entry 的身份（producer、evidence class、consumer、risk taxonomy）
2. 将 17 个 entry 归纳为少数 Policy Family，避免 17 套独立 Gate
3. 定义每个 Policy Family 的 Assessment + Admission 规则
4. 所有 entry 统一经过四层模型：`EvidenceRecord → EvidenceAssessment → ContextAdmissionDecision → CuratedEvidenceBundle`

完成时，得到的是 **Context Admission Contract**，不是 17 处 `if/else`。

---

## 1. Evidence Levels (继承自 Rebaseline)

| Level | Definition |
|-------|-----------|
| **STATICALLY CONFIRMED** | 代码存在、结构正确，通过代码阅读验证 |
| **LOCAL TEST PROVEN** | 本地测试/smoke 通过，有 test artifact |
| **PRODUCTION OBSERVED** | Requires: active production path identity + real request/evidence + admission decision/receipt + confirmed downstream consumer/context |

**当前 PRODUCTION OBSERVED = 0 entries.**

---

## 2. Per-Entry Contract

### 2.1 MCP Entry Points (S1–S11)

| # | Entry | Producer | Evidence Class | Active Runtime Path | Consumer | Reaches Model Context? | Risk Taxonomy | Current Evidence Level |
|---|-------|----------|---------------|---------------------|----------|----------------------|---------------|----------------------|
| S1 | `stock_analysis` | `stock_data.get_stock_full_data()` | Structured financial data (7 dims, known schema) | `mcp_server.py:546-631` | MCP caller → stock-analyst.md prompt → LLM | YES | stock domain: realtime, financials, fund_flow, valuation, management | STATICALLY CONFIRMED (QC informational only; admission enforcement path NOT PROVEN; prior "PRODUCTION OBSERVED" claim only covered direct function probe, not stock_analysis→admission→consumer chain) |
| S2 | `search(stock+code)` | Tavily/Brave → `enforce_search_results()` | External search (unstructured, claim-classified) | `mcp_server.py:678-790` with Gate | MCP caller → LLM prompt | YES | stock domain (4 domains classified) | LOCAL TEST PROVEN (38 tests, P0 fixture PASS) |
| S3 | `search(stock,no code)` | Tavily/Brave → empty AuthoritativeTrustState | External search (unstructured, unclassified in practice) | `mcp_server.py:678-790` NO_CODE path | MCP caller → LLM prompt | YES | stock domain (declared fail-closed, actual allow-all) | STATICALLY CONFIRMED |
| S4 | `search(news)` | `news_providers.unified_news_search_v2()` | External search (news-specific providers, own QC) | `mcp_server.py:731-756` | MCP caller → LLM prompt | YES | news domain (no Trust Gate taxonomy) | STATICALLY CONFIRMED |
| S5 | `search(macro)` | `unified_search(query, "macro")` | External search (general) | `mcp_server.py:758` | MCP caller → LLM prompt | YES | macro domain (no Trust Gate taxonomy) | STATICALLY CONFIRMED |
| S6 | `search(industry)` | `unified_search(query, "industry")` | External search (general) | `mcp_server.py:758` | MCP caller → LLM prompt | YES | industry domain (no Trust Gate taxonomy) | STATICALLY CONFIRMED |
| S7 | `search(extract)` | URL content fetch | External search (raw URL content) | `mcp_server.py:758` | MCP caller → LLM prompt | YES | any domain (unclassified content) | STATICALLY CONFIRMED |
| S8 | `macro_snapshot` | `macro_data.get_macro_data()` | Structured market indicators (macro: CPI/PMI/M2/LPR) | `mcp_server.py:638-648` | MCP caller → LLM prompt | YES | macro indicators (low stock-domain overlap) | STATICALLY CONFIRMED |
| S9 | `market_pulse` | 东方财富盘面数据 | Semi-structured market data (涨停池/强势股/异动) | `mcp_server.py:658-668` | MCP caller → LLM prompt | YES | market heat (contains individual stock references — NOT low risk) | STATICALLY CONFIRMED |
| S10 | `video_extract` | YouTube/B站 字幕提取 | Unstructured media transcript | `mcp_server.py:797` | MCP caller → LLM prompt | YES | any domain (raw transcript, no content classification) | STATICALLY CONFIRMED |
| S11 | `wind_query` | Wind/Tushare/JQ → `_enforce_trust_gate_or_block()` | Structured financial data (known schema, provider chain) | `mcp_server.py:93-156` | MCP caller → LLM prompt | YES | stock domain (G2 field integrity + G3 provenance, fail-closed) | LOCAL TEST PROVEN |

### 2.2 Non-MCP Entry Points (R1–R6)

| # | Entry | Producer | Evidence Class | Active Runtime Path | Consumer | Reaches Model Context? | Risk Taxonomy | Current Evidence Level |
|---|-------|----------|---------------|---------------------|----------|----------------------|---------------|----------------------|
| R1 | `ResearchSession` | `run_research_workflow()` → `_run_trust_gate()` | Structured financial data (gateway_* evidence, gated) | `research_runtime/workflow.py:116` | Session consumer → LLM (when active) | YES | stock domain | LOCAL TEST PROVEN (DONE, 16 events, 2 evidence; contract drifted) |
| R2 | IMA KB search | `search_in_investment_research()` | Institutional research (curated KB excerpts) | IMA MCP tools | MCP caller → LLM prompt | YES | research domain (no Trust Gate taxonomy) | STATICALLY CONFIRMED |
| R3 | IMA full-text | `fetch_media_content()` (endpoint unverified) | Institutional research (full document) | IMA MCP tools | MCP caller → LLM prompt | UNCONFIRMED | research domain | NOT PROVEN |
| R4 | Vera orchestration | NOT BUILT | N/A | N/A | N/A | N/A | N/A | NOT APPLICABLE |
| R5 | Brief engine | Brief assembly pipeline | Synthesized/derived (multi-source assembly) | Brief assembly (per `project_brief_engine_scheduler_fix_20260812`) | LLM prompt | UNCONFIRMED | multi-domain (derived from admitted evidence) | NOT VERIFIED |
| R6 | Direct LLM prompt | `prompts/stock-analyst.md` | Consumer context (NOT an evidence producer) | `prompts/stock-analyst.md:86-90` | LLM | YES (Layer 2 only) | stock domain (prompt-level constraints, no structural enforcement) | STATICALLY CONFIRMED |

**注：** R6 (Direct LLM prompt) 是 consumer context，不是 evidence producer。它不出产 evidence，但定义了什么 evidence 可以进入以及以什么形式进入。在 Contract 中它属于 admission policy 的 consumer 端约束。

---

## 3. Policy Family Induction

17 个 entry 不产生 17 套 Gate。归纳为 6 个 Policy Family：

| Policy Family | Entries | Evidence Class | Shared Characteristic |
|---------------|---------|---------------|----------------------|
| **P1: Structured Financial Data** | S1, S11, R1 | Known schema, provider chain, Trust Gate domains | Provider identity verifiable; field integrity (G2) + provenance (G3) applicable; Contract v0.2 structural strip rules apply |
| **P2: External Search & News** | S2, S3, S4, S5, S6, S7 | Unstructured web content, claim-classified | Provenance = search_external; per-claim domain classification; admission gated by structured baseline availability |
| **P3: Structured Market Indicators** | S8, S9 | Semi-structured market data, known providers | Known schema and providers; lower stock-domain overlap (S8) to individual stock references (S9); lighter assessment than P1 |
| **P4: Media Content** | S10 | Unstructured transcript, any domain possible | No schema; content classification required before admission; highest uncertainty |
| **P5: Institutional Research** | R2, R3 | Curated KB content, known source identity | Source identity known (IMA KB); content is curated but claims within are not schema-validated; different trust model from open web |
| **P6: Synthesis & Assembly** | R5, R6 | Derived/synthesized output; consumer context | Does not produce new evidence; consumes admitted evidence; synthesis must not introduce new factual claims; consumer context defines what evidence classes are admissible |

**R4 (Vera orchestration):** NOT APPLICABLE. Will be classified when built. Most likely a consumer of all 6 families, with its own orchestration-level admission policy.

---

## 4. Policy Family Definitions

### P1: Structured Financial Data Policy

**Entries:** S1 (stock_analysis), S11 (wind_query), R1 (ResearchSession)

**Evidence Class:** Structured financial data with known schema and provider chain.

**Required Assessment (EvidenceAssessment):**
| Check | Rule | Applies To |
|-------|------|-----------|
| Provider identity | Provider name + tier verified against Capability Registry | S1, S11, R1 |
| Field integrity (G2) | CRITICAL_DIMENSIONS present per action type | S11 (enforced), S1 (NOT enforced — GAP), R1 (enforced for gateway_* evidence) |
| Provenance chain (G3) | Provider chain traced; real/derived/fallback/mock classified | S1 (classified but informational), S11 (enforced), R1 (enforced) |
| Freshness | Timestamp validated; stale/cached flagged | S1 (realtime cache TTL), S11, R1 |
| Completeness | Per-dimension availability assessed | S1 (_qc_stock informational), S11, R1 |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Strip unavailable domains | `(unavailable, *)` → STRIP from context; blocked_use record |
| Strip absent domains | `(absent, *)` → STRIP; no search补全 |
| Cap derived | `(available, derived)` → ALLOW with provenance annotation; CAP claim level; block percentile/peer_comparison/target_price/valuation_judgment |
| Downgrade fallback | `(available, fallback)` → ALLOW with downgrade marker; not sole basis for strong conclusion |
| Allow real/verified_real | `(available, real/verified_real)` → ALLOW full |
| Reject mock | `(*, mock)` → REJECT |
| Max claim strength | Per Contract v0.2 Section 3.2 domain state → max allowed output table |

**Mandatory Choke Point:** Context assembly before LLM call. S11 already has fail-closed enforcement (`_enforce_trust_gate_or_block`). S1 does NOT — QC is informational. R1 has `_run_trust_gate` but contract drifted.

**Current Gap:** S1 (stock_analysis) structured output bypasses admission entirely. QC annotates but does not enforce. This is the largest single gap in P1.

---

### P2: External Search & News Policy

**Entries:** S2 (search stock+code), S3 (search stock no code), S4 (search news), S5 (search macro), S6 (search industry), S7 (search extract)

**Evidence Class:** Unstructured web content. Provenance = `search_external`.

**Required Assessment (EvidenceAssessment):**
| Check | Rule | Applies To |
|-------|------|-----------|
| Claim/domain classification | Extract factual claims from (title + content); classify into Trust Gate domains | S2 (IMPLEMENTED — 4 stock domains), S3 (classifier available but baseline state empty), S4–S7 (NOT IMPLEMENTED — no classifier) |
| Source identity | URL domain recorded; not a substitute for provider credential | All |
| Content risk flag | Financial claims detected? Stock mentions? Individual security references? | S4–S7 (NOT IMPLEMENTED) |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Per-claim domain BLOCK | If claim matches domain where structured baseline = unavailable/absent → BLOCK entire result (prevents partial evidence leakage) |
| Per-claim domain ALLOW | If claim matches domain where structured baseline = available/derived → ALLOW with provenance = search_external |
| Unclassified → ALLOW with marker | No domain match → ALLOW, provenance = search_external/unclassified |
| No baseline → FAIL CLOSED for protected domains | If AuthoritativeTrustState unavailable, protected-domain claims BLOCKED; unclassified ALLOW |
| Max claim strength | search_external evidence CANNOT be sole basis for: valuation judgment, trading signal, management assessment |

**Mandatory Choke Point:** After search result retrieval, before context assembly. S2 has this (`enforce_search_results` in `mcp_server.py:714`). S3–S7 do NOT.

**Per-Entry Gap:**
| Entry | Current State | Gap |
|-------|--------------|-----|
| S2 | LOCAL TEST PROVEN | Extend domain classifier coverage (currently 4 stock domains) |
| S3 | STATICALLY CONFIRMED (allow-all in practice) | Require code OR build structured baseline from available data |
| S4 | STATICALLY CONFIRMED (no Gate) | Define news domain taxonomy; build news classifier; wire to admission |
| S5 | STATICALLY CONFIRMED (no Gate) | Define macro domain taxonomy; build classifier |
| S6 | STATICALLY CONFIRMED (no Gate) | Define industry domain taxonomy; build classifier |
| S7 | STATICALLY CONFIRMED (no Gate) | Content classification on raw URL text; highest uncertainty |

**Policy约束：** S4–S7 不可直接复用 stock 四域 classifier。News/macro/industry/extract 各自需要独立的 domain taxonomy + classifier，或统一的 content risk flag 机制。Policy 定义必须在 classifier 实现之前。

---

### P3: Structured Market Indicators Policy

**Entries:** S8 (macro_snapshot), S9 (market_pulse)

**Evidence Class:** Semi-structured market data from known providers.

**Required Assessment (EvidenceAssessment):**
| Check | Rule | Applies To |
|-------|------|-----------|
| Provider identity | AkShare/东方财富 — known provider, known endpoint | S8, S9 |
| Schema validation | Macro indicators (CPI/PMI/M2/LPR) have known fields; market_pulse has known structure (涨停池/强势股/异动) | S8, S9 |
| Freshness | Data timestamp from provider | S8, S9 |
| Individual security reference detection | market_pulse contains individual stock codes/names — must be classified | S9 (NOT IMPLEMENTED) |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Macro indicators → ALLOW | CPI/PMI/M2/LPR are aggregate indicators; no individual security claim risk |
| Market pulse → INDIVIDUAL STOCK REFERENCES | 涨停池/强势股 contain individual securities; if those securities have structured baseline, admission must check domain availability |
| Max claim strength | Macro: can inform sector/macro view. Market pulse: can describe market heat; CANNOT substitute for individual stock analysis |

**Mandatory Choke Point:** Context assembly. Currently none — both go through `_wrap_response()` without admission check.

**Current Gap:** S8 is genuinely low risk for stock Trust Gate domains (macro indicators don't make claims about individual securities). S9 is NOT low risk — it contains individual stock references (涨停池) that can trigger stock-domain claims. Both lack admission enforcement.

---

### P4: Media Content Policy

**Entries:** S10 (video_extract)

**Evidence Class:** Unstructured media transcript. Any domain claim possible.

**Required Assessment (EvidenceAssessment):**
| Check | Rule |
|-------|------|
| Content classification | Run transcript through domain classifier to detect stock-domain claims |
| Source identity | Platform (YouTube/B站) + video ID recorded |
| Risk flag | Does transcript contain financial claims? Stock mentions? Individual security references? |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Per-domain BLOCK | Same as P2: if transcript contains claims matching unavailable/absent domains → BLOCK those segments |
| Unclassified → ALLOW with marker | Narrative content without financial claims → ALLOW |
| Max claim strength | Transcript content is lowest-trust provenance; CANNOT be sole basis for any financial claim |

**Mandatory Choke Point:** After transcript extraction, before context assembly.

**Current Gap:** No content classification. No admission enforcement. Transcript text enters context unexamined.

---

### P5: Institutional Research Policy

**Entries:** R2 (IMA KB search), R3 (IMA full-text)

**Evidence Class:** Curated institutional research content. Source identity known (IMA KB), content curated but claims within are not schema-validated.

**Required Assessment (EvidenceAssessment):**
| Check | Rule |
|-------|------|
| Source identity | IMA KB ID + media_id; known institutional source |
| Content classification | Extract claims; classify into Trust Gate domains (stock domains + research-specific) |
| Freshness | Publication date from KB metadata |
| Provenance | `institutional_research` (distinct from `search_external` — source is curated, not open web) |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Institutional source → higher baseline trust | IMA KB content has known provenance; ALLOW with source attribution |
| Per-domain BLOCK still applies | If KB excerpt contains capital_flow claim AND capital_flow = unavailable → BLOCK that claim |
| Research context vs trading context | Same KB content: ALLOW for research session, RESTRICT for real-time trading context |
| Max claim strength | Can inform research view; CANNOT substitute for structured data in trading decisions |

**Mandatory Choke Point:** After IMA response, before context assembly.

**Current Gap:** No admission enforcement. IMA content enters context directly. Full-text endpoint capability unverified.

---

### P6: Synthesis & Assembly Policy

**Entries:** R5 (Brief engine), R6 (Direct LLM prompt)

**Evidence Class:** R5 produces synthesized content from admitted evidence. R6 is a consumer context template.

**Required Assessment (EvidenceAssessment):**
| Check | Rule | Applies To |
|-------|------|-----------|
| Constituent evidence trace | Every factual claim in synthesis must trace to an admitted EvidenceRecord | R5 |
| No new factual claims | Synthesis can reorganize/contextualize but CANNOT introduce new numbers, names, or domain claims not present in source evidence | R5 |
| Prompt template audit | Prompt sections that request specific domains must map to required evidence classes | R6 |

**Required Admission (ContextAdmissionDecision):**
| Rule | Detail |
|------|--------|
| Consumer context defines admissible evidence classes | stock-analyst.md prompt = stock domain consumer → requires P1 + P2 evidence; macro analysis = requires P3 evidence |
| Synthesis output = CuratedEvidenceBundle | Brief engine output IS a CuratedEvidenceBundle — must carry bundle_id, admitted_evidence_ids, claim_to_evidence_links, bundle_hash |
| Prompt template as admission spec | Prompt sections that request unavailable domains → template must be pre-stripped or replaced with placeholder BEFORE evidence assembly |

**Mandatory Choke Point:** Brief assembly pipeline (R5); prompt template construction (R6).

**Current Gap:** R5 NOT VERIFIED. R6 is prompt-only (Layer 2) — no structural enforcement that prompt sections match available evidence classes.

---

## 5. Entry → Policy Family Mapping

```
S1  stock_analysis         → P1  Structured Financial Data
S11 wind_query             → P1  Structured Financial Data
R1  ResearchSession        → P1  Structured Financial Data

S2  search(stock+code)     → P2  External Search & News
S3  search(stock,no code)  → P2  External Search & News
S4  search(news)           → P2  External Search & News
S5  search(macro)          → P2  External Search & News
S6  search(industry)       → P2  External Search & News
S7  search(extract)        → P2  External Search & News

S8  macro_snapshot         → P3  Structured Market Indicators
S9  market_pulse           → P3  Structured Market Indicators

S10 video_extract          → P4  Media Content

R2  IMA KB search          → P5  Institutional Research
R3  IMA full-text          → P5  Institutional Research

R5  Brief engine           → P6  Synthesis & Assembly
R6  Direct LLM prompt      → P6  Synthesis & Assembly

R4  Vera orchestration     → NOT APPLICABLE (future: consumer of P1–P6)
```

---

## 6. Mandatory Choke Point Topology

所有 6 个 Policy Family 共享同一个 admission topology：

```
Evidence Producer (15 evidence-producing entries；R6 = consumer-policy surface 非 producer；R4 = NOT APPLICABLE)
    │
    ↓
EvidenceRecord (immutable, hash-identified)
    │
    ↓
EvidenceAssessment (per policy family)
    │
    ↓
ContextAdmissionDecision (per consumer + purpose)
    │
    ↓
CuratedEvidenceBundle (admitted only)
    │
    ↓
Model Context (LLM / Vera / Presenter)
```

**Choke Point = ContextAdmissionDecision layer.** 每一份要进入 model context 的 evidence 必须经过此层。没有绕过路径。

**当前状态：**
- P1: S11 enforced (LOCAL TEST PROVEN), S1 NOT enforced, R1 contract drifted
- P2: S2 enforced (LOCAL TEST PROVEN), S3–S7 NOT enforced
- P3: S8, S9 NOT enforced
- P4: S10 NOT enforced
- P5: R2, R3 NOT enforced
- P6: R5 NOT VERIFIED, R6 prompt-only (Layer 2)

**实现约束：**
- Choke point 是 single logical authority；物理部署 TBD（in-process hook / sidecar / service）
- 不是 optional library — 调用方不能选择是否过 admission
- 每个 producer → consumer 路径必须携带 admission receipt
- `_wrap_response()` 不是合适的 choke point（formatting 函数，可被绕过）

---

## 7. Gap Summary

| # | Gap | Severity | Policy Family | Entries Affected |
|---|-----|----------|---------------|-----------------|
| G1 | stock_analysis structured output no admission | **BLOCKING** — largest single gap | P1 | S1 |
| G2 | search(news/macro/industry/extract) no admission | **BLOCKING** | P2 | S4, S5, S6, S7 |
| G3 | search(stock,no code) allow-all in practice | **HIGH** | P2 | S3 |
| G4 | market_pulse individual stock references no admission | **HIGH** | P3 | S9 |
| G5 | video_extract no content classification | **HIGH** | P4 | S10 |
| G6 | IMA content no admission | **HIGH** | P5 | R2, R3 |
| G7 | Brief engine not verified | **MEDIUM** | P6 | R5 |
| G8 | Direct prompt no structural enforcement | **MEDIUM** | P6 | R6 |
| G9 | ResearchSession contract drifted | **MEDIUM** | P1 | R1 |
| G10 | No per-content-type taxonomy for S4–S7, S10, R2–R3 | **BLOCKING** — policy must precede code | P2, P4, P5 | S4–S7, S10, R2–R3 |

**G10 是最高优先级：** P2/P4/P5 的 domain taxonomy + classifier 必须先定义，才能写 admission code。不可把 stock 四域规则泛化到 news/macro/video/IMA。

---

## 8. Per-Family Unclassified Default Strategy

**Clarification #2:** "Unclassified → ALLOW with marker" 不是通用默认。每个 Policy Family 必须按 consumer purpose 区分未分类默认策略。

| Policy Family | Consumer: Research | Consumer: Trading/Stock Action |
|---------------|-------------------|-------------------------------|
| **P1 Structured Financial** | N/A — structured data is always classified by domain | N/A — structured data is always classified by domain |
| **P2 External Search** | Unclassified → ALLOW with `unclassified/search_external` marker; blocked_use record | Unclassified → **FAIL CLOSED** if content contains financial keywords OR stock mentions; ALLOW with marker only if no financial signal detected |
| **P3 Market Indicators** | Unclassified field → ALLOW with `unclassified/market_indicator` marker | S9 individual stock reference → classify against structured baseline; unclassified reference → **FAIL CLOSED** |
| **P4 Media Content** | Unclassified → ALLOW with `unclassified/transcript` marker | Unclassified → **FAIL CLOSED** if any financial keyword detected; ALLOW only after content classification PASS |
| **P5 Institutional Research** | Unclassified → ALLOW with `institutional_research/unclassified` marker + source attribution | Unclassified claim → **FAIL CLOSED**; institutional source does not waive classification requirement for trading context |
| **P6 Synthesis & Assembly** | Unclassified constituent → REJECT synthesis; cannot trace to admitted evidence | Unclassified constituent → REJECT synthesis; synthesis with untraced claim → BLOCK |

**原则:** Research consumer 可以接受 marker + provenance record（事后可审计）。Trading/stock action consumer 对未分类内容必须 fail closed — 缺少可判定的 classification 本身即是风险信号。

**对 P2 原先 "Unclassified → ALLOW with marker" 的修正:** 该规则仅对 research consumer 成立。对 trading/stock consumer，分类器漏检 financial claim 不构成放行理由；在 trading context 下，无法判定 = 不应进入。

---

## 9. EvidenceRecord Contract

**Clarification #3:** 冻结 EvidenceRecord 的 identity、canonicalization、raw reference access 与 retention。

### 9.1 Identity

> **AMENDED by v0.2 M9 (2026-08-12)：** 以下内容已被 `VERA_ARCHITECTURE_REVIEW_v0.2.md` Adjudication 1 修订取代。

```
EvidenceRecord.id = SHA3-256( JCS_canonical({
    producer_id: ...,
    evidence_class: ...,
    collected_at: ...,
    raw_hash: ...,
    schema_version: ...
}) )
EvidenceRecord.content_hash = SHA3-256(raw_payload_bytes)
```

- `id` 是 **capture identity**：相同 raw payload 在不同采集时间 → 不同 id（代表不同采集事件）
- `content_hash` 是**纯 content-addressed**：独立于采集时间，用于跨采集去重
- 所有 hash 输入必须是 **JCS canonical object**（RFC 8785），禁止字符串拼接
- `raw_hash` = SHA3-256(raw_payload_bytes)，在 normalization 之前计算
- `schema_version` = EvidenceRecord schema 版本号，用于 migration

### 9.2 Canonicalization

写入 EvidenceRecord 之前必须 canonicalize：

| Step | Rule |
|------|------|
| 1. Timestamp normalize | 所有 timestamp 转为 UTC ISO 8601 |
| 2. Field order | JSON keys 按字典序排序（RFC 8785 JCS） |
| 3. Numeric normalize | 浮点数保留原始精度，不截断不四舍五入 |
| 4. Null vs absent | `null` 和 field absent 不可互换；保留原始语义 |
| 5. Encoding | UTF-8，normalization form C (NFC) |

### 9.3 Raw Reference Access

- EvidenceRecord **不存储** raw payload copy
- EvidenceRecord 存储 `raw_hash` + `raw_reference`（controlled URI/path，非直接文件系统路径）
- Raw payload 的读权限独立于 EvidenceRecord 的读权限
- Consumer 默认只访问 normalized + assessed 内容；raw reference access 需要独立授权（research audit / incident review）
- 目的：防止 sensitive raw data proliferation，同时保留 audit trail

### 9.4 Retention

| Tier | Content | Minimum Retention | Rationale |
|------|---------|-------------------|-----------|
| EvidenceRecord | id, producer_id, evidence_class, collected_at, raw_hash, raw_reference, schema_version | 90 days | Audit baseline |
| EvidenceAssessment | assessment_id, record_id, dimensions, freshness, classification | 90 days | Tied to record lifecycle |
| ContextAdmissionDecision | decision_id, record_id, consumer, purpose, verdict, policy_version, receipt | 90 days | Tied to record lifecycle |
| CuratedEvidenceBundle | bundle_id, admitted_record_ids, bundle_hash | 30 days (cache); 90 days (audit) | Bundle is consumer-specific; shorter cache TTL |
| Raw payload | raw bytes at raw_reference | Per provider agreement; minimum 30 days | Governed by provider ToS, not this contract |

---

## 10. Admission Receipt Minimum Fields

**Clarification #4:** 每个 admission decision 必须产生可验证 receipt。Receipt 不依赖 trust — 任何 consumer 可独立验证。

### 10.1 Required Fields

> **AMENDED by v0.2 M10/M11 (2026-08-12)：** receipt 拆为 DecisionReceipt（本节）与 BundleManifest；`max_claim_strength` 枚举扩展为 6 值；`bundle_hash` 从 DecisionReceipt 移除。以下 JSON 为修订后版本。
>
> **AMENDED by I0 M20/M21 (2026-08-13)：** ACR-1 — `receipt_id` = `SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})`（对齐 M9 全局 JCS 规则），receipt 增 `receipt_schema_version`；ACR-2 — receipt 增 `assessment_id` + `assessment_result_hash`（freeze clause 四元组可仅凭 receipt 验证）。

```json
{
  "receipt_id": "SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})",
  "receipt_schema_version": "<e.g. '0.1'>",
  "decision_id": "<unique per admission decision>",
  "assessment_id": "<EvidenceAssessment.assessment_id, = L3.assessment_ref>",
  "assessment_result_hash": "<EvidenceAssessment.assessment_result_hash>",
  "producer_id": "<entry identifier, e.g. 'S2.search.stock' >",
  "evidence_record_id": "<EvidenceRecord.id>",
  "consumer": "<e.g. 'stock-analyst.md', 'Vera.ResearchSession'>",
  "purpose": "research | trading_signal | portfolio_review | market_monitor | brief_assembly",
  "policy_family": "P1 | P2 | P3 | P4 | P5 | P6",
  "policy_version": "<e.g. 'v0.1'>",
  "verdict": "ALLOW | ALLOW_WITH_MARKER | DOWNGRADE | BLOCK",
  "allowed_use": ["<e.g. 'fundamental_overview', 'market_context'>"],
  "blocked_use": ["<e.g. 'valuation_judgment', 'trading_signal'>"],
  "max_claim_strength": "OBSERVED_FACT | DERIVED_INDICATOR | ATTRIBUTED_CLAIM | ANALYST_OPINION | INFORMATIONAL | NO_CLAIM",
  "assessment_dimensions": {
    "provider_identity": "VERIFIED | UNVERIFIED | NOT_APPLICABLE",
    "field_integrity": "PASS | PARTIAL | FAIL | NOT_APPLICABLE",
    "provenance": "real | derived | fallback | external | institutional | transcript",
    "freshness": "ISO8601 timestamp or STALE/UNKNOWN",
    "classification": "classified:<domain_list> | unclassified | not_applicable"
  },
  "evidence_hash": "<EvidenceRecord.raw_hash>",
  "timestamp": "<ISO8601 UTC>",
  "audit_trail": {
    "assessor_id": "<component that ran assessment>",
    "admission_enforcer_id": "<component that ran admission>",
    "bypass_detected": false
  }
}
```

### 10.1b BundleManifest（与 DecisionReceipt 分离）

**AMENDED by v0.2 M11：** bundle 层级的清单在 **bundle finalization 之后**生成 — 单条 decision 产生时 bundle 尚未成型，无法确定最终 `bundle_hash`。

**AMENDED by I0 M23 (2026-08-13)：** `bundle_hash` 改为 manifest 无自引用 canonical representation 的 hash（绑定 schema version / consumer / purpose / 有序 record IDs / decision IDs / curated-content hash）；`curated_content` 为有序 fragment 列表，逐项携带 `evidence_record_id` + `decision_id`（逐项 provenance 可验证）。bundle identity = content-addressed：`bundle_id = bundle_hash`（I0 OPC #4 FROZEN 2026-08-13）；`generated_at` 保持审计元数据，不进入 identity。

```json
{
  "bundle_id": "<= bundle_hash (content-addressed identity; I0 OPC #4 FROZEN 2026-08-13)>",
  "bundle_schema_version": "<e.g. '0.1'>",
  "admitted_record_ids": ["<EvidenceRecord.id...>"],
  "member_decision_ids": ["<DecisionReceipt.decision_id...>"],
  "curated_content_hash": "<SHA3-256 of JCS(curated_content)>",
  "generated_at": "<ISO8601 UTC, bundle finalization time; 不进 bundle_hash 输入>",
  "consumer": "<must match all member DecisionReceipts.consumer>",
  "purpose": "<must match all member DecisionReceipts.purpose>",
  "bundle_hash": "<SHA3-256 of JCS{bundle_schema_version, consumer, purpose, admitted_record_ids, member_decision_ids, curated_content_hash}>"
}
```

### 10.2 Non-Bypassable Verification

任一 consumer 收到 CuratedEvidenceBundle 时，必须验证：

1. `receipt_id` 存在且 hash 匹配
2. `evidence_record_id` 对应已知 EvidenceRecord
3. `consumer` + `purpose` 匹配当前 consumer context
4. `verdict` ∈ {ALLOW, ALLOW_WITH_MARKER, DOWNGRADE}（BLOCK 的不会到达 consumer）
5. freshness：在 **consumer admission 时刻**，以 `context_time − data_as_of`（receipt.assessment_dimensions.freshness 的 timestamp 语义）对 consumer purpose 的 freshness policy 求值（max age 按 purpose 定义，如 `trading_signal` 短、`research` 长、`brief_assembly` 允许跨会话）— **AMENDED by v0.2 M11：禁止"必须在当前 session 时间窗口内"**，那会破坏可重放的历史 bundle、异步 brief 和跨会话 research — **AMENDED by I0 M22：`receipt.timestamp` 仅审计用途，不参与 freshness 判定**（一个签发时新鲜的 bundle，消费时仍可能已过期）— **AMENDED by I0 M24（ACR-3 CLOSED，2026-08-13）：** max_age 按 `(purpose, temporal_semantics)` 二维求值（temporal_semantics 仅影响 freshness 评价，**不进入 admission identity** — 四元组保持）；86400s 是 **duration threshold**，非"上一交易日数据天然有效"的业务规则
6. BundleManifest 存在且 `member_decision_ids` 覆盖 bundle 内全部 evidence；`admitted_record_ids` 覆盖全部 record；`bundle_hash` 与 `curated_content_hash` 两级匹配 — **AMENDED by v0.2 M11：bundle 级验证移至 BundleManifest；AMENDED by I0 M23：两级 hash + 无自引用 canonical rep**
7. `bypass_detected` = false
8. assessment 绑定链：`receipt.assessment_id` = `decision.assessment_ref`；`receipt.evidence_record_id` = `assessment.record_id`；`receipt.assessment_result_hash` = `assessment.assessment_result_hash`；`assessment_dimensions` 快照 = L2 值 — **ADDED by I0 M21 (ACR-2)**

**验证失败 → consumer 必须拒绝 bundle。** 没有"soft verify" — receipt check 是 mandatory enforcement point。

### 10.3 Receipt 与 EvidenceRecord 的关系

```
EvidenceRecord (immutable, content-addressed)
    │
    ├── EvidenceAssessment (reusable across consumers)
    │
    ├── ContextAdmissionDecision (per consumer + purpose)
    │       │
    │       └── AdmissionReceipt (this section)
    │
    └── CuratedEvidenceBundle (per consumer, carries receipt)
```

同一 EvidenceRecord 对不同 consumer/purpose 产生不同 receipt。Receipt 记录的是 admission decision，不是 evidence fact。

---

## 11. States

```
Current-State Rebaseline:      FROZEN / PARTIALLY VALID
Production Context Coverage:   NOT YET PROVEN (0/15 PRODUCTION OBSERVED; 15 evidence-producing
                               entries; R6 consumer-policy surface + R4 NA excluded, M14)
This Contract:                 ACCEPTED DESIGN BASELINE (v0.1 + 4 clarifications + M9/M10/M11
                               + I0 M20–M23 amendments; 2026-08-13)
  Clarification 1: S1 evidence level corrected — admission path STATICALLY CONFIRMED
  Clarification 2: Per-family unclassified default by consumer purpose (Section 8)
  Clarification 3: EvidenceRecord contract frozen (Section 9)
  Clarification 4: Admission receipt minimum fields frozen (Section 10)
  AMENDED by v0.2 M9/M10/M11 (2026-08-12): Sections 9.1 / 10.1 / 10.2 superseded —
     capture identity + content_hash; 6-value claim strength; DecisionReceipt/BundleManifest split
  AMENDED by I0 M20–M24 (2026-08-13): Sections 10.1 / 10.1b / 10.2 amended —
     ACR-1 receipt_id JCS + receipt_schema_version; ACR-2 assessment_id + result hash + V8;
     freshness = context_time − data_as_of (timestamp audit-only); max_age = f(purpose, temporal_semantics) (M24);
     bundle_hash = manifest 无自引用 canonical rep + 两级 hash
Review Verdict:                PARTIALLY PROVEN → accepted; v0.2 FINAL FREEZE: PASS
Freeze Clause:                 valid receipt ≠ evidence globally trusted — authorization is
                               consumer + purpose + assessment_id + policy_version 共同决定
Next:                          Vera Target Architecture v1
Implementation:                NOT AUTHORIZED
Coverage Completion:           NOT CLAIMABLE until I2b complete
```

---

## Appendix A: Policy Family Quick Reference

| Family | Entries | Assessment | Admission | Choke Point Status |
|--------|---------|-----------|-----------|-------------------|
| P1 Structured Financial | S1, S11, R1 | G2+G3+Freshness+Completeness | Contract v0.2 strip rules + derived cap + fallback downgrade | S11: enforced; S1: GAP; R1: drifted |
| P2 External Search | S2–S7 | Claim classification + source URL | Per-domain BLOCK/ALLOW; search_external provenance; no- baseline → fail-closed | S2: enforced; S3–S7: GAP |
| P3 Market Indicators | S8, S9 | Provider + schema + stock reference detection | Macro: ALLOW; Market pulse: individual stock reference check | All: GAP |
| P4 Media Content | S10 | Content classification + source platform | Per-domain BLOCK; lowest-trust provenance | All: GAP |
| P5 Institutional Research | R2, R3 | Source identity + claim classification + freshness | Institutional provenance; per-domain BLOCK still applies; research vs trading context | All: GAP |
| P6 Synthesis & Assembly | R5, R6 | Constituent evidence trace; no new claims | Consumer context defines admissible classes; synthesis = CuratedEvidenceBundle | R5: NOT VERIFIED; R6: Layer 2 only |
