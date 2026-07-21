# Vera PPT V4 最终执行清单 - 给C

> **更新时间**: 2026-07-21 01:15  
> **基于**: Team Agent辩论结果 + G最终指示  
> **执行者**: C  
> **审核者**: G → A

---

## 🎯 核心原则（Team Agent共识）

### ✅ 采用"双层叙事"策略
1. **对用户讲情感**："数字员工"、"豆包能回答，Vera能干活"
2. **对行业讲壁垒**："信任基础设施"、"Trust Gate"
3. **对评委讲增长**："商业模式"、"并入公司平台计划"

### ✅ 三个"保留"（辩护者胜出）
1. ✅ 保留"豆包能回答你问题，Vera能替你干活"金句
2. ✅ 保留双层定位（用户层+基础设施层）
3. ✅ 保留已验证的视觉资产（四台阶、液态玻璃风格）

### ⚠️ 两个"避免"
1. ❌ 不编造未验证的数据
2. ❌ 不过度宣称"已成为标准"

---

## 📁 PPT文件路径

### 主目录
```
/Users/Zhuanz/finance-suite/roadshow-2026-06/html/
```

### 现有文件（需要修改/保留）
```bash
✅ fig1-cover.html                        # 封面 - 保留
✅ fig2-vera-overall-architecture.html    # 整体架构 - 保留
✅ fig3-trust-gate-flow.html             # Trust Gate - 保留
✅ fig4-research-runtime.html            # Research Runtime - 保留
✅ fig5-skill-ecosystem.html             # Skill生态 - 保留
🔧 fig6-vera-vs-doubao.html              # 竞品对比 - 需重构
🔧 fig7-closing.html                     # 结束页 - 需替换
✅ fig-enterprise-architecture-v1.html   # 企业架构 - 需微调
```

### 需要新建的文件
```bash
🆕 fig0-era-opportunity.html             # 时代机会（P0）
🆕 fig1-pain-triangle.html               # 痛点三角（P0）
🆕 fig-business-model.html               # 商业模式（P0）
🆕 fig-industry-applications.html        # 应用场景（P1）
🆕 fig-future-vision.html                # 未来规划（P1）
```

### 样式文件
```
deck.css - 统一样式（保持不变）
```

---

## 🔴 P0 任务 - 今晚必须完成

### 任务 #1: 新增"时代机会"页

**文件名**: `fig0-era-opportunity.html`

**页面标题**: 2026: 金融AI从生成内容进入可信决策时代

**内容结构**:
```markdown
━━━━━━━━━━━━━━━━━━━━━━━━
2026: 金融AI从生成内容进入可信决策时代
(2026: Financial AI Entering Trust Era)
━━━━━━━━━━━━━━━━━━━━━━━━

四个时代信号:

📊 模型成熟 (Model Maturity)
• Claude 5 / GPT-5 在金融场景表现接近人类
• [需要A提供引用] OpenAI/Anthropic官方声明

📈 机构提效需求 (Institution Efficiency)
• 华尔街投行已有60%使用AI辅助研究
• [需要A提供引用] 高盛/摩根研报

⚖️ 监管可信要求 (Regulatory Trust)
• [需要A提供] 证券业协会/央行AI合规文件
• 金融AI输出需可追溯、可审计

🔄 研究数字化瓶颈 (Research Bottleneck)
• 传统研究流程难以规模化
• 人工尽调成本持续上升

━━━━━━━━━━━━━━━━━━━━━━━━
核心矛盾:
生成答案 ≠ 可信决策
━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 措辞规范:
✅ "金融AI信任窗口期"
✅ "可信要求提升"
❌ 避免"唯一"、"必然"、"已成为"
```

**如果A无法提供真实引用**:
- 可以用"据行业报告"、"据公开资料"
- 不要编造具体引用来源
- 重点放在"四个信号"的客观描述

---

### 任务 #2: 新增"痛点三角"页

