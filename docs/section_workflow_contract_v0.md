# Section Workflow Contract v0

**日期**：2026-06-07  
**Sprint**：Sprint 3  
**状态**：CONTRACT DRAFT — 纯定义，无 Runtime 实现，无 LLM，无生产变更

---

## 1. 一句话目标

Section 是 Research Runtime 的最小执行单元。  
每个 Section 只能消费 EvidenceBundle，必须产出带 QC + Citations 的 SectionOutput，且永远不能接触 raw Gateway Response。

---

## 2. Section 状态机

Section 生命周期由状态机管理，状态只能单向推进。

```
PENDING
  ↓ (依赖满足 + evidence manifest 存在)
READY
  ↓ (开始执行)
RETRIEVING
  ↓ (evidence 收集完成)
ANALYZE
  ↓ (LLM 占位 / 真实 LLM 完成)
QC
  ↓ (QC 通过)
DONE

特殊路径：
PENDING → SKIPPED   (depends_on 失败时)
任意状态 → FAILED   (非预期错误时)
```

**状态转移规则**：

| 当前状态 | 允许的下一状态 | 条件 |
|---------|--------------|------|
| PENDING | READY | 所有 depends_on 的 section 均为 DONE |
| PENDING | SKIPPED | 任意 depends_on 的 section 为 SKIPPED 或 FAILED |
| READY | RETRIEVING | 开始收集 evidence |
| RETRIEVING | ANALYZE | evidence manifest 非空，且至少一个 EvidenceBundle 存在 |
| RETRIEVING | FAILED | evidence manifest 为空（无可用 evidence） |
| ANALYZE | QC | LLM stub / 真实 LLM 完成 |
| QC | DONE | QC 通过 |
| QC | FAILED | QC 不通过（evidence 不足 / trust_status 全为 failure） |
| 任意 | FAILED | 非预期异常 |

**不变量**：

- `ANALYZE` 阶段不得开始，如果 `section.evidence_manifest` 为空。
- `SKIPPED` section 不得被视为 `DONE`（不能被下游 depends_on 的 section 当作满足条件）。
- raw Gateway Response 不得出现在 `SectionInput.evidence` 中。

---

## 3. Section 输入 / 输出 Schema

### 3.1 SectionInput

```python
@dataclass(frozen=True)
class SectionInput:
    section_id: str                          # Section 唯一 ID，格式：section:<name>
    symbol: str                              # 标的代码
    query: str                               # 研究问题
    evidence_manifest: list[EvidenceManifestEntry]  # 必须非空才能进入 ANALYZE
    allowed_use_filter: list[str]            # 只接受哪些 allowed_use 的 EvidenceBundle
    required_evidence_types: list[str]       # 必须存在的 evidence 类型
    optional_evidence_types: list[str]       # 可选的 evidence 类型

@dataclass(frozen=True)
class EvidenceManifestEntry:
    manifest_id: str                         # Manifest 条目唯一 ID，格式：manifest:<uuid>
    evidence_bundle: EvidenceBundle          # 必须是 EvidenceBundle，不得是 raw dict
    evidence_type: str                       # 数据类型（quote / financials / macro_snapshot 等）
    as_of: str | None                        # 数据时间戳
```

**不变量**：

- `EvidenceManifestEntry.evidence_bundle` 必须是 `EvidenceBundle` 实例，否则拒绝。
- `SectionInput.evidence_manifest` 为空时，Section 不得进入 `ANALYZE`。
- `EvidenceBundle.trust_status == "failure"` 的条目可以存在于 manifest，但不得贡献 evidence。

---

### 3.2 SectionOutput

```python
@dataclass
class SectionOutput:
    section_id: str                          # 对应 SectionInput.section_id
    status: SectionStatus                    # DONE / FAILED / SKIPPED
    qc: SectionQC                            # QC 结果（见第 5 节）
    body: str                                # Section 正文（LLM 输出 / stub）
    citations: list[SectionCitation]         # 引用列表（必须存在，可为空）
    used_evidence_ids: list[str]             # 实际使用的 manifest_id 列表
    limitations: list[str]                   # 限制披露（partial / failure evidence 的声明）
    created_at: str                          # 生成时间戳
```

