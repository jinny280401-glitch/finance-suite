# I0 — Schema Contract v0.1（Spine 对象 Schema Specification）

**卡：** Implementation Plan — I0
**状态：** FROZEN / OPEN PARAMETERS CLOSED (2026-08-13)（Design Freeze；非 PROVEN）
**Mode：** Schema Specification Only / No Production Types / No Wiring
**日期：** 2026-08-13
**输入（全部 FROZEN）：**
- `VERA_TARGET_ARCHITECTURE_v1.md` — FROZEN (M14–M18 amended)
- `VERA_ARCHITECTURE_REVIEW_v0.2.md` — FROZEN (FINAL FREEZE: PASS)
- `CONTEXT_ADMISSION_COVERAGE_CONTRACT_v0.1.md` — ACCEPTED DESIGN BASELINE (+ M9/M10/M11)
- `IMPLEMENTATION_PLAN_GAP_MAP_v0.1.md` — FROZEN / I0 INPUT
- `CURRENT_STATE_ARCHITECTURE_REBASELINE_v0.1.md` — FROZEN (REFERENCE)

---

## I0 边界（用户裁决 2026-08-13）

I0 只回答：**Spine 上各对象"是什么"，以及它们之间必须满足什么机器可验证契约。**

**允许：** schema、字段、enum、ID/hash 规则、lattice、引用完整性、schema-level invariants；schema fixture/validator（仅验证 spec，不接生产）。

**禁止：** production dataclass/Pydantic、数据库表、API、middleware、现有 `_qc` 接线、migration、deployment、改 15 个入口。尤其禁止"为了验证 schema，顺便在 stock_analysis 接一下"。

**出口证据（四类）：** Schema frozen + normative examples + invalid fixtures + machine validation tests。

**晋级状态名：** `I0 SCHEMA CONTRACT PROVEN` — 不得写成 "Evidence Layer implemented"，不得开始计算 1/15 production coverage。**即便四类证据齐备，最多证明 "spec + fixture validator"，仍不等同于 Evidence Layer 已实现或 production enforcement 已实现（C 裁决 2026-08-13）。**

**ACR 规则：** 若 I0 发现冻结架构本身存在矛盾，必须触发 **Architecture Change Request**（ACR Register，§9），不得在 implementation spec 里偷偷修正。非矛盾的歧义以 OBS 记录并给出显式归一化（§10）。

---

## 修订记录（C Review 2026-08-13）

| # | 修订 | 内容 | 对应 C 结论 |
|---|------|------|-----------|
| CR1 | ACR-1 裁决 | `receipt_id = SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})`；DecisionReceipt 增 `receipt_schema_version`（必填），避免 receipt 结构演进产生身份歧义 | #1 PROVEN → 采纳 |
| CR2 | ACR-2 裁决 | DecisionReceipt 增 `assessment_id`（必填）+ `assessment_result_hash`（必填）；V8 校验 assessment ID / record ID / result hash 与 L3 `assessment_ref` 一致 | #2 NOT PROVEN → 采纳方案 (a) |
| CR3 | Freshness 基准修正 | V5 改为 consumer admission 时以 `data_as_of` 对 purpose policy 求值；receipt.timestamp 仅审计；L2 `freshness` 时间语义冻结为 data-as-of | #3 NOT PROVEN → 采纳 |
| CR4 | Bundle 完整性闭合 | `bundle_hash` = manifest 无自引用 canonical representation 的 hash（绑定 consumer/purpose/有序 member IDs/record IDs/curated-content hash/schema version）；L4-I15 升级为逐项 provenance 对应 | #4 NOT PROVEN → 采纳 |
| CR5 | 机器验证语义 | 状态改为 `DRAFT / schema validation pending`；验证器声明**受限 JCS profile** 并拒绝未覆盖 edge cases；classification domain list canonical order 规则 | #5 PARTIAL → 采纳 |
| CR6 | media_transcript ceiling 限定 | trading ceiling = INF **仅允许无 financial signal 的上下文存在**；任何 financial signal 仍由 P4 默认策略 BLOCK | 审查确认项 → 采纳 |

---

## Freeze 裁决（用户，2026-08-13）

**I0_SCHEMA_CONTRACT_v0.1 — FREEZE: PASS WITH OPEN PARAMETERS**

- 冻结类型：**Schema Design Freeze**，不是 I0 SCHEMA CONTRACT PROVEN
- CR1–CR6 已消除阻塞 schema freeze 的问题：receipt_id 确定性公式 / receipt 回指 L2（assessment_id + assessment_result_hash）/ freshness 与 receipt 时间剥离（context_time − data_as_of）/ manifest 去自引用 + fragment 逐项 provenance / JCS 能力如实收窄 / media_transcript financial-signal 限定
- F22–F26 确认；**F17 必须 PASS** 是硬约束：证明已区分"审计时间旧"与"data_as_of 仍满足 purpose freshness"
- **下一步序列：** Schema Design Freeze → **Open Parameter Closure** → Materialize F1–F26 → Validator → I0 SCHEMA CONTRACT PROVEN
- **Open Parameter Closure 四类（仍属 schema spec 层，非 production implementation）：** max_age 数值 / 受控词表与 registry / decision_id 公式 / bundle_id 公式。关闭前不得 materialize fixtures — 否则暂定参数被固化成"事实标准"
- **ACR 传播：** 先 freeze I0，再传播回 Coverage Contract — 已执行：M20（ACR-1）/ M21（ACR-2）/ M22（CR3，§10.2 #5）/ M23（CR4，§10.1b）/ M24（ACR-3，§10.2 #5）
- **无需重开架构评审**；除非参数关闭过程中发现改变 CR1–CR6 语义或 Target Architecture 不变量的情况 → 触发 ACR
- **参数裁决（2026-08-13）：** #2/#3/#4 FROZEN（已回写 §1.3.2/§4.1/§6.1）；#1 经 **ACR-3 CLOSED / ACCEPTED（2026-08-13）**，6×5 数值矩阵已冻结（§1.8）。Open Parameters 全部关闭；Task #9 解锁。**ACR-3 CLOSED ≠ I0 PROVEN** — 仅意味着设计参数全部关闭，schema 自洽性仍需 fixture/validator 证明

---

## 0. Object Inventory

| 对象 | 层 | 身份字段 | 冻结来源 |
|------|-----|---------|---------|
| **EvidenceRecord** | L1 | `id` (capture identity) + `content_hash` + `normalized_content_hash` (M17) | v0.2 A1 / Coverage §9 (M9) |
| **EvidenceAssessment** | L2 | `assessment_id` + `assessment_result_hash` (M18) | v0.2 A1 (R1) |
| **ContextAdmissionDecision** | L3 | `decision_id` | v0.2 A1 |
| **DecisionReceipt** | L4 | `receipt_id` | Coverage §10.1 (M11) + CR1/CR2 |
| **BundleManifest** | L4 | `bundle_id` + `bundle_hash` | Coverage §10.1b (M11) + CR4 |
| **CuratedEvidenceBundle** | L4 | `bundle_id` | v0.2 A1 (R4) + CR4 |

**显式排除：**
- **R6 Direct LLM prompt（consumer-policy surface）** — 非 evidence 对象，不产生 L1/L2/L3。其契约 = §8 验证清单 + consumer context 定义；schema 延后至 I4 prompt audit / I6 Capability Registry。
- **Capability Registry** — I6 范畴（Target Architecture §6 排除项 5）。

---

## 1. 共享原语

### 1.1 Hash 规则（M9 全局）

- 所有 hash 输入必须是 **JCS canonical object**（RFC 8785 JSON Canonicalization Scheme），**禁止字符串拼接**。
- Hash 函数：**SHA3-256**，输出 64 位小写 hex。
- 唯一冻结例外：`content_hash = SHA3-256(raw_payload_bytes)` — 输入是 raw bytes 而非 JSON object（v0.2 A1 公式本身如此）。

