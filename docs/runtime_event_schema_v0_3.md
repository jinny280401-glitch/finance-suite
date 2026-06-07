# Runtime Event Schema v0.3

**日期**：2026-06-07  
**基准**：v0.2（research_runtime/events.py）  
**Sprint**：Sprint 3 — Section Workflow Contract

---

## 变更摘要

v0.3 在 v0.2 基础上新增 Section Workflow 专用事件类型。  
不修改现有 `RuntimeEvent` / `RuntimeEventLog` 数据结构，只扩展事件 `type` 枚举和 payload 规范。

---

## 1. 现有事件类型（v0.2，保持不变）

| type | payload 关键字段 | 说明 |
|------|----------------|------|
| state_entered | state | Workflow 状态机阶段切换 |
| provider_selected | provider, mode | Provider 选择 |
| evidence_retrieved | evidence_count | Evidence 检索完成 |
| context_built | — | Context 构建完成 |
| qc_completed | passed, evidence_count | QC 检查完成 |
| artifact_written | latest, events | Artifact 写入完成 |
| workflow_completed | state, qc_passed, evidence_count | Workflow 完成 |
| workflow_failed | error | Workflow 失败 |

---

## 2. 新增事件类型（v0.3）

### 2.1 Section 状态机事件

| type | payload 必填字段 | 说明 |
|------|----------------|------|
| `section_state_entered` | `section_id`, `state` | Section 进入新状态 |
| `section_skipped` | `section_id`, `reason`, `failed_dependency` | Section 因依赖失败被跳过 |
| `section_failed` | `section_id`, `reason` | Section 自身执行失败 |

**payload 示例 — section_state_entered**：

```json
{
  "section_id": "section:industry_overview",
  "state": "ANALYZE"
}
```

**payload 示例 — section_skipped**：

```json
{
  "section_id": "section:company_positioning",
  "reason": "dependency_skipped",
  "failed_dependency": "section:industry_overview"
}
```

---

### 2.2 Evidence Manifest 事件

| type | payload 必填字段 | 说明 |
|------|----------------|------|
| `section_manifest_built` | `section_id`, `manifest_count`, `blocked_count` | Manifest 构建完成（非空） |
| `section_manifest_empty` | `section_id` | Manifest 为空，Section 不得进入 ANALYZE |

**payload 示例 — section_manifest_built**：

```json
{
  "section_id": "section:company_positioning",
  "manifest_count": 2,
  "blocked_count": 0
}
```

**payload 示例 — section_manifest_empty**：

```json
{
  "section_id": "section:revenue_structure"
}
```

---

### 2.3 Section QC 事件

| type | payload 必填字段 | 说明 |
|------|----------------|------|
| `section_qc_passed` | `section_id`, `status`, `evidence_count` | Section QC 通过 |
| `section_qc_failed` | `section_id`, `status`, `missing_types` | Section QC 失败 |

**payload 示例 — section_qc_passed**：

```json
{
  "section_id": "section:industry_overview",
  "status": "partial",
  "evidence_count": 1
}
```

**payload 示例 — section_qc_failed**：

```json
{
  "section_id": "section:revenue_structure",
  "status": "failure",
  "missing_types": ["financials"]
}
```

---

### 2.4 Section 输出事件

| type | payload 必填字段 | 说明 |
|------|----------------|------|
| `section_output_written` | `section_id`, `citation_count`, `limitation_count` | Section 输出写入完成 |

**payload 示例**：

```json
{
  "section_id": "section:industry_overview",
  "citation_count": 2,
  "limitation_count": 1
}
```

---

## 3. 不变量

1. **所有 Section 事件 payload 必须包含 `section_id`**。  
   审计工具通过 `section_id` 追踪 Section 的完整生命周期。

2. **`section_manifest_empty` 触发后必须跟随 `section_state_entered(state=FAILED)`**。  
   不允许 manifest 为空后继续执行 ANALYZE。

3. **`section_skipped` 必须包含 `failed_dependency`**。  
   不允许用"unknown"作为 failed_dependency 值。

4. **`section_qc_failed` 必须包含 `missing_types`**。  
   空列表合法（表示缺失原因是 evidence 全为 failure，而非类型缺失）。

---

## 4. v0.3 与 v0.2 的兼容性

- v0.3 不修改 `RuntimeEvent` 数据结构。
- v0.3 不修改 `RuntimeEventLog` 接口。
- 新增事件类型使用相同的 `event_id` / `session_id` / `created_at` 字段。
- 已有消费端（Runtime Panel / smoke 工具）无需修改。

---

*本文档为 Runtime Event Schema v0.3 扩展定义，不包含代码变更。*
