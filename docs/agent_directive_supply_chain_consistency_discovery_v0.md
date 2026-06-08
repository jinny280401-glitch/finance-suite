# Agent Directive: Supply Chain Consistency Discovery Sprint v0

> **Issued:** 2026-06-08
> **Status:** LOCKED — supersedes any prior P0b / Gate / Runtime planning
> **Audience:** C (Codex), other AI agents, human collaborators working on Finance Suite
> **Effective:** Immediately

---

## 1. Context

Serenity skill 接入后暴露了一个根本问题：我们有"产业链思考方法"，但没有"产业链上下游勾稽质检系统"。本指令**冻结**当前切片并启动 Discovery Sprint，**不进入 P0b / Gate / Runtime 阶段**。

直接写 P0b Gate 契约大概率会退化为"LLM 看了几份 PDF 然后说'我觉得对得上'"——这正是过去半年一直在防的失败模式。

正确顺序：先证明"产业链一致性"能从概念压成**可验证对象**，再写契约。

---

## 2. Locked Slice (do not modify)

```
P0a      External Intelligence Provider Strategy      PASS
L0       Verification Ontology                        NEXT  ← current focus
P0a.5    Supply Chain Consistency Model               NEXT
  P0a.5a  Definition of Consistency
  P0a.5b  Boundary of Verifiability
  P0a.5c  Matching & Tolerance Methodology
P0b      Extraction Schema v0
P0c      Matching + Tolerance Contract v0
P0d      Verdict Contract v0
P1       Gate Runtime
```

**任何对 P0b / P0c / P0d / P1 的提前产出都不允许。**

---

## 3. Hard Constraints (locked)

### 3.1 8-Column Worksheet 结构锁定

```
1. Serenity Question
2. Assertion
3. Extraction Field
4. Evidence Source
5. Matching Rule
6. Tolerance
7. Verdict
8. Conflict Source
```

**Question ≠ Assertion 必须分离**。一个 Question 拆出 ≥1 个 Assertion，Aggregation Function 当前 TBD。简化合并会被打回。

### 3.2 P0a.5b 必须按 3 类拆（防 methodology 升级为 evidence 的核心闸门）

| 子类 | 含义 | 处理方式 |
|---|---|---|
| **a** 永远无法验证 | 管理层能力、研发文化、战略执行力、未来技术路线 | **禁止**升级为 evidence；Report Assembly 不得基于此得出结论 |
| **b** 当前数据源覆盖不到 | 海外非中港台上市公司、非上市公司内部数据、商业秘密客户清单 | 标记 `deferred_not_available`；数据源扩展时 revisit |
| **c** 理论可验但 cost 太高 | 海关逐单、招投标全量历史、工商变更全量 | 标记 `gated_by_cost`；user 显式 opt-in 才跑 |

不拆 3 类会被打回。

### 3.3 Verdict 5 状态（locked）

```
verified              找到支撑证据，cross-check 通过
tried_not_found       主动查询了，没找到支撑证据
not_attempted         还没查询（留 placeholder）
conflicting_evidence  找到反证
tolerance_unresolved  数据有，但 tolerance 边界外无法判定
```

### 3.4 Conflict Source 5 Subtype（locked，仅 Verdict = conflicting_evidence 时填）

```
direct_contradiction     A 说客户是 B，B 说不是
chain_contradiction      上游/下游整体链对不上
amount_contradiction     量级对不上
direction_contradiction  方向对不上（A 涨 B 跌）
timing_contradiction     跨期窗口对不上
```

**联动约束**：Verdict = `conflicting_evidence` → Conflict Source 必填；其他 Verdict → Conflict Source 必空。禁止 `verified + chain_contradiction` 这类自相矛盾。

---

## 4. Required Reading (do not duplicate)

- **L0 Verification Ontology v0 草稿**: `docs/L0_verification_ontology_v0_draft.md`
- **8 列 worksheet 模板**: `docs/8_column_worksheet_template_v0_draft.md`

读这两份后必须能回答：5 类 invariant、ListedCompany ≠ OperatingEntity 拆分理由、VerificationAttempt 不可变性、P0a.5b 三类边界。

---

