# 林妹妹 Agent v2.0 — 金融研究 OS

林妹妹是基于 OpenClaw + Finance Suite MCP 技术栈打造的金融投研数字员工，7×24 小时在线。
v2.0 阶段的核心变化是**底层架构从"工具集合 + 数据源 + 生成结果"升级成 Intent Layer → Workflow Runtime → Research Runtime → QC → Trust Gate → Report Assembly**。

围绕这条主干，本次重写把产品拆成 **7 个模块**，而不是过去的 5 个功能点。

> **每个研究结论都能追溯到具体证据、数据源、时间戳与允许用途（Allowed Use）。**

---

## 系统能力图

```
            用户
             ↓
        Intent Layer          ← 模块 1：智能意图路由
             ↓
        Workflow Runtime
             ↓
        Research Runtime       ← 模块 2：金融研究引擎
             ↓
        QC Layer               ← 模块 2 内置
             ↓
        Trust Gate             ← 模块 3：可信研究系统
             ↓
        Evidence Bundle
             ↓
        Report Assembly
             ↑
   Finance Data Gateway       ← 模块 4：金融数据网关
             ↑
        External Intelligence  ← 模块 6：外部情报与年报季报验证
         (Serenity · G Method)
```

---

## 七大功能模块

### 模块 1 — 智能意图路由层（Intent Layer）【新增】

这是最近最大的新增能力。

可识别的意图类别：

- 个股研究
- 市场脉搏
- 集合竞价
- 科技早盘
- 深度研究
- 板块热度
- 新闻解读
- 视频拆解

**解决的问题**

过去：用户说"科技早盘"，Agent 把它识别成个股研究 → 直接进入 `stock_analysis` → 报错。

现在：Intent Layer 先判断用户想要什么 → 再选择对应的 Workflow → 最后调用匹配的 Provider。路由过程会写入 `routing_reasoning` + `routing_evidence`，任何一次错配都能复盘。

这是 Runtime 重构最重要的成果之一，也是 v2.0 区别于 v1 的入口标志。

---

### 模块 2 — 金融研究引擎（Research Runtime）【升级】

对应 Research Runtime v0.8。

支持两类研究：

| 研究类型 | 章节形态 |
| --- | --- |
| 个股研究 | 基本面、财务、估值、一致预期、产业链 |
| 深度研究 | 多章节报告、Section 依赖关系、Evidence 驱动生成 |

v2.0 的关键升级：

- **Section QC**：每个章节有独立的质检结果（`passed` / `warnings` / `errors`）。
- **Evidence Bundle**：原始 Gateway 响应经过 `_strip_blocked_fields` + provider 分类 + trust_status 判定后，才能进入推理链路。
- **Citation Contract**：每个 claim 必须挂到至少一个 evidence_id；不允许"裸结论"。
- **Lineage 追溯**：从最终 report 反向追到 provider，再追到原始数据源。

状态机：`INIT → PLAN → RETRIEVE → BUILD_CONTEXT → ANALYZE → QC → SYNTHESIZE → DONE`，任意阶段失败进入 `FAILED`。

不再是单次 prompt + LLM 直出。

---

### 模块 3 — Trust Gate 可信研究系统【新增】

这是最近新增且最重要的能力，也是 Finance Suite 现在的**核心护城河**。

**过去链路**

```
Provider → LLM
```

**当前链路**

```
Provider → QC → Trust Gate → Evidence Bundle → LLM
```

**三档可信契约**

| Provider 类别 | Trust Status | 允许使用场景 |
| --- | --- | --- |
| `MOCK`（仅 smoke test） | `passed` | 仅 `smoke` |
| `FALLBACK`（降级数据） | `passed` | 仅 `overview`（基本面速览） |
| `PRODUCTION`（真实生产数据） | `passed` | `overview` / `analysis` / `production_research` |

**禁止行为**

- 短线建议
- 资金流推断
- 仓位建议
- 交易建议

**强制阻断字段**：`_qc`、`raw`、`payload` —— 这三个字段不得进入 LLM 上下文，必须在 Evidence Bundle 阶段被剥离。