**不变量**：

- `citations` 字段必须存在，不得为 `None`（可为空列表）。
- `used_evidence_ids` 中的每个 ID 必须能在 `SectionInput.evidence_manifest` 中找到对应条目。
- `status == SKIPPED` 时，`body` 为空字符串，`citations` 为空列表。
- `status == FAILED` 时，`body` 为空字符串，`qc.passed == False`。

---

### 3.3 SectionCitation

```python
@dataclass(frozen=True)
class SectionCitation:
    citation_id: str                         # 引用唯一 ID，格式：cite:<uuid>
    manifest_id: str                         # 对应 EvidenceManifestEntry.manifest_id
    field_used: str                          # 使用的字段名（例如：pe / revenue / gdp）
    allowed_use_observed: str                # 实际使用时对应的 allowed_use 值
```

---

## 4. depends_on 依赖规则

### 4.1 定义

```python
@dataclass
class SectionDependency:
    section_id: str                          # 依赖的 section_id
    require_status: SectionStatus = SectionStatus.DONE  # 默认：必须 DONE
```

一个 Section 可以有 0 到 N 个 `depends_on`。

### 4.2 规则

**规则 1：依赖必须在 PENDING 阶段检查**

Section 从 `PENDING` 推进时，先检查所有 `depends_on`：
- 所有依赖均为 `DONE` → 可进入 `READY`
- 任意依赖为 `SKIPPED` 或 `FAILED` → 当前 section 进入 `SKIPPED`

**规则 2：SKIPPED 不等于 DONE**

如果 Section A depends_on Section B，而 Section B 是 `SKIPPED`，则 Section A 也必须是 `SKIPPED`。  
不能让 `SKIPPED` 的依赖通过检查。

**规则 3：循环依赖不允许**

如果 Section A depends_on Section B，且 Section B depends_on Section A，这是无效配置。
验证时必须检测循环依赖并报错。

**规则 4：依赖失败传播**

```text
Section B → FAILED
Section A (depends_on B) → SKIPPED（不是 FAILED）
```

`SKIPPED` 代表"因依赖未满足而跳过"，不是"自身执行失败"。

### 4.3 示例

```python
# 行业速览不依赖任何 Section
industry_overview = SectionWorkflow(
    section_id="section:industry_overview",
    depends_on=[],
    ...
)

# 公司定位依赖行业速览完成
company_positioning = SectionWorkflow(
    section_id="section:company_positioning",
    depends_on=[SectionDependency("section:industry_overview")],
    ...
)

# 情景推演依赖公司定位和行业速览
scenario_analysis = SectionWorkflow(
    section_id="section:scenario_analysis",
    depends_on=[
        SectionDependency("section:company_positioning"),
        SectionDependency("section:industry_overview"),
    ],
    ...
)
```

---

## 5. Section QC Contract 对接点

### 5.1 SectionQC 结构

```python
@dataclass
class SectionQC:
    passed: bool                             # 是否通过 QC
    status: str                              # "success" / "partial" / "failure"
    evidence_count: int                      # 实际使用的 evidence 数量
    evidence_all_real: bool                  # 所有 evidence 是否来自 REAL provider
    has_fallback_evidence: bool              # 是否包含 FALLBACK provider 的 evidence
    has_mock_evidence: bool                  # 是否包含 MOCK provider 的 evidence
    missing_required_types: list[str]        # 缺失的必需 evidence 类型
    blocked_evidence_count: int              # 被 Trust Gate 拦截的 evidence 数量
    limitations: list[str]                   # 需要披露的限制
```

### 5.2 QC 规则

| 条件 | QC status | passed |
|------|-----------|--------|
| 所有 required_evidence_types 存在，全部 REAL provider | success | True |
| required_evidence_types 全存在，含 FALLBACK provider | partial | True |
| required_evidence_types 存在，含 MOCK provider | partial | False（不可生产发布） |
| 任意 required_evidence_type 缺失 | failure | False |
| evidence_manifest 为空 | failure | False（不得进入 ANALYZE） |

### 5.3 与 Trust Gate Contract 的对接点