**文件名**: `fig1-pain-triangle.html`

**页面标题**: 证券行业AI应用的三重困境

**内容结构**:
```markdown
━━━━━━━━━━━━━━━━━━━━━━━━
证券行业AI应用的三重困境
(Three Challenges in Financial AI)
━━━━━━━━━━━━━━━━━━━━━━━━

💰 成本困境 (Cost Dilemma)
• 数据采购: Wind万得年费30万+ (行业通用成本)
• 人工尽调: 5-10天/项目 (行业平均水平)
• 重复劳动: 同样问题反复查询

⚠️ 风险困境 (Risk Dilemma)
• AI幻觉风险: 虚假数据导致决策失误
• 监管风险: 无法追溯数据来源
• 合规风险: 缺少审计证据链

⏱️ 时间困境 (Time Dilemma)
• 信息爆炸: 每日新增研报1000+篇
• 决策窗口: 市场机会转瞬即逝
• 人力瓶颈: 无法规模化处理

━━━━━━━━━━━━━━━━━━━━━━━━
核心矛盾:
需要AI效率 + 需要人工可信度
(Need AI Efficiency + Human Trust)
━━━━━━━━━━━━━━━━━━━━━━━━
```

**数据来源说明**:
- Wind年费、尽调时间：行业公开数据
- 不使用Vera的具体数据（避免无法验证）
- 突出"行业通用痛点"而非"Vera解决了多少"

---

### 任务 #3: 重构竞品对比页

**文件名**: `fig6-vera-vs-doubao.html` (原地修改)

**保留**:
- ✅ 四台阶进度条视觉（已验证资产）
- ✅ 液态玻璃风格

**修改内容**:

**新标题**: 三类产品解决的是不同层级的问题

**对比表** (从功能PK改为定位差异):
```markdown
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 维度         │ 信息终端     │ AI助手       │ Vera         │
│              │ (Wind/彭博)  │ (豆包/千问)  │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 核心任务     │ 查询信息     │ 生成答案     │ 可信研究流程 │
│ (Core Task)  │              │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 数据角色     │ 信息源       │ 训练数据     │ 可验证证据   │
│ (Data Role)  │              │              │ (Evidence)   │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 输出形式     │ 数据结果     │ 自然语言答案 │ 带边界的结论 │
│ (Output)     │              │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 可追溯性     │ 数据级       │ 较弱         │ 证据链级     │
│ (Traceability)│              │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 决策责任     │ 人工承担     │ AI幻觉风险   │ 人机协作边界 │
│ (Responsibility)│             │              │ 清晰         │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 资产沉淀     │ 使用记录     │ 对话记录     │ 机构研究资产 │
│ (Asset)      │              │              │              │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 适用场景     │ 信息查询     │ 通用对话     │ 金融决策支持 │
│ (Scenario)   │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘

核心差异:
豆包解决"能不能对话"
Vera解决"输出能不能用于金融决策"

类比:
就像支付需要风控中台 (Risk Control Layer)
金融AI需要信任基础设施 (Trust Infrastructure)
```

**⚠️ 重要**: 
- 优先用中文，括号里是英文（G指示）
- 不贬低竞品，突出"定位差异"
- 保留视觉的四台阶，但改文字内容

---

### 任务 #4: 新增商业模式页

**文件名**: `fig-business-model.html`

**页面标题**: 商业模式与公司平台整合计划

