# Runtime Consolidation Review

**日期**：2026-06-07  
**状态**：审计文档 — 只读分析，无代码变更

---

## 执行摘要

Finance Suite（`/Users/Zhuanz/finance-suite`）持有 **Contract 定义 + Smoke 验证**。  
Open BB（`/Users/Zhuanz/Documents/Open BB`）持有 **可运行 Runtime 实现 + 8 个 Smoke 全通过**。

两套系统在做同一件事：金融研究 Agent 的 Evidence → Section → Report 链路。  
语义方向一致，但命名和结构存在差异。

---

## Part 1：Evidence 对齐

### Finance Suite 定义

```python
# evidence_manifest_contract_v0.md
Evidence(evidence_id, title, summary, provider, provider_tier,
         qc_status, allowed_use, blocked_fields, data, as_of, created_at)
```

- ID 格式：`evidence:<uuid-hex-8>`
- 禁止字段：`_qc / raw / payload / raw_response / gateway_response / provider_payload`
- 从 `EvidenceBundle` 通过 `bundle_to_evidence()` 转换

### Open BB 实现

```python
# citation.py
EvidenceCitation(source_id, provider, as_of, fetched_at,
                 used_in_section, confidence, quote_or_fact_ref)
```

- ID 格式：`{trace_id}:{index:02d}:{provider}`（例如 `research-abc123:00:quotegw`）
- 无禁止字段机制
- 从 `GatewayResult` 通过 `from_gateway_result()` 转换

### 对齐分析

| 维度 | Finance Suite | Open BB | 对齐状态 |
|------|-------------|---------|---------|
| 唯一标识 | `evidence_id`（UUID） | `source_id`（组合键） | ⚠️ 不一致 |
| 来源追踪 | `provider` + `provider_tier` | `provider` | ✅ 兼容 |
| 数据时间 | `as_of` | `as_of` | ✅ 一致 |
| 获取时间 | 无 | `fetched_at` | ⚠️ Open BB 更丰富 |
| 可信度 | `qc_status`（success/partial/failure） | `confidence`（high/medium/low/mock） | ⚠️ 语义不同 |
| 权限控制 | `allowed_use` 白名单 | 无 | ❌ Open BB 缺失 |
| 字段拦截 | `blocked_fields` 物理删除 | 无 | ❌ Open BB 缺失 |
| 数据体 | `data: dict`（已清洗） | 无（data 在 GatewayResult 中，Citation 不持有） | ⚠️ 架构差异 |
| Section 绑定 | 无（由 Manifest 关联） | `used_in_section` 直接绑定 | ⚠️ 绑定方式不同 |

### 关键差异

1. **Finance Suite 的 Evidence 持有清洗后的 data；Open BB 的 EvidenceCitation 不持有 data**  
   Open BB 的 data 留在 `GatewayResult.data` 中，Citation 只是引用记录。

2. **Finance Suite 有 `allowed_use` + `blocked_fields`；Open BB 没有**  
   Open BB 的 Trust Gate 边界弱于 Finance Suite。`confidence = "mock"` 只是标记，不阻断使用。

3. **ID 格式不同**  
   Finance Suite 用纯 UUID，Open BB 用组合键（trace_id + index + provider）。

---

## Part 2：SectionContract 对齐

### Finance Suite 定义

```python
# section_workflow_contract_v0.md
SectionInput(section_id, symbol, query, evidence_manifest,
             allowed_use_filter, required_evidence_types, optional_evidence_types)

SectionOutput(section_id, status, qc, body, citations, used_evidence_ids,
              limitations, created_at)
```

- 状态机：PENDING → READY → RETRIEVING → ANALYZE → QC → DONE / SKIPPED / FAILED
- Section ID 格式：`section:<english_name>`
- depends_on 用英文 ID

### Open BB 实现

```python
# section_contract.py
SectionContract(section_id, title, depends_on, input_refs, output_artifact,
                qc_required, retry_policy)

# sections.py
RuntimeSection(name, status, evidence_ids, output, qc, retry_count,
               error, skip_reason, output_contract)

# section_output.py
SectionOutput(section_id, title, body, citations, qc, state, generated_at)
```

- 状态机：PENDING → RUNNING → DONE / FAILED / SKIPPED
- Section ID 格式：中文标题直接作为 ID（例如 `"行业速览"`）
- depends_on 用中文标题

### 对齐分析

