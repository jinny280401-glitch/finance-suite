# VIBE_CODING_PATTERN_SYNTHESIS v0.1

**定位：** Vera 下一阶段产品战略设计输入（非研究报告）
**输入：** C 的 Vibe Coding Product Pattern Report + CC 的 Trust Infrastructure Scan
**原始报告：** `VIBE_CODING_PRODUCT_PATTERN_REPORT_v0.1.md`（CC）、C 的独立报告（Codex）—— 两篇保留为 Evidence Artifact
**目标场景：** 金融杯省赛第一
**约束：** 不增加 Governance Scope；不改生产代码；聚焦产品表达

---

## Part 1 — AI Native Product Lessons（来自 C 的报告）

### 为什么现在小团队可以快速造产品？

不是因为模型更强了。而是四个东西同时成熟了：

1. **Task Decomposition（任务拆解）**
   AI 可以把"做个金融分析工具"拆成：数据定义 → 采集 → 结构化 → 审查 → 发布。拆得越细，每步越可靠。

2. **Agent Workflow（Agent 工作流）**
   不再是一个人写 prompt → AI 一次性输出。而是 Planner → Builder → Reviewer → Gate 的循环。每一步产出可检查的中间结果。

3. **Rapid Validation（快速验证）**
   手工川一周 MVP、Jon Cheney $400 周末构建 → $15K 订单 → $1M/6个月。瓶颈不在"能不能做出来"，在"做出来的是不是别人想要的"。

4. **Continuous Iteration（持续迭代）**
   不是一次性完美交付。先出"59 分"产品 → 用户反馈 → 下一次迭代。AI 让每次迭代成本趋近于零。

### 五个不靠模型优势的产品规律

| 规律 | 含义 | Vera 应用 |
|---|---|---|
| 先卖"完成结果"，不卖"模型能力" | 首页说"10分钟得到可审计的公司研究卡"，不说"AI金融助手" | 比赛 Demo 第一屏必须是产出物，不是能力描述 |
| Prompt 不是产品边界，状态机和数据契约才是 | Prompt 漂移，Schema 可测试 | Trust Gate 是代码不是 prompt |
| 低成本 MVP 的关键是窄任务 | 一次验证一个决策，不做全能产品 | 三个 Demo 各做一件事 |
| 多 Agent 的价值来自独立性，不来自角色数量 | Reviewer 必须看原始证据，不能只润色 Builder 输出 | Adversarial Reviewer 用不同模型+只读权限 |
| 信任设计成界面，不是免责声明 | 用户一眼看到：主张、证据、来源等级、更新时间、冲突证据、审查状态 | 四栏 UI 优于聊天框 |

### 最核心的产品哲学

> **Vera 的单位产出不应是一篇报告，而是一组可复查、可拒绝、可继续迭代的研究主张。**（C）

---

## Part 2 — Why Finance Needs More Than Vibe Coding（来自 CC 的报告）

### 普通 Vibe Coding 的链路

```
Idea → Prompt → App
```

这在金融场景下不够。因为：

- Prompt 生成的"分析"可能引用过时数据
- "看起来对"的数字可能不是算出来的而是生成的
- 没有办法证明一条主张来自哪里
- 用户不知道什么时候应该相信，什么时候应该怀疑

### 金融需要的链路

```
Idea → Evidence → Claim → Review → Approval → Output
```

每一步要有证据：

| 普通 AI 产品 | Vera |
|---|---|
| "根据最新财报..." | 财报链接 + 发布时间 + 数据摘录 |
| "预计未来增长..." | **拒答**：当前证据不支持未来预测 |
| "估值合理..." | DCF 参数表 + 计算过程 + 假设清单 |
| "行业领先..." | 市场份额数据 + 来源 + 可比公司对比 |

### Vera 的差异化

不是"AI 更强"。

而是：

> **别人展示 AI 帮人写答案，Vera 展示 AI 如何在金融场景下知道什么时候应该回答，什么时候应该拒绝。**

这个差异化应该成为比赛表达的核心。

### Trust 层当前状态（如实，不夸大）

| 能力 | 状态 | 比赛如何表达 |
|---|---|---|
| Evidence Object（证据对象） | Designed | "每条主张绑定来源、时间、类型" |
| Claim Gate（主张门） | Specified | "未达证据门槛的主张自动拦截" |
| Maker/Checker 分离 | Specified | "Builder 和 Reviewer 是不同的 AI，审查者不能修改被审查的内容" |
| Cryptographic Attestation | Inspired（参考 Aevum/Tessera 设计） | "设计目标：研究结论可离线验证" |
| Offline Verification | Future Research | —（比赛不提及） |

**原则：Declared ≠ Effective。** 比赛只展示 Specified 以上的能力，不声称未验证的能力。