**Trust Gate 拒绝路径**：`missing_source` 或 `missing_content` 直接返回 `blocked`，不允许任何后续推理。

---

### 模块 4 — 金融数据网关（Finance Data Gateway）【保留并改名】

原名称"多源数据自动降级"已不再准确，改名为 **Finance Data Gateway**。

**已接入数据源**

- Wind
- Tushare Pro
- JoinQuant（聚宽）
- 东方财富
- 同花顺 iFinD
- Tavily / Brave 搜索
- 公开新闻源（新浪财经 / 雪球 / 知乎）

**Provider 状态机**

明确区分 **REAL / FALLBACK / MOCK** 三档，这是 v2.0 新增的关键规则：

- **不能**再用"有返回结果 = 能力完成"作为宣传口径。
- 必须显式标注每个 Provider 当前命中的档位（`_qc.fallback_source`）。
- MOCK 数据仅出现在 smoke test，任何对外报告出现 MOCK Provider 即视为异常。

**为什么改名**：网关（Gateway）的语义是"前端只看见一个统一出口"，比"自动降级"更能体现 Provider Runtime 的职责边界。

---

### 模块 5 — 市场温度计（Market Temperature）【新增规划模块】

最近已完成 **Contract + Benchmark + Acceptance** 三件套：

- Architecture：**PASS**
- Implementation：**HOLD**（待 G 显式启动）

**输出**

- 市场温度（risk-on / neutral / risk-off）
- 热点主题
- 风险偏好
- 情绪状态

**强制约束**

- **Explainable**：每个分数必须能解释，禁黑盒分数。
- **Evidence Traceable**：必须能溯源到原始证据（数据 + 来源 + 时间），禁无法溯源评分。
- **Mini Card 原则**：一句话市场结构 + 三因子 + 一入口，禁长报告。

这块还在 Architecture 阶段，**不能**对外宣称已上线。

---

### 模块 6 — 外部情报与年报季报验证（External Intelligence）【新增】

这是 Serenity 接入后形成的新模块，也是 G 方法论在产品侧的**Methodology Consumer**。

**定位**

External Intelligence **不是** Provider、**不是** Runtime、**也不是** Trust Gate。它是独立的能力层，只消费 G 方法论，不参与 Runtime 编排。

**核心数据源（不是八卦，是公司自己签字盖章的官方文件）**

- **年报 / 季报** —— A 股、港股、美股（10-K / 10-Q）的标准定期报告
- **招股说明书** —— IPO / 再融资时披露的完整公司信息
- **重大事项公告** —— 监管要求下的强制披露事项（关联交易、收购、扩产等）

> 之前用「工商变更 / 客户访谈 / 行业新闻」描述这套链路——但这些都是二手信息。Serenity 现在只从**年报、季报、招股书、公告**里抽取，公司对自己内容签字盖章。

**当前作用（按 G 方法论的 Field → Rule → Verdict）**

| 阶段 | 做什么 | 产物 |
|---|---|---|
| **Field 抽取** | 从年报 / 季报的「管理层讨论」「主营业务」「财务报表附注」里抽结构化字段 | 营收分项、前五大客户、在建工程、产能利用率、关联交易 |
| **Rule 套用** | 用确定性规则判断字段是否触发异常 | 例如:前五大客户集中度 > 60% → flag 供应链风险 |
| **Verdict 产出** | Rule 输出即结论,**不依赖 LLM** | verdict = "供应链高集中风险" / "扩产进度滞后" 等 |
| **Evidence 追溯** | 每条结论都能回到「年报 P.XX / 第 X 节 / 表 X」 | Evidence Bundle 的 page+section 引用 |

**已经在用的案例（每条都基于具体年报 / 季报）**

- 沐邦（**2025 年报**——玩具 + 光伏跨界）
- 派能（**2026 一季报**——储能扩产进度）
- 北方华创（**2025 年报**——半导体设备产业链）
- 工业富联（**2025 年报**——代工业务客户结构）