- SectionQC 不重新评估 `EvidenceBundle.trust_status`，只读取它。
- Trust Gate 的 `allowed_use` 决定 evidence 能用于什么，SectionQC 决定 Section 能否生产发布。
- 如果 `EvidenceBundle.trust_status == "failure"` 的 evidence 进入 manifest，SectionQC 应将其计入 `blocked_evidence_count`，不计入 `evidence_count`。

---

## 6. Runtime Event 最小事件清单

Section Workflow 执行过程中，必须能通过事件追踪 `section_id`。

### 6.1 必需事件

```python
SECTION_EVENTS = {
    # Section 状态机事件
    "section_state_entered":     {"section_id": str, "state": str},
    "section_skipped":           {"section_id": str, "reason": str, "failed_dependency": str},
    "section_failed":            {"section_id": str, "reason": str},

    # Evidence Manifest 事件
    "section_manifest_built":    {"section_id": str, "manifest_count": int, "blocked_count": int},
    "section_manifest_empty":    {"section_id": str},  # 触发 RETRIEVING → FAILED

    # QC 事件
    "section_qc_passed":         {"section_id": str, "status": str, "evidence_count": int},
    "section_qc_failed":         {"section_id": str, "status": str, "missing_types": list},

    # 输出事件
    "section_output_written":    {"section_id": str, "citation_count": int, "limitation_count": int},
}
```

### 6.2 不变量

- 所有 Section 事件的 payload 必须包含 `section_id`。
- `section_skipped` 事件必须包含 `failed_dependency`（哪个依赖失败导致跳过）。
- `section_manifest_empty` 事件触发后，Section 必须进入 `FAILED`，不得进入 `ANALYZE`。

---

## 7. 红线（Hard Constraints）

以下约束继承自 Trust Gate Contract，在 Section 层必须强制执行：

| 红线 | 来源 |
|------|------|
| raw Gateway Response 不得出现在 `SectionInput.evidence_manifest` 中 | Trust Gate Contract §6 |
| `EvidenceBundle.trust_status == "failure"` 的条目不得贡献 `body` 内容 | Trust Gate Contract §3 |
| `MOCK` provider 的 evidence 不得用于生产发布的 Section | Trust Gate Contract ProviderClass |
| `evidence_manifest` 为空时不得进入 `ANALYZE` | 本 Contract §2 |
| `SKIPPED` 不得被视为 `DONE` | 本 Contract §4.2 |
| `SectionOutput.citations` 不得为 `None` | 本 Contract §3.2 |

---

## 8. 11 个 Research Section 的 Contract 概要

| section_id | 必需 evidence 类型 | 可选 evidence 类型 | depends_on |
|---|---|---|---|
| section:industry_overview | industry_data | macro_snapshot | — |
| section:company_positioning | quote, company_profile | — | section:industry_overview |
| section:revenue_structure | financials | — | section:company_positioning |
| section:core_products | company_profile | — | section:company_positioning |
| section:customer_structure | company_profile | financials | section:company_positioning |
| section:competitive_landscape | peers | industry_data | section:industry_overview |
| section:industry_environment | industry_data | macro_snapshot | section:industry_overview |
| section:growth_variables | financials | consensus | section:revenue_structure |
| section:risk_factors | company_profile, financials | macro_snapshot | section:company_positioning |
| section:management_track_record | financials | consensus | section:revenue_structure |
| section:scenario_analysis | financials, peers | consensus, macro_snapshot | section:growth_variables, section:competitive_landscape |

---

## 附录：Contract 版本边界

**v0 范围**：

- ✅ Section 状态机定义
- ✅ SectionInput / SectionOutput / SectionCitation schema
- ✅ depends_on 规则
- ✅ Evidence Manifest 引用方式
- ✅ SectionQC Contract 对接点
- ✅ Runtime Event 最小清单
- ✅ 11 个 Section 概要

**v0 不包括**：

- ❌ LLM Prompt Builder 实现
- ❌ Report Assembly Contract
- ❌ Action Gate Contract
- ❌ Meta Workflow Runtime
- ❌ 生产路由变更
- ❌ UI 变更

---

*本文档为 Section Workflow Contract v0，纯定义，无代码实现。*
