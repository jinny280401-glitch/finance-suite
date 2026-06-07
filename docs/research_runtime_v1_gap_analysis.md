# Research Runtime v1 Gap Analysis

**日期**：2026-06-07  
**基准**：Trust Gate Runtime Sprint 2 CLOSED（commit 5d43da9）  
**状态**：架构缺口分析 — 只读分析，无代码变更

---

## 执行摘要

Trust Gate Runtime Sprint 2 完成了 **Gateway → Evidence Bundle 边界收口**，建立了 LLM 入口的第一道硬防线。

但 Research Runtime v1 要成为可运行的研究生成系统，还缺少：

1. **Section Workflow Contract**（如何从 Evidence Bundle 组装 Section）
2. **Evidence Manifest Schema**（多证据如何追溯到来源）
3. **Runtime Event Schema 扩展**（Trust Gate / Section / LLM 事件）
4. **Action Gate 设计**（LLM 输出后如何拦截高风险建议）
5. **Meta Workflow Runtime 启动时机**（何时从设计进入实现）
6. **v1 路线图**（3-6 个 Sprint 的依赖链）

---

## 1. 已稳定的 Contract

### 1.1 Trust Gate Contract ✅

**位置**：`docs/trust_gate_contract.md`  
**代码**：`research_runtime/evidence_bundle.py`  
**验收**：Sprint 2 smoke 5/5 PASS

**已定义**：

| 项目 | 说明 |
|------|------|
| EvidenceBundle 结构 | `evidence / allowed_use / blocked_fields / trust_status / reason / source` |
| `build_evidence_bundle()` | Gateway Response → EvidenceBundle 转换函数 |
| `generate_section_body()` | 类型约束，拒绝 raw Gateway Response |
| ProviderClass 分类 | MOCK / FALLBACK / REAL 三级 |
| `allowed_use` 权限白名单 | `["fundamental_overview"]` / `["valuation_analysis"]` 等 |
| `blocked_fields` 硬删除 | 物理删除字段，不保留再提示模型 |

**覆盖范围**：

- ✅ Gateway → Trust Gate → Evidence Bundle → LLM 单向流
- ✅ raw `_qc` / `payload` / `raw` 硬删除
- ✅ prompt boundary 注入拦截（`generate_section_body()` 类型检查）
- ✅ workflow bypass 路径收口（`session.add_evidence_bundle()` 守卫）

**不覆盖**：

- ❌ 多个 Evidence Bundle 如何组合成一个 Section
- ❌ Section 如何引用 Evidence（citation 机制）
- ❌ LLM 输出后如何拦截高风险行动建议

---

### 1.2 Finance Data Gateway v1 Contract ✅

**位置**：`docs/data_gateway_v1_contract.md`  
**状态**：设计冻结，实现未全覆盖

**已定义**：

| 项目 | 说明 |
|------|------|
| FinanceDataResponse 结构 | 统一返回格式（ok / symbol / data_type / provider / _qc） |
| `_qc.status` | success / partial / failure 三态 |
| `_qc.reason` | 机器可读原因枚举（delayed_source / missing_fields / all_providers_failed） |
| Source Taxonomy | Tier 1-4 信源分层（Wind/iFinD → Tushare/JoinQuant → AkShare → 雪球/新浪） |
| Provider Route Policy | Registry ≠ Route，Route Policy 决定实际执行顺序 |

**覆盖范围**：

- ✅ Gateway 返回契约定义
- ✅ QC 字段语义
- ✅ 信源分层定义

**不覆盖**：

- ❌ 如何从多个 Gateway Response 构建完整 Research Context
- ❌ 跨维度证据冲突如何处理（例如：quote.pe=20 vs financials.pe=22）
- ❌ 时间戳不一致如何展示（例如：quote as_of 2026-06-01 vs financials as_of 2026-03-31）

---

### 1.3 Runtime Event Schema (v0.2) ✅

**位置**：`research_runtime/events.py`  
**状态**：基础事件已实现

**已定义**：