---

## Part 3 — Vera Target Architecture

### 不叫"Agent Architecture"

比赛评委听到"Agent 架构"会想到"又一个 chatbot"。

叫：

> **Trusted Research Production Line（可信研究生产线）**

这比 Agent 更能传达：这是一个有质量控制的流程，不是黑箱生成。

### 架构

```
User Question（用户输入自然语言问题）
        ↓
[1] Research Brief Rewriter        ← 把模糊问题变成结构化研究任务
        ↓                             范围、对象、时间窗、所需证据类型、禁止推断
[2] Evidence Collector             ← 寻找并保存事实
        ↓                             URL + 原文摘录 + 采集时间 + 来源等级
[3] Claim Builder                  ← 事实 → 结构化主张
        ↓                             每条主张绑定 Evidence Pack
[4] Trust Gates × 4               ← 自动质量检查
    ├─ Citation Gate                主张是否有来源？
    ├─ Freshness Gate               数据是否在有效期内？
    ├─ Numeric Gate                 数字是否正确？（计算 vs 生成）
    └─ Conflict Gate                是否有矛盾证据？
        ↓
    ┌─ 任一 Gate 失败 → 返回 [1] 或 [2]，重新采集证据
    │
[5] Adversarial Reviewer           ← 独立 AI，专找漏洞
        ↓                             不同模型、只读权限、只能看原始证据
    ┌─ 证据不足 → 返回 [2]
    │
[6] Human Approval                 ← 人工放行
        ↓                             展示：主张 + 证据 + Gate 结果 + Reviewer 意见
[7] Traceable Research Output      ← 可追溯输出
                                     Run ID + 模型版本 + 证据快照 + 审查记录
```

### 关键设计决策

1. **每一步有明确的"完成定义"** — 不是 prompt 说了算，是代码检查
2. **Gate 失败是正常结果** — "当前证据不足"比"生成一段看起来对的"更好
3. **Human Approval 不是摆设** — 人在此看到的是 Gate 结果 + Reviewer 质疑，不是原始 AI 输出
4. **Output 自带溯源** — 每一条主张可以点开看到证据链

---

## Part 4 — 金融杯最值得做的三个 Demo

比赛需要同时满足：普通用户一眼看懂 + 专业评委认为有技术壁垒 + 不违反 Trust Governance 边界。

### Demo 1：一分钟公司研究卡（BrandPeek 型）

**用户输入：** "帮我看看贵州茅台最近有什么变化"

**输出（不是研报，是研究卡）：**

```
贵州茅台 · 最近变化
━━━━━━━━━━━━━━━━━━━━━

变化 1：营收增速放缓
  事实：2026H1 营收同比增长 9.2%（去年同期 16.7%）
  证据：2026 半年报 第 12 页 [链接]
  解释：渠道改革红利消退，直销占比趋于稳定
  风险：消费复苏不达预期可能进一步拖累增速
  审查：✓ Citation ✓ Freshness ✓ Numeric

变化 2：批价企稳回升
  事实：飞天茅台批价从 ¥2,350 回升至 ¥2,520
  证据：今日酒价 2026-08-03 [链接]
  解释：中秋备货启动 + 厂家控量保价
  冲突证据：部分地区批价仍低于 ¥2,400（来源：XX）
  审查：✓ Citation ✓ Freshness ⚠️ Conflict（区域差异）

变化 3：分红政策调整
  事实：公司公告将分红比例从 51.9% 提升至 60%
  证据：2026-07-28 董事会决议公告 [链接]
  解释：响应监管导向，提升股东回报
  审查：✓ Citation ✓ Freshness ✓ Numeric

━━━━━━━━━━━━━━━━━━━━━
本次研究：Run #20260803-001 · 证据 7 条 · 审查通过 3/3 主张
```

**为什么讨喜：**
- 普通用户：3 条变化 + 一眼看懂，不需要读研报
- 专业评委：每条绑定证据 + 审查状态 + 冲突标注 + Run ID 追溯
- 差异化：不是"AI 说茅台会涨"，而是"这 3 条变化有 7 条证据支持，1 条有区域差异"

---

### Demo 2：AI 研究质检员（JeniCards + Nixly 型）

**场景：** 同一句话，普通 AI vs Vera 的对比

**普通 AI：**
> "公司未来增长确定，建议关注。"

**Vera：**
```
━━━━━━━━━━━━━━━━━━━━━
审查结果：❌ 无法发布
━━━━━━━━━━━━━━━━━━━━━

问题主张："公司未来增长确定"

Citation Gate：❌ 未提供支持"未来增长确定"的证据
Freshness Gate：— 不适用
Numeric Gate：❌ "增长确定"不是可量化主张
Conflict Gate：— 不适用

当前证据只支持：
  ✓ 过去 3 年营收复合增长率 12.3%（来源：年报）
  ✓ 管理层指引 2026 年增长 8-12%（来源：业绩说明会）

不支持：
  ✗ 对未来增长的确定性判断
  ✗ 对股价方向的任何预测

建议：将主张改为"过去 3 年营收复合增长率 12.3%，管理层指引 2026 年增长 8-12%"
━━━━━━━━━━━━━━━━━━━━━
```

