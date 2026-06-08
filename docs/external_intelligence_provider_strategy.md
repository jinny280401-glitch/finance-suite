# External Intelligence Provider Strategy

日期：2026-06-08

## 1. 决策

Finance Suite 将外部智能输入分为四层：

1. **Provider**：产生原始数据或外部证据，例如 Wind、iFinD、Choice、Tushare、JoinQuant、AkShare、Tavily。
2. **Skill**：提供方法论、研究框架、输出模板或核验清单，不产生数据。
3. **Agent**：执行任务编排、检索、分析、审阅或对话。
4. **Research System**：拥有最终研究编排权，负责 Provider Route Policy、QC、Trust Gate、Section Workflow 和 ReportAssembly。

`serenity-skill` 在本体系内被分类为 **Methodology Consumer**。它只能消费已经通过系统边界处理的 evidence 或 report section，输出研究框架、核验清单、候选优先级和对话素材；它不是 Provider，不拥有数据源，不参与 QC，不参与 Trust Gate producer 侧，不修改 ReportAssembly。

## 2. 背景

Serenity Skill 适合产业链、供应链、卡点、瓶颈、主题深度调研类任务。它补足的是主题研究的方法论层，而不是 Finance Suite / trading-system 的数据 runtime。

如果第三方 skill 被允许反向定义 Provider、QC 或 Trust Gate 边界，Research Runtime 会被上游方法论工具反向塑形，最终导致：

- Provider usage 被绕过。
- `_qc` 与 freshness 被弱化。
- Trust Gate producer 白名单失效。
- ReportAssembly 混入未验证 evidence。
- 量化筛选路径被主题研究 prompt 接管。

因此先冻结边界，再允许项目级 skill 接入。

## 3. 五条红线

1. **Skill 不注册 Provider**：不得写入 Provider Registry，不得声明 allowed_usage 或 quota。
2. **Skill 不生产 Evidence**：不得绕过 Gateway、QC、Trust Gate 直接生成可进报告的 evidence。
3. **Skill 不进入 Trust Gate producer 侧**：Trust Gate 只接收 Provider/Gateway 产物；Skill 只能在 Trust Gate 之后消费已处理结果。
4. **Skill 不修改 ReportAssembly**：不得让 ReportAssembly 读取 skill 生成的 raw prompt、raw source 或未经 Trust Gate 的字段。
5. **Skill 不接管默认 runtime**：黄金坑、因子扫描、个股快照、快答、四重门继续走原 Finance Suite / trading-system 数据链路、QC 和 Trust Gate。

## 4. Consumer Contract

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

## 5. 与现有契约的关系

- `docs/provider_route_policy.md` 定义 Provider 的 allowed_usage / disallowed_usage；Skill Consumer 不占用 Provider allowed_usage 配额。
- `docs/trust_gate_runtime_v0.md` 定义 Gateway Response 到 Evidence Bundle 的强制转换；Skill Consumer 只能位于 Trust Gate 之后。
- `docs/report_assembly_contract_v0.md` 约束 ReportAssembly 输入；Skill Consumer 不得成为 ReportAssembly 的 raw input。
- `/Users/Zhuanz/trading-system/.claude/skills/serenity-skill/` 是项目级安装，不进入 user-level skill 池。

## 6. Serenity 接入状态

Serenity Skill 的项目级安装属于本 ADR 的 P1 子项：

- 安装位置：`/Users/Zhuanz/trading-system/.claude/skills/serenity-skill/`
- 触发范围：产业链、供应链、卡点、瓶颈、主题深度调研
- 禁止范围：黄金坑、因子扫描、个股快照、快答、四重门
- 运行边界：Methodology Consumer，只读 evidence / section output / user prompt，不拥有 Provider runtime

后续任何 Serenity 代码接入、Prompt 接入或 Agent 编排接入，都必须先证明不违反本 ADR 的五条红线。
