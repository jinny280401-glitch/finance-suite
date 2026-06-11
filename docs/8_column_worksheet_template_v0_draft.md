# 8-Column Worksheet Template — v0 Draft

> **Status:** TEMPLATE for Session 1+. NOT a contract.
> **Owner:** Session 1 参与者共同维护
> **Created:** 2026-06-08
> **Hard constraint:** 8 列已锁定。Verdict 5 状态 + Conflict Source 5 subtype 引用 L0 ontology Section 2.2.4 / 2.2.7。**不允许修改列结构**。

---

## 0. 一句话定位

8 列工作表是 L0 ontology 的**操作界面**——每次跑 Discovery case 时，**一行 = 一次 VerificationAttempt**。本模板不是契约，是 Session 1 现场填表的工作表。

---

## 1. 元数据

```
Case:              _____________  (e.g. 光伏-硅料新势力产能翻倍)
Claim ID:          _____________  (来自 L0 Section 2.2.2)
Question:          _____________  (Serenity 输出)
Date of Run:       _____________
Run Owner:         _____________  (主填人)
Reviewer:          _____________  (复核人)
```

---

## 2. 8 列定义 (locked, 不可改列名/列序)

| # | 列名 | 含义 | 填入者 | Done 标准 |
|---|---|---|---|---|
| 1 | **Serenity Question** | Serenity 提出的产业链问题 | 人类 / Serenity | 问题表述明确，可拆出 ≥1 个 assertion |
| 2 | **Assertion** | Question 拆出的可独立验证断言 | 人类 | 断言表述明确，可被 1 个 matching rule 处理 |
| 3 | **Extraction Field** | 从 evidence source 抽取的字段 | LLM（Session 1: 人类手工指定） | 字段名对应 L0 Section 4.1 critical 字段 |
| 4 | **Evidence Source** | 具体 evidence 容器引用 | LLM / 人类 | ≥1 个 Filing/BiddingRecord/CustomsRecord/Patent，有 source_url 或 filing_id |
| 5 | **Matching Rule** | 5 类 invariant 之一 | 人类（claim_type 决定推荐） | 引用 L0 Section 5 的 Type 1-5 |
| 6 | **Tolerance** | 容忍度参数 | 人类（P0a.5c 后由 contract 给出默认） | 数值 + 单位（金额/比例/季度） |
| 7 | **Verdict** | 5 状态判定 | LLM（Session 1: 人类判定） | 5 状态枚举值之一 |
| 8 | **Conflict Source** | 冲突来源（仅 conflicting_evidence） | LLM | 5 subtype 之一，**仅当 Verdict = conflicting_evidence** |

---

## 3. Verdict 5 状态（locked from L0 Section 2.2.4）

```
verified              找到支撑证据，cross-check 通过
tried_not_found       主动查询了，没找到支撑证据
not_attempted         还没查询（留 placeholder）
conflicting_evidence  找到反证
tolerance_unresolved  数据有，但 tolerance 边界外无法判定
```

---

## 4. Conflict Source 5 subtype（locked from L0 Section 2.2.7）

```
direct_contradiction    A 说客户是 B，B 说不是
chain_contradiction     上游/下游整体链对不上
amount_contradiction    量级对不上
direction_contradiction 方向对不上（A 涨 B 跌）
timing_contradiction    跨期窗口对不上
```

**联动约束**：
- Verdict = `conflicting_evidence` → Conflict Source **必填**
- Verdict = 其他 → Conflict Source **必空**
- 禁止 `verified + chain_contradiction` 这类自相矛盾

---

## 5. Example Row（光伏 case placeholder，Session 1 现场重填）

> ⚠️ 此行仅作 template 演示，**attempt_id = EXAMPLE-DO-NOT-COMMIT**。Session 1 必须基于用户选定的实际研报重填。

### Assertion Row