**内容结构** (严格区分当前/未来):
```markdown
━━━━━━━━━━━━━━━━━━━━━━━━
商业模式与公司平台整合计划
(Business Model & Integration Plan)
━━━━━━━━━━━━━━━━━━━━━━━━

📍 当前阶段 (Current Stage: 2026 Q3)
━━━━━━━━━━━━━━━━━━━━━━━━

✅ 华福证券内部部署 (Internal Deployment)
• 投研团队订阅使用
• 验证可行性和稳定性

✅ 功能验证 (Function Validation)
• 深度调研功能
• 财报分析功能
• 估值分析功能

━━━━━━━━━━━━━━━━━━━━━━━━
近期计划 (Near-term Plan: 2026 Q4 - 2027 H1)
━━━━━━━━━━━━━━━━━━━━━━━━

🎯 并入公司平台 (Platform Integration)

1️⃣ 投研平台整合
• 接入公司现有投研平台
• 作为"AI投研助手"模块
• 保持独立能力，支持API调用

2️⃣ 同舟系统整合
• 与同舟工作流打通
• 支持企业微信/飞书接入
• 多端协同使用

3️⃣ 技术接口开放
• 提供REST API接口
• 支持内部系统调用
• 可集成到现有工作流

━━━━━━━━━━━━━━━━━━━━━━━━
未来愿景 (Future Vision: 2027 H2+)
━━━━━━━━━━━━━━━━━━━━━━━━

🌐 探索方向 (Exploration):

• 平台授权模式 (Platform License)
  └─ 探索向同业开放能力

• Skill生态 (Skill Ecosystem)
  └─ 第三方开发者基于Vera开发行业技能

• 推动标准形成 (Standard Formation)
  └─ 联合行业探索可信AI输出规范

⚠️ 说明:
未来生态处于探索阶段，不计入当前商业模式

━━━━━━━━━━━━━━━━━━━━━━━━
整合路径:
内部验证 → 平台整合 → 能力开放
(Internal → Integration → Open)
━━━━━━━━━━━━━━━━━━━━━━━━
```

**关键修改点** (G指示):
- ❌ 删除"华福内部使用人数"、"使用频率/效果数据"
- ❌ 删除"同业意向"
- ✅ 改为"未来并入公司内部平台的计划"
- ✅ 重点讲"投研平台整合"+"同舟系统整合"

**措辞规范**:
- ✅ "探索"、"推动"、"计划"
- ❌ "已实现"、"已成为"、"确定"

---

### 任务 #5: 微调企业架构图

**文件名**: `fig-enterprise-architecture-v1.html` (原地修改)

**主要修改**: 中英文顺序调整（G指示）

**当前命名** → **新命名**:
```
Trust Gate → 信任防守门 (Trust Gate)
QC Layer → 质量检查层 (QC Layer)
Knowledge Layer → 知识溯源层 (Knowledge Layer)
Research Runtime → 研究引擎 (Research Runtime)
Workflow Runtime → 工作流引擎 (Workflow Runtime)
Evidence Bundle → 证据链 (Evidence Bundle)
```

**原则**: 
- ✅ 优先用中文，括号里是英文
- ✅ 保持视觉风格不变
- ✅ 只改文字标注

---

## 🟡 P1 任务 - 明早完成

### 任务 #6: 新增应用场景页

**文件名**: `fig-industry-applications.html`

**页面标题**: 一个可信研究底座，支撑多类金融工作流

**内容结构**:
```markdown
━━━━━━━━━━━━━━━━━━━━━━━━
一个可信研究底座，支撑多类金融工作流
(One Trust Infrastructure, Multiple Workflows)
━━━━━━━━━━━━━━━━━━━━━━━━

✅ 当前支持场景:

1️⃣ 公司研究 (Company Research)
   • 深度调研报告
   • 财务分析
   • 估值分析

2️⃣ 行业研究 (Industry Research)
   • 行业趋势分析
   • 竞争格局研究
   • 政策影响评估

3️⃣ 投研辅助 (Research Support)
   • 快速信息检索
   • 多维度数据对比
   • 证据链溯源

🔵 未来场景 (探索中):

4️⃣ 投后管理 (Post-investment)
   • 持仓公司跟踪
   • 风险预警

5️⃣ 客户服务 (Client Service)
   • 投资者教育
   • 产品解读

6️⃣ 合规审查 (Compliance)
   • 研究报告审核
   • 数据来源验证

━━━━━━━━━━━━━━━━━━━━━━━━
核心能力:
从"一个问题一个答案"
到"一套流程多个场景"
━━━━━━━━━━━━━━━━━━━━━━━━
```

