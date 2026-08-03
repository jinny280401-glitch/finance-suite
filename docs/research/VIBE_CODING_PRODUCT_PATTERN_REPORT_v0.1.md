# Vibe Coding Product Pattern Report v0.1

**Date:** 2026-08-03
**Purpose:** 从 GitHub/开源社区寻找 AI 时代快速验证和构建产品的新范式，为 Vera / Finance Suite 下一阶段提供可迁移模式
**Scope:** 研究，非代码实施。不改生产。

---

## 1. Top 10 项目观察

### 1.1 Spec Kit（110k stars — 2026 年增长最快的 AI 工具项目）

| 维度 | 分析 |
|---|---|
| GitHub | GitHub 开源，spec-driven development (SDD) |
| 一句话价值 | 用 `spec.md` 作为单一事实源，防止 AI "看起来对但不对" |
| 为什么有意思 | 七步工作流（constitution → specify → plan → clarify → tasks → analyze → implement），AI 执行的是意图而非猜测 |
| 构建成本 | 开源免费 |
| AI 使用方式 | spec 是 AI 的"外部记忆"；修改发生在 spec 层而非调试层 |
| 技术栈 | CLI 工具 |
| 核心创新 | 把传统 SDD 方法论适配到 AI agent 时代 —— spec 作为 agent 的 immutable contract |
| 是否适合 Vera | **高度适合**。Vera 的 Evidence Manifest + Capability Claim 本质上就是 spec 文档。SDD 工作流可适配为 "Evidence → Claim → Review → Output" |
| 可借鉴点 | 1) spec-as-contract 模式 2) constitution 文件（不可变约束层）3) clarify 步骤（AI 不确定就问，不猜）|
| 不可复制原因 | 工具本身不适合直接套用（代码生成场景 ≠ 研究分析场景），方法论可迁移 |

**Vera 专项：**
- **A. Research Workflow:** `constitution → specify → plan → clarify` 映射到 `Governance Constitution → Evidence Manifest → Research Plan → Clarify Gaps`
- **B. Trust:** spec.md 作为不可变合同 → Vera 的 Trust Gate 前置约束
- **C. Product Experience:** 七步流程可视化，每一步有明确的"完成定义"

---

### 1.2 Athena Loops（agentloop）— orchestrator → worker → reviewer 确定性循环

| 维度 | 分析 |
|---|---|
| GitHub | luckeyfaraday/athena-loops，MIT 许可 |
| 一句话价值 | "循环是 harness（确定性代码），不是 skill"——控制流在代码里，判断在 prompt 里 |
| 为什么有意思 | 设计原则极简：goal → decompose → fan-out to workers → aggregate → review gate → loop until pass。和 Vera D28 的 Builder/Reviewer 身份分离完全一致 |
| 构建成本 | 开源，Python 库 |
| AI 使用方式 | 一个 Agent 接口驱动多种后端（Claude, Codex, opencode, aider, Grok）；MCP server + CLI 双形态 |
| 技术栈 | Python, MCP |
| 核心创新 | 确定性 harness + 可替换 prompt —— harness 不变，判断标准可变 |
| 是否适合 Vera | **高度适合**。Vera 的 Agent 协作层可以直接吸收这个模式 |
| 可借鉴点 | 1) harness≠skill 的架构原则 2) swappable review rubric 3) loop-until-pass 的确定性实现 |
| 不可复制原因 | 通用框架，需要定制化为金融研究场景 |

**Vera 专项：**
- **A. Research Workflow:** `Orchestrator → Worker[] → Reviewer → Gate` 映射到 Vera 的 `Evidence Collection → Agent Analysis → Review → Output Gate`
- **B. Trust:** review gate 是代码强制的，不是 prompt 请求的
- **C. Product Experience:** CLI + MCP server 双形态 = Vera 可以同时服务交互式和自动化场景

---

### 1.3 MakerChecker — Agent 的 maker/checker 分离网关