### 1.2 JCS 与记录级 canonicalization 分工（M17）

- **JCS** 仅定义 canonical serialization（key 字典序、UTF-8、数字表示），用于 hash 输入。
- **记录级规则**（Coverage §9.2，独立于 JCS）：timestamp 一律 UTC ISO 8601；`null` 与 field absent 不可互换；浮点保留原始精度；编码 UTF-8 NFC。这些是记录内容规则，不是 JCS 的一部分。

### 1.3 枚举总表

| 枚举 | 值 | 冻结来源 |
|------|-----|---------|
| `content_type` | `structured_financial` / `search_result` / `news_article` / `macro_indicator` / `market_pulse` / `media_transcript` / `institutional_research_full_text` / `institutional_research_excerpt` / `synthesis_brief` / `prompt_template` | v0.2 A3 D1 |
| `source_type` | `internal_provider` / `external_search` / `institutional_kb` / `media_platform` / `derived` | v0.2 A3 D2 |
| `retrieval_mode` | `direct_api` / `search_fetch` / `kb_lookup` / `url_extract` / `media_extract` / `pipeline_assembly` | v0.2 A3 D3 |
| `temporal_semantics` | `realtime` / `eod` / `historical` / `static_reference` / `periodic_indicator` / `rolling` | v0.2 A3 D4 |
| `provenance` | `real` / `derived` / `fallback` / `external` / `institutional` / `transcript` | v0.2 A1 L2 |
| `provider_identity` | `VERIFIED` / `UNVERIFIED` / `NOT_APPLICABLE` | v0.2 A1 + §10.1 镜像（OBS-6） |
| `field_integrity` | `PASS` / `PARTIAL` / `FAIL` / `NOT_APPLICABLE` | 同上 |
| `freshness` | ISO 8601 timestamp（= **data_as_of**，CR3）/ `STALE` / `UNKNOWN` | v0.2 A1 L2 + CR3 |
| `classification` | `classified:<sorted domain_list>` / `unclassified` / `not_applicable`；domain_list ∈ 11 值 closed list（§1.3.2） | v0.2 A1 L2 + CR5 + OPC #2 |
| `verdict` | `ALLOW` / `ALLOW_WITH_MARKER` / `DOWNGRADE` / `BLOCK` | v0.2 A1 L3 |
| `purpose` | `research` / `trading_signal` / `portfolio_review` / `market_monitor` / `brief_assembly` | Coverage §10.1 |
| `producer_id` | 15-entry 集合（S1–S11, R1, R2, R3, R5；M14） | Target Arch §5 |
| `policy_family` | `P1`–`P6` | Coverage §3 |
| `evidence_class` | 6 个粗粒度值（见 1.3.1 映射） | Coverage §2 + A3 D1（OBS-7） |
| `consumer` | 不透明标识符；registry baseline = {stock-analyst.md, Vera.ResearchSession, brief-engine}（§1.3.2） | §10.1 例 + OPC #2 |
| `schema_version` / `policy_version` / `normalization_version` / `receipt_schema_version` / `bundle_schema_version` | 字符串版本号；policy_version registry = {v0.1}（§1.3.2）；其余随各对象 schema 演进 | §9.1 / M17 / CR1 / CR4 + OPC #2 |

**CR5 — classification canonical order：** `classified:<domain_list>` 的 domain 必须按字典序排序、逗号分隔，作为 `assessment_result_hash` 的确定性前提。domain 词表本身未封闭（open parameter，§14）。

#### 1.3.1 `evidence_class` ↔ `content_type` 映射（OBS-7 归一化）

L1 的 `id` hash 输入包含 `evidence_class`（A1 冻结），L1 另存 G10 `content_type`（§3.4 冻结）。两者不重复：`evidence_class` 是 §2 的粗粒度类，`content_type` 是 D1 的细粒度类。映射如下（全部由冻结表推导）：

| evidence_class | content_type（覆盖入口） |
|----------------|------------------------|
| `structured_financial` | `structured_financial`（S1, S11, R1） |
| `external_search` | `search_result`（S2, S3, S5, S6, S7）/ `news_article`（S4） |
| `market_indicator` | `macro_indicator`（S8）/ `market_pulse`（S9） |
| `media_transcript` | `media_transcript`（S10） |
| `institutional_research` | `institutional_research_excerpt`（R2）/ `institutional_research_full_text`（R3） |
| `synthesis` | `synthesis_brief`（R5） |

**不变量 L1-I6**：`evidence_class == coarse(content_type)`，按上表。

### 1.3.2 I0 Registry Baseline（OPC #2 FROZEN，2026-08-13）

**classification domain 词表（11 值，closed）：** `capital_flow, valuation, management, financials`（adopt 现有 P2 分类器 4 域）+ `news_event, sentiment, macro, industry, regulatory, company_profile, other`

**allowed_use / blocked_use 词表（7 值，closed）：** `fundamental_overview, market_context, valuation_judgment, trading_signal, price_reference, background_context, attribution_source`

**policy_version registry：** 初始 `{v0.1}`。递增规则：改变 verdict / ceiling / 默认策略行为 → 新版本号；仅措辞修正不升版本。

**consumer registry：** 初始 `{stock-analyst.md, Vera.ResearchSession, brief-engine}`。

**规则：** 均为 schema-level closed list；新增条目走 M 编号 amendment，运行时不得自造。Capability Registry 属 I6，与本节无关。

### 1.4 Claim Strength Lattice（M16）

6 值枚举冻结（R3）：`OBSERVED_FACT` / `DERIVED_INDICATOR` / `ATTRIBUTED_CLAIM` / `ANALYST_OPINION` / `INFORMATIONAL` / `NO_CLAIM`

**偏序关系**（Hasse）：

```
        OBSERVED_FACT
             │
        DERIVED_INDICATOR
             │
      ┌──────┴──────┐
ATTRIBUTED_CLAIM  ANALYST_OPINION   ← 同级 ⊥ 不可互换
      └──────┬──────┘
        INFORMATIONAL
             │
         NO_CLAIM
```

机器可验证形式 — ≤ 关系表（自反 + 以下严格对）：
- `OF ≥ {DI, AC, AO, INF, NC}`；`DI ≥ {AC, AO, INF, NC}`；`AC ≥ {INF, NC}`；`AO ≥ {INF, NC}`；`INF ≥ NC`
- `AC` 与 `AO` **不可比**（⊥）

**glb 规则（M16 冻结）：**
1. 单源 claim 继承：synthesis 中只来自单一 constituent 的 claim，类别 = 该 constituent 的类别（glb(x, x) = x）
2. 多源合并取 glb：`glb(AC, AO) = INFORMATIONAL`；`glb(DI, AC) = AC`；`glb(OF, DI) = DI`；其余按 ≤ 表推导
3. Synthesis 整体上限 = 全部 constituent 类别的 glb
4. **同层切换禁止**：AC → AO 或 AO → AC 不允许（结果必须 ≤ 两者共同下界 INF）

**全链路单调性不变量（X-I4）：**
```
constituent → synthesis: ≤ glb(constituents)
L2 → L3: max_claim_strength ≤ D6 ceiling(content_type, provenance, purpose)
consumer purpose: trading ≤ research 的同源上限
类别边界: "别人说了什么"(AC/AO) 永远不能升到 "系统计算出了什么"(DI/OF)
```

### 1.5 D5 Assessment Dimensions 适用矩阵（冻结）

每个 `content_type` 声明哪些维度适用（✓ = 必须判定，✗ = 必须 `NOT_APPLICABLE`）：