**⚠️ 重要**: 明确区分"当前支持"和"未来场景"

---

### 任务 #7: 新增未来规划页

**文件名**: `fig-future-vision.html`

**替换**: 当前的 `fig7-closing.html`

**页面标题**: 从可信研究智能体走向行业应用基础设施

**内容结构**:
```markdown
━━━━━━━━━━━━━━━━━━━━━━━━
从可信研究智能体走向行业应用基础设施
(From Trusted Agent to Industry Infrastructure)
━━━━━━━━━━━━━━━━━━━━━━━━

🎯 发展路径:

2026 Q3-Q4: 机构场景验证
├─ 华福证券内部深度使用
├─ 完善Trust Gate和Evidence Chain
└─ 积累真实研究案例

2027 H1: 平台能力整合
├─ 接入投研平台和同舟系统
├─ 企业微信/飞书多端协同
└─ API能力对内开放

2027 H2+: 推动标准形成
├─ 探索向同业开放Trust Layer能力
├─ 联合行业制定可信AI输出规范
└─ 构建开放的Skill生态

━━━━━━━━━━━━━━━━━━━━━━━━
核心目标:
让每一个金融AI应用
都能接入可信基础设施
━━━━━━━━━━━━━━━━━━━━━━━━

我们正在构建的不是一个产品
而是行业可信AI应用的基础设施层

━━━━━━━━━━━━━━━━━━━━━━━━
欢迎试用体验
(Welcome to Try)
━━━━━━━━━━━━━━━━━━━━━━━━
```

**措辞规范**:
- ✅ "推动标准形成"
- ✅ "探索开放"
- ✅ "构建基础设施"
- ❌ "已成为标准"
- ❌ "行业领导地位"

---

## 🟢 P2 任务 - 保持现状

### 保留 #1: 核心金句
**文件**: 所有页面底部

**保留**: "豆包能回答你问题，Vera能替你干活"

**不修改理由**: 
- 已验证的有效话术
- 用户层价值表达
- 评委记忆点

---

### 保留 #2: 双层定位
**文件**: fig1-cover.html + fig-enterprise-architecture-v1.html

**封面**: "面向证券行业的可信研究智能体"
**架构页**: "金融AI员工基础设施"

**不修改理由**:
- 对用户讲"数字员工"
- 对行业讲"基础设施"
- 两者不矛盾

---

### 保留 #3: 已验证视觉资产
- ✅ 液态玻璃风格
- ✅ 四台阶进度条
- ✅ 深蓝底色 #0a0a1a
- ✅ 渐变强调色（青-蓝-紫）

---

## 📋 最终页面顺序（19页）

```
1.  fig1-cover.html                      # 封面
2.  fig0-era-opportunity.html            # 时代机会 🆕
3.  fig1-pain-triangle.html              # 痛点三角 🆕
4.  fig2-vera-overall-architecture.html  # Vera是什么
5.  fig-enterprise-architecture-v1.html  # 五层架构 🔧
6.  fig3-trust-gate-flow.html           # Trust Gate详解
7.  fig4-research-runtime.html          # Research Runtime
8.  fig5-skill-ecosystem.html           # Skill生态
9.  fig-industry-applications.html      # 应用场景 🆕
10. fig6-vera-vs-doubao.html            # 竞品对比 🔧
11. fig-business-model.html             # 商业模式 🆕
12. fig-future-vision.html              # 未来规划 🆕
```