| 维度 | 分析 |
|---|---|
| GitHub | makerchecker/MakerChecker，v1.2.0 (Jul 2026) |
| 一句话价值 | Agent "可证明地不能批准自己的工作"——职责分离作为硬编码安全网关 |
| 为什么有意思 | 三个独立包：`mc scan`（静态风险扫描）、`@makerchecker/embedded`（嵌入式强制原语）、自托管服务器（审批收件箱）。Ed25519 签名 hash-chained 审计日志，离线可验证 |
| 构建成本 | 开源，TypeScript |
| AI 使用方式 | LangChain + Claude Agent SDK 连接器，"审批"作为独立的安全层 |
| 技术栈 | TypeScript, Ed25519, hash-chained ledger |
| 核心创新 | 不是你"请求 AI 自我审查"——是你硬编码了它不能 |
| 是否适合 Vera | **高度适合**。Vera 的 Trust Gate 需要的就是这个：Builder 和 Reviewer 必须是不同的 agent identity，且 Reviewer 的拒绝权不能被 Builder 绕过 |
| 可借鉴点 | 1) maker/checker 作为架构层而非 prompt 层 2) 离线可验证审计日志 3) 静态风险扫描器 |
| 不可复制原因 | 作为独立网关部署，Vera 可能需要嵌入式方案而非独立服务 |

**Vera 专项：**
- **A. Research Workflow:** `mc scan` 可以扫描研究报告的风险信号（missing evidence, unsupported claims）
- **B. Trust:** **核心借鉴**：Provable segregation of duties。Vera 的 Builder/Reviewer 分离需要有这一层的证明机制
- **C. Product Experience:** 审批收件箱模式 → Vera 的 Research Review Queue

---

### 1.4 Tessera — 答案可追溯到证据的信任层

| 维度 | 分析 |
|---|---|
| GitHub | robert-vetter/tessera |
| 一句话价值 | 每个 AI 答案都扎根于可追溯的源记录，"不可证明的 claims 被拒绝，而不是被猜测" |
| 为什么有意思 | 统一的 knowledge graph → 每个 claim 必须能追溯到源节点。CI 强制的 faithfulness score（底线 1.000）。MCP-native |
| 构建成本 | 开源 |
| AI 使用方式 | MCP 工具，agent 查询时自动关联证据 |
| 技术栈 | Knowledge graph, MCP |
| 核心创新 | faithfulness 作为 CI 指标 —— 不是"看起来可信"，而是"可被机器验证" |
| 是否适合 Vera | **核心参考项目**。Vera 的 Evidence Manifest 本质上就是 Tessera 的 knowledge graph 的协议层版本 |
| 可借鉴点 | 1) faithfulness score 作为 CI gate 2) claim → source 回溯 3) "不可证明就拒绝"的默认行为 |
| 不可复制原因 | knowledge graph 基建成本高，Vera 可以用 Evidence Manifest JSON 替代图数据库 |

**Vera 专项：**
- **A. Research Workflow:** 每个研究输出的 claim 自动关联到 Evidence Manifest 条目
- **B. Trust:** faithfulness score < 1.000 → pipeline halt。这是 Vera Trust Gate 的量化标准
- **C. Product Experience:** "这条结论基于以下 3 条证据"——可视化溯源

---

### 1.5 Mira — 投资论文追踪系统（可刷新的 thesis）

