# Report Assembly Contract v0

**日期**：2026-06-07  
**Sprint**：Sprint 4B  
**状态**：CONTRACT DRAFT — 纯定义，无 Runtime 实现，无 LLM，无生产变更

---

## 1. 一句话目标

Report 只能从 SectionOutput 合法拼装。  
Report Assembly 不接触 Evidence / Gateway / Provider raw data，只消费 Section 的最终产出。

---

## 2. ReportInput Contract

### 2.1 ReportInput Schema

```python
@dataclass
class ReportInput:
    report_id: str                          # 格式：report:<uuid-hex-8>
    symbol: str                             # 标的代码
    query: str                              # 研究问题
    section_outputs: list[SectionOutput]    # 所有 Section 的产出
    section_order: list[str]                # Section 出现在 Report 中的顺序
    created_at: str                         # Report 组装开始时间
```

### 2.2 不变量

1. `section_outputs` 中的每个 `SectionOutput` 必须有唯一的 `section_id`
2. `section_order` 中的每个 `section_id` 必须在 `section_outputs` 中存在
3. `section_outputs` 中不得包含 raw Evidence / Gateway Response / Provider Payload
4. ReportInput 的唯一 Evidence 入口是 `SectionOutput.citations`（间接引用）

### 2.3 禁止的字段

ReportInput 中不得出现：

```python
REPORT_FORBIDDEN = {
    "raw_evidence", "evidence_bundle", "evidence_bundles",
    "gateway_response", "provider_payload", "_qc", "raw", "payload",
}
```

---

## 3. ReportOutput Contract

### 3.1 ReportOutput Schema

```python
@dataclass
class ReportOutput:
    report_id: str                          # 对应 ReportInput.report_id
    symbol: str                             # 标的代码
    title: str                              # Report 标题
    body_sections: list[ReportSection]      # 正文（只包含 DONE section）
    assembly_warnings: list[AssemblyWarning]  # FAILED / SKIPPED / partial 的警告
    citation_index: list[CitationIndexEntry]  # 全局引用索引
    assembly_qc: AssemblyQC                 # Assembly-level QC
    created_at: str                         # Report 生成完成时间
```

### 3.2 ReportSection

```python
@dataclass(frozen=True)
class ReportSection:
    section_id: str                         # 对应 SectionOutput.section_id
    title: str                              # Section 标题
    body: str                               # Section 正文（来自 SectionOutput.body）
    citation_ids: list[str]                 # 该 Section 使用的 citation_id 列表
    qc_status: str                          # SectionOutput.qc.status
    limitations: list[str]                  # SectionOutput.limitations
```

**不变量**：

- `body` 直接来自 `SectionOutput.body`，Report Assembly 不修改正文内容
- `citation_ids` 直接来自 `SectionOutput.citations` 的 `citation_id` 列表
- 只有 `SectionOutput.status == DONE` 的 Section 才能进入 `body_sections`

---

## 4. Section Ordering 规则

### 4.1 排序依据

`section_order` 定义了 Section 在 Report 中出现的顺序。

默认顺序（与依赖图拓扑排序一致）：

```python
DEFAULT_SECTION_ORDER = [
    "section:industry_overview",
    "section:company_positioning",
    "section:competitive_landscape",
    "section:industry_environment",
    "section:revenue_structure",
    "section:core_products",
    "section:customer_structure",
    "section:risk_factors",
    "section:growth_variables",
    "section:management_track_record",
    "section:scenario_analysis",
]
```

### 4.2 规则

1. `section_order` 中只包含 `status == DONE` 的 Section
2. `status == FAILED` / `SKIPPED` 的 Section 不出现在 `section_order` 中
3. 如果某个 Section 不在 `section_order` 中但 `status == DONE`，视为 Contract 违规（防止静默丢弃）

---

## 5. Missing / FAILED / SKIPPED Section 处理规则

### 5.1 AssemblyWarning Schema

```python
@dataclass(frozen=True)
class AssemblyWarning:
    section_id: str                         # 受影响的 Section ID
    status: str                             # "FAILED" / "SKIPPED" / "PARTIAL"
    reason: str                             # 人类可读的原因
    impact: str                             # 对 Report 完整性的影响描述
```

### 5.2 处理规则

| SectionOutput.status | 处理方式 | 进入 body_sections? | 进入 assembly_warnings? |
|---------------------|---------|--------------------|-----------------------|
| DONE | 正常纳入正文 | ✅ 是 | ❌ 否 |
| DONE（qc.status="partial"） | 纳入正文 + 警告 | ✅ 是 | ✅ 是（标记 PARTIAL） |
| FAILED | 不纳入正文，必须警告 | ❌ 否 | ✅ 是 |
| SKIPPED | 不纳入正文，必须警告 | ❌ 否 | ✅ 是 |

### 5.3 禁止静默丢弃

**红线**：FAILED / SKIPPED section 不得静默丢弃。

如果一个 SectionOutput 的 `status` 是 FAILED 或 SKIPPED，它必须出现在 `assembly_warnings` 中。  
Report Assembly 不允许"忽略"任何 Section — 要么展示其正文（DONE），要么披露其缺失原因（FAILED / SKIPPED）。