| 事件类型 | 说明 |
|---------|------|
| state_entered | 状态机阶段切换 |
| provider_selected | Provider 选择 |
| evidence_retrieved | Evidence 检索完成 |
| context_built | Context 构建完成 |
| qc_completed | QC 检查完成 |
| artifact_written | Artifact 写入完成 |
| workflow_completed | Workflow 完成 |
| workflow_failed | Workflow 失败 |

**覆盖范围**：

- ✅ 单一 workflow 的生命周期事件
- ✅ 基础可观测性（哪个阶段 / 哪个 provider / 多少 evidence）

**不覆盖**：

- ❌ Trust Gate 事件（evidence_allowed / evidence_blocked / gate_reason）
- ❌ Section-level 事件（section_started / section_completed / section_qc_failed）
- ❌ LLM 调用事件（prompt_sent / tokens_used / model_used / completion_received）
- ❌ Action Gate 事件（action_blocked / action_allowed / risk_score）

---

## 2. 未定义的 Contract

### 2.1 Section Workflow Contract ❌

**缺口**：如何从 Evidence Bundle 组装成一个 Section？

**需要定义**：

```python
@dataclass
class SectionWorkflow:
    section_id: str
    title: str
    required_evidence_types: list[str]  # 必需的 evidence 类型
    optional_evidence_types: list[str]  # 可选的 evidence 类型
    allowed_use_filter: list[str]       # 只接受哪些 allowed_use
    min_evidence_count: int             # 最少需要几个 evidence
    llm_prompt_template: str            # Prompt 模板
    qc_rules: list[QCRule]              # Section-level QC 规则
```

**关键问题**：

1. Section 需要哪些 evidence 类型才能开工？
   - 例如：**行业速览** Section 需要 `industry_overview` (required) + `macro_snapshot` (optional)
   - 如果 `industry_overview` 缺失，Section 是否应该整体阻断？

2. 如果部分 evidence 缺失，Section 如何降级？
   - 例如：`macro_snapshot` 失败，行业速览 Section 应该：
     - 标记为 `partial`
     - 在正文中披露"宏观数据不可用"
     - 不生成宏观相关判断

3. Section 内部如何引用 Evidence？（citation 机制）
   - 例如：Report 正文写"公司 PE 为 20"，如何追溯到哪个 Evidence Bundle？

4. Section 的 QC 门槛是什么？
   - 例如：如果 Section 使用的 evidence 中有 50% 是 FALLBACK provider，Section 是否应该标记为 `partial`？

**当前状态**：未定义，Section Workflow 逻辑散落在各处，无统一契约。

---

### 2.2 Report Assembly Contract ❌

**缺口**：如何从 11 个 Section 组装成完整 Report？

**需要定义**：

```python
@dataclass
class ReportAssembly:
    sections: list[Section]              # 11 个 Section
    overall_qc: QCResult                 # Report-level QC
    coverage_report: CoverageReport      # 覆盖率报告
    disclosure_items: list[str]          # 需要披露的限制
    artifact_path: str                   # 最终 artifact 路径
```

**关键问题**：

1. 哪些 Section 是必需的？
   - 例如：行业速览 + 公司定位必须有，其他可选
   - 如果缺少必需 Section，Report 是否应该整体阻断？

2. 如果超过 N 个 Section 失败，Report 是否应该整体阻断？
   - 例如：11 个 Section 中 5 个失败，Report 是否还能发布？

3. Report-level QC 如何聚合 Section-level QC？
   - 例如：Section A 是 `partial`，Section B 是 `success`，Report-level QC 应该是什么？

4. Disclosure 如何从各 Section 收集？
   - 例如：Section A 披露"宏观数据不可用"，Section B 披露"同业数据不可用"，Report 最终应该如何展示这些限制？

**当前状态**：未定义，Report 组装逻辑不存在。

---

### 2.3 Action Gate Contract ❌

**缺口**：LLM 输出后如何拦截高风险行动建议？

**需要定义**：

```python
@dataclass
class ActionGate:
    allowed_action_types: list[str]     # 允许的行动类型
    blocked_action_types: list[str]     # 禁止的行动类型
    risk_threshold: float               # 风险阈值
    
def filter_actions(
    llm_output: str, 
    evidence_bundle: EvidenceBundle
) -> ActionGateResult:
    """从 LLM 输出中提取行动建议，根据 evidence 可信度拦截高风险建议"""
    pass
```

