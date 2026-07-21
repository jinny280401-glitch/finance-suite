# Vera 5 张 Image2 液态玻璃架构图指令

> 用途：给 Image2 / 图像生成工具使用，生成可插入答辩 PPT 的 16:9 视觉架构图。
> 参考风格：液态玻璃 UI，半透明黑色玻璃胶囊，厚玻璃折射边缘，高光反射，蓝/紫/粉/橙霓虹边缘光，柔和阴影，浅灰或深色科技背景。
> 注意：这不是 ASCII 图。ASCII 文件继续保留给 Word/Markdown；本文件用于生成 PNG/JPG 视觉图。
> 内容结构唯一源头（SSOT）：`/Users/Zhuanz/finance-suite/roadshow-2026-06/ASCII架构图指令-v2.md`。
> 本文件只负责把 v2 的 5 张图转成 Liquid Glass / Dark Mode / Apple WWDC 风格视觉图，不另行定义内容。

---

## 通用 Image2 风格指令

每张图生成前，先把这段作为统一风格要求放进 prompt：

```text
Create a premium 16:9 presentation slide visual in liquid glass UI style.

Visual style:
- futuristic liquid glass interface, glossy translucent rounded capsules and panels
- black smoky glass surfaces with thick refractive edges
- blue, cyan, violet, magenta, and warm orange neon rim lights
- realistic reflections, soft shadows, subtle caustics, layered depth
- clean enterprise fintech aesthetic, high-end Apple-like UI kit feeling
- dark graphite or soft light-gray background, no clutter
- use large readable Chinese title text and short readable node labels
- avoid tiny dense text, avoid messy paragraphs, avoid decorative characters
- layout must be clear enough for a pitch deck screenshot
- aspect ratio 16:9, high resolution, sharp typography

Brand and theme:
- Product name: Vera Agent v2.0
- Positioning: 面向证券行业的 Agent 员工平台
- Core contrast: 豆包能回答你问题，Vera 能替你干活
```

如果 Image2 支持参考图，把这张作为风格参考：

```text
/Users/Zhuanz/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_7yg3fzv9t5wp11_07ec/temp/RWTemp/2026-06/dbd94e1df749cd5c0f161665e086bbed/765e4ae466d3da66e9372efd1c98f758.jpg
```

---

## 图1：Vera Overall Architecture

```text
Use the universal liquid glass style.

Design a 16:9 fintech architecture slide.

Main title:
图1：Vera Overall Architecture

Subtitle:
更可信的 Agent 员工平台

Content layout:
Create a vertical six-layer architecture made of glossy liquid-glass panels, matching the v2 SSOT:
用户入口 -> Vera Agent -> Trust Gate -> Evidence Layer -> Research Runtime -> Skills -> Output

Node labels and micro labels:
1. 用户入口
   微信 / 飞书 / 企微 / Web
2. Vera Agent
   意图识别 + 工作流编排
3. Trust Gate
   PRODUCTION / FALLBACK / MOCK + 阻断字段
   make this layer the visual center, brighter rim light, marked as core moat
4. Evidence Layer
   Evidence Bundle / Citation / Completeness
5. Research Runtime
   取数 / 质检 / 分析 / 建议 / 追踪
6. Skills
   业务推进表 / 报销 / 会议 / 董事会 / 写稿 / 研报 / JIEZHU
7. Output
   合规研报 / 代劳任务完成 / 风险提示

Bottom slogan:
豆包能回答你问题，Vera 能替你干活。

Composition:
- Trust Gate should visually glow as the core moat
- keep text sparse and readable
- use glass capsules, not flat boxes
- no stock photos, no people, no cartoons
```

---

## 图2：Trust Gate Contract Flow

```text
Use the universal liquid glass style.

Design a 16:9 fintech trust-control slide.

Main title:
图2：Trust Gate Contract Flow

Subtitle:
数据可信度决定 allowed_use

Content layout:
Top half: a decision flow made of liquid-glass capsules:
用户提问 -> 意图识别 -> 越界检测 -> Trust Gate -> 数据来源档位 -> allowed_use

Add a red/pink glowing blocked branch from 越界检测:
短线建议 / 仓位建议 / 交易建议 / 资金流推断 -> BLOCKED

Bottom half: a clean glass table with 4 columns:
Provider / Trust Status / allowed_use / 数据源

Rows:
MOCK / passed / smoke test only / 测试环境
FALLBACK / passed / overview / JoinQuant、东财
PRODUCTION / passed / overview + analysis + research / Wind、Tushare

Add a warning strip:
禁止回答：短线建议 / 仓位建议 / 交易建议 / 资金流推断

Bottom slogan:
豆包能回答你问题，Vera 能替你干活。

Composition:
- Trust Gate and BLOCKED branch should be visually memorable
- use red only for blocked risk, blue/violet for safe flow
- readable Chinese text, not too dense
```