---

## 6. Citation Index 聚合规则

### 6.1 CitationIndexEntry Schema

```python
@dataclass(frozen=True)
class CitationIndexEntry:
    citation_id: str                        # 全局唯一 Citation ID
    evidence_id: str                        # 对应的 Evidence ID
    section_id: str                         # 引用来自哪个 Section
    field_used: str                         # 引用了哪个字段
    provider: str                           # Provider 名称
```

### 6.2 聚合规则

1. 遍历所有 `status == DONE` 的 `SectionOutput.citations`
2. 为每个 Citation 创建一条 `CitationIndexEntry`，附加 `section_id`
3. `citation_id` 全局唯一（如果两个 Section 引用了同一个 Evidence 的同一个字段，仍然是两条不同的 CitationIndexEntry）
4. FAILED / SKIPPED Section 的 citations 不进入 Citation Index

### 6.3 Citation Index 用途

- 用户可通过 Citation Index 查看 Report 引用了哪些 Evidence
- 每个 `evidence_id` 可通过 Lineage Store 追溯到 Provider（继承 Sprint 4A）
- Citation Index 是 Report 的"参考文献列表"

---

## 7. Assembly QC Contract

### 7.1 AssemblyQC Schema

```python
@dataclass
class AssemblyQC:
    passed: bool                            # 是否通过 Assembly QC
    status: str                             # "success" / "partial" / "failure"
    total_sections: int                     # Section 总数
    done_sections: int                      # DONE Section 数量
    failed_sections: int                    # FAILED Section 数量
    skipped_sections: int                   # SKIPPED Section 数量
    partial_sections: int                   # DONE 但 qc.status="partial" 的数量
    citation_count: int                     # Citation Index 总条目数
    has_critical_section_missing: bool      # 关键 Section 是否缺失
    warnings: list[str]                     # QC 警告列表
```

### 7.2 QC 规则

| 条件 | status | passed |
|------|--------|--------|
| 所有 Section 均 DONE，无 partial | success | True |
| 所有 Section 均 DONE，部分 partial | partial | True |
| 有 FAILED / SKIPPED，但关键 Section 全部 DONE | partial | True |
| 关键 Section 缺失（FAILED / SKIPPED） | failure | False |
| 0 个 Section DONE | failure | False |

### 7.3 关键 Section 定义

以下 Section 为关键 Section（Report 的必要组成部分）：

```python
CRITICAL_SECTIONS = [
    "section:industry_overview",
    "section:company_positioning",
]
```

如果任意 CRITICAL_SECTIONS 中的 Section 不是 DONE，`has_critical_section_missing = True`，`passed = False`。

非关键 Section（scenario_analysis 等）缺失时 Report 仍可发布，但 `status = "partial"`。

---

## 8. Runtime Event 最小扩展

### 8.1 Report Assembly 事件

```python
ASSEMBLY_EVENTS = {
    "report_assembly_started":    {"report_id": str, "total_sections": int},
    "report_section_included":    {"report_id": str, "section_id": str},
    "report_section_excluded":    {"report_id": str, "section_id": str, "status": str, "reason": str},
    "report_citation_indexed":    {"report_id": str, "citation_count": int},
    "report_assembly_qc":         {"report_id": str, "status": str, "passed": bool},
    "report_assembly_completed":  {"report_id": str, "done_sections": int, "warning_count": int},
}
```

### 8.2 不变量

- 所有 Assembly 事件 payload 必须包含 `report_id`
- `report_section_excluded` 必须包含 `reason`（不得为空字符串）
- `report_assembly_completed` 必须在所有 section 处理完成后触发

---

## 9. 红线

| 红线 | 来源 |
|------|------|
| Report 只能消费 SectionOutput，不得消费 Evidence / Gateway / Provider raw data | 本 Contract §2 |
| 只有 `status == DONE` 的 SectionOutput 才能进入 `body_sections` | 本 Contract §5.2 |
| FAILED / SKIPPED section 必须进入 `assembly_warnings`，不得静默丢弃 | 本 Contract §5.3 |
| Citation Index 必须从 `SectionOutput.citations` 聚合，不得从其他来源获取 | 本 Contract §6.2 |
| ReportOutput 必须带 `assembly_qc` | 本 Contract §7.1 |
| raw Gateway Response 不得出现在 ReportInput / ReportOutput | 本 Contract §2.3 |

---

## 10. 与上游 Contract 的关系

```text
Trust Gate Contract
  ↓ 输出 EvidenceBundle
Evidence Manifest Contract (Sprint 4A)
  ↓ 输出 EvidenceManifest → Section 消费
Section Workflow Contract (Sprint 3)
  ↓ 输出 SectionOutput
Report Assembly Contract (本文档, Sprint 4B)
  ↓ 输出 ReportOutput
```

Report Assembly 不直接依赖 Trust Gate 或 Evidence Manifest。  
它只消费 SectionOutput — 所有信任边界已由上游 Contract 保障。

---

*本文档为 Report Assembly Contract v0，纯定义，无代码实现。*