| 维度 | 分析 |
|---|---|
| GitHub | byteseek/Mira |
| 一句话价值 | "Source → Claim → Expectation → Thesis → Event Delta → Decision Log → Postmortem" 完整链条 |
| 为什么有意思 | claim 级 evidence log + refresh boundary（`stale_after`, `must_refresh_if`）+ controlled vocabulary。AI 拓展认知带宽，人类保留最终判断，系统约束输出为可证伪的 claim |
| 构建成本 | 开源 |
| AI 使用方式 | Agent-native workspace，thesis 是持久化实体 |
| 技术栈 | TypeScript, PostgreSQL |
| 核心创新 | 论文（thesis）作为一等公民 —— 有生命周期、有效期、刷新条件、事后检验 |
| 是否适合 Vera | **直接对标**。Vera 的 Research Output 目前是一次性的，Mira 的 thesis 生命周期模型可以直接引入 |
| 可借鉴点 | 1) thesis 生命周期 2) refresh boundary 3) claim-level evidence 4) postmortem 闭环 |
| 不可复制原因 | 独立产品，Vera 只需吸收 pattern 而非复制产品 |

**Vera 专项：**
- **A. Research Workflow:** Research Output → Thesis（持久化）→ Event Delta（更新）→ Decision Log → Postmortem
- **B. Trust:** `stale_after` / `must_refresh_if` → Vera 的 Freshness Model (F-03)
- **C. Product Experience:** 论文仪表盘——看到每篇研究的状态（fresh/stale/refuted）

---

### 1.6 FinSight-AI — 有 resilience 的金融研究 agent 工作流

| 维度 | 分析 |
|---|---|
| GitHub | juanjuandog/FinSight-AI |
| 一句话价值 | "Evidence traceability + resilient workflows"——不是又一个 RAG demo |
| 为什么有意思 | 显式状态机（creation → ingestion → metric calculation → indexing → intelligence build → report generation），Redis Lua single-flight 防重，pgvector hybrid retrieval，报告缓存绑定数据快照 |
| 构建成本 | 开源 |
| AI 使用方式 | Multi-agent pipeline with state machine |
| 技术栈 | Python, Redis, PostgreSQL/pgvector |
| 核心创新 | idempotency + fencing tokens —— 和 Vera 需要的 Runtime Evidence 完全一致 |
| 是否适合 Vera | **基础设施参考**。Vera 的 Agent 工作流需要这个级别的 resilience |
| 可借鉴点 | 1) 任务状态机 2) single-flight 防重 3) 报告版本绑定数据快照 |
| 不可复制原因 | 完整产品，Vera 只需吸收 resilience pattern |

**Vera 专项：**
- **A. Research Workflow:** 状态机 → Agent 执行每一步有明确的"完成"定义
- **B. Trust:** 报告缓存绑定数据快照 → Vera 的 Evidence Timestamp 绑定
- **C. Product Experience:** 可视化工作流状态（当前在哪个阶段）

---

### 1.7 FinRobot — 确定性计算 + LLM 叙事

| 维度 | 分析 |
|---|---|
| GitHub | AI4Finance-Foundation/FinRobot |
| 一句话价值 | "Deterministic compute, LLM narration"——所有数字由纯 Python 算子计算，LLM 只负责推理和叙事 |
| 为什么有意思 | Lead Agent 编排 5 个 role-based sub-agents + 3 个 debate agents (bull/bear/judge)。估值模型（DCF, DDM, LBO, WACC, comps, Monte Carlo）都是确定性 Python，带完整溯源 |
| 构建成本 | 开源 |
| AI 使用方式 | 分层 agent：orchestrator → specialists → debate |
| 技术栈 | Python, LLM |
| 核心创新 | "数字是算出来的，不是生成出来的"——这直接对应 Vera 的 Provider 层和 LLM 层的职责分离 |
| 是否适合 Vera | **架构参考**。Vera 的 Provider → Agent 边界应该就是"Compute → Narrate"边界 |
| 可借鉴点 | 1) Compute/Narrate 分离 2) Bull/Bear/Judge debate 3) 全溯源计算 |
| 不可复制原因 | 估值模型不是 Vera 当前重点，架构模式可迁移 |

**Vera 专项：**
- **A. Research Workflow:** Provider 层（compute）→ Agent 层（narrate）→ Review 层（judge）
- **B. Trust:** 数字不可生成 → Provider 输出必须可验证
- **C. Product Experience:** Debate 结果的可视化（bull case vs bear case vs judge synthesis）