| content_type | provider_identity | field_integrity | provenance | freshness | classification |
|--------------|:---:|:---:|:---:|:---:|:---:|
| structured_financial | ✓ | ✓ | ✓ | ✓ | ✓ |
| search_result | ✗ | ✗ | ✓ | ✓ | ✓ |
| news_article | ✗ | ✗ | ✓ | ✓ | ✓ |
| macro_indicator | ✓ | ✓ | ✓ | ✓ | ✗ |
| market_pulse | ✓ | ✓ | ✓ | ✓ | ✓ |
| media_transcript | ✗ | ✗ | ✓ | ✓ | ✓ |
| institutional_research_full_text | ✓ | ✗ | ✓ | ✓ | ✓ |
| institutional_research_excerpt | ✓ | ✗ | ✓ | ✓ | ✓ |
| synthesis_brief | ✗ | ✗ | ✓ | ✓ | ✓ |
| prompt_template | ✗ | ✗ | ✗ | ✗ | ✗ |

（institutional_research_excerpt 的 classification 附加 traceability-to-original 要求，见 §3.3 冻结）

### 1.6 D6 Claim Ceiling 函数

`ceiling(content_type, provenance, purpose)` — L3 `max_claim_strength` 的上限。冻结行 + 推导行（OBS-4）+ TBD 行：

| content_type | 条件 | research | trading | 来源 |
|--------------|------|----------|---------|------|
| structured_financial | provenance=real | OF | OF | D6 |
| structured_financial | provenance=derived | DI | DI | D6 |
| structured_financial | provenance=fallback | INF | INF | D6 |
| search_result | classified（domain available） | AC | AC | D6 |
| search_result | unclassified | **TBD** | NC | D6 trading 行；research 行未冻结 |
| news_article | — | AC | AC | D6 |
| macro_indicator | — | OF（as-of publish） | OF | D6 |
| market_pulse | — | OF（market heat fact） | OF | D6 |
| media_transcript | — | AC | **INF（OBS-4 推导，CR6 限定）** | D6 "(research only)" + 单调性 |
| institutional_research_full_text | — | AO（marked） | INF | §3.3 |
| institutional_research_excerpt | — | INF | NC | §3.3 |
| synthesis_brief | — | glb(constituents) | glb(constituents) | D6 + M16（OBS-3） |
| prompt_template | 无 L1/L3（R6 非 producer） | — | — | M14 |

**OBS-4 推导链：** D6 行 `media_transcript` 标 "ATTRIBUTED_CLAIM ✓ (research only)" → trading ≠ AC；单调性 "trading ≤ research 的同源上限" → trading ceiling = INF（AC 的下一个严格下界）。

**CR6 限定：** `media_transcript` 的 trading ceiling = INF **仅允许无 financial signal 的上下文存在**（只支撑背景信息级内容）；任何 financial signal 仍由 P4 默认策略 BLOCK（§1.7）处理 — 该 ceiling 不得被误读为"可用于交易判断"。

### 1.7 Unclassified 默认策略表（§8 → verdict 归一化）

| Family | Research | Trading |
|--------|----------|---------|
| P1 | N/A（结构化必分类） | N/A（结构化必分类） |
| P2 | `ALLOW_WITH_MARKER`（marker=`unclassified/search_external`） | financial_signal → **BLOCK**；无信号 → `ALLOW_WITH_MARKER` |
| P3 | `ALLOW_WITH_MARKER`（marker=`unclassified/market_indicator`） | S9 个股引用 → 对照 baseline；未分类引用 → **BLOCK** |
| P4 | `ALLOW_WITH_MARKER`（marker=`unclassified/transcript`） | financial_signal → **BLOCK**；分类 PASS 后 → `ALLOW` |
| P5 | `ALLOW_WITH_MARKER`（marker=`institutional_research/unclassified` + attribution） | **BLOCK** |
| P6 | 未溯源 constituent → **BLOCK** | 未溯源 constituent → **BLOCK**；untraced claim → **BLOCK** |

**OBS-2 归一化：** §8 措辞 "FAIL CLOSED" 与 "REJECT synthesis" 映射为 verdict 枚举的 `BLOCK` — 不新增枚举值。

`financial_signal(content)` 是 policy 谓词（金融关键词/个股提及检测），**I0 只定义其形态为布尔谓词，检测实现属 I2**；fixture 以显式 `financial_signal: true/false` 标志注入。

### 1.8 Freshness Policy（M11 + CR3）

**CR3 — L2 `freshness` 时间语义冻结：** timestamp 形式 = **data_as_of（数据内容所指时点）**，不是 assessed_at（后者有独立字段）。取值规则按 D4 temporal_semantics 推导：

| temporal_semantics | data_as_of 语义 |
|--------------------|----------------|
| `realtime` | provider 返回的行情数据时点 |
| `eod` | 交易日/日终标识对应的日期 |
| `historical` | 数据区间最后一个数据点时刻 |
| `static_reference` | 版本/最后更新时间（无时效约束） |
| `periodic_indicator` | 指标发布时点 |
| `rolling` | 快照时刻 |

**V5 评估基准（CR3）：** 在 **consumer admission 时刻**，以 `context_time − assessment.freshness(data_as_of)` 对 purpose policy 求值。`receipt.timestamp` 仅保留审计用途（admission 发生时间），**不参与 freshness 判定** — 一个签发时新鲜的 bundle，消费时仍可能已过期。

**STALE / UNKNOWN 的 consumer 侧判定（CR3 冻结）：**
- `STALE` → V5 **FAIL**（任何有 max_age 约束的 purpose）；`brief_assembly`（跨会话、无 max_age）→ PASS
- `UNKNOWN` → V5 **FAIL**（trading_signal / market_monitor / portfolio_review，fail-closed）；research / brief_assembly → PASS

**禁止 session-window 检查**（M11 — 会破坏可重放历史 bundle、异步 brief、跨会话 research）。

**参数模型（ACR-3 CLOSED / ACCEPTED，2026-08-13）：** `max_age = f(purpose, temporal_semantics)` — temporal_semantics 是 freshness policy 的输入维度，**不进入** admission identity（严格保持 consumer + purpose + assessment_id + policy_version 四元组），只决定在该 purpose 下如何解释 data_as_of 的时效要求。

**冻结矩阵（单位：秒；∞ = 无约束）：**

| temporal_semantics | trading_signal | market_monitor | portfolio_review | research | brief_assembly |
|--------------------|----------------|----------------|------------------|----------|----------------|
| realtime | 900 | 1800 | 86400 | 2592000 | ∞ |
| eod | 86400 | 172800 | 604800 | 2592000 | ∞ |
| rolling | 86400 | 604800 | 2592000 | 7776000 | ∞ |
| periodic_indicator | 5184000 | 5184000 | 10368000 | 31536000 | ∞ |
| historical | 604800 | 2592000 | 10368000 | 31536000 | ∞ |
| static_reference | 2592000 | 7776000 | 15552000 | 31536000 | ∞ |

**解释规则（ACR-3 裁决锁定）：** 86400s 是 **duration threshold**，不是"上一交易日数据天然有效"的业务规则。fixture 必须至少覆盖周末/节假日或跨交易日场景，证明系统计算 `context_time − data_as_of` → freshness policy，而非 `date(data_as_of) == previous_trading_day → PASS`。两者不可混。

| purpose | max_age 模型 | 状态 |
|---------|---------|------|
| 全部 purpose | f(purpose, temporal_semantics) 6×5 冻结矩阵 | **FROZEN（ACR-3 CLOSED）** |
| brief_assembly | 跨会话（无 max_age 约束） | 冻结 |

---

## 2. L1 EvidenceRecord

### 2.1 字段表