| 维度 | Finance Suite | Open BB | 对齐状态 |
|------|-------------|---------|---------|
| Section ID | `section:industry_overview` | `"行业速览"` | ⚠️ 语言不同 |
| 状态机 | 7 态（含 READY/RETRIEVING/ANALYZE/QC） | 5 态（PENDING/RUNNING/DONE/FAILED/SKIPPED） | ⚠️ 粒度不同 |
| depends_on | 英文 ID 列表 | 中文标题 tuple | ⚠️ 格式不同 |
| Evidence 输入 | `evidence_manifest: list[EvidenceManifestEntry]` | `evidence_ids: list[str]`（source_id 引用） | ⚠️ 结构不同 |
| Retry | 无（Contract 层不定义） | `RetryPolicy(max_retries, retryable_on)` | ✅ Open BB 更丰富 |
| QC | `SectionQC` 结构化（10 字段） | `dict[str, Any]`（松散） | ⚠️ Finance Suite 更严格 |
| Output | `SectionOutput`（含 limitations / used_evidence_ids） | `SectionOutput`（无 limitations / used_evidence_ids） | ⚠️ Finance Suite 更丰富 |
| Citations | `list[Citation]`（结构化对象） | `list[str]`（source_id 字符串列表） | ⚠️ 类型不同 |

### 关键差异

1. **Section ID 语言不同**  
   Finance Suite 用英文（`section:industry_overview`），Open BB 用中文（`"行业速览"`）。  
   合并时需要建立映射表。

2. **状态机粒度不同**  
   Finance Suite 有 7 个状态（更适合 Contract 验证），Open BB 有 5 个状态（更适合执行）。  
   RUNNING ≈ RETRIEVING + ANALYZE + QC 的合并。

3. **Evidence 输入方式不同**  
   Finance Suite 通过 `EvidenceManifest` 结构化传入，Open BB 通过 `evidence_ids` 字符串列表传入。  
   Finance Suite 的方式更安全（Manifest 可以拦截 raw dict），Open BB 的方式更轻量。

---

## Part 3：EvidenceStore / EvidenceCitation / EvidenceManifest 映射

### 语义映射表

| Finance Suite 概念 | Open BB 概念 | 语义等价？ |
|---|---|---|
| `Evidence` | 无直接对应（data 在 GatewayResult 中） | ❌ 不等价 |
| `EvidenceManifest`（per section 的 Evidence 集合） | `EvidenceStore.for_section(section_name)` | ⚠️ 近似等价 |
| `Citation`（citation_id → evidence_id → field_used） | `EvidenceCitation`（source_id → provider → used_in_section） | ⚠️ 近似等价 |
| `EvidenceLineage`（evidence_id → provider → trust_gate_status） | `EvidenceCitation.from_gateway_result()`（隐式 lineage） | ⚠️ 近似等价 |
| `LineageStore`（evidence_id → EvidenceLineage） | `EvidenceStore`（source_id → EvidenceCitation） | ⚠️ 近似等价 |

### 核心差异

```text
Finance Suite 模型：
  Evidence（持有 data）→ Manifest（per section 筛选）→ Citation（引用具体字段）

Open BB 模型：
  GatewayResult（持有 data）→ EvidenceCitation（引用记录，不持有 data）→ EvidenceStore（全局索引）
```

**关键区别**：

- Finance Suite 的 `Evidence` 是"清洗后的事实载体"（持有 data，已删除 blocked_fields）
- Open BB 的 `EvidenceCitation` 是"引用记录"（不持有 data，只是指针）

这意味着：
- Finance Suite 的链路是：`data 在 Evidence 里 → Section 从 Evidence 读 data`
- Open BB 的链路是：`data 在 GatewayResult 里 → Section 从 GatewayResult 读 data，Citation 只是记录`

**风险**：Open BB 的模型允许 Section 直接接触 `GatewayResult.data`（未经 Trust Gate 物理删除），而 Finance Suite 的模型强制 Section 只能接触 `Evidence.data`（已清洗）。

---

## Part 4：ReportAssembly 差异

### Finance Suite 定义

```python
ReportOutput(report_id, symbol, title, body_sections, assembly_warnings,
             citation_index, assembly_qc, created_at)
```

- `body_sections`：只包含 DONE section
- `assembly_warnings`：FAILED / SKIPPED / PARTIAL 强制披露
- `citation_index`：`list[CitationIndexEntry]`
- `assembly_qc`：结构化 QC（10 字段，含 `has_critical_section_missing`）

### Open BB 实现

```python
ReportAssembly(symbol, trace_id, generated_at, sections, failed_sections,
               skipped_sections, missing_sections, citation_index, qc_passed)
```

- `sections`：只包含 DONE section
- `failed_sections` / `skipped_sections`：分别记录
- `citation_index`：`dict[str, EvidenceCitation]`
- `qc_passed`：单一 bool

### 对齐分析

| 维度 | Finance Suite | Open BB | 对齐状态 |
|------|-------------|---------|---------|
| Report ID | `report_id`（UUID） | `trace_id` | ✅ 兼容 |
| DONE 收录 | ✅ 只有 DONE 进 body | ✅ 只有 DONE 进 sections | ✅ 一致 |
| FAILED 处理 | `assembly_warnings` 中标记 | `failed_sections` 列表 | ✅ 语义一致 |
| SKIPPED 处理 | `assembly_warnings` 中标记 | `skipped_sections` 列表 | ✅ 语义一致 |
| PARTIAL 处理 | 进 body + 生成 warning | 无 PARTIAL 概念 | ⚠️ Finance Suite 更细 |
| Citation Index | `list[CitationIndexEntry]`（含 section_id） | `dict[str, EvidenceCitation]` | ⚠️ 结构不同 |
| QC | `AssemblyQC`（10 字段结构化） | `qc_passed: bool` | ⚠️ Finance Suite 更丰富 |
| Critical Section | 定义了 `CRITICAL_SECTIONS` | 无 | ❌ Open BB 缺失 |
| missing_sections | 无 | 有（v0.9+ 预留） | ✅ Open BB 更前瞻 |