---

### 1.8 Tripwire — 本地优先的 epistemic agent 模板

| 维度 | 分析 |
|---|---|
| GitHub | camerontjs-dot/Tripwire |
| 一句话价值 | 把 AI agent 变成"投资组合怀疑论者"——必须先 steelman 反方论点，产出可证伪的"绊线"条件 |
| 为什么有意思 | "Disconfirming evidence first"——每一条记录带 provenance，append-only audit log，validate-then-log 写入 |
| 构建成本 | 开源模板 |
| AI 使用方式 | Agent 模板（Claude），local-first |
| 技术栈 | Python, Claude |
| 核心创新 | "Tripwire"——可观察条件，一旦触发就应重新考虑原结论。和 Mira 的 `must_refresh_if` 异曲同工 |
| 是否适合 Vera | **方法论参考**。Vera 的 Research Output 应该自带 falsifiability conditions |
| 可借鉴点 | 1) Disconfirming evidence first 2) Tripwire（可证伪条件）3) Validate-then-log |
| 不可复制原因 | 模板级别，作为方法论吸收 |

**Vera 专项：**
- **A. Research Workflow:** 每个 Research Output 包含 "什么情况下这个结论不再成立"
- **B. Trust:** append-only audit log + validate-then-log → Vera 的 Evidence Receipt
- **C. Product Experience:** Tripwire 仪表盘——哪些结论已经"触线"需要重新审视

---

### 1.9 Aevum — 加密审计内核（AI agent 的"黑匣子"）

| 维度 | 分析 |
|---|---|
| GitHub | aevum-labs/aevum，v0.9.0 (Jun 2026) |
| 一句话价值 | AI agent 的独立加密审计内核——每个 action 记录进 Ed25519 签名的 hash-chained ledger |
| 为什么有意思 | 五个 hardcoded "无条件屏障"（crisis, classification ceiling, consent, audit immutability, provenance）。COSE_Sign1 receipts + RFC 3161 timestamps。独立 `aevum-verify` 工具可离线验证 |
| 构建成本 | 开源，Rust |
| AI 使用方式 | Adapters for LangGraph, Anthropic SDK, OpenAI Agents, CrewAI, MCP, Google ADK, Microsoft Agent Framework |
| 技术栈 | Rust, Ed25519, COSE, SHA3-256 |
| 核心创新 | 不是"审计日志文件"——是加密签名的事件链，不可篡改，离线可验证 |
| 是否适合 Vera | **Trust 层参考**。Vera 的 Evidence Receipt 需要这个级别的不可篡改性 |
| 可借鉴点 | 1) 加密签名事件链 2) 离线独立验证 3) 五个无条件屏障 |
| 不可复制原因 | 需要 Rust 基础设施，Vera 可以从协议层吸收 pattern |

**Vera 专项：**
- **A. Research Workflow:** Agent 执行的每一步都可以被独立审计
- **B. Trust:** **终极参考**。Vera 的 Evidence Receipt 应该做到"离线可验证"——不信任运行环境的 operator 也能验证证据
- **C. Product Experience:** 审计轨迹可视化——"这个结论经过了以下 7 步，每一步都有签名"

---

### 1.10 Crucible — Quality-gated 多 agent 研究

| 维度 | 分析 |
|---|---|
| GitHub | Starlight143/crucible |
| 一句话价值 | "Quality gate halts pipeline when evidence too thin"——证据不足就停止，不确定就标注 unknown |
| 为什么有意思 | 5 个 specialist analysts + parallel evidence gathering + 7-direction debate + risk-gated analysis。不支持的主张被标记为 `hallucination_flags` |
| 构建成本 | 开源 |
| AI 使用方式 | Multi-agent with quality gates |
| 技术栈 | Python |
| 核心创新 | "停止"作为默认行为——不确定就停止，而不是编造 |
| 是否适合 Vera | **Trust Gate 参考**。Vera 的 insufficient_data gate 就是这个模式 |
| 可借鉴点 | 1) Evidence threshold gate 2) Unknown > Hallucination 3) 7-direction debate |
| 不可复制原因 | 通用研究框架，Vera 已有自己的 gate 设计 |