**关键问题**：

1. 哪些行动建议是高风险的？
   - 买卖建议（"建议买入" / "建议卖出"）
   - 仓位建议（"建议持仓 30%"）
   - 短线择时（"建议短线布局"）
   - 目标价（"目标价 XX 元"）

2. `evidence.allowed_use = ["fundamental_overview"]` 时，哪些行动建议应该被拦截？
   - 例如：基本面 overview 只能用于描述，不能用于买卖建议

3. 如何从 LLM 自由文本输出中检测行动建议？
   - 方案 A：结构化输出（LLM 返回 JSON，Action Gate 过滤 `action_recommendations` 字段）
   - 方案 B：关键词检测（正则匹配"建议买入" / "建议卖出" / "目标价"等）
   - 方案 C：二次 LLM 调用（专门的 Action Classifier 判断是否包含高风险建议）

4. 拦截后如何替换？
   - safe body？（替换为"基于当前数据不足以给出买卖建议"）
   - 部分保留？（保留基本面描述，删除行动建议部分）
   - 整体阻断？（Section 标记为 `blocked`，不输出内容）

**当前状态**：未定义，Trust Gate 只拦截输入，不拦截输出。

**示例**：

当前 Trust Gate 只能做到：

```text
Gateway Response (partial)
  ↓
Trust Gate (allowed_use = ["fundamental_overview"])
  ↓
Evidence Bundle
  ↓
LLM
  ↓
LLM 输出："建议短线布局，目标价 XX" ← 这里无拦截！
```

**需要做到**：

```text
LLM 输出："建议短线布局，目标价 XX"
  ↓
Action Gate
  ↓
Safe Body："基于当前数据不足以给出短线择时和目标价建议"
```

---

## 3. Runtime Event Schema 缺口

### 3.1 Trust Gate 事件缺失

**当前问题**：Trust Gate 运行无事件记录，无法追踪：
- 哪些 evidence 被允许进入 LLM？
- 哪些 evidence 被拦截？
- 为什么被拦截？

**需要新增**：

```python
TRUST_GATE_EVENTS = [
    "trust_gate_started",           # Trust Gate 开始
    "evidence_allowed",             # Evidence 被允许
    "evidence_blocked",             # Evidence 被拦截
    "evidence_stripped",            # 哪些字段被删除
    "provider_class_detected",      # MOCK / FALLBACK / REAL
]
```

**用途**：
- 调试：为什么这个 evidence 被拦截？
- 审计：哪些 evidence 进入了 LLM？
- 监控：Trust Gate 拦截率是多少？

---

### 3.2 Section-level 事件缺失

**当前问题**：只有 workflow-level 事件，无 Section 粒度，无法追踪：
- 哪个 Section 耗时最长？
- 哪个 Section QC 失败最多？
- 哪个 Section 的 evidence 不足？

**需要新增**：

```python
SECTION_EVENTS = [
    "section_started",              # Section 开始
    "section_evidence_collected",   # Section 收集到的 evidence
    "section_llm_called",           # Section 调用 LLM
    "section_qc_passed",            # Section QC 通过
    "section_qc_failed",            # Section QC 失败
    "section_completed",            # Section 完成
]
```

**用途**：
- 了解哪个 Section 耗时最长
- 了解哪个 Section QC 失败最多
- Runtime Panel 可以按 Section 分组展示进度

---

### 3.3 LLM 调用事件缺失

**当前问题**：无 LLM 调用记录，无法追踪：
- Token 消耗
- 模型选择
- 调用失败原因

**需要新增**：

```python
LLM_EVENTS = [
    "llm_prompt_sent",              # LLM prompt 发送
    "llm_completion_received",      # LLM completion 接收
    "llm_tokens_used",              # LLM tokens 消耗
    "llm_model_used",               # LLM 模型选择
    "llm_call_failed",              # LLM 调用失败
]
```