**更新index.html的slides数组**:
```javascript
const slides = [
  {src: 'fig1-cover.html', title: '封面'},
  {src: 'fig0-era-opportunity.html', title: '时代机会'},
  {src: 'fig1-pain-triangle.html', title: '痛点三角'},
  {src: 'fig2-vera-overall-architecture.html', title: 'Vera是什么'},
  {src: 'fig-enterprise-architecture-v1.html', title: '五层架构'},
  {src: 'fig3-trust-gate-flow.html', title: 'Trust Gate'},
  {src: 'fig4-research-runtime.html', title: 'Research Runtime'},
  {src: 'fig5-skill-ecosystem.html', title: 'Skill生态'},
  {src: 'fig-industry-applications.html', title: '应用场景'},
  {src: 'fig6-vera-vs-doubao.html', title: '竞品对比'},
  {src: 'fig-business-model.html', title: '商业模式'},
  {src: 'fig-future-vision.html', title: '未来规划'},
];
```

---

## ⚠️ 关键数据缺口（需要A提供）

### 时代机会页需要（如无法提供可用行业通用说法）:
- [ ] 监管文件引用（证券业协会/央行）
- [ ] 或投行研报引用（高盛/摩根/顶级券商）

**如果没有**:
- 用"据行业报告"、"据公开资料"
- 不编造具体引用

---

## ✅ 执行前检查清单

### 文件操作
- [ ] 先备份现有文件
- [ ] 新建文件时复制deck.css链接
- [ ] 修改后本地预览（open xxx.html）
- [ ] 确认无误后更新index.html

### 内容规范
- [ ] 所有术语"中文(English)"顺序
- [ ] 没有未经验证的数据
- [ ] 没有"已成为标准"等过度宣称
- [ ] 当前/未来场景明确区分

### 视觉规范
- [ ] 保持液态玻璃风格
- [ ] 保持深蓝底色
- [ ] 保持金句位置
- [ ] 保持四台阶视觉（竞品页）

---

## 📊 验收标准

### C执行完成后自查
- [ ] 新建了5个页面（P0: 4个 + P1: 1个）
- [ ] 修改了2个页面（竞品对比+企业架构）
- [ ] 更新了index.html的slides数组
- [ ] 所有中英文顺序正确
- [ ] 没有编造数据

### G审核标准
- [ ] 时代机会页有真实引用（或合理替代）
- [ ] 痛点三角数据真实可信
- [ ] 竞品对比从定位差异而非功能PK
- [ ] 商业模式重点讲公司平台整合
- [ ] 未来规划用"推动"而非"已成"

### A最终验收
- [ ] 符合老师所有意见
- [ ] 定位升级清晰（工具→基础设施）
- [ ] 技术细节准确
- [ ] 整体逻辑顺畅

---

## 🚀 执行时间表

**今晚 (23:00 - 02:00)**:
- P0任务 #1-5 (5个文件)
- 重点：时代机会、痛点三角、商业模式、竞品对比

**明早 (08:00 - 11:00)**:
- P1任务 #6-7 (2个文件)
- 应用场景、未来规划

**明午 (11:00 - 12:00)**:
- 全局检查
- 修正错误
- 准备提交

---

## 💡 技术提示

### 新建HTML文件模板
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>页面标题</title>
<link rel="stylesheet" href="deck.css">
<style>
  /* 页面特定样式 */
</style>
</head>
<body>
<div class="slide">
  <!-- 内容区 -->
</div>
</body>
</html>
```

### 复制样式参考
- 封面样式: fig1-cover.html
- 内容页样式: fig2-vera-overall-architecture.html
- 架构图样式: fig-enterprise-architecture-v1.html

---

## 🎯 最终目标

完成V4叙事升级：
- ✅ 从"工具"升级到"基础设施"
- ✅ 保留用户价值表达
- ✅ 增强行业定位
- ✅ 明确商业路径
- ✅ 避免过度宣称

**时间紧迫，聚焦P0任务！**

---

**制作时间**: 2026-07-21 01:15  
**预计完成**: 2026-07-21 03:00 (P0)  
**最终提交**: 2026-07-21 下午

**加油！明天就要提交了！** 🚀