### 关键差异

1. **QC 粒度**：Finance Suite 有 10 字段结构化 QC；Open BB 只有一个 bool。
2. **Critical Section**：Finance Suite 定义了关键 Section（缺失则 Report 不可发布）；Open BB 没有。
3. **Citation Index 结构**：Finance Suite 是 flat list + section_id 关联；Open BB 是 dict（source_id → Citation）。

---

## Part 5：最终决策建议

### 选项分析

| 选项 | 优势 | 劣势 |
|------|------|------|
| A. 保留双 Runtime | 各自独立演进，不互相阻塞 | 语义漂移风险持续增加，长期维护成本翻倍 |
| B. Finance Suite = Contract Source，Open BB = Implementation Source | 分工清晰，Contract 驱动实现 | 需要 Open BB 向 Contract 对齐（一次性成本） |
| C. 完全合并为一个仓库 | 维护成本最低，单一事实源 | 合并工作量大，文件冲突风险 |

### 推荐：方案 B

```text
Finance Suite = Contract Source of Truth
Open BB = Implementation Source of Truth
```

**理由**：

1. **Finance Suite 的 Contract 更严格**  
   - `allowed_use` / `blocked_fields` / `EvidenceManifest` 是 Trust Gate 的核心保障
   - Open BB 缺少这些约束，长期看是安全隐患

2. **Open BB 的 Runner 更成熟**  
   - 状态机 + retry + depends_on 执行 + 8 个 smoke 已通过
   - Finance Suite 只有 Contract stub，无可运行 Runner

3. **合并方向清晰**  
   - Open BB 的 `EvidenceCitation` 需要升级为 Finance Suite 的 `Evidence`（加入 `allowed_use` + `blocked_fields` + data 持有）
   - Open BB 的 `GatewayQC` 需要对齐 Finance Suite 的 `_qc` 语义（status: success/partial/failure + reason）
   - Open BB 的 Section ID 需要加入英文 alias（保留中文 title，加英文 section_id）
   - Open BB 的 `qc_passed: bool` 需要升级为结构化 `AssemblyQC`

### 合并优先级

```text
P0（安全边界）：
  Open BB 加入 allowed_use + blocked_fields → 对齐 Trust Gate Contract
  
P1（追溯能力）：
  Open BB EvidenceCitation 升级为 Evidence（持有 data）
  Open BB 加入 EvidenceLineage（追溯到 Provider）

P2（QC 结构化）：
  Open BB GatewayQC → 对齐 _qc.status/reason/missing_fields
  Open BB ReportAssembly.qc_passed → 升级为 AssemblyQC

P3（命名对齐）：
  Section ID 加入英文 alias
  Open BB source_id → 对齐 evidence_id 格式
```

### 结论

```
┌─────────────────────────────────────────┐
│  PASS — 可以按方案 B 推进               │
│                                         │
│  Finance Suite = Contract Source         │
│  Open BB = Implementation Source         │
│                                         │
│  合并方向：Open BB 向 Contract 对齐     │
│  优先级：P0 > P1 > P2 > P3             │
│                                         │
│  不 BLOCK 任何一方的独立演进            │
│  但新增功能必须先查 Contract 再实现     │
└─────────────────────────────────────────┘
```

---

## 附录：文件对照表

| Finance Suite 文件 | Open BB 对应文件 | 说明 |
|---|---|---|
| `docs/trust_gate_contract.md` | 无 | ❌ Open BB 缺 Trust Gate Contract |
| `docs/evidence_manifest_contract_v0.md` | 无 | ❌ Open BB 缺 Manifest Contract |
| `docs/citation_contract_v0.md` | `citation.py` | ⚠️ 部分对齐 |
| `docs/evidence_lineage_contract_v0.md` | `citation.from_gateway_result()` | ⚠️ 隐式 lineage |
| `docs/section_workflow_contract_v0.md` | `section_contract.py` + `sections.py` | ⚠️ 语义一致，结构不同 |
| `docs/report_assembly_contract_v0.md` | `report_assembly.py` | ⚠️ 语义一致，QC 粒度不同 |
| `research_runtime/evidence_bundle.py` | `gateway/result.py` | ⚠️ 功能重叠 |
| 无 Runner | `research_app.py` + `engine.py` | ❌ Finance Suite 缺 Runner |

---

*本文档为 Runtime Consolidation Review，纯审计结论，无代码变更。*