## 5. Required Actions (Discovery Sprint)

### 5.1 Session 1: 90 分钟, 光伏/储能 case

- 选定 1 份真实研报（用户决定）
- 8 列 worksheet 填 2-3 个核心 assertion
- **至少 1 个 `[NEGATIVE TEST]` 断言**——故意挑故事明显有水分的方向，必须逼出 `conflicting_evidence`（SC2 硬条件）
- 记录 Open Question Q1/Q2/Q3/Q6 初步答案
- 验证 L0 entity / relation 在 case 1 下能稳定映射

### 5.2 Session 2: 90 分钟, 半导体设备 case

- 测 `direct_contradiction` 路径（设备厂 vs fab 设备采购清单）
- 验证 ontology 跨 case 稳定性
- 验证 SC1 初步迹象

### 5.3 Session 3: 90 分钟, 苹果链 case

- 测 `timing_contradiction` + `amount_contradiction`（Apple 财年 vs 立讯季度）
- 验证 5 种 Verdict 状态覆盖（SC2 硬条件：≥ 4 种）
- 验证 Aggregation Function 的可设计性（Q4）

### 5.4 Session 4: 60 分钟, Synthesis

- 3 case 横向对照
- 验证 SC1 / SC2 / SC3 全部通过
- 输出 P0a.5a / P0a.5b / P0a.5c 三个子文档初稿

---

## 6. Guardrails (禁止事项)

```
❌ 写 P0b Extraction Schema 契约（在 Session 4 之前）
❌ 写 P0c / P0d 契约
❌ 设计 Gate Runtime 任何部分
❌ 从 8 列 worksheet 直接产出契约
❌ 用 LLM "感觉对得上" 当 verified evidence
❌ 让 P0a.5b.a 项目（永远不可验证）成为证据基础
❌ 修改 8 列结构（列名/列序/列数）
❌ 简化 Question / Assertion 合并
❌ 跳过 negative assertion（SC2 硬条件）
```

---

## 7. Acceptance Criteria (hardcoded, 不达 = Sprint 不算完成)

```
SC1: 3 case 共用同一套 L0 entity / relation / property
     不允许一个 case 一套 entity/property 命名

SC2: 5 种 Verdict 至少覆盖 4 种
     conflicting_evidence 必须在 ≥1 个 case 真实出现

SC3: P0a.5b.a 至少列 5 个永远不可验证的具体问题
     且必须定义 Report Assembly 对每个问题的处理方式
     （沉默 / 标注 / 拒绝引用）
```

3 条全部通过才能进入 P0b 契约阶段。

---

## 8. After Discovery Sprint

Sprint 完成后，**下一个 directive** 会处理：
- P0a.5a / P0a.5b / P0a.5c 三个子文档冻结
- 然后 P0b / P0c / P0d 契约

当前指令**不预先规划**这些，由 sprint 结果决定。

---

## 9. Open Questions（Session 1 必须初步回答）

| # | 问题 | 影响 |
|---|---|---|
| Q1 | Product 粒度（SKU / category / tuple） | 所有 Type 1/2 matching 精度 |
| Q2 | EvidenceSource 是否抽象 | P0b 复杂度 |
| Q3 | Tolerance 怎么定（按金额/行业/claim_type） | P0c 默认值 |
| Q4 | Aggregation Function（多 Verdict 怎么聚） | P0d / Report Assembly |
| Q6 | ConflictSource 5 subtype 是否够 | P0d 字段 |
| Q7 | 海外 counterparty 怎么 match | 苹果链可验证性 |
| Q8 | 一对多分摊怎么算 | Type 1 matching |

不是所有问题 Session 1 都能解决，但必须**记录**哪些解决了、哪些推到后续 session。

---

## 10. Coordination

- **任务跟踪**: 已建 8 个 task（project tracking system），依赖链已设
- **架构决策**: 已写入 Engram, id `6798b8febcf7`
- **后续会话**: Session 1 完成后单独发 v1 directive 处理 P0a.5 冻结

---

## 11. Changelog

- 2026-06-08: v0 issued. Locks slice, 8 columns, P0a.5b 3-class, SC1/2/3. Supersedes any prior P0b planning.
