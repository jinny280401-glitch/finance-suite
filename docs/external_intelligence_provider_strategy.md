# External Intelligence Provider Strategy

日期：2026-06-08

## 1. 决策

本 ADR 冻结一条顶层治理约束：

```text
Provider 永不反向定义 Runtime。
```

Finance Suite 将外部智能输入分为四层：

1. **Provider**：产生原始数据或外部证据，例如 Wind、iFinD、Choice、Tushare、JoinQuant、AkShare、Tavily。
2. **Skill**：提供方法论、研究框架、输出模板或核验清单，不产生数据。
3. **Agent**：执行任务编排、检索、分析、审阅或对话。
4. **Research System**：拥有最终研究编排权，负责 Provider Route Policy、QC、Trust Gate、Section Workflow 和 ReportAssembly。

`serenity-skill` 在本体系内被分类为 **Methodology Consumer**。它只能消费已经通过系统边界处理的 evidence 或 report section，输出研究框架、核验清单、候选优先级和对话素材；它不是 Provider，不拥有数据源，不参与 QC，不参与 Trust Gate producer 侧，不修改 ReportAssembly。

## 2. North Star 原则

1. **Runtime owns orchestration**：Research Runtime 决定研究编排、证据准入、Section Workflow 和 ReportAssembly。Provider、Skill、Agent 都不能反向定义主链路。
2. **Gateway owns provider normalization**：Provider 只能进入 Gateway；Provider-specific schema 不得泄漏到 GatewayResult / FinanceDataResponse 之后。
3. **Trust Gate owns LLM eligibility**：LLM 永远不直接消费 Provider Output 或 raw Gateway Response，只消费 Evidence Bundle / Section Output。

这三条原则与 `docs/data_gateway_v1_contract.md` 的 6 阶段链路一致：

```text
Provider
↓
Gateway
↓
QC
↓
Trust Gate
↓
Evidence
↓
LLM
```

## 3. 背景

Serenity Skill 适合产业链、供应链、卡点、瓶颈、主题深度调研类任务。它补足的是主题研究的方法论层，而不是 Finance Suite / trading-system 的数据 runtime。

如果第三方 skill 被允许反向定义 Provider、QC 或 Trust Gate 边界，Research Runtime 会被上游方法论工具反向塑形，最终导致：

- Provider usage 被绕过。
- `_qc` 与 freshness 被弱化。
- Trust Gate producer 白名单失效。
- ReportAssembly 混入未验证 evidence。
- 量化筛选路径被主题研究 prompt 接管。

因此先冻结边界，再允许项目级 skill 接入。

## 4. 五条红线

1. **Skill 不注册 Provider**：不得写入 Provider Registry，不得声明 allowed_usage 或 quota。
2. **Skill 不生产 Evidence**：不得绕过 Gateway、QC、Trust Gate 直接生成可进报告的 evidence。
3. **Skill 不进入 Trust Gate producer 侧**：Trust Gate 只接收 Provider/Gateway 产物；Skill 只能在 Trust Gate 之后消费已处理结果。
4. **Provider schema 不越过 Gateway**：`docs/data_gateway_v1_contract.md` 第 1 节已明文禁止 Provider 直接把原始数据送进 LLM。本 ADR 不重写该规则，只把它提升为外部智能接入红线。
5. **allowed_use 决定可用语义**：`docs/trust_gate_contract.md` 已通过 `EvidenceBundle.allowed_use` 落地 prompt 权限白名单。Skill / Agent 不能扩大 allowed_use，只能读取或收窄使用语境。

补充约束：Skill 不接管默认 runtime。黄金坑、因子扫描、个股快照、快答、四重门继续走原 Finance Suite / trading-system 数据链路、QC 和 Trust Gate。

## 5. ProviderClass 命名

ADR 与代码统一使用大写枚举名：

```text
MOCK / FALLBACK / REAL
```

代码落点：

- `research_runtime/evidence_bundle.py`
- `smoke_trust_gate_premerge.py`

含义：

- `MOCK`：只能用于 `workflow_smoke` / `runtime_test`，不得进入生产发布 Section。
- `FALLBACK`：只能用于低风险 overview / historical context，不得生成市场择时、仓位、买卖建议。
- `REAL`：可进入完整分析能力，但仍必须经过 QC、Trust Gate、Evidence Bundle。

## 6. stock_analysis=PARTIAL 落点