这些 case 都在做验证体系建设，Serenity 用 G 方法论做**cross-case 锚点**——同一个 rule 套到不同公司的年报上，横向比较才有意义。

**为什么不让 Provider Runtime 干这事?**

- Provider Runtime 拿的是**实时行情 / 财务快照**(Wind、Tushare、JQ、东财),颗粒度到日频
- External Intelligence 拿的是**报告期切片**(年报、季报、招股书),颗粒度到季
- 两层数据**不可替代**:实时数据看不到客户集中度,年报数据看不到今天的异动
- 因此 External Intelligence 是**独立能力层**,不是 Provider 的扩展,不是 Runtime 的子模块,也不是 Trust Gate 的兜底

---

### 模块 7 — 自动化助手体系（保留并扩展）

**晨会助手**

- 集合竞价扫描
- 科技早盘
- 市场温度扫描

**自选股监控**

- 价格提醒
- 异动提醒
- 资金变化

**内容助手**

- 视频拆解（YouTube / B 站）
- 新闻聚合（7x24）
- 研报摘要

**多端触达**

- 微信 / 飞书 / 企微 / Web

---

## 已下线 / 不再宣传的旧卖点

| 旧卖点 | 处置 |
| --- | --- |
| "已接入 12 个金融数据源" | ❌ 删除。改成"金融数据网关 + Provider Runtime" |
| "Wind 失败 → Tushare 立即接管" | ❌ 删除。改成"REAL / FALLBACK / MOCK 三档状态机" |
| "38 天无宕机" | ❌ 删除。改成"生产环境持续运行，自动降级机制保障服务连续性" |

理由：v2.0 阶段核心竞争力已从"数据源数量 + 故障接管"转移到"Trust Gate + Evidence Bundle + Intent Layer"，旧卖点会误导客户对护城河的判断。

---

## 三、核心技术栈（v2.0）

- **OpenClaw** — 多渠道统一路由网关
- **Finance Suite MCP Server** — 数据网关 + Research Runtime + Trust Gate 实现
- **Research Runtime v0.8** — 状态机驱动的本地研究引擎
- **Contract Layer** — Data / Evidence / Trust Gate / Section / Artifact 五件套（`docs/architecture/contracts/`）
- **多模型聚合**（OpenRouter：Claude / Gemini / Kimi / GLM） — 仅作为文本理解组件，不做唯一决策者

---

## 四、Demo 场景设计（3 个，可现场演示）

### 场景一：科技早盘 — 路由分类（2 分钟）

**痛点**：用户口语化的需求（如"科技早盘"）过去会被误识别为个股研究，导致工具错配。

**演示步骤**

1. 微信发送："科技早盘"
2. Intent Layer 命中 `科技早盘` 意图，写入 `routing_reasoning` + `routing_evidence`
3. Workflow 触发集合竞价 + 板块热度扫描，返回今日开盘 15 分钟科技板块异动清单
4. 展示路由证据链（每一步都可以解释为什么走这条路）

**Wow 时刻**：让评委看到"科技早盘"和"个股研究"在底层是完全不同的两条路径，不再是同一个 stock_analysis 的不同 prompt。

**预计时长**：2 分钟

---

### 场景二：派能储能 — Trust Gate 边界演示（3 分钟）

**痛点**：传统金融 Agent 会给出"建议买入 / 仓位 / 止损位"等越界内容，存在合规风险。

**演示步骤**

1. 提问："派能储能现在能买吗？给个仓位建议。"
2. Trust Gate 拒答：返回 `blocked`，reason = `blocked_field_position_recommendation`
3. 自动 fallback 到允许路径：返回基本面速览（overview）+ 派能扩产进度（External Intelligence 验证）
4. 展示 Evidence Bundle：每条结论都挂到 evidence_id，可溯源到 Wind 财报 / 公司公告 / 行业研究

**Wow 时刻**：让评委看到 Agent **主动拒绝越界请求**，而不是顺着用户瞎说。

**预计时长**：3 分钟

---

### 场景三：沐邦 — External Intelligence 年报字段验证（3 分钟）

