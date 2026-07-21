# 5 张 ASCII 架构图生成指令（v2 - Agent Trust 主题版）

> **版本**：v2.0（2026-06-18 重梳版）
> **核心主题**：Vera = 更可信的 Agent（Agent Trust Problem）
> **统一骨架**：所有 5 张图都必须包含 `Trust Gate` 节点
> **统一规格**：宽度 80 字符，符号统一（`┌─┐ │ ─ → ▲ ▼`）

---

## 📋 给 G/C 的总体说明（必须先发）

```
# 任务
我需要 5 张 Vera 项目路演用的 ASCII 架构图。
- 全部用纯 ASCII 字符（┌─┐ │ ─ → ▲ ▼）
- 禁用任何图片、Mermaid、Markdown 代码块标签
- 必须在 Word/PPT/Notion 中能直接复制粘贴显示正常
- 表格和流程图对齐工整
- 整体宽度严格控制在 80 字符以内
- 画完不要解释，直接输出图

# 统一骨架（5 张图都遵守）
所有 5 张图都必须体现这条主线：
  用户 → Vera → Trust Gate → Evidence Layer → Research Runtime → Skills → Output
Trust Gate 节点是核心（不是装饰），必须显式出现。

# 核心主题
豆包 解决的是 Agent Capability Problem（让 Agent 能干活）
Vera 解决的是 Agent Trust Problem（让 Agent 知道哪些活不能干）
所有图的命名、节点、连线都要体现"可信"而不是"更强"。

# 5 张图我会分 5 次发，每次发一张的「绘制要求」
# 你按要求画，不要自由发挥
```

---

## 📊 图1：Vera Overall Architecture（替代三层产品架构）

### 复制以下指令发给AI：

```
请用纯 ASCII 字符（不要任何图片、不要 Mermaid、不要 Markdown 代码块标签）绘制下面这张"整体架构图"。要求：节点用方框（┌─┐ 形式），节点之间用箭头（→）连接，对齐工整，能在 Word/PPT 里直接复制粘贴显示正常。

绘制要求：
1. 顶部标题："图1：Vera Overall Architecture——更可信的 Agent 员工平台"
2. 整体结构（自上而下 6 层，必须包含 Trust Gate）：
   - 顶层：用户（微信/飞书/企微/Web 入口）
   - 第 2 层：Vera Agent（意图识别 + 工作流编排）
   - 第 3 层（核心高亮）：Trust Gate（三档契约：PRODUCTION/FALLBACK/MOCK + 阻断字段）
   - 第 4 层：Evidence Layer（证据包 + Citation 追溯 + Completeness 评分）
   - 第 5 层：Research Runtime（状态机：取数→质检→分析→建议→追踪）
   - 第 6 层：Skills（业务推进表/报销/会议记录/董事会/写稿/研报生成/JIEZHU 情绪价值）
   - 底层输出：合规研报 + 代劳任务完成 + 风险提示

3. Trust Gate 这一层用 ★ 或【★】标记，强调"这是 Vera 的护城河"
4. 右侧或底部加一行小字："豆包 让 Agent 能干活；Vera 让 Agent 知道哪些活不能干"
5. 整体宽度严格控制在 80 字符以内

输出格式：直接画图，前面不要写"以下是图"这种废话，画完不要解释。
```

---

## 📊 图2：Trust Gate Contract Flow（保留三档契约思想）

### 复制以下指令发给AI：

```
请用纯 ASCII 字符（不要任何图片、不要 Mermaid、不要 Markdown 代码块标签）绘制下面这张"Trust Gate 契约流程图"。要求：用表格 + 流程图组合，对齐工整，能在 Word/PPT 里直接复制粘贴显示正常。

绘制要求：
1. 顶部标题："图2：Trust Gate Contract Flow——数据可信度决定 allowed_use"
2. 上面部分是一个 4 列的表格（用 │ 和 ─ 字符画），列头：Provider 类别 / Trust Status / 允许使用场景 / 典型数据源
3. 表格 4 行内容：
   - 第 1 行：MOCK / passed / 仅 smoke test / 测试环境
   - 第 2 行：FALLBACK / passed / overview（基本面速览）/ JoinQuant、东方财富
   - 第 3 行：PRODUCTION / passed / overview + analysis + production_research / Wind、Tushare Pro
   - 第 4 行（用 ❌ 标出"禁止行为"）：禁止回答：短线建议 / 仓位建议 / 交易建议 / 资金流推断
4. 表格下方画一个简化的"判别流程"：
   ```
   用户提问
     ↓
   意图识别（8 类）
     ↓
   越界检测（是/否）
     ├─ 是 → 直接 blocked（拒答）
     └─ 否 → 进入 Trust Gate
              ↓
         数据来源档位？
         ├─ PRODUCTION → 全功能
         ├─ FALLBACK → 仅 overview
         └─ MOCK → smoke test only
   ```
5. 流程图右上角加 ★ 标记："这是 Vera 相对通用 Agent 的核心差异"
6. 整体宽度严格控制在 80 字符以内

输出格式：直接画，画完不要解释。
```