**为什么讨喜：**
- 评委看到的是"质量控制"不是"又一个 chatbot"
- 对比展示比单独展示强 10 倍
- 技术壁垒：四道 Gate 是代码不是 prompt；Reviewer 是独立模型；Gate 失败的处理逻辑
- 这直接对应 G 说的核心差异化："知道什么时候应该回答，什么时候应该拒绝"

---

### Demo 3：研究过程透明工作台

**不是 Demo 1 和 Demo 2 的替代，是"如果评委想看内部"。**

展示界面：

```
┌─ 研究问题 ─────────────────────────────────────────────┐
│ "贵州茅台最近有什么变化？"                                │
│ → Brief Rewriter: 拆解为 3 个子任务                       │
├─ 证据采集 ─────────────────────────────────────────────┤
│ ✓ 财报数据（2026 半年报）                   来源：上交所   │
│ ✓ 批价数据（今日酒价）                       来源：第三方   │
│ ✓ 公告（分红调整）                           来源：上交所   │
│ ⚠️ 券商研报（未采用）                         原因：非一手   │
├─ 主张构建 ─────────────────────────────────────────────┤
│ 原始数据 12 条 → 结构化主张 3 条                          │
│ 舍弃主张 2 条（证据不足）                                  │
├─ Trust Gate 审查 ──────────────────────────────────────┤
│ ✓ Citation (7/7 主张有来源)                               │
│ ✓ Freshness (7/7 数据在有效期内)                          │
│ ✓ Numeric (3/3 数字经验证)                                │
│ ⚠️ Conflict (批价存在区域差异)                             │
├─ Adversarial Reviewer ─────────────────────────────────┤
│ Reviewer 意见：批价区域差异建议标注（已采纳）                │
│ Reviewer 模型：Claude Opus 5（与 Builder 隔离）            │
├─ Human Approval ───────────────────────────────────────┤
│ [展示审查结果] → [人工确认/修改/驳回]                       │
├─ 输出 ──────────────────────────────────────────────────┤
│ Run #20260803-001 · 7 条证据 · 3 条主张 · 全链追溯          │
└────────────────────────────────────────────────────────┘
```

**为什么讨喜：**
- 这不是"黑箱 AI 输出"——每一步可见、可理解、可质疑
- 评委看到的不是 prompt engineering，是工程化信任
- 用户看到的是"我有控制权"——可以在任何一步介入

---

## 三个 Demo 如何串联比赛叙事

**开场（Demo 2 — 质检员）：** 制造冲突。"大家看，普通 AI 会说'公司未来增长确定'——但我们认为这句话不应该被发布。为什么？因为它没有证据。"

**主体（Demo 1 — 研究卡）：** 展示正面能力。"当有证据的时候，Vera 可以在 1 分钟内产出可审计的研究卡。"

**深度（Demo 3 — 透明工作台）：** 评委想看技术壁垒时展示。"这不是 prompt engineering——这是一个有 7 步质量控制的生产线。每一步都可以独立验证。"

**收尾：** "Vera 不是更好的 AI。Vera 是知道什么时候应该回答、什么时候应该拒绝的 AI。"

---

## 当前状态（比赛前不扩张）

```
Vera Product Strategy v0.1
├── Architecture:    Trusted Research Production Line (SPECIFIED)
├── Demo 1:          Company Research Card (DESIGNED)
├── Demo 2:          Research Quality Inspector (DESIGNED)
├── Demo 3:          Transparent Workbench (DESIGNED)
├── Trust Gates:     Citation / Freshness / Numeric / Conflict (SPECIFIED)
├── Governance:      FROZEN — 不增加新规则
├── Implementation:  NOT STARTED — 等待比赛策略确认
└── Evidence Base:   2 篇原始报告保留为 Artifact
```

---

## 附录：原始报告索引

- `VIBE_CODING_PRODUCT_PATTERN_REPORT_v0.1.md` — CC 的 Trust Infrastructure + Financial Agent 扫描
- C 的独立报告（Codex）— Product Pattern Layer + Agent Framework 扫描
- `AUCTION_RUNTIME_EVIDENCE_BUNDLE.md` — R-01 第一个生产案例（Evidence Governance 验证）
- `AUCTION_RUNTIME_FIX_PROPOSAL.md` — R-01 修复方案（Layer 1 + Layer 2 双层防御）
