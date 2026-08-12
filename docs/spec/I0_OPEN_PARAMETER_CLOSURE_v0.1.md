# I0 — Open Parameter Closure v0.1

**卡：** Implementation Plan — I0（承接 I0 Schema Contract FREEZE: PASS WITH OPEN PARAMETERS）
**状态：** CLOSED — 四类参数全部 FROZEN（2026-08-13；#1 经 ACR-3 CLOSED / ACCEPTED）
**Mode：** Schema Spec 层参数冻结（非 production implementation）
**日期：** 2026-08-13
**输入：** `I0_SCHEMA_CONTRACT_v0.1.md` — FROZEN / OPEN PARAMETERS PENDING（§14 open parameters）

---

## 0. 边界与裁决规则

- 本卡只关闭 I0 §14 的 open parameters。不产生生产类型、不接线、不动 15 入口。
- 冻结后的值以 amendment 回写 I0_SCHEMA_CONTRACT。
- **ACR 触发条件（用户裁决）：** 若参数关闭过程发现改变 CR1–CR6 语义或 Target Architecture 不变量的情况 → 触发 ACR，不得静默吸收。当前四类提案均不触及 CR1–CR6 语义与 lattice / freeze clause 不变量，无需重开架构评审。
- 顺序（用户锁定）：Schema Design Freeze → **Open Parameter Closure（本卡）** → Materialize F1–F26 → Validator → I0 SCHEMA CONTRACT PROVEN。
- 关闭后：F25 等 freshness fixture 直接用冻结值，不再需要 fixture-local 策略快照。

---

## 1. 参数类 1：max_age 数值

**现状与 grounding：**
- M11 冻结"purpose-specific"原则；数值未冻结（OBS-5）；brief_assembly = 跨会话（无 max_age，已冻结）。
- 现有代码 `trust_gate/boundaries/g3_freshness.py` 有 **per-action** 阈值表（stock 24h / financials 120d / consensus 30d / peers 7d / valuation 7d / shareholders 120d / calendar 30d / connect 5min），但其自身 WARNING 声明：Phase 1a 默认值、wind_query only、**禁止复制为全局规则**。该表在 I1 落地时作为 per-action SLA 输入保留；与本卡 purpose-level max_age 是两个维度，**不合并**。
- 现有 G3 已区分 `data_timestamp` vs `retrieved_at`（F-03）——与 CR3 的 data_as_of 语义一致。

**关键发现（提案内修正，非 ACR）：** 单一 flat 数值 per purpose 会与冻结的 D6 可采纳性矛盾 — 例如 trading_signal 若 flat 15 min，则昨日 EOD 数据（D6 允许 structured_financial/real → OF）会被误判 STALE。因此 max_age 需以 **(purpose × temporal_semantics)** 二元组定义。这仍是 M11"按 purpose 定义"的细化（每个 purpose 内的政策按数据时态细分），不改变 CR1–CR6 语义；若你认为超出"purpose-specific 数值"的裁决范围，按 ACR 处理。

**裁决（2026-08-13）：** ACR-3 **CLOSED / ACCEPTED** — `max_age = f(purpose, temporal_semantics)` 是 CR3 的合法具体化；temporal_semantics 仅决定 freshness policy 如何评价 data_as_of，**不进入 admission identity**（consumer + purpose + assessment_id + policy_version 保持四元组）。eod/trading = 86400s 为初始冻结值。**解释规则锁定：86400s 是 duration threshold，不是"上一交易日数据天然有效"的业务规则** — fixture 必须覆盖周末/节假日或跨交易日场景，证明计算的是 context_time − data_as_of → freshness policy，而非 date(data_as_of) == previous_trading_day → PASS。本矩阵已冻结回写 I0 §1.8。

**冻结矩阵（ACR-3 CLOSED 2026-08-13；本表为人读单位，冻结数值以 I0 §1.8 秒单位矩阵为准；∞ = 无约束）：**

| temporal_semantics | trading_signal | market_monitor | portfolio_review | research | brief_assembly |
|--------------------|----------------|----------------|------------------|----------|----------------|
| realtime | 15 min | 30 min | 24 h | 30 d | ∞ |
| eod | 24 h（adopt G3 stock=86400） | 48 h | 7 d | 30 d | ∞ |
| rolling | 1 d | 7 d | 30 d | 90 d | ∞ |
| periodic_indicator | 60 d | 60 d | 120 d | 365 d | ∞ |
| historical | 7 d | 30 d | 120 d | 365 d | ∞ |
| static_reference | 30 d | 90 d | 180 d | 365 d | ∞ |

**校准依据：**
- eod/trading_signal 24h：直接 adopt G3 `stock=86400`（昨收可用、T+2 stale 的同一推理）。
- realtime/trading_signal 15 min（=900s）：G3 WARNING 明确"实时行情需 minute-level"。
- periodic_indicator 60–365d：覆盖月度（CPI/PMI）与季度（财报类指标）发布周期；更细周期走 amendment。
- research 长窗口（30–365d）：M11"research 长"方向。
- static_reference 有 max_age 而非 ∞：版本型数据仍须定期复核，防止无限期引用过期资料。

**STALE/UNKNOWN 判定**已在 CR3 冻结，本卡不动。

---

## 2. 参数类 2：受控词表与 registry