---

## 图3：Research Runtime Workflow

```text
Use the universal liquid glass style.

Design a 16:9 research operating system slide.

Main title:
图3：Research Runtime Workflow

Subtitle:
状态机驱动的可追溯研究链路

Content layout:
Create an elegant state-machine flow with glossy connected capsules:
PLAN -> RETRIEVE -> BUILD_CONTEXT -> ANALYZE -> QC -> SYNTHESIZE -> DONE

Micro labels:
PLAN: 列提纲 / 拆问题
RETRIEVE: Wind -> Tushare -> JQ -> 东财
BUILD_CONTEXT: 证据包 + 阻断字段剥离
ANALYZE: 财务对比 + 估值计算
QC: completeness + 异常检测
SYNTHESIZE: 11 章节报告
DONE: evidence_id

Add a side glass panel titled:
可审计约束

Inside the side panel:
evidence_id
source
timestamp
allowed_use

Add a bottom warning line:
Blocked fields: _qc / raw / payload never enter final LLM context.

Bottom slogan:
研究质量 = 数据完整性 x 分析深度 x 合规边界

Composition:
- flow must feel like a controlled research runtime dashboard
- QC node should have a subtle inspection glow
- avoid tiny paragraphs
```

---

## 图4：Skill Ecosystem

```text
Use the universal liquid glass style.

Design a 16:9 skill ecosystem slide.

Main title:
图4：Skill Ecosystem

Subtitle:
每个痛点，都长出一个 Skill

Content layout:
Create a three-layer upward growth structure using stacked translucent glass panels.

Bottom layer title:
已落地 Skill
Items:
投研 / 会议 / 报销 / 董事会 / 写稿 / JIEZHU

Middle layer title:
规划中 Skill
Items:
业务线索挖掘 / 客户跟进 / 合规审核

Top layer title:
AI 员工数字团队
Text:
每一个高频痛点 -> 一个 Skill

Between layers add glowing upward arrows:
痛点驱动
业务深水区

Bottom slogan:
发现痛点 -> 转化成 Skill -> 让同事早点下班

Composition:
- use glass hierarchy, not a literal tree
- warm green/cyan glow for growth, violet/blue for enterprise tech
- keep it polished and pitch-deck friendly
```

---

## 图5：Vera vs 豆包

```text
Use the universal liquid glass style.

Design a 16:9 comparison slide.

Main title:
图5：Vera vs 豆包

Subtitle:
能回答问题，还是能替你干活？

Content layout:
Split the slide into two large liquid-glass columns.

Left column title:
豆包
Tagline:
能回答你问题

Left flow:
Question -> Answer -> Explanation -> Reference

Right column title:
Vera
Tagline:
能替你干活

Right flow:
Intent -> Trust Gate -> Evidence -> Research Runtime -> Allowed Use -> Output

Make Trust Gate and Allowed Use glow brighter as Vera's moat.

Below the two columns, add a compact comparison strip:
交付：回答 vs 执行
闭环：对话完成 vs 任务完成
Trust Gate：非核心 vs 核心
Evidence QC：非核心 vs 核心
Allowed Use：非核心 vs 核心
合规研报：非核心 vs 核心交付

Bottom slogan:
豆包能回答你问题，Vera 能替你干活。

Composition:
- this is the most important judge-facing slide
- make the difference instantly visible
- left side can be cyan/blue, right side violet/magenta/orange highlights
- no clutter, no long text, strong symmetry
```

---

## Image2 使用建议

1. 优先逐张生成，不要一次生成五张，保证中文文字可控。
2. 如果中文变形，改成生成英文版节点，再由 PPT 手动覆盖中文文字。
3. 如果图太花，追加：
   `reduce decorative glow, make layout cleaner, keep only architecture nodes and readable labels`
4. 如果文字太小，追加：
   `use fewer labels, larger typography, more spacing`
5. 如果像营销海报而不是架构图，追加：
   `make it a clear enterprise architecture diagram, not a poster`