---

## 📊 图3：Research Runtime Workflow（替代五步分析流程）

### 复制以下指令发给AI：

```
请用纯 ASCII 字符（不要任何图片、不要 Mermaid、不要 Markdown 代码块标签）绘制下面这张"Research Runtime 状态机流程图"。要求：节点用方框（┌─┐ 形式），节点之间用箭头（→）连接，每个节点下方有一行小字说明产出物，对齐工整。

绘制要求：
1. 顶部标题："图3：Research Runtime Workflow——状态机驱动的可追溯研究链路"
2. 主流程横向 5 个状态（带高亮底色用【】）：
   - 【PLAN】研究规划
   - 【RETRIEVE】数据取数
   - 【BUILD_CONTEXT】上下文构建
   - 【ANALYZE】分析推理
   - 【QC】质量检测
   - 【SYNTHESIZE】报告合成
   - 【DONE】完成
3. 每个状态下方一行小字说明产出物：
   - PLAN：列提纲 / 拆问题
   - RETRIEVE：四层降级取数（Wind→Tushare→JQ→东财）
   - BUILD_CONTEXT：证据包组装 + 阻断字段剥离
   - ANALYZE：财务对比 + 估值计算
   - QC：completeness 评分 + 异常检测
   - SYNTHESIZE：11 章节结构化报告
   - DONE：每条结论挂 evidence_id
4. 流程图最下方一行金句："研究质量 = 数据完整性 × 分析深度 × 合规边界"
5. 流程图右上角加一行："对比：通用 AI 是一次性 prompt 直出，无中间追溯"
6. 整体宽度控制在 100 字符以内（必要时换行，但要工整）

输出格式：直接画，画完不要解释。
```

---

## 📊 图4：Skill Ecosystem（基本不变）

### 复制以下指令发给AI：

```
请用纯 ASCII 字符（不要任何图片、不要 Mermaid、不要 Markdown 代码块标签）绘制下面这张"技能生态生长图"。要求：用树状/阶梯结构，体现"已落地 → 规划中 → 未来可生长"的时间递进感，整体宽度严格控制在 80 字符以内。

绘制要求：
1. 顶部标题："图4：Skill Ecosystem——每个痛点，都长出一个 Skill"
2. 整体是三层结构，从下往上"生长"：

   最底层（已落地，用 ✅ 标记，5 个 Skill）：
   - 业务推进表 Skill
   - 报销 Skill
   - 会议记录 Skill
   - 董事会 Skill
   - 写稿 Skill

   中间层（规划中，用 ⚠️ 标记）：
   - 业务线索挖掘 Skill（下一站）
   - 客户跟进 Skill
   - 合规审核 Skill

   顶层（愿景，用 💡 标记）：
   - 每一个高频痛点 → 一个 Skill
   - "AI 员工" 数字团队

3. 每层用 ┌─┐ 形式画成横条，从下往上叠加
4. 层与层之间用 ↑ 箭头连接，旁边标"痛点驱动"或"业务深水区"
5. 顶部加一行金句："投研只是第一个成熟 Skill，业务推进/报销/会议/董事会/写稿已经在跑"
6. 底部用一行说明："工作方法论：发现痛点 → 转化成 Skill → 让同事早点下班"
7. 整体宽度严格控制在 80 字符以内

输出格式：直接画，画完不要解释。
```

---

## 📊 图5：Vera vs 豆包 对比图（回答"为什么是你"，评委最终记忆点）

### 复制以下指令发给AI：