| 字段 | 类型 | 必填 | 说明 | 冻结来源 |
|------|------|:---:|------|---------|
| `id` | hex(64) | ✓ | **capture identity** = SHA3-256(JCS{producer_id, evidence_class, collected_at, raw_hash, schema_version}) | A1 / §9.1 (M9) |
| `content_hash` | hex(64) | ✓ | SHA3-256(raw_payload_bytes)；跨采集去重 | A1 (M9) |
| `raw_hash` | hex(64) | ✓ | SHA3-256(raw_payload_bytes)，normalization 之前 | §9.1；OBS-1（恒等于 content_hash） |
| `producer_id` | string | ✓ | 15-entry 标识（例 `S2.search.stock`） | A1 / §10.1 |
| `evidence_class` | enum(6) | ✓ | 粗粒度类（1.3.1 映射） | A1 / §2 |
| `collected_at` | ISO 8601 UTC | ✓ | 采集时间 | A1 |
| `raw_reference` | object | ✓ | 受控定位符 + immutable reference version | A1（L1 注） |
| `schema_version` | string | ✓ | Record schema 版本 | A1 / §9.1 |
| `content_type` | enum(10) | ✓ | G10 D1 | v0.2 §3.4 |
| `source_type` | enum(5) | ✓ | G10 D2 | v0.2 §3.4 |
| `retrieval_mode` | enum(6) | ✓ | G10 D3 | v0.2 §3.4 |
| `temporal_semantics` | enum(6) | ✓ | G10 D4 | v0.2 §3.4 |
| `normalized_content` | any JSON | ✗ | 语义归一化产物（转换结果，非原始事实） | A1 / M17 |
| `normalized_content_hash` | hex(64) | 条件 | SHA3-256(JCS(normalized_content))；有 normalized_content 则必填 | M17 |
| `normalization_version` | string | 条件 | 归一化管线版本；同上 | M17 |

`raw_reference` 形状（**PROPOSED**，A1 只冻结"必须携带 version/object-hash"）：`{ "reference": "<controlled URI>", "object_hash": "<引用对象的 version/object-hash>" }`

**禁止字段**（A1 裁决）：`allowed_use` / `blocked_use` / `max_claim_strength` / `trust_status` / `verdict` — 出现在 L1 即 schema 违规（这是对现有 `EvidenceBundle` fact+admission 耦合的正式裁决）。

### 2.2 不变量

| ID | 不变量（机器可验证形式） |
|----|--------------------------|
| L1-I1 | 必填字段齐全；`normalized_content` 存在 ⇔ `normalized_content_hash` + `normalization_version` 存在 |
| L1-I2 | `id == SHA3-256(JCS{producer_id, evidence_class, collected_at, raw_hash, schema_version})`（可重算） |
| L1-I3 | `content_hash == SHA3-256(raw_payload_bytes)` 且 `raw_hash == content_hash`（OBS-1：两公式冻结为同值，强制相等防未来 drift） |
| L1-I4 | 若存在 `normalized_content_hash`：`== SHA3-256(JCS(normalized_content))` |
| L1-I5 | 禁止字段集合不出现（fact purity 结构检查） |
| L1-I6 | 枚举成员合法；`producer_id` ∈ 15-entry；`evidence_class == coarse(content_type)`（1.3.1） |
| L1-I7 | `collected_at` 为合法 UTC ISO 8601 |
| L1-I8 | `raw_reference` 携带 version/object-hash（不可变引用，A1 L1 注） |
| L1-I9 | 不可变：一经产生不可改写；更新 = 新 record（append-only，设计级） |

---

## 3. L2 EvidenceAssessment

### 3.1 字段表

| 字段 | 类型 | 必填 | 说明 | 冻结来源 |
|------|------|:---:|------|---------|
| `assessment_id` | hex(64) | ✓ | SHA3-256(JCS{record_id, assessment_policy_version, assessed_at, assessor_id}) | A1 |
| `record_id` | ref → L1 | ✓ | 指向 EvidenceRecord | A1 |
| `assessed_at` | ISO 8601 UTC | ✓ | 评估执行时间 | A1 (R1) |
| `assessor_id` | string | ✓ | 组件标识 + 版本 | A1 (R1) |
| `assessment_policy_version` | string | ✓ | 当时适用的 assessment policy 版本 | A1 (R1) |
| `assessment_result_hash` | hex(64) | ✓ | SHA3-256(JCS(5 维度输出值)) | M18 |
| `provider_identity` | enum | ✓ | VERIFIED / UNVERIFIED / NOT_APPLICABLE | A1（OBS-6） |
| `field_integrity` | enum | ✓ | PASS / PARTIAL / FAIL / NOT_APPLICABLE | A1（OBS-6） |
| `provenance` | enum(6) | ✓ | real/derived/fallback/external/institutional/transcript | A1 |
| `freshness` | enum/ISO | ✓ | timestamp（= **data_as_of**，CR3）/ STALE / UNKNOWN | A1 + CR3 |
| `classification` | enum | ✓ | classified:[sorted domains]（CR5）/ unclassified / not_applicable | A1 + CR5 |

**语义（R1 冻结）：** L2 不是永恒事实。同一 record 可有多个有效 assessment（taxonomy/freshness policy 演进产生新版本）。每个 assessment 一经产生不可变；"某个 assessment 是唯一正确的"不成立。**classification 结果与 consumer 无关** — consumer 影响的是 L3，不是 L2。

### 3.2 不变量

| ID | 不变量 |
|----|--------|
| L2-I1 | `assessment_id == SHA3-256(JCS{record_id, assessment_policy_version, assessed_at, assessor_id})` |
| L2-I2 | `assessment_result_hash == SHA3-256(JCS({provider_identity, field_integrity, provenance, freshness, classification}))`；classification domain list 先按字典序排序（CR5，hash 确定性前提） |
| L2-I3 | `record_id` ∈ 已知 L1 集合（引用完整性） |
| L2-I4 | 维度适用一致性：对 `record.content_type` 按 D5 矩阵 — ✓ 维度必须有非 NOT_APPLICABLE 值；✗ 维度必须为 NOT_APPLICABLE |
| L2-I5 | 各维度枚举值合法（1.3）；`freshness` 为 timestamp 时其语义为 data_as_of（CR3） |
| L2-I6 | **Conflict 检测（M18）**：存在两条 assessment 同 (record_id, assessor_id, assessment_policy_version) 且 `assessment_result_hash` 不同 → 必须被报告为 conflict，不得静默并存（可由数据推导，schema 不加字段） |
| L2-I7 | Append-only：assessment 不可改写；重新评估 → 新 assessment_id（assessed_at 变化 ⇒ id 变化） |

---

## 4. L3 ContextAdmissionDecision

### 4.1 字段表

| 字段 | 类型 | 必填 | 说明 | 冻结来源 |
|------|------|:---:|------|---------|
| `decision_id` | hex(64) | ✓ | 每 decision 唯一；公式 **FROZEN**（见下） | A1 + OPC #3 |
| `record_id` | ref → L1 | ✓ | | A1 |
| `assessment_ref` | ref → L2 | ✓ | 绑定**具体** assessment_id；禁止 "latest" 语义 | A1 |
| `consumer` | string | ✓ | | A1 |
| `purpose` | enum(5) | ✓ | | §10.1 |
| `policy_family` | enum(6) | ✓ | | A1 |
| `policy_version` | string | ✓ | 允许 policy 演进 | A1 |
| `verdict` | enum(4) | ✓ | ALLOW / ALLOW_WITH_MARKER / DOWNGRADE / BLOCK | A1 |
| `allowed_use` | string[] | ✓ | use-class 词表 = 7 值 closed list（§1.3.2） | A1 + OPC #2 |
| `blocked_use` | string[] | ✓ | 同上 | A1 + OPC #2 |
| `max_claim_strength` | enum(6) | ✓ | ≤ D6 ceiling | A1 / M16 |

