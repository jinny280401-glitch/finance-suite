# Section Dependency Review

**日期**：2026-06-07  
**Sprint**：Sprint 3 Closure Review  
**状态**：只读审计 — 无代码变更，无设计变更

---

## 审计对象

`docs/section_workflow_contract_v0.md` §8 中定义的 11 个 Research Section 依赖图。

---

## 1. 环检测

**结论：NONE — DAG 无环**

依赖图为有向无环图（DAG），不存在任何循环依赖。  
所有 Section 均可按拓扑顺序执行。

---

## 2. 孤立 Section 检测

**结论：NONE — 无孤立节点**

所有 11 个 Section：
- 要么有 depends_on（被至少一个其他 Section 依赖）
- 要么自身是根节点（`section:industry_overview`，其他 Section 的依赖起点）

无任何 Section 既无 depends_on 又不被任何 Section 依赖。

---

## 3. 多父节点 Section（被 2+ Section 依赖）

| Section | 入度（in-degree） | 被哪些 Section 依赖 |
|---------|----------------|--------------------|
| `section:company_positioning` | **4** | revenue_structure, core_products, customer_structure, risk_factors |
| `section:industry_overview` | **3** | company_positioning, competitive_landscape, industry_environment |
| `section:revenue_structure` | **2** | growth_variables, management_track_record |

**观察**：

- `section:company_positioning` 是最高风险节点（入度 4）。
  如果该 Section FAILED 或 SKIPPED，下游 4 个 Section 全部 SKIPPED。

- `section:industry_overview` 是整个图的根节点（Level 0），入度 3。
  如果该 Section FAILED，除 `scenario_analysis` 外的所有非 Level-0 Section 均会受影响。

- `section:revenue_structure` 入度 2，是 growth_variables 和 management_track_record 的共同前置。

---

## 4. 最长依赖链

**长度：5**

```
section:industry_overview
  ↓
section:company_positioning
  ↓
section:revenue_structure
  ↓
section:growth_variables
  ↓
section:scenario_analysis
```

**含义**：在顺序执行模式下，`scenario_analysis` 必须等待 4 层前置 Section 全部完成。  
如果任何一层 FAILED，`scenario_analysis` 必然 SKIPPED。

---

## 5. 拓扑层次分布

| Level | Section | 说明 |
|-------|---------|------|
| **0** | industry_overview | 唯一根节点，全图起点 |
| **1** | company_positioning, competitive_landscape, industry_environment | 直接依赖根节点 |
| **2** | core_products, customer_structure, revenue_structure, risk_factors | 依赖 company_positioning |
| **3** | growth_variables, management_track_record | 依赖 revenue_structure |
| **4** | scenario_analysis | 全图最深节点，依赖 growth_variables + competitive_landscape |

---

## 6. 风险项

### Risk-1：industry_overview 单点故障

`section:industry_overview` 是唯一根节点，入度 3，是整个依赖图的单点故障。

- 如果 `industry_overview` FAILED → `company_positioning` SKIPPED → 下游 4 个 Level-2 Section 全部 SKIPPED → `growth_variables` / `management_track_record` SKIPPED → `scenario_analysis` SKIPPED
- 实际影响：**10 个 Section 中 9 个受影响**（仅 `competitive_landscape` / `industry_environment` 与 `industry_overview` 并行，但它们自身依赖 `industry_overview`，因此也 SKIPPED）

**含义**：`industry_overview` 的 evidence 可用性对整个 Report 最关键，应优先保障 `industry_data` 的 evidence 来源。

---

### Risk-2：scenario_analysis 脆弱性

`scenario_analysis` 依赖 2 条独立链路：

```
chain-A: industry_overview → company_positioning → revenue_structure → growth_variables
chain-B: industry_overview → competitive_landscape
```

两条链路任意一条断裂，`scenario_analysis` 即 SKIPPED。

**含义**：`scenario_analysis` 是整个 Report 中最脆弱的 Section，不应作为 Report 的必需 Section。建议在 Report Assembly Contract（Sprint 4B）中将其标注为 optional。

---

### Risk-3：company_positioning 是关键中间节点

入度 4，是 Level-1 中唯一的关键中间节点。

- 如果 `company_positioning` FAILED（例如 `quote` + `company_profile` evidence 均不可用）→ Level-2 的 4 个 Section 全部 SKIPPED

**含义**：`company_positioning` 的 QC 应该比其他 Level-1 Section 更宽松（例如：`quote` 缺失时只标记为 partial，不直接 FAILED），以避免大面积 cascade failure。

---

## 7. 审计结论

| 检查项 | 结果 |
|--------|------|
| 循环依赖 | ✅ NONE |
| 孤立节点 | ✅ NONE |
| 多父节点 | ✅ 存在，合理（非 bug） |
| 最长链长度 | ✅ 5（可接受） |
| 单点故障 | ⚠️ industry_overview（见 Risk-1） |
| 脆弱节点 | ⚠️ scenario_analysis（见 Risk-2） |
| 关键中间节点 | ⚠️ company_positioning（见 Risk-3） |

**整体判断**：

依赖图结构合理，无 Contract 层面的阻断问题。  
三个风险项均属于执行层风险（evidence 可用性），不是 Contract 定义错误。  
Sprint 4A 设计 Evidence Manifest 时应将 Risk-1 / Risk-2 纳入考量。

---

## 8. Sprint 4A 建议

根据本次审计，Evidence Manifest Contract 设计时需要关注：

1. **industry_overview 的 evidence 来源必须有明确的降级链**  
   `industry_data` 缺失时，`industry_overview` 应该能以 `partial` 状态完成，而非直接 FAILED。

2. **scenario_analysis 在 Report Assembly 中应标注为 optional**  
   不应因 `scenario_analysis` SKIPPED 导致整个 Report 阻断。

3. **company_positioning 的 required_evidence_types 应支持 partial 模式**  
   当 `quote` 或 `company_profile` 只有其一时，允许 `partial` 状态进入 ANALYZE。

---

*本文档为 Sprint 3 Closure Review 输出，纯审计结论，无代码变更，无设计变更。*