**Vera 专项：**
- **A. Research Workflow:** 证据不足 → pipeline halt → 标注 unknown，不要生成
- **B. Trust:** `hallucination_flags` → Vera 的 `hallucination_risk` QC 维度
- **C. Product Experience:** 质量门状态可视化——绿灯（通过）/ 黄灯（部分证据）/ 红灯（证据不足，halt）

---

## 2. 五个 AI Native 产品规律

### Pattern 1: Single-Purpose > Platform

成功的项目都做一件事。MakerChecker 只管 maker/checker 分离。Aevum 只管审计日志。Tessera 只管 evidence grounding。Spec Kit 只管 spec→code。

**对 Vera 的启示：** Vera 的每个模块（Evidence Manifest, Trust Gate, Provider Adapter）应该是独立可用的单功能组件，而不是巨型平台的一个子模块。

### Pattern 2: Deterministic Harness + LLM Judgment

Athena Loops 的核心理念：**循环是代码，判断是 prompt。** 控制流（fan-out, aggregate, gate, retry）是确定性的 Python/TypeScript。LLM 只负责需要判断的部分（decomposition strategy, review rubric）。

**对 Vera 的启示：** Vera 的 Agent 编排应该是确定性代码，Prompt 只是可替换的策略层。Trust Gate 的逻辑（gate open/closed）是代码，不是 LLM 调用。

### Pattern 3: Maker/Checker as Architecture, Not Prompt

MakerChecker、Athena Loops、auto-cmux 都实现了**身份分离**：做的人和审的人必须是不同的 agent identity，使用不同的 model。审查者不能修改它审查的东西（只读权限）。

**对 Vera 的启示：** Vera 的 Builder/Reviewer 分离需要做到：Reviewer 是一个独立的 agent identity，没有 write 权限，使用不同的模型，review 结果必须有加密签名。

### Pattern 4: Evidence-First, Ship Ugly

Tripwire 的"Disconfirming evidence first"。Mira 的 thesis refresh boundary。Crucible 的 evidence threshold gate。FinSight-AI 的 evidence traceability。

**共同点：** 不确定的东西标注 unknown，不编造。证据不足时 pipeline halt。可证伪条件内置在输出里。

**对 Vera 的启示：** Research Output 应该自带"什么情况下这个结论不再成立"和"claim → source 映射"。

### Pattern 5: 1 Week MVP, 1 Month Stable（极低成本验证）

手工川：一周 MVP，一个月上线。Jon Cheney：一个周末 $400 构建完整业务。Aakash Gupta：$0 资金 3 个产品。

**共同方法论：**
1. 先交付"59 分"产品验证需求
2. 用真实用户反馈驱动迭代
3. AI 做 build，人做 test 和 domain judgment
4. 瓶颈不在技术，在"应该构建什么"

**对 Vera 的启示：** Vera 的每个新能力（新的 Provider、新的分析类型）应该走"一周实现+一个月稳定"的快节奏，不追求首次完美。

---

## 3. 对 Vera 的 10 个可借鉴点