**FROZEN（OPC #3，2026-08-13；PROPOSED 原样升格，字段集不变）：** `decision_id = SHA3-256(JCS{record_id, assessment_ref, consumer, purpose, policy_family, policy_version})`。确定性（无时间/随机分量，可重放）；五元组唯一性与 L3-I3 一致；hash 输入为 canonical object（M9，无字符串拼接）。

### 4.2 不变量

| ID | 不变量 |
|----|--------|
| L3-I1 | `assessment_ref` 必须等于某条 L2 `assessment_id` 的字面值（引用完整性；不可为 "latest"） |
| L3-I2 | `record_id == assessment.record_id`（绑定一致） |
| L3-I3 | 同一 (record_id, consumer, purpose, policy_version) 至多一条有效 decision（A1："一个 (record, consumer, purpose) 一个 decision"） |
| L3-I4 | `verdict` ∈ 4 值；当 classification 为 unclassified 时，verdict 必须符合 §1.7 默认策略表（family × purpose × financial_signal） |
| L3-I5 | `max_claim_strength` ≤ D6 ceiling（lattice ≤，§1.6）；downgrade 允许，**upgrade 违反** |
| L3-I6 | `policy_family` == record 所属 family（entry → family 映射，Coverage §5） |
| L3-I7 | `policy_version` ∈ {v0.1}（registry baseline §1.3.2；新增版本走 amendment） |
| L3-I8 | `decision_id` 全集合内唯一 |

---

## 5. L4 DecisionReceipt

### 5.1 字段表（§10.1 修订版，M11 后 + CR1/CR2）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `receipt_id` | hex(64) | ✓ | = SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})（**CR1 裁决**） |
| `receipt_schema_version` | string | ✓ | Receipt schema 版本；进 receipt_id hash 输入（**CR1**） |
| `decision_id` | ref → L3 | ✓ | |
| `assessment_id` | ref → L2 | ✓ | = L3.assessment_ref（**CR2**） |
| `assessment_result_hash` | hex(64) | ✓ | = L2.assessment_result_hash（**CR2**） |
| `producer_id` | string | ✓ | entry 标识 |
| `evidence_record_id` | ref → L1 | ✓ | = L3.record_id |
| `consumer` | string | ✓ | |
| `purpose` | enum(5) | ✓ | |
| `policy_family` | enum(6) | ✓ | |
| `policy_version` | string | ✓ | |
| `verdict` | enum(4) | ✓ | |
| `allowed_use` | string[] | ✓ | |
| `blocked_use` | string[] | ✓ | |
| `max_claim_strength` | enum(6) | ✓ | |
| `assessment_dimensions` | object | ✓ | 5 维度快照（provider_identity / field_integrity / provenance / freshness / classification，含 NOT_APPLICABLE） |
| `evidence_hash` | hex(64) | ✓ | = EvidenceRecord.raw_hash |
| `timestamp` | ISO 8601 UTC | ✓ | admission 发生时间；**仅审计用途（CR3）** |
| `audit_trail` | object | ✓ | {assessor_id, admission_enforcer_id, bypass_detected} |

**禁止字段（M11）：** `bundle_hash` / `bundle_id` — receipt 是 per-decision 产物，bundle 尚未成型。

### 5.2 不变量

| ID | 不变量 |
|----|--------|
| L4-I1 | 必填字段齐全（上表） |
| L4-I2 | 无 `bundle_hash` / `bundle_id`（M11 结构检查） |
| L4-I3 | `decision_id` ∈ L3 集合；`evidence_record_id` ∈ L1 集合；`evidence_hash == record.raw_hash` |
| L4-I4 | receipt 为 decision 的镜像：consumer / purpose / policy_family / policy_version / verdict / allowed_use / blocked_use / max_claim_strength 与对应 L3 一致；`producer_id == record.producer_id`；`assessment_id == decision.assessment_ref`（CR2） |
| L4-I5 | `receipt_id == SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})`（**CR1 公式**） |
| L4-I6 | `assessment_dimensions` 快照 == L2 五维度值；`assessment_result_hash == L2.assessment_result_hash`（CR2） |
| L4-I7 | `timestamp` 为合法 UTC ISO 8601；仅审计用途，不参与 freshness 判定（CR3） |
| L4-I8 | `audit_trail.bypass_detected == false`（§10.2 #7） |

---

## 6. L4 BundleManifest + CuratedEvidenceBundle

### 6.1 BundleManifest（§10.1b + CR4）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `bundle_id` | hex(64) | ✓ | = `bundle_hash`（content-addressed identity；OPC #4 FROZEN）；generated_at 不进 identity |
| `bundle_schema_version` | string | ✓ | Manifest schema 版本（**CR4**） |
| `consumer` | string | ✓ | must match all member receipts.consumer |
| `purpose` | enum(5) | ✓ | must match all member receipts.purpose |
| `admitted_record_ids` | ref[] 有序 | ✓ | 本 bundle 的全部 L1 id（**CR4**） |
| `member_decision_ids` | ref[] 有序 | ✓ | 全部 member DecisionReceipt.decision_id |
| `curated_content_hash` | hex(64) | ✓ | SHA3-256(JCS(curated_content))（**CR4**） |
| `generated_at` | ISO 8601 UTC | ✓ | bundle finalization 时间；**不进 bundle_hash 输入**（CR4 最小集） |
| `bundle_hash` | hex(64) | ✓ | manifest 无自引用 canonical representation 的 hash（**CR4**） |

**CR4 — `bundle_hash` 公式：**
```
bundle_hash = SHA3-256( JCS({
    bundle_schema_version,
    consumer,
    purpose,
    admitted_record_ids,      // 有序
    member_decision_ids,      // 有序
    curated_content_hash
}) )
```
**无自引用**：`bundle_id` 与 `bundle_hash` 自身不进入 hash 输入。同一 `curated_content` 替换 receipt / 成员决策 / 用途都会改变 bundle_hash。

### 6.2 CuratedEvidenceBundle（A1 L4 + R4 + CR4）

| 字段 | 说明 |
|------|------|
| `bundle_id` | 与 manifest 一致 |
| `curated_content` | 有序 fragment 列表，每 fragment = `{content, evidence_record_id, decision_id}`（逐项 provenance trace，**CR4**）；content 只含 admitted + stripped 后的内容 |
| `admitted_record_ids` | 进入本 bundle 的 L1 id（有序） |
| `decision_ids` | 对应 L3 |
| `decision_receipts` | member receipts |
| `bundle_manifest` | finalization 后必填（R4） |

### 6.3 不变量

| ID | 不变量 |
|----|--------|
| L4-I9 | Manifest 字段齐全；`consumer` / `purpose` 与全部 member receipts 一致（§10.1b "must match"） |
| L4-I10 | `bundle_hash == SHA3-256(JCS({bundle_schema_version, consumer, purpose, admitted_record_ids, member_decision_ids, curated_content_hash}))`（CR4 公式） |
| L4-I10b | `curated_content_hash == SHA3-256(JCS(curated_content))`（两级 hash：内容 → manifest） |
| L4-I11 | `member_decision_ids` == 全部 receipts 的 decision_id 有序集合；`admitted_record_ids` == 全部 receipts 的 evidence_record_id 有序去重集合（覆盖检查，§10.2 #6 + CR4） |
| L4-I12 | Finalization ordering（M11）：`generated_at ≥ max(receipt.timestamp)` |
| L4-I13 | `bundle_id` 与 manifest.bundle_id 一致；`bundle_id == bundle_hash`（content-addressed，OPC #4）；全集合唯一 |
| L4-I14 | `curated_content` 不含 raw payload / raw_reference（结构检查：consumer 只见 stripped 内容） |
| L4-I15 | **逐项 provenance（CR4 升级）**：∀ fragment：`decision_id ∈ member_decision_ids` ∧ `evidence_record_id ∈ admitted_record_ids` ∧ receipt(decision_id).evidence_record_id == fragment.evidence_record_id（content → record/decision 不可变 trace） |
| L4-I16 | bundle 内 receipt 的 verdict ∈ {ALLOW, ALLOW_WITH_MARKER, DOWNGRADE} — BLOCK 的不会到达 consumer（§10.2 #4） |