**用途**：
- Token 消耗追踪
- 模型选择验证
- 调用失败调试

---

## 4. Evidence Manifest 缺口

### 4.1 当前问题

**问题**：多个 Evidence Bundle 进入 Section 后，无法溯源"这句话来自哪个 Evidence"。

**示例**：

Report 正文写：
> 公司 PE 为 20，行业平均 PE 为 25。

用户问：这个 PE 数据来自哪里？

**当前无法回答**：
- 哪个 provider？（Wind？JoinQuant？AkShare？）
- 哪个 timestamp？（2026-06-01？2026-03-31？）
- partial 还是 success？

---

### 4.2 需要定义

```python
@dataclass
class EvidenceManifest:
    evidence_id: str                        # Evidence 唯一 ID
    evidence_bundle: EvidenceBundle         # 完整 Evidence Bundle
    used_in_sections: list[str]             # 用于哪些 Section
    citations: list[Citation]               # 引用列表
    
@dataclass
class Citation:
    section_id: str                         # Section ID
    line_range: tuple[int, int]             # 行范围
    evidence_id: str                        # Evidence ID
    field_used: str                         # 使用了哪个字段
```

**用途**：
- Report 每一句话都能追溯到 Evidence
- 用户可以点击 Report 中的数据，看到来源 provider / timestamp / QC status
- 审计时可以验证 Report 是否只使用了 allowed evidence

---

## 5. Action Gate 设计缺口

### 5.1 当前问题

**Trust Gate 只拦截输入，不拦截输出**：

```text
Gateway Response (partial)
  ↓
Trust Gate (allowed_use = ["fundamental_overview"])
  ↓
Evidence Bundle
  ↓
LLM
  ↓
LLM 输出："建议短线布局，目标价 XX" ← 这里无拦截！
```

**问题**：即使 `allowed_use` 限制了输入，LLM 仍可能生成不可信的行动建议。

---

### 5.2 需要设计

```text
LLM 输出
  ↓
Action Gate
  ↓
Safe Body（如果包含高风险建议，替换为 safe 版本）
```

**Action Gate 规则**：

| evidence.allowed_use | 允许的行动建议 | 禁止的行动建议 |
|---|---|---|
| `["fundamental_overview"]` | 基本面描述 | 买卖建议 / 短线择时 / 仓位建议 / 资金流判断 |
| `["fundamental_overview", "valuation_analysis"]` | 基本面 + 估值分析 | 买卖建议 / 短线择时 / 仓位建议 |
| `["fundamental_overview", "valuation_analysis", "peer_comparison"]` | 基本面 + 估值 + 同业对比 | 买卖建议 / 短线择时 / 仓位建议 |

**实现方式**：
- **方案 A：结构化输出**（推荐）  
  LLM 返回 JSON，Action Gate 过滤 `action_recommendations` 字段。可靠性最高。

- **方案 B：关键词检测**  
  正则匹配"建议买入" / "建议卖出" / "目标价"等。容易误判。

- **方案 C：二次 LLM 调用**  
  专门的 Action Classifier 判断是否包含高风险建议。成本高。

---

## 6. Meta Workflow Runtime 应该何时启动

### 6.1 当前状态

**Meta Workflow**：DESIGN FREEZE  
**实现**：未启动

**已完成**：
- `docs/meta_workflow_review.md`（设计审阅）
- `examples/*.yaml`（示例 YAML）
- `examples/invalid/*.yaml`（反例）

---

### 6.2 启动条件

**不应立即启动的原因**：

1. **Section Workflow Contract 缺失**  
   Meta Workflow 需要编排 Section，但 Section Contract 不存在。

2. **Evidence Manifest 缺失**  
   Meta Workflow 需要追踪 Evidence 使用，但 Manifest Schema 不存在。

3. **Action Gate 缺失**  
   Meta Workflow 输出需要经过 Action Gate，但 Gate 设计不存在。

**启动顺序**：

```text
Phase 1: Section Workflow Contract 定义
  ↓
Phase 2: Evidence Manifest Schema 定义
  ↓
Phase 3: Action Gate 设计 + 实现
  ↓
Phase 4: Runtime Event Schema 扩展
  ↓
Phase 5: Meta Workflow Runtime v0（最小可运行版本）
```