| # | 借鉴点 | 来源 | Vera 应用 |
|---|---|---|---|
| 1 | **Spec-as-Contract** | Spec Kit | Evidence Manifest 作为 Agent 的不可变合同——Agent 不能偏离 manifest 定义的 evidence boundary |
| 2 | **Harness ≠ Skill** | Athena Loops | Agent 编排逻辑是确定性 Python 代码，Prompt 是可替换策略层——Trust Gate 永远不应是 LLM 判断 |
| 3 | **Maker/Checker 加密分离** | MakerChecker + Aevum | Builder 和 Reviewer 是不同的 agent identity + 不同 model + Reviewer 无 write 权限 |
| 4 | **Faithfulness Score as CI Gate** | Tessera | claim → source 回溯率 < 100% → pipeline fail。自动化、量化、强制 |
| 5 | **Thesis Lifecycle** | Mira + Tripwire | Research Output 从一次性快照升级为持久化实体：`stale_after`, `must_refresh_if`, tripwire conditions |
| 6 | **Evidence Threshold Gate** | Crucible | 证据不足 → halt，不生成。`hallucination_flags` 标记未验证的主张 |
| 7 | **Compute/Narrate 分离** | FinRobot | Provider 层管数字（确定性），Agent 层管叙事（LLM）。两层不混合 |
| 8 | **Idempotency + Single-Flight** | FinSight-AI | 研究任务去重——同一 query 的重复请求不触发重复计算 |
| 9 | **离线可验证审计** | Aevum | Evidence Receipt 加密签名，不信任 operator 也能独立验证 |
| 10 | **Ship Ugly, Validate Demand** | Vibe Coding 案例 | 新能力先交付 MVP，用真实用户反馈驱动迭代，不追求首次完美 |

---

## 4. 不应该学习的反模式

### Anti-Pattern 1: 巨型 Agent 平台

**症状：** "一个 Agent 做所有事"——1 个 prompt 试图同时做 data collection + analysis + report + review
**为什么失败：** 上下文窗口污染、责任不清、无法独立验证每一步
**Vera 现状：** Vera 已经是分层架构（Provider → Agent → Gate → Output），保持这个方向

### Anti-Pattern 2: Prompt-Only Guardrails

**症状：** "请在回答前仔细检查事实"——把验证放在 prompt 里
**为什么失败：** LLM 不能可靠地自我审查。prompt 里的 guardrail 不是 guardrail
**Vera 现状：** QC 已经有硬编码的 `_qc_auction()`，保持代码层 gate

### Anti-Pattern 3: "看起来对"的 Demo

**症状：** RAG demo 跑通 → 宣称产品完成。但没有处理 stale data、missing source、edge case
**为什么失败：** demo 和生产的差距在于 resilience，不在于 happy path
**Vera 现状：** Evidence Governance 已经在处理这个问题——继续推进 Runtime Evidence 闭环

### Anti-Pattern 4: 不断扩 prompt

**症状：** 每次出错就往 prompt 里加一句话。6 个月后 prompt 2000 行
**为什么失败：** prompt 膨胀 → 上下文污染 → 性能退化 → 更难 debug
**替代方案：** 改 harness（代码），不改 prompt。规则进 CLAUDE.md/skills，不进 system prompt

### Anti-Pattern 5: 自审自批

**症状：** 同一个 agent/model 既写又审。"请审查你刚才的输出"
**为什么失败：** 模型对自己的错误有盲区。自审通过率虚高
**Vera 现状：** D28 已经规定了 Builder/Reviewer 分离——不要因为"省 token"而合并

---

## 5. 下一阶段可快速验证的小实验

### Experiment 1: Spec-as-Contract for One Research Task（1 周）

**目标：** 为一个研究任务（如"集合竞价分析"）写 Evidence Manifest → 让 Agent 严格按 manifest 执行 → 验证 deviation rate
**验证：** Agent 是否会产生 manifest 之外的主张？如果有，gate 是否拦截？
**成本：** 0（需要写一个 manifest 文件 + 修改一处 gate 逻辑）
**来源：** Spec Kit 的 `spec.md` 模式

### Experiment 2: Maker/Checker Identity Separation（1 周）

**目标：** 为一次研究任务使用两个不同的 agent identity（Builder=Sonnet, Reviewer=Opus），Reviewer 只有只读工具
**验证：** Reviewer 是否发现了 Builder 未发现的问题？Reviewer 的拒绝率是多少？
**成本：** ~$0.5-2 API 费用
**来源：** MakerChecker + Athena Loops

