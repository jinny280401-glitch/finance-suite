# Evidence Lineage Contract v0

**日期**：2026-06-07  
**Sprint**：Sprint 4A  
**状态**：CONTRACT DRAFT — 纯定义，无 Runtime 实现

---

## 1. 一句话目标

任意 Citation 必须追溯到 Evidence，任意 Evidence 必须追溯到 Trust Gate，任意 Trust Gate 必须追溯到 Provider。

这条链路是 Finance Suite 的事实可信性基础。

---

## 2. 完整 Lineage 链路

```text
Provider（Wind / Tushare / JoinQuant / AkShare）
  ↓
Gateway Response（FinanceDataResponse + _qc）
  ↓
Trust Gate（build_evidence_bundle）
  ↓
EvidenceBundle（trust_status / allowed_use / blocked_fields）
  ↓
Evidence（evidence_id / title / summary / data）
  ↓
EvidenceManifest（per section 筛选后的 Evidence 列表）
  ↓
Citation（citation_id → evidence_id → field_used）
  ↓
Section Output（body 正文 + citations 列表）
```

---

## 3. Lineage Record Schema

```python
@dataclass(frozen=True)
class EvidenceLineage:
    evidence_id: str               # 对应 Evidence.evidence_id
    provider: str                  # 原始 Provider 名称
    provider_tier: int             # 信源层级（1-4）
    gateway_timestamp: str         # Gateway Response 的时间戳
    trust_gate_status: str         # Trust Gate 输出的 trust_status
    trust_gate_reason: str | None  # Trust Gate 给出的 reason
    trust_gate_blocked_fields: list[str]  # Trust Gate 删除的字段
    allowed_use: list[str]         # Trust Gate 输出的权限白名单
    as_of: str | None              # 数据口径时间
```

**用途**：

给定任意一个 `evidence_id`，通过 `EvidenceLineage` 可以回答：

1. **数据来自哪个 Provider？** → `lineage.provider`
2. **Provider 的可信等级？** → `lineage.provider_tier`
3. **什么时候从 Gateway 获取的？** → `lineage.gateway_timestamp`
4. **Trust Gate 的判定结果？** → `lineage.trust_gate_status`
5. **哪些字段被 Trust Gate 删除了？** → `lineage.trust_gate_blocked_fields`
6. **这份 Evidence 能用于什么？** → `lineage.allowed_use`
7. **数据本身的口径时间？** → `lineage.as_of`

---

## 4. Lineage 追溯规则

### 4.1 正向追溯（Provider → Section Output）

```text
给定 provider="wind", symbol="600519.SH"
  ↓
找到所有 lineage.provider == "wind" 的 evidence_id
  ↓
找到包含这些 evidence_id 的 Manifest
  ↓
找到引用这些 evidence_id 的 Citation
  ↓
找到包含这些 Citation 的 Section Output
```

**用途**：回答"Wind 的数据最终出现在了哪些 Section 中？"

---

### 4.2 反向追溯（Section Output → Provider）

```text
给定 section_output.citations[0].citation_id
  ↓
取 citation.evidence_id
  ↓
查找 EvidenceLineage(evidence_id)
  ↓
得到 provider / provider_tier / trust_gate_status / as_of
```

**用途**：回答"这句话的数据来源是谁？可信吗？什么时候的数据？"

---

### 4.3 断裂检测

如果任何一层无法追溯，视为 Lineage 断裂：

| 断裂位置 | 含义 | 严重性 |
|---------|------|--------|
| Citation → Evidence 断裂 | Citation 引用了不存在的 evidence_id | P0 — Contract 违规 |
| Evidence → Lineage 断裂 | Evidence 无对应 Lineage 记录 | P0 — 事实来源不可追溯 |
| Lineage → Provider 断裂 | Lineage.provider 为空 | P1 — 降级为 "unknown provider" |
| Lineage → Trust Gate 断裂 | Lineage.trust_gate_status 为空 | P0 — Trust Gate 被绕过 |

---

## 5. Lineage 构建时机

```text
build_evidence_bundle(gateway_response)
  ↓ 同时生成
Evidence + EvidenceLineage

不得事后补 Lineage。
```

**规则**：

- Lineage 必须在 `bundle_to_evidence()` 转换时同步创建
- 不允许 Evidence 存在但 Lineage 不存在
- 不允许先创建 Evidence 再回头补 Lineage

---

## 6. Lineage Store

```python
@dataclass
class LineageStore:
    records: dict[str, EvidenceLineage]   # key = evidence_id

    def get(self, evidence_id: str) -> EvidenceLineage | None:
        return self.records.get(evidence_id)

    def add(self, lineage: EvidenceLineage) -> None:
        if lineage.evidence_id in self.records:
            raise ValueError(f"Duplicate lineage for {lineage.evidence_id}")
        self.records[lineage.evidence_id] = lineage

    def trace_back(self, citation: Citation) -> EvidenceLineage | None:
        """从 Citation 反向追溯到 Lineage"""
        return self.get(citation.evidence_id)
```

**不变量**：

- `LineageStore` 中每个 `evidence_id` 只能有一条 Lineage 记录
- 所有 `EvidenceManifest.evidences` 中的 `evidence_id` 必须在 `LineageStore` 中有对应记录

---

## 7. 验证函数签名

```python
def validate_lineage_completeness(
    manifest: EvidenceManifest,
    lineage_store: LineageStore,
) -> list[str]:
    """检查 Manifest 中所有 Evidence 是否有完整 Lineage，返回断裂列表"""
    ...

def validate_citation_lineage(
    citations: list[Citation],
    manifest: EvidenceManifest,
    lineage_store: LineageStore,
) -> list[str]:
    """检查所有 Citation 是否能追溯到 Provider，返回断裂列表"""
    ...
```

---

## 8. 红线

| 红线 | 来源 |
|------|------|
| Evidence 必须有对应 Lineage 记录 | 本 Contract §5 |
| Lineage 必须在 Evidence 创建时同步生成 | 本 Contract §5 |
| Lineage.trust_gate_status 不得为空 | 本 Contract §4.3 |
| Lineage.provider 为空时标记为 P1 降级 | 本 Contract §4.3 |
| Citation → Evidence → Lineage 链路任意断裂 = Contract 违规 | 本 Contract §4.3 |

---

## 9. 完整链路验证示例

```text
用户看到 Report 正文：
  "公司 PE 为 20"

追溯路径：
  Section Output body 中第 3 句
    ↓ citations[2]
  Citation(citation_id="cite:abc123", evidence_id="evidence:def456", field_used="pe")
    ↓ evidence_id
  Evidence(evidence_id="evidence:def456", provider="wind", data={"pe": 20})
    ↓ lineage_store.get("evidence:def456")
  EvidenceLineage(
    provider="wind",
    provider_tier=1,
    gateway_timestamp="2026-06-07T10:00:00Z",
    trust_gate_status="success",
    allowed_use=["fundamental_overview", "valuation_analysis", "peer_comparison"],
    as_of="2026-06-06",
  )

结论：
  这个 PE=20 来自 Wind（Tier 1），数据口径 2026-06-06，
  Trust Gate 判定为 success，允许用于基本面+估值+同业对比。
```

---

*本文档为 Evidence Lineage Contract v0，纯定义，无代码实现。*