### 2.1 classification domain 词表（closed list）

**提案（11 值）：** `capital_flow, valuation, management, financials`（**adopt** 现有 `search_enforcer._DOMAIN_PATTERNS` 的 4 域）+ 按 G10 扩展 `news_event, sentiment, macro, industry, regulatory, company_profile, other`。

规则（已冻结 CR5 保持）：`classified:<sorted>` 按字典序排序；词表封闭，新增 domain 走 amendment（M 编号），运行时不得自造。

### 2.2 allowed_use / blocked_use 词表

**提案（7 值，closed）：** `fundamental_overview, market_context, valuation_judgment, trading_signal`（**adopt** Coverage §10.1 示例已有 4 值）+ `price_reference, background_context, attribution_source`（P4/P5 marker 与 brief 用途所需）。

### 2.3 policy_version registry

**提案：** 初始条目 `v0.1`。递增规则：任何改变 verdict / ceiling / 默认策略行为的变化 → 新版本号；仅措辞修正不升版本。I1 落地时的实际版本以 registry 条目为准。

### 2.4 consumer registry

**提案：** 初始条目 `stock-analyst.md, Vera.ResearchSession, brief-engine`（均来自冻结文档示例）。新增 consumer 走 amendment。consumer 标识符本身不透明（I0 已冻结）。

**机制说明：** 以上 registry 在 I0 均为 schema-level closed list（文档冻结），不建运行时 registry；Capability Registry 属 I6，与本卡无关。

---

## 3. 参数类 3：decision_id 确定性公式

**现状：** I0 PROPOSED：`SHA3-256(JCS{record_id, assessment_ref, consumer, purpose, policy_family, policy_version})`

**提案：冻结该公式。**
- 确定性：无时间/随机分量，可重放。
- 唯一性：五元组保证，与 L3-I3"同 (record_id, consumer, purpose, policy_version) 至多一条 decision"一致。
- append-only 语义：同 record 重评估 → assessment_ref 变化 → 新 decision_id，与 L2-I7 呼应。
- 与 receipt_id（CR1 公式）不冲突：receipt_id 额外绑定 receipt_schema_version + timestamp。

---

## 4. 参数类 4：bundle_id 确定性公式

| 选项 | 公式 | 论证 |
|------|------|------|
| **A（推荐）** | `bundle_id = bundle_hash` | content-addressed identity：身份 = 完整性 hash，零新增字段；内容变 → id 变，符合 append-only；与 L1 content-addressed 精神一致；重放/校验无需额外重算 |
| B | `SHA3-256(JCS{bundle_schema_version, consumer, purpose, member_decision_ids, generated_at})` | 相同内容重复生成得不同 id；但引入 generated_at 破坏确定性与可重放性，且与"hash = 身份"直觉相悖 |
| C | 计数器 / UUID | 非确定性，违反确定性身份原则 |

**提案：A。** `bundle_id` 与 `bundle_hash` 字段并存但恒等（保留 bundle_id 字段，避免未来 identity 语义演变时改 schema）。I0 冻结的"bundle_id 全集合唯一"（L4-I13）由 content-addressed 唯一性保证。

---

## 5. 裁决结果（2026-08-13）

| # | 参数类 | 裁决 | 状态 |
|---|--------|------|------|
| 1 | max_age | ACR-3 CLOSED / ACCEPTED；6×5 矩阵冻结回写 I0 §1.8；86400s = duration threshold，非"上一交易日天然有效"业务规则 | FROZEN |
| 2 | 词表与 registry | 接受；冻结为 I0 registry baseline（I0 §1.3.2）；G3 per-action SLA ≠ I0 global policy 分层保持 | FROZEN |
| 3 | decision_id | 接受；PROPOSED 公式原样升 FROZEN，字段集不变；hash 输入为 canonical object，不回退字符串拼接 | FROZEN |
| 4 | bundle_id | 接受 A：bundle_id = bundle_hash；generated_at 保持审计元数据，不进入 identity | FROZEN |

已执行：ACR-3 CLOSED → 6×5 矩阵冻结回写 I0 §1.8 → M24 传播至 Coverage §10.2 #5。后续：Task #9（materialize F1–F26 + validator）→ 全 PASS → 提交用户裁决 I0 SCHEMA CONTRACT PROVEN（ACR-3 CLOSED ≠ PROVEN，不得提前）。

---

## States

```
Open Parameter Closure:    CLOSED — 四类参数全部 FROZEN（2026-08-13；#1 经 ACR-3 CLOSED/ACCEPTED）
ACR-3:                     CLOSED / ACCEPTED（freshness dimensionality，I0 §9；传播 M24 至 Coverage §10.2 #5）
I0 Schema Contract:        FROZEN / OPEN PARAMETERS CLOSED
Fixtures / Validator:      MATERIALIZED — Regression 29/29 全 PASS（2026-08-13；3 valid + 26 invalid；exit 0）
I0 Validation Evidence:    PASS（29/29；design-level skip 已登记）
I0 SCHEMA CONTRACT PROVEN: NOT YET — 唯一未闭合语义 = D6 research×search_result×unclassified TBD
                           （2026-08-13 用户裁决：健康状态；关闭路径 = D6 单格裁决 → 2 判别 fixture → regression → Task #10）
```