---

## 7. 跨对象不变量

| ID | 不变量 |
|----|--------|
| X-I1 | 引用链闭合：L2.record_id → L1 ✓；L3.assessment_ref → L2 ✓；receipt.decision_id → L3 ✓；receipt.assessment_id → L2 ✓（CR2）；receipt.evidence_record_id → L1 ✓；manifest.member_decision_ids → receipts ✓。悬空引用 = 无效 |
| X-I2 | **四元组授权（freeze clause）**：(consumer, purpose, assessment_id, policy_version) 全部可由 receipt **独立验证**（CR2 后 receipt 自包含）；bundle 被 consumer 接受的前提 = 四元组匹配当前 context + V8 链通过。receipt 验证通过 ≠ evidence 全局可信 |
| X-I3 | L3 必经过 L2（结构：L3 无 assessment_ref = 无效）；L4 receipts 必经过 L3（结构：receipt 无 decision_id = 无效） |
| X-I4 | 全链路 claim 单调性（§1.4）：constituent→synthesis ≤ glb；L3 ≤ D6 ceiling；trading ≤ research；receipt == L3 强度（镜像） |

---

## 8. Non-Bypassable Verification（§10.2 七项 → 机器检查）

| 检查 | 冻结条款 | invariant 映射 | 机器检查 |
|------|---------|---------------|---------|
| V1 | receipt_id 存在且 hash 匹配 | L4-I5 | 重算 SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})（CR1 公式） |
| V2 | evidence_record_id 对应已知 EvidenceRecord | L4-I3 / X-I1 | 引用解析 |
| V3 | consumer + purpose 匹配当前 context | X-I2 | 上下文比对 |
| V4 | verdict ∈ {ALLOW, ALLOW_WITH_MARKER, DOWNGRADE} | L4-I16 | 结构检查（BLOCK 不出现在 bundle） |
| V5 | **consumer admission 时**，`context_time − data_as_of` 对 purpose policy 求值 | §1.8（CR3） | 用 receipt.assessment_dimensions.freshness 的 data_as_of；STALE/UNKNOWN 按 CR3 规则；receipt.timestamp 不参与；max_age 用 fixture-local 策略快照（数值未冻结） |
| V6 | Manifest 存在且覆盖 + 两级 hash 匹配 | L4-I9/I10/I10b/I11 | 集合等价 + bundle_hash / curated_content_hash 重算 |
| V7 | bypass_detected == false | L4-I8 | 布尔检查 |
| V8 | **assessment 绑定链（CR2）** | X-I2 / L4-I4 / L4-I6 | receipt.assessment_id == decision.assessment_ref；receipt.evidence_record_id == decision.record_id == assessment.record_id；receipt.assessment_result_hash == assessment.assessment_result_hash；维度快照 == L2 值 |

**验证失败 → consumer 必须拒绝 bundle。没有 "soft verify"（§10.2 冻结）。**

---

## 9. ACR Register（ACR-1/ACR-2/ACR-3 CLOSED）

### ACR-1：receipt_id 公式与 M9 全局 hash 规则冲突 — **CLOSED（CR1 裁决）**

| 项 | 内容 |
|----|------|
| **冲突** | Coverage §10.1 冻结 `receipt_id = "SHA3-256(decision_id + timestamp)"`（字符串拼接）；v0.2 A1 冻结全局规则"所有 hash 输入必须是 JCS canonical object，**禁止字符串拼接**"（M9） |
| **来源 A** | Coverage Contract §10.1（Clarification 4 冻结；M10/M11 修订未触及该行） |
| **来源 B** | v0.2 A1 "Hash 规则"（M9，后冻结且全局） |
| **裁决** | `receipt_id = SHA3-256(JCS{receipt_schema_version, decision_id, timestamp})` — 与 M9 一致；加入 `receipt_schema_version` 避免 receipt 结构演进产生身份歧义（C 建议，CR1） |
| **传播** | 已执行（2026-08-13）：Coverage §10.1 AMENDED by I0 **M20** |

### ACR-2：DecisionReceipt 缺 assessment_id，四元组无法仅凭 receipt 验证 — **CLOSED（CR2 裁决）**

| 项 | 内容 |
|----|------|
| **冲突** | v0.2 §7 freeze clause：授权 = consumer + purpose + **assessment_id** + policy_version；但 §10.1 DecisionReceipt 字段集无 assessment_id，§10.2 七项验证也无 assessment 绑定检查 |
| **来源 A** | v0.2 §7 Freeze Declaration（冻结条款） |
| **来源 B** | Coverage §10.1 / §10.2（M11 修订后仍无 assessment_id） |
| **裁决** | 方案 (a)：`DecisionReceipt.assessment_id` 必填 + 增 `assessment_result_hash`（C 建议，CR2）。V8 校验 assessment ID / record ID / result hash 与 L3 `assessment_ref` 一致 |
| **传播** | 已执行（2026-08-13）：Coverage §10.1 + §10.2（V8）AMENDED by I0 **M21** |

---

### ACR-3：freshness 参数维度从 purpose-only 具体化为 f(purpose, temporal_semantics) — **CLOSED / ACCEPTED（2026-08-13）**

| 项 | 内容 |
|----|------|
| **冲突** | M11 / Coverage §10.2 #5 冻结 "max age 按 purpose 定义"（purpose-specific）。Open Parameter Closure 发现 flat purpose-only 数值与冻结 D6 可采纳性矛盾：trading_signal 若 flat 15 min，昨日 EOD（D6 允许 structured_financial/real → OF for trading）会被误判 STALE |
| **来源 A** | Coverage §10.2 #5（M11 修订后文本） |
| **来源 B** | v0.2 D6 ceiling 冻结行（eod 数据对 trading 可采纳） |
| **裁决（用户，2026-08-13）— CLOSED / ACCEPTED** | `max_age = f(purpose, temporal_semantics)` 是 CR3 的合法具体化。temporal_semantics 仅决定 freshness policy 如何评价 data_as_of，**不进入 admission identity**（严格保持 consumer + purpose + assessment_id + policy_version 四元组）。eod/trading = 86400s 作为 I0 初始冻结值 |
| **范围** | 极窄 consistency ACR：只确认 (a) purpose × temporal_semantics 是 CR3 的合法具体化；(b) 不改变 admission identity。不重开 Architecture Review |
| **解释规则锁定** | 86400s 是 **duration threshold**，不是"上一交易日数据天然有效"的业务规则。fixture 必须至少覆盖周末/节假日或跨交易日场景，证明系统计算的是 `context_time − data_as_of` → freshness policy，而非 `date(data_as_of) == previous_trading_day → PASS`。两者不可混 |
| **传播** | 已执行（2026-08-13）：6×5 矩阵冻结入 §1.8；Coverage §10.2 #5 AMENDED by I0 **M24** |

---

## 10. Observations（已文档化的归一化，非矛盾）