**痛点**：单靠行情数据看不到公司跨界业务的真实结构，年报里"玩具 + 光伏"的拆分才是硬证据。

**演示步骤**

1. 提问："沐邦的玩具业务是否真实支撑光伏跨界？"
2. Research Runtime 启动深度研究 workflow
3. External Intelligence（Serenity）从**沐邦 2025 年报**抽取:
   - Field: 营收分项（玩具 vs 光伏）、前五大客户、在建工程、关联交易
   - Rule: 客户集中度 > 60% → flag；光伏在建工程 vs 玩具营收 → 跨界强度判定
   - Verdict: "玩具现金牛 / 光伏在建烧钱" 或 "光伏已自给现金流"
4. QC → Trust Gate → Evidence Bundle → 报告生成
5. 展示最终报告：每个 claim 都能回到「沐邦 2025 年报 P.XX / 第 X 节 / 表 X」

**Wow 时刻**：让评委看到 cross-source 验证链——同一结论被多份年报 / 季报的同名字段支持，且每个字段都可证伪。

**预计时长**：3 分钟

---

## 五、差异化优势总结

| 维度 | 通用 ChatGPT / Claude | 林妹妹 Agent v2.0 |
| --- | --- | --- |
| **意图识别** | 单轮 prompt，无路由 | Intent Layer + 8 类意图，路由可解释 |
| **金融数据深度** | 无实时行情 | Finance Data Gateway + Wind/Tushare/JQ/AkShare/东财/同花顺 直连 |
| **数据可信度** | 无质检机制，幻觉严重 | Trust Gate 三档契约，禁越界、禁幻觉 |
| **Provider 透明度** | 黑盒 | REAL/FALLBACK/MOCK 三档显式标注 |
| **研究结构** | 一次性 prompt 输出 | Research Runtime 状态机 + Section QC + Evidence Bundle |
| **跨源验证** | 单一来源 | External Intelligence（Serenity）从年报 / 季报 / 招股书抽字段,G 方法论 Field→Rule→Verdict |
| **合规边界** | 用户提什么答什么 | Trust Gate 主动拒绝越界（短线 / 仓位 / 交易建议） |
| **多渠道** | 仅 Web | 微信 / 飞书 / 企微 / Web 一套 Agent 实例 |

---

## 六、v2.0 当前真实状态（不夸大）

### 可宣传（已实现）

| 模块 | 状态 |
| --- | --- |
| Intent Layer | ✅ 已上线，8 类意图 |
| Research Runtime | ✅ v0.8，smoke 5/5 |
| Finance Data Gateway | ✅ Wind → Tushare → JQ → 东财 主链路上线 |
| Trust Gate | ✅ Contract v0 已冻结，runtime 通过 |
| Evidence Bundle | ✅ 三档 ALLOWED_USE + 阻断字段已落地 |
| External Intelligence | ✅ Serenity 已接入 4 个 case |

### 已宣传但需注明开发中

| 模块 | 状态 |
| --- | --- |
| Market Temperature | ⚠️ Architecture PASS / Implementation HOLD；等 G 显式启动；不宣称已上线 |

### 不进入宣传（Roadmap / 内部研究线）

- ❌ Session 2 / 3（Case Validation 后续）—— 内部 gate-driven 工作
- ❌ Runtime 下一阶段（v1 之后）—— 路线图，未冻结
- ❌ Ontology —— 内部研究主题，不对外披露

---

## 七、下一阶段方向

1. **Market Temperature 实施**（Architecture 已 PASS，等 G 显式启动）
2. **Report Assembly Contract v1**（Artifact 层补齐，与现有 4 个 Contract 拼成完整链路）
3. **晨会助手接入 Market Temperature**（温度计上线后第一时间进入产品形态）
4. **商业化**：订阅制 SaaS（基础版 ¥99 / 专业版 ¥299 / 旗舰版 ¥799），目标服务 100+ 投研团队

---

**联系方式**：林嘉勤
**项目网站**：https://touziagent.com
**技术栈开源**：OpenClaw (https://github.com/cnceo/openclaw) + Finance Suite MCP Server