**预计时间线**：
- Phase 1-2：1-2 个 Sprint
- Phase 3-4：1 个 Sprint
- Phase 5：1 个 Sprint

**最早启动时机**：Phase 4 完成后

---

## 7. v1 路线图

### Sprint 3: Section Workflow Contract（预计 2 周）

**目标**：定义 Section Workflow 契约，实现 Section 从 Evidence Bundle 到输出的基础逻辑。

**交付物**：
- `docs/section_workflow_contract.md`
- `research_runtime/section.py`（SectionWorkflow / Section / SectionQC）
- `smoke_section_workflow.py`（5 个 Section 示例）

**验收标准**：
- ✅ 11 个 Section 的 Contract 全部定义
- ✅ Section 从 Evidence Bundle 构建的逻辑清晰
- ✅ Section QC 规则明确
- ✅ Smoke test 5/5 PASS

---

### Sprint 4: Evidence Manifest + Report Assembly（预计 2 周）

**目标**：实现 Evidence 追溯机制和 Report 组装逻辑。

**交付物**：
- `docs/evidence_manifest_contract.md`
- `docs/report_assembly_contract.md`
- `research_runtime/manifest.py`
- `research_runtime/report.py`
- `smoke_report_assembly.py`

**验收标准**：
- ✅ Evidence Manifest Schema 定义
- ✅ Citation 机制可追溯到 Evidence
- ✅ Report Assembly 逻辑明确
- ✅ Smoke test 5/5 PASS

---

### Sprint 5: Action Gate + Runtime Event 扩展（预计 1 周）

**目标**：实现 Action Gate 和扩展 Runtime Event Schema。

**交付物**：
- `docs/action_gate_contract.md`
- `research_runtime/action_gate.py`
- `research_runtime/events.py`（扩展 Trust Gate / Section / LLM 事件）
- `smoke_action_gate.py`

**验收标准**：
- ✅ Action Gate 规则定义
- ✅ 高风险行动建议可被拦截
- ✅ Runtime Event 覆盖 Trust Gate / Section / LLM
- ✅ Smoke test 5/5 PASS

---

### Sprint 6: Meta Workflow Runtime v0（预计 1 周）

**目标**：实现 Meta Workflow Runtime 最小可运行版本。

**交付物**：
- `research_runtime/meta_workflow.py`
- `smoke_meta_workflow.py`

**验收标准**：
- ✅ YAML 定义可被解析
- ✅ Section 按依赖顺序执行
- ✅ Evidence 正确传递
- ✅ Report 正确组装
- ✅ Smoke test 5/5 PASS

---

## 附录：关键决策记录

### A1: 为什么 Trust Gate 不拦截输出？

**理由**：Trust Gate 的职责是"拦截不可信输入"，不是"拦截不可信输出"。

**分工**：
- Trust Gate：拦截输入（Gateway Response → Evidence Bundle）
- Action Gate：拦截输出（LLM Output → Safe Body）

**好处**：
- 职责单一
- 可独立测试
- 可独立迭代

---

### A2: 为什么 Section Workflow 要先于 Meta Workflow？

**理由**：Meta Workflow 是 Section 的编排层，Section 是 Meta Workflow 的执行单元。

**类比**：
- Section Workflow = 函数定义
- Meta Workflow = 函数调用编排

**好处**：
- 先定义函数，再编排调用，符合自下而上原则
- Section 可以独立测试
- Meta Workflow 可以晚点启动

---

### A3: 为什么 Evidence Manifest 要单独定义？

**理由**：Manifest 是 Report 的"源代码映射"（source map），不是 Report 本身。

**类比**：
- Report = 编译后的二进制
- Evidence Manifest = 调试符号表

**好处**：
- Report 可以不带 Manifest 发布（轻量）
- Manifest 可以按需加载（审计时）
- Manifest 可以独立演进（不影响 Report 格式）

---

*本文档为 Research Runtime v1 的架构缺口分析，不包含实现代码。*