| ID | 内容 | 处理 |
|----|------|------|
| OBS-1 | `content_hash` 与 `raw_hash` 公式相同（均 = SHA3-256(raw_payload_bytes)） | 保留两字段，L1-I3 强制相等（防未来 drift）；冗余非矛盾 |
| OBS-2 | §8 "FAIL CLOSED" / "REJECT" 不在 verdict 枚举中 | 归一化为 `BLOCK`，不新增枚举值（§1.7） |
| OBS-3 | D6 矩阵 synthesis 行"跨类型取最小"为 M16 前表述 | M16 已撤销 min() → 以 glb 解读 |
| OBS-4 | D6 `media_transcript` 标 "(research only)" 未给 trading 行 | 单调性推导 trading ceiling = INF（§1.6）+ CR6 限定 |
| OBS-5 | freshness max_age 数值未冻结；portfolio_review/market_monitor 未提及 | policy 参数表 TBD，不发明数值（§1.8） |
| OBS-6 | A1 L2 维度枚举无 NOT_APPLICABLE，§10.1 镜像含 NOT_APPLICABLE | L2 维度枚举统一含 NOT_APPLICABLE；D5 ✗ 维度必须 NOT_APPLICABLE（L2-I4） |
| OBS-7 | `evidence_class`（§2 粗粒度）与 `content_type`（D1 细粒度）双字段 | 冻结映射表 1.3.1 + L1-I6 一致性检查 |
| OBS-8 | 冻结不变量表无 decision_id 公式独立检查项（L3-I8 仅"全集合唯一"；validator 将公式检查挂 L3-I8 标签实现） | 用户裁决（2026-08-13）：(a) **ACCEPTED / NON-BLOCKING TAXONOMY DEBT** — 公式已 §4.1 FROZEN 且 validator 已实际检查，非 contract 缺失；未来 registry 重构可拆 uniqueness/formula 两项，当前不影响 correctness；不 amendment |

---

## 11. Normative Example（happy-path 链）

完整合法实例，S11 路径（structured_financial / real / trading consumer）。**hash 一律以 `<…>` 占位**：fixture materialize 时用验证器同一套 jcs/sha3 实现实算回填，保证文档示例、fixture、验证器三者同一 hash 语义。

```jsonc
// ① Producer raw payload（S11 wind_query，不属于任何层）
{ "code": "600519", "pe": 28.3, "pb": 7.5 }

// ② L1 EvidenceRecord（capture wrapper 产出）
{
  "id": "<sha3-256 of JCS{producer_id,evidence_class,collected_at,raw_hash,schema_version}>",
  "content_hash": "<sha3-256 of raw bytes>",
  "raw_hash": "<same as content_hash — L1-I3>",
  "producer_id": "S11.wind_query",
  "evidence_class": "structured_financial",
  "collected_at": "2026-08-13T02:15:00Z",
  "raw_reference": { "reference": "wind://daily/600519", "object_hash": "<ref version>" },
  "schema_version": "0.1",
  "content_type": "structured_financial",
  "source_type": "internal_provider",
  "retrieval_mode": "direct_api",
  "temporal_semantics": "realtime",
  "normalized_content": { "code": "600519", "pe": 28.3, "pb": 7.5 },
  "normalized_content_hash": "<sha3-256 of JCS(normalized_content)>",
  "normalization_version": "1.0"
}

// ③ L2 EvidenceAssessment
{
  "assessment_id": "<sha3-256 of JCS{record_id,assessment_policy_version,assessed_at,assessor_id}>",
  "record_id": "<L1.id>",
  "assessed_at": "2026-08-13T02:15:01Z",
  "assessor_id": "gate.assessor.v1",
  "assessment_policy_version": "v0.1",
  "assessment_result_hash": "<sha3-256 of JCS(dimensions)>",
  "provider_identity": "VERIFIED",
  "field_integrity": "PASS",
  "provenance": "real",
  "freshness": "2026-08-13T02:14:59Z",   // = data_as_of（CR3），非 assessed_at
  "classification": "classified:[valuation]"
}

// ④ L3 ContextAdmissionDecision
{
  "decision_id": "<sha3-256 of JCS{record_id, assessment_ref, consumer, purpose, policy_family, policy_version}>",
  "record_id": "<L1.id>",
  "assessment_ref": "<L2.assessment_id>",
  "consumer": "stock-analyst.md",
  "purpose": "trading_signal",
  "policy_family": "P1",
  "policy_version": "v0.1",
  "verdict": "ALLOW",
  "allowed_use": ["fundamental_overview"],
  "blocked_use": ["valuation_judgment"],
  "max_claim_strength": "OBSERVED_FACT"
}

// ⑤ DecisionReceipt（CR1/CR2 后；无 bundle_hash — M11）
{
  "receipt_id": "<sha3-256 of JCS{receipt_schema_version,decision_id,timestamp}>",
  "receipt_schema_version": "0.1",
  "decision_id": "<L3.decision_id>",
  "assessment_id": "<L2.assessment_id>",           // CR2
  "assessment_result_hash": "<L2.assessment_result_hash>",  // CR2
  "producer_id": "S11.wind_query",
  "evidence_record_id": "<L1.id>",
  "consumer": "stock-analyst.md",
  "purpose": "trading_signal",
  "policy_family": "P1",
  "policy_version": "v0.1",
  "verdict": "ALLOW",
  "allowed_use": ["fundamental_overview"],
  "blocked_use": ["valuation_judgment"],
  "max_claim_strength": "OBSERVED_FACT",
  "assessment_dimensions": {
    "provider_identity": "VERIFIED",
    "field_integrity": "PASS",
    "provenance": "real",
    "freshness": "2026-08-13T02:14:59Z",
    "classification": "classified:[valuation]"
  },
  "evidence_hash": "<L1.raw_hash>",
  "timestamp": "2026-08-13T02:15:02Z",   // 仅审计（CR3）
  "audit_trail": {
    "assessor_id": "gate.assessor.v1",
    "admission_enforcer_id": "gate.enforcer.v1",
    "bypass_detected": false
  }
}

// ⑥ BundleManifest（finalization 后生成；CR4 后）
{
  "bundle_id": "<same as bundle_hash (content-addressed)>",
  "bundle_schema_version": "0.1",
  "consumer": "stock-analyst.md",
  "purpose": "trading_signal",
  "admitted_record_ids": ["<L1.id>"],
  "member_decision_ids": ["<L3.decision_id>"],
  "curated_content_hash": "<sha3-256 of JCS(curated_content)>",
  "generated_at": "2026-08-13T02:15:03Z",
  "bundle_hash": "<sha3-256 of JCS{bundle_schema_version,consumer,purpose,admitted_record_ids,member_decision_ids,curated_content_hash}>"
}

// ⑦ CuratedEvidenceBundle（consumer 唯一可见物；CR4 后 fragment trace）
{
  "bundle_id": "<same as manifest>",
  "curated_content": [
    { "content": { "code": "600519", "pe": 28.3, "pb": 7.5 },
      "evidence_record_id": "<L1.id>",
      "decision_id": "<L3.decision_id>" }
  ],
  "admitted_record_ids": ["<L1.id>"],
  "decision_ids": ["<L3.decision_id>"],
  "decision_receipts": [ "<DecisionReceipt ⑤>" ],
  "bundle_manifest": { "<BundleManifest ⑥>" }
}
```

---

## 12. Invalid Fixture Catalog（待 materialize）

每类一个 fixture，带 `expected_violation` 标签指向 invariant。**注（CR3/CR5/ACR-3）：** F17/F25 的 freshness 阈值直接使用 §1.8 **冻结矩阵**数值（Open Parameters CLOSED，无需 fixture-local 快照）；JCS 越界输入按受限 profile 处理为 REJECT 而非 PASS。