### Experiment 3: Faithfulness Score Prototype（2 周）

**目标：** 为一个 Research Output 建立 claim → source 映射，计算 faithfulness score
**验证：** 哪些 claim 找不到 source？faithfulness score 是否低于预期？
**成本：** 0（手工标注 + 现有 Evidence Manifest 字段）
**来源：** Tessera 的 faithfulness CI gate

### Experiment 4: Thesis Lifecycle Prototype（2 周）

**目标：** 为一个已有 Research Output 加上 `stale_after` 和 `must_refresh_if` 字段
**验证：** 7 天后再请求同一分析，系统是否自动标记 stale？是否触发 refresh？
**成本：** 0（加字段 + 加一个 freshness check）
**来源：** Mira + Tripwire

### Experiment 5: Ship Ugly — 一个新 Provider Adapter 的 5 天上线（1 周）

**目标：** 选一个以前没接的数据源（如 OpenBB 或 FRED），5 天内走完 "Provider → Adapter → QC → Agent → Output" 全链路
**验证：** 不走完美路线——先产出能跑的，再迭代。记录实际耗时 vs 预估
**成本：** 可能 $0-5 API 费用（取决于数据源）
**来源：** Vibe Coding 的 "1 week MVP" 节奏

---

## 6. 特别关注：三个类比方向

### 6.1 JeniCards 类 —— AI 帮 AI 改进输入

**模式：** 不是人类写更好的 prompt，而是 AI 帮人类构建更高质量的研究任务定义
**Vera 对应：** Agent 如何在接到研究请求后，自动 refine query、识别 missing dimensions、提出澄清问题
**借鉴项目：** Spec Kit 的 clarify 步骤 —— AI 不确定就问，不猜

### 6.2 Nixly 类 —— Prompt + Guardrail 控制质量

**模式：** 在 prompt 层面设置硬约束（必须包含 X、不能超过 Y、如果 Z 则 fallback）
**Vera 对应：** Trust Gate 前置约束 —— 不是事后审查，而是执行前就定义了"什么算通过"
**借鉴项目：** MakerChecker 的静态风险扫描器 —— 执行前就知道哪些操作需要审批

### 6.3 BrandPeek 类 —— 低成本完成复杂产品

**模式：** 用极低成本（$0-500）验证一个复杂场景的产品可行性
**Vera 对应：** 如何在 1-2 周内验证"一个金融研究 Agent 能比原始 ChatGPT 好多少"
**借鉴项目：** Jon Cheney 的 $400 周末构建 → 5 天后 $15K 订单 → 6 个月 $1M 收入

---

## 7. 核心结论

> **在 AI 编程时代，一个小团队如何用 Agent + Governance + 极低成本，持续构建可信产品？**

答案不在某一个项目里，而在五个规律的组合：

1. **单功能组件 + 确定性编排** — 每个模块做一件事，编排逻辑是代码不是 prompt
2. **Maker/Checker 架构分离** — 做的人和审的人是不同身份，审查者不能修改
3. **Evidence-First** — 不可证明的主张被拒绝，不确定的标注 unknown
4. **量化 Faithfulness** — 信任不是二元的，是可以 CI 度量的连续指标
5. **Ship Ugly → Evidence → Iterate** — 先跑通，再收集证据，再优化。不追求首次完美

**Vera 当前的最大机会：** 从 "Feature Development" 节奏转向 "Pattern Absorption + Rapid Validation" 节奏。竞争对手不是其他金融 AI 产品，而是"不用 AI 的分析师"。胜利条件不是功能更多，而是**证据更可信 + 构建更快**。

---

*Sources: GitHub trending (2026 W31), awesome-vibe-coding, Athena Loops, MakerChecker, Mira, FinSight-AI, FinRobot, Tripwire, Aevum, Tessera, Crucible, Spec Kit, various vibe coding case studies*
