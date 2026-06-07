# Citation Contract v0

**日期**：2026-06-07  
**Sprint**：Sprint 4A  
**状态**：CONTRACT DRAFT — 纯定义，无 Runtime 实现

---

## 1. 一句话目标

Section Output 中的每一个事实主张（claim）必须通过 Citation 回溯到 Evidence。  
Citation 是 Section Output 与 Evidence 之间的绑定记录。

---

## 2. Citation Schema

```python
@dataclass(frozen=True)
class Citation:
    citation_id: str               # 格式：cite:<uuid-hex-8>
    evidence_id: str               # 对应 Evidence.evidence_id
    field_used: str                # 引用了 Evidence.data 中的哪个字段
    provider: str                  # 该 Evidence 的 provider（冗余，用于快速展示）
```

**v0 不包含**：

- ❌ `url`（URL 属于 UI 层，不属于 Contract 层）
- ❌ `page_number`（Report 尚未分页）
- ❌ `quote`（引用原文属于 LLM 输出解析，不属于 Contract 层）
- ❌ `line_range`（行范围属于 Renderer 层）

**v0 保证**：

- ✅ 任意 Citation 必须能回溯到一个 Evidence（通过 `evidence_id`）
- ✅ Citation 必须指明引用了哪个字段（通过 `field_used`）
- ✅ Citation 不依赖 raw Gateway Response

---

## 3. Citation 与 Evidence 的绑定规则

### 3.1 合法 Citation

一个 Citation 合法当且仅当：

1. `citation.evidence_id` 存在于当前 Section 的 `EvidenceManifest.evidences` 中
2. `citation.field_used` 存在于对应 `Evidence.data` 的 key 中
3. 对应 Evidence 的 `qc_status` 不是 `"failure"`

### 3.2 非法 Citation

以下情况视为 Contract 违规：

| 情况 | 原因 |
|------|------|
| `evidence_id` 不在当前 Section 的 Manifest 中 | Section 引用了不属于自己的 Evidence |
| `field_used` 不在对应 Evidence.data 中 | 引用了不存在的字段（可能是 blocked_field） |
| 对应 Evidence 的 `qc_status == "failure"` | 引用了不可信 Evidence |
| `evidence_id` 指向 raw Gateway Response | 绕过了 Trust Gate |

---

## 4. Section Output 中的 Citation 使用

### 4.1 SectionOutput.citations 规则

```python
@dataclass
class SectionOutput:
    ...
    citations: list[Citation]          # 必须存在，不得为 None
    used_evidence_ids: list[str]       # 实际使用的 evidence_id 列表
    ...
```

**规则**：

1. `citations` 列表中的每个 `citation.evidence_id` 必须出现在 `used_evidence_ids` 中
2. `used_evidence_ids` 中的每个 ID 必须在当前 Section 的 Manifest 中找到对应 Evidence
3. `status == SKIPPED` 时，`citations` 为空列表
4. `status == DONE` 时，`citations` 可以为空列表（例如：Section 未引用任何具体数据字段）

### 4.2 Citation 数量

v0 不强制最少 Citation 数量。

**理由**：某些 Section 可能基于 Evidence 的整体存在性做判断，而非引用具体字段。  
例如：`section:industry_environment` 可能仅因为 `industry_data` 存在而生成概述，不引用具体 PE/Revenue 字段。

后续可通过 SectionQC 的 `min_citation_count` 规则升级约束。

---

## 5. Citation 验证函数签名

```python
def validate_citations(
    citations: list[Citation],
    manifest: EvidenceManifest,
) -> list[str]:
    """验证所有 Citation 的合法性，返回违规列表（空列表 = 全部合法）"""
    ...
```

**验证内容**：

1. `citation.evidence_id` 在 `manifest.evidences` 中存在
2. `citation.field_used` 在对应 `Evidence.data` 中存在
3. 对应 Evidence 的 `qc_status != "failure"`

---

## 6. 红线

| 红线 | 来源 |
|------|------|
| Citation 必须通过 `evidence_id` 回溯到 Evidence | 本 Contract §3.1 |
| Citation 不得引用不在当前 Manifest 中的 Evidence | 本 Contract §3.2 |
| Citation 不得引用 `qc_status == "failure"` 的 Evidence | Trust Gate Contract §3 |
| `citations` 字段不得为 `None` | Section Workflow Contract §3.2 |

---

*本文档为 Citation Contract v0，纯定义，无代码实现。*