| # | 违规内容 | 违反 |
|---|---------|------|
| F1 | L1 携带 `allowed_use` 字段 | L1-I5 |
| F2 | L1 `id` 与重算不符 | L1-I2 |
| F3 | L1 `content_hash ≠ raw_hash` | L1-I3 |
| F4 | L1 有 `normalized_content` 无 `normalization_version` | L1-I1 |
| F5 | L2 search_result 的 `provider_identity=VERIFIED`（D5 ✗） | L2-I4 |
| F6 | L2 `assessment_result_hash` 与维度不符 | L2-I2 |
| F7 | L2 同 (record, assessor, policy_version) 两 assessment result 不同，未报告 conflict | L2-I6 |
| F8 | L3 `assessment_ref` 悬空 | L3-I1 |
| F9 | L3 search_result(trading) `max_claim_strength=DERIVED_INDICATOR`（超 ceiling） | L3-I5 |
| F10 | L3 fallback provenance 给 OBSERVED_FACT（upgrade） | L3-I5 |
| F11 | L3 P2 trading unclassified → ALLOW（违反 §8 默认策略） | L3-I4 |
| F12 | receipt 携带 `bundle_hash` | L4-I2 |
| F13 | receipt verdict=BLOCK 出现在 bundle | L4-I16 |
| F14 | manifest `member_decision_ids` 缺失一条 | L4-I11 |
| F15 | manifest `consumer` 与 receipt 不一致 | L4-I9 |
| F16 | receipt 悬空 `decision_id` | X-I1 |
| F17 | receipt timestamp 超龄但 data_as_of 新鲜（**反例：必须 PASS** — timestamp 不参与 freshness，CR3）；含跨交易日/周末场景：判定 = context_time − data_as_of 对冻结矩阵求值（duration threshold），非 date 相等判定（ACR-3） | L4-I7 语义 + ACR-3 |
| F18 | synthesis_brief strength 高于 glb(constituents) | X-I4 |
| F19 | `bypass_detected: true` | L4-I8 |
| F20 | `collected_at` 非 ISO 8601 | L1-I7 |
| F21 | 字符串拼接 hash（`id` 用 `"a"+"b"` 语义重算不符） | M9 全局 / L1-I2 |
| F22 | manifest `bundle_hash` 与无自引用 canonical rep 不符（替换 member 后未重算） | L4-I10 |
| F23 | curated_content fragment 缺 `decision_id` trace | L4-I15 |
| F24 | receipt `assessment_result_hash` 与 L2 不符 | L4-I6 / V8 |
| F25 | consumer-time 超龄：context_time − data_as_of 超过**冻结矩阵**对应值（V5 FAIL）；含 eod/trading 跨交易日边界（周五 EOD，周一开盘 > 86400s → FAIL） | V5（CR3）+ ACR-3 |
| F26 | JCS 受限 profile 越界输入（lone surrogate / 超范围数字）→ 验证器 REJECT | CR5 |

---

## 13. 验证器计划（machine validation）

- 文件：`docs/spec/validate_i0_schema_contract.py` — **stdlib only**（json / hashlib / unicodedata / re / sys），零第三方依赖，不 import 任何生产代码。
- 自实现 `jcs()`：**受限 JCS profile（CR5）**，明确覆盖范围与拒绝规则：
  - 覆盖：object（key 字典序）、array、string（合法 Unicode）、bool、null、有限数字
  - 数字规则：±2^53 内整数精确序列化；非整数必须可经 Python repr 最短往返（否则 REJECT）
  - 拒绝规则：lone surrogate、超范围数字 → **REJECT**（输入错误，不算 PASS）
  - **明确声明：受限 profile ≠ 完整 RFC 8785 兼容**
- 检查注册表：`{invariant_id → check_fn}`，覆盖 L1-I1..I9 / L2-I1..I7 / L3-I1..I8 / L4-I1..I16 / X-I1..I4 / V1..V8。
- Fixture 布局：`docs/spec/fixtures/valid/*.json` + `docs/spec/fixtures/invalid/*.json`（后者携带 `expected_violation` 标签，验证器断言"恰好被该 invariant 拒绝"）；freshness 类 fixture 自带 fixture-local policy 快照（F17/F25）。
- 退出码：任何 unexpected pass/fail → 非零。
- **不接生产**：验证对象只有 fixtures，不触碰 15 个入口。

---

## 14. States

```
I0 Schema Contract:            FROZEN / OPEN PARAMETERS CLOSED（2026-08-13）
ACR Register:                  ACR-1/ACR-2/ACR-3 CLOSED（已传播 Coverage = M20/M21/M24；CR3/CR4 一致性 = M22/M23）
Parameters #1/#2/#3/#4:        FROZEN（6×5 矩阵 §1.8 / registry baseline §1.3.2 / decision_id 公式 §4.1 / bundle_id = bundle_hash §6.1）
Fixtures / Validator:          MATERIALIZED — 29/29 全 PASS（2026-08-13；exit 0）
                                valid 3（normative_full_chain / f17_audit_old_data_fresh / f17_eod_weekend_boundary）
                                invalid 26（F1–F16/F18–F26；f25 拆 realtime + eod 跨交易日；f26 = JCS REJECT）
                                validator: validate_i0_schema_contract.py（stdlib only；受限 JCS profile CR5）
                                fixture 实算: generate_i0_fixtures.py（与 validator 同一 jcs/sha3 实现）
I0 Validation Evidence:        PASS — Regression 29/29（2026-08-13；L1-I9/L2-I7/X-I3 design-level skip 已登记，非假装测过）
I0 SCHEMA CONTRACT PROVEN:     NOT YET — 唯一未闭合语义 = D6 research×search_result×unclassified TBD
                               （2026-08-13 用户裁决：NOT YET 为健康状态，非失败；关闭路径 = D6 单格裁决 → 2 判别 fixture → 全量 regression → Task #10）
Evidence Layer implemented:    NOT CLAIMABLE
Production enforcement:        NOT CLAIMABLE
Normative Examples:            SPEC 版已有（§11）+ fixture 实算（valid/normative_full_chain.json）
Invalid Fixtures:              CATALOG F1–F26（§12）+ fixture 实算（invalid/*.json，_meta 声明 expected_violations）
Machine Validation Tests:      PLAN 已定（受限 JCS profile, §13）；实现待
Production Wiring:             NOT AUTHORIZED
Production Coverage:           0/15（I0 不改变该口径）
```

**禁止声明（C 裁决）：** 即便四类证据齐备，最多证明 "spec + fixture validator" — 不等同于 Evidence Layer 已实现，不等同于 production enforcement 已实现。

---

## Appendix A: 冻结来源索引

| 本文件内容 | 冻结来源 |
|-----------|---------|
| L1 字段表 + 禁止字段 + hash 规则 | v0.2 A1（R2/M9）+ Coverage §9 |
| L1 normalized_content_hash / normalization_version | Target Arch §2 ② (M17) |
| L2 字段表 + versioned judgment + append-only | v0.2 A1（R1/M8） |
| L2 assessment_result_hash + conflict | Target Arch §2 ③ (M18) |
| L2 freshness 时间语义 = data_as_of | v0.2 A1 + D4（CR3 冻结） |
| L3 字段表 + per-(consumer,purpose) + assessment_ref | v0.2 A1 |
| L4 DecisionReceipt 字段 + 无 bundle_hash | Coverage §10.1（M10/M11）+ CR1/CR2（ACR 裁决） |
| BundleManifest + finalization ordering | Coverage §10.1b（M11）+ CR4 |
| 6-value lattice + glb + 单调性 | v0.2 A3（R3/M10）+ Target Arch §4（M16） |
| 六维 taxonomy 枚举 | v0.2 A3 D1–D4 |
| D5 适用矩阵 / D6 ceiling | v0.2 A3 D5/D6 + §3.3 + CR6 限定 |
| 未分类默认策略 | Coverage §8（Clarification 2） |
| freshness purpose-specific / 禁 session-window | Coverage §10.2 #5（M11）+ CR3 |
| 四元组 freeze clause | v0.2 §7 + CR2（receipt 自包含） |
| 15-entry 分母 | Target Arch §5（M14） |
| producer → raw / wrapper → L1 术语 | Target Arch §1（M15） |