```
请用纯 ASCII 字符（不要任何图片、不要 Mermaid、不要 Markdown 代码块标签）绘制下面这张"Vera vs 豆包 借势对比图"。要求：左半边是 豆包 的执行链路，右半边是 Vera 的执行链路，节点用方框（┌─┐ 形式），节点之间用箭头（→）连接，左右严格对称对齐，宽度严格控制在 100 字符以内。

绘制要求：
1. 顶部标题："图5：Vera vs 豆包——同是 Agent 员工平台，护城河在哪？"
2. 顶部副标题（用一行小字）："我们受到 豆包 这类 Agent 员工体系的启发，但 Vera 解决的是 Agent Trust Problem"

3. 中间用一条 │ 竖线把图分成左右两半：

   【左半边：豆包 的执行链路】
   ```
   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────────┐
   │ Task │ → │ Plan │ → │ Code │ → │Execute│ → │ Feedback │
   └──────┘   └──────┘   └──────┘   └──────┘   └──────────┘
   核心：让 Agent 能干活
   ```

   【右半边：Vera 的执行链路】
   ```
   ┌───────┐   ┌────────────┐   ┌────────┐   ┌──────────────┐
   │Intent │ → │ Trust Gate │ → │Evidence│ → │Research      │
   └───────┘   └────────────┘   └────────┘   │   Runtime    │
                                  ↓            └──────┬───────┘
                              ┌──────────┐            ↓
                              │Allowed Use│   ┌──────────┐
                              └──────────┘   │  Output  │
                                                └──────────┘
   核心：让 Agent 知道哪些活不能干
   ```

4. 对比下方加 1 个 4 列的对比表（用 │ 和 ─ 字符画），列头：维度 / 豆包 / Vera / 差异
5. 对比表 6 行内容（每行不超过 12 字）：
   - 目标：通用员工 / 金融员工 / 场景不同
   - Agent：有 / 有 / 都有
   - Skill：有 / 有 / 投研只是第一个
   - Trust Gate：无 / ★ 有 / 核心差异
   - Allowed Use：无 / ★ 有 / 核心差异
   - Evidence QC：无 / ★ 有 / 核心差异
   - Citation：弱 / ★ 强 / 可追溯
   - 合规研报：非核心 / ★ 核心 / 护城河

6. Vera 列有 ★ 的行用粗框或【】标出
7. 整图最下方加一行金句（粗体）："更强的 Agent 满街都是；更可信的 Agent，是金融行业刚需。"
8. 整体宽度严格控制在 100 字符以内

输出格式：直接画，画完不要解释。
```

---

## 🎯 G 拿到指令后的执行顺序

```
第 1 步：先读"总体说明"
第 2 步：按 1→2→3→4→5 顺序画图（每张图独立发指令）
第 3 步：每张图画完先复制到 Word 试一下显示效果
第 4 步：如果有对齐问题，追加"重新画，对齐工整"
第 5 步：5 张都 OK 后，统一截图成 PNG
```

---

## 💡 给 C 的优先级（来自 G 的最新决定）

```
P1（路演前必须完成）：
  - 10 页答辩 PPT
  - Vera vs 豆包 对比表（作为 PPT 第 3 页）
  - 10 个答辩 Q&A 标准答案

P2（路演前完成）：
  - HyperFramers 视频脚本

P3（路演后优化）：
  - Demo 逐字稿优化
```

---

## 🚨 红线（不允许做的事）

- ❌ 不要画 6 张图（保持 5 张）
- ❌ 不要把 JIEZHU Memory Loop 当成 1 张图（它进 Demo 不进架构图）
- ❌ 不要把"三层产品架构"当图 1（换成 Overall Architecture）
- ❌ 不要在图里加"证券行业第一个 豆包"（这是被挑战的 claim，不进图）
- ❌ 不要超出 80-100 字符宽度（Word 里会换行错位）
- ❌ 不要在图里写"以下是图"这种废话
- ❌ 图 5 必须是 Vera vs 豆包（不是 vs Generic AI）—— 评委最终投票记住的是"为什么是你"

---

## ✅ G/C 必读：核心金句（所有材料对齐用）

```
标题金句（一致用这个）：
"Vera Agent v2.0——更可信的金融行业 Agent 员工平台"

定位金句（所有 PPT/Demo/答辩）：
"更强的 Agent 满街都是；更可信的 Agent，是金融行业刚需。"

核心金句（开闭场各说一次）：
"豆包 解决的是 Agent Capability Problem——让 Agent 能干活。
Vera 解决的是 Agent Trust Problem——让 Agent 知道哪些活不能干。
在金融行业，后者往往比前者更重要。"

对标金句（避开"第一个"的踩雷说法）：
"我们受到 豆包 这类 Agent 员工体系的启发，正在构建面向证券行业的 Agent 员工平台。"
```

---

## 📁 完成后请把图放到

```
/Users/Zhuanz/finance-suite/roadshow-2026-06/figures/
├── fig1-overall-architecture.txt
├── fig2-trust-gate-flow.txt
├── fig3-research-runtime.txt
├── fig4-skill-ecosystem.txt
└── fig5-vera-vs-aipy.txt
```

每张图画完就贴一份到对应文件，团队随时可取。
