# Evidence Manifest Contract v0

**日期**：2026-06-07  
**Sprint**：Sprint 4A  
**状态**：CONTRACT DRAFT — 纯定义，无 Runtime 实现，无 LLM，无生产变更

---

## 1. 一句话目标

Section 只能通过 Evidence Manifest 消费 Evidence。  
Manifest 是 Section 看到的唯一 Evidence 入口。

---

## 2. Evidence Contract

### 2.1 Evidence ID 规则

唯一标识为 `evidence_id`，格式：

```
evidence:<uuid-hex-8>
```

**不用**：`provider_id`、`source_id`、`citation_id`、`manifest_id`。

**理由**：

- 多个 provider 可以产出同一个 evidence（例如：Wind 和 JoinQuant 都能提供 PE）
- evidence_id 是逻辑标识，代表"一份已通过 Trust Gate 的事实"
- provider_id 是来源标识，一个 evidence 可以关联多个 provider（降级场景）

---

### 2.2 Evidence 最小 Schema

```python
@dataclass(frozen=True)
class Evidence:
    evidence_id: str               # 格式：evidence:<uuid-hex-8>
    title: str                     # 简短标题（例如："贵州茅台 基本面快照"）
    summary: str                   # 一句话摘要
    provider: str                  # 最终提供数据的 provider 名称
    provider_tier: int             # 信源层级（1-4）
    qc_status: str                 # "success" / "partial" / "failure"
    allowed_use: list[str]         # Trust Gate 输出的权限白名单
    blocked_fields: list[str]      # Trust Gate 删除的字段列表
    data: dict[str, Any]           # 清洗后的事实数据（不含 _qc / raw / payload）
    as_of: str | None              # 数据时间戳（ISO 8601）
    created_at: str                # Evidence 创建时间戳
```

**禁止出现的字段**：

```python
FORBIDDEN_FIELDS = {"raw_response", "gateway_response", "provider_payload", "_qc", "raw", "payload"}
```

Evidence 中不得包含上述任何字段。如果存在，视为 Contract 违规。

---

### 2.3 Evidence 与 EvidenceBundle 的关系

```text
EvidenceBundle（Trust Gate 输出）
  ↓ 赋予 evidence_id + title + summary
Evidence（Manifest 消费的最终形态）
```

**转换规则**：

```python
def bundle_to_evidence(bundle: EvidenceBundle, evidence_id: str, title: str, summary: str) -> Evidence:
    """将 Trust Gate 输出转换为 Manifest 可消费的 Evidence"""
    return Evidence(
        evidence_id=evidence_id,
        title=title,
        summary=summary,
        provider=bundle.source.get("provider", "unknown"),
        provider_tier=bundle.source.get("provider_tier", 0),
        qc_status=bundle.trust_status,
        allowed_use=bundle.allowed_use,
        blocked_fields=bundle.blocked_fields,
        data=bundle.evidence,
        as_of=bundle.source.get("as_of"),
        created_at=<current_timestamp>,
    )
```

**不变量**：

- 转换后 `Evidence.data` 中不得包含任何 `FORBIDDEN_FIELDS` 中的字段
- `Evidence.qc_status` 直接继承 `EvidenceBundle.trust_status`，不重新计算

---

## 3. Manifest Contract

### 3.1 EvidenceManifest Schema

```python
@dataclass
class EvidenceManifest:
    manifest_id: str               # 格式：manifest:<uuid-hex-8>
    section_id: str                # 目标 Section ID
    evidences: list[Evidence]      # 该 Section 可用的 Evidence 列表
    created_at: str                # Manifest 创建时间戳
```

**不变量**：

1. `evidences` 列表中的每个 `Evidence` 必须有唯一的 `evidence_id`
2. `evidences` 列表中不得包含 `qc_status == "failure"` 且 `allowed_use == []` 的 Evidence（Trust Gate 已拦截的不应进入 Manifest）
3. Section 只能通过 `EvidenceManifest.evidences` 访问 Evidence，不得绕过 Manifest 直接访问 EvidenceBundle 或 Gateway Response
4. `manifest_id` 全局唯一，不可复用

---

### 3.2 Manifest 构建规则

```text
ResearchSession.evidence_bundles (list[EvidenceBundle])
  ↓ bundle_to_evidence() 转换
Evidence Pool
  ↓ 按 section 的 required_evidence_types + allowed_use_filter 筛选
EvidenceManifest (per section)
```

**筛选规则**：

1. `Evidence.qc_status == "failure"` 且 `Evidence.allowed_use == []` → 不进入 Manifest
2. `Evidence.allowed_use` 与 `Section.allowed_use_filter` 无交集 → 不进入该 Section 的 Manifest
3. 通过筛选的 Evidence 按 `provider_tier` 升序排列（Tier 1 优先）

**结果**：

- Manifest 为空 → Section 不得进入 ANALYZE（继承 Sprint 3 §2 红线）
- Manifest 非空 → Section 可进入 ANALYZE

---

### 3.3 Manifest 与 Sprint 3 的兼容性

Sprint 3 中定义的 `EvidenceManifestEntry` 在 Sprint 4A 中被 `EvidenceManifest` + `Evidence` 替代：

| Sprint 3 | Sprint 4A | 说明 |
|-----------|-----------|------|
| `EvidenceManifestEntry.manifest_id` | `EvidenceManifest.manifest_id` | 提升为 Manifest 级别 ID |
| `EvidenceManifestEntry.evidence_bundle` | `Evidence`（从 bundle 转换） | 不再直接持有 EvidenceBundle |
| `EvidenceManifestEntry.evidence_type` | `Evidence.title` + Section 的 `required_evidence_types` 匹配 | 类型标签外移 |

---

## 4. Section 消费 Manifest 的规则

```text
Section 收到 EvidenceManifest
  ↓
只能读取 manifest.evidences[n].data
只能读取 manifest.evidences[n].allowed_use
只能读取 manifest.evidences[n].title / summary / provider
  ↓
不得读取 raw EvidenceBundle
不得读取 Gateway Response
不得读取 Provider Payload
```

**接口约束**：

```python
def build_section_context(manifest: EvidenceManifest) -> SectionContext:
    """Section 唯一合法的 Evidence 消费入口"""
    if not isinstance(manifest, EvidenceManifest):
        raise TypeError("build_section_context requires EvidenceManifest")
    ...
```

---

## 5. 红线

| 红线 | 来源 |
|------|------|
| Evidence 中不得包含 `_qc` / `raw` / `payload` / `raw_response` / `gateway_response` / `provider_payload` | Trust Gate Contract §6 |
| Section 不得绕过 Manifest 访问 EvidenceBundle | 本 Contract §4 |
| Trust Gate 已拦截的 Evidence（`allowed_use == []`）不得进入 Manifest | 本 Contract §3.2 |
| `evidence_id` 全局唯一，不可复用 | 本 Contract §2.1 |
| Manifest 为空时 Section 不得进入 ANALYZE | Section Workflow Contract §2 |

---

*本文档为 Evidence Manifest Contract v0，纯定义，无代码实现。*