`stock_analysis=PARTIAL` 的规则不由 Serenity 或任何 skill 决定。它由 Trust Gate 的 `allowed_use` 字段决定。

允许：

```text
fundamental_overview
```

禁止：

```text
short_term_signal
fund_flow
position_sizing
buy_sell_recommendation
```

当前落地文件：

- `docs/trust_gate_contract.md`
- `docs/trust_gate_runtime_v0.md`
- `research_runtime/evidence_bundle.py`
- `smoke_trust_gate_runtime_v0.py`
- `smoke_trust_gate_workflow_v1.py`
- `smoke_trust_gate_premerge.py`

## 7. Consumer Contract

Methodology Consumer 必须满足：

- `consumer_class = methodology_consumer`
- `provider_registration = false`
- `evidence_producer = false`
- `trust_gate_producer = false`
- `report_assembly_writer = false`
- `allowed_inputs = trust_gate_evidence | section_output | user_prompt | public_source_path`
- `allowed_outputs = research_framework | verification_checklist | ranked_research_priority | prompt_pack`
- `disallowed_outputs = raw_provider_data | executable_trade_signal | buy_sell_instruction | report_evidence`

`serenity-skill` 当前只允许：

- 读取用户问题和已通过边界处理的研究素材。
- 组织产业链层级、scarce layer、证据强弱、风险和下一步核验。
- 输出 research partner 对话素材或 prompt pack。

## 8. 与现有契约的关系

- `docs/data_gateway_v1_contract.md` 定义 Provider → Gateway → QC → Trust Gate → Evidence → LLM 的主链路，并禁止 Provider 原始数据直接进入 LLM。
- `docs/provider_route_policy.md` 定义 Provider 的 allowed_usage / disallowed_usage；Skill Consumer 不占用 Provider allowed_usage 配额。
- `docs/trust_gate_contract.md` 定义 EvidenceBundle.allowed_use；Skill Consumer 不得扩大 allowed_use。
- `docs/trust_gate_runtime_v0.md` 定义 Gateway Response 到 Evidence Bundle 的强制转换；Skill Consumer 只能位于 Trust Gate 之后。
- `docs/report_assembly_contract_v0.md` 约束 ReportAssembly 输入；Skill Consumer 不得成为 ReportAssembly 的 raw input。
- `docs/research_runtime_v1_gap_analysis.md` 明确 Research Runtime v1 仍处 Gap Analysis；因此本 ADR 是治理边界，不声称所有代码路径已经全量接入 Trust Gate。
- `/Users/Zhuanz/trading-system/.claude/skills/serenity-skill/` 是项目级安装，不进入 user-level skill 池。

## 9. Sprint 顺序

Trust Gate Runtime Sprint 2 已 CLOSED。Research Runtime v1 仍处 Gap Analysis。

Sprint 3 起点应加入：

```text
P0a: Strategy ADR freeze
```

P0a 完成后再进入 Provider / Skill / Agent 的具体 P1 接入项。Serenity Skill 项目级安装是 P1 子项，但任何进一步接入必须引用本 ADR。

## 10. Serenity 接入状态

Serenity Skill 的项目级安装属于本 ADR 的 P1 子项：

- 安装位置：`/Users/Zhuanz/trading-system/.claude/skills/serenity-skill/`
- 触发范围：产业链、供应链、卡点、瓶颈、主题深度调研
- 禁止范围：黄金坑、因子扫描、个股快照、快答、四重门
- 运行边界：Methodology Consumer，只读 evidence / section output / user prompt，不拥有 Provider runtime

后续任何 Serenity 代码接入、Prompt 接入或 Agent 编排接入，都必须先证明不违反本 ADR 的五条红线。

## 11. Non-Goals

本 ADR 不做：

- 不接 Wind。
- 不接 iFinD / Choice 新能力。
- 不实现 Provider Registry。
- 不实现 Gateway strategy engine。
- 不修改 Trust Gate Runtime。
- 不修改 Research Runtime v1。
- 不声明 Trust Gate Runtime 已经全量覆盖所有 Provider 路径；具体覆盖度以 `trust_gate_runtime_sprint*_acceptance.md` 与 smoke 结果为准。

特别声明：

今天接 Wind、明天接 Alice、后天接 Bloomberg，都不能让外部 Provider、外部 Skill、外部 Agent 反向定义 Finance Suite Runtime。新外部智能源只能在本 ADR 定义的四层模型内登记，并接受 Provider Route Policy、QC、Trust Gate、Evidence、ReportAssembly 的现有边界。