| 列 | 值 |
|---|---|
| attempt_id | `EXAMPLE-DO-NOT-COMMIT` |
| 1. Serenity Question | 硅料新势力 X 公司未来两年硅料产能能否翻倍至 30 万吨？ |
| 2. Assertion | 在建项目 capex 投入 ≥ 50 亿元 |
| 3. Extraction Field | `CapexProject.total_budget`; `OperatingEntity.files.Filing.disclosed_capex` |
| 4. Evidence Source | X 公司 2024 年报 (filing_id: AN-2024-001); 2025 半年报 (filing_id: AN-2025H1-001); 在建工程明细公告 |
| 5. Matching Rule | Type 3 (Cash vs Logistics) — capex 应支撑产能扩张 |
| 6. Tolerance | ±15%（金额口径差异容忍） |
| 7. Verdict | `_____________` (Session 1 现场填) |
| 8. Conflict Source | `_____________` (仅 conflicting_evidence 时填) |

---

## 6. 多 Assertion 拆分原则（per G 锁定指令）

一个 Question 拆多少 Assertion 是设计决策：

| 数量下限 | 理由 |
|---|---|
| ≥ 2 | 否则 Question 粒度太粗，聚合函数无意义 |
| ≥ 3 | 覆盖不同 invariant type，SC2 验证不充分 |
| ≥ 1 个 `[NEGATIVE TEST]` | 故意挑能逼出 `conflicting_evidence` 的断言（SC2 硬条件） |

### 光伏 case 拆分示例（4 个 assertion）

| ID | 维度 | Invariant | 备注 |
|---|---|---|---|
| A1 | 现金 | Type 3 (Cash vs Logistics) | capex ≥ 50 亿 |
| A2 | 上游 | Type 1 (Mirror) | 工业硅采购量同比 +100% |
| A3 | 容量 | Type 2 (Capacity Chain) | 在建/现有 ≥ 1.0 |
| A4 `[NEGATIVE TEST]` | 反证 | Type 3 + Type 2 | 实际产能 vs 公告产能（挑数字最可疑的一个）|

---

## 7. 8 列填表的硬规则

```
HR1  每行必须有唯一 attempt_id，example row 标 EXAMPLE-DO-NOT-COMMIT
HR2  Verdict = conflicting_evidence 时，Conflict Source 必填；其他状态必空
HR3  Tolerance 必须有数值 + 单位，禁止"适中""合理"等模糊词
HR4  Evidence Source 必须有可追溯 ID，拒绝"大概是某年报""好像是某公告"
HR5  Matching Rule 只能引用 L0 Section 5 的 Type 1-5，禁止自创
HR6  Negative assertion 在 Assertion 列前标注 [NEGATIVE TEST]
HR7  Question 列在第一次出现后保持稳定，Session 内不改写
HR8  同一 Assertion 的多次尝试 = 多行（append-only audit trail）
```

---

## 8. 8 列与 L0 ontology 的映射

| 8 列 | L0 entity | 备注 |
|---|---|---|
| 1. Serenity Question | `Claim.question_id` (parent) | 一个 Question 可拆多 Claim |
| 2. Assertion | `Claim.assertion_id` (child) | per G 锁定 Question/Assertion 分离 |
| 3. Extraction Field | `ExtractionField` (TBD entity) | 对应 L0 Section 4.1 critical 字段 |
| 4. Evidence Source | `Filing` / `BiddingRecord` / `CustomsRecord` / `Patent` 引用 | typed reference |
| 5. Matching Rule | `MatchingRule` 引用 L0 Section 5 Type 1-5 | claim_type 决定推荐哪类 |
| 6. Tolerance | `Tolerance` 参数 | 数值 + 单位 |
| 7. Verdict | `Verdict.verdict_state` | 5 状态枚举 |
| 8. Conflict Source | `Verdict.conflict_subtype` | 仅 conflicting_evidence |

**关键不变量**：
- 一行 = 一个 `VerificationAttempt`（不可变，append-only）
- 报告里"产业链一致性结论" = 该 Question 下所有 `Verdict` 的聚合函数（**聚合函数本身是 TBD**，P0d 决定）

---

## 9. Session 1 后的产物

- 工作表 freeze 为 `case1_worksheet_v0.md`
- 作为 L0 ontology 修订输入（**只允许改 L0 / P0a.5 草稿**）
- **不允许从这张表直接产出 P0b 契约**（per G 锁定指令）

---

## 10. Changelog

- 2026-06-08: v0 模板创建。8 列锁定 (Question / Assertion / Extraction Field / Evidence Source / Matching Rule / Tolerance / Verdict / Conflict Source)。Verdict 5 状态 + Conflict Source 5 subtype 引用 L0 ontology。
