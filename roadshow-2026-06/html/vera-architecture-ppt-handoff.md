# Vera PPT 叙事重构 — Codex Goal

## 目标

把 PPT 从「介绍 Vera 的功能」重构为「证明可信 AI 为什么值得存在」。从 18 页压缩到 10 页。

核心 Slogan：**让 AI 在不知道的时候，诚实地说不知道。**

---

## CC 已完成

| 文件 | 内容 |
|------|------|
| `fig-hook-why-not-trust.html` | Hook 页：AI 已经能回答。为什么金融行业还不敢相信？ |
| `fig-trust-contrast.html` | 对比页：通用 AI 编造 vs Vera 诚实说不知道 |
| `fig7-closing.html` | 已更新：让金融行业敢把 AI 的答案交给客户 |

---

## Codex 待办

### A. 改 5 页文案（只改文字，不动布局/CSS/结构）

**1. fig-pain-triangle.html — 聚焦幻觉代价**

- `<h1>` 从"行业痛点"改为 **"AI 幻觉：金融行业不能承受的成本"**
- 副标题/eyebrow 强调：错行情、错研报、错引用、错来源

**2. fig1-cover.html — 重新定位**

- lead 文案从"不是回答问题的通用 Bot，而是能完成研究任务的数字员工"改为 **"不消除幻觉，管理幻觉。在不知道的时候，诚实地说不知道。"**

**3. fig-vera-three-views.html — Skills 重新叙事**

- 标题从"Vera 核心 Skills"改为 **"Trust Gate 守护下的可信能力"**
- 副标题改为 **"不是功能列表，而是可信的具象证明"**

**4. fig3-trust-gate-flow.html — Trust Gate 加大冲击力**

- 标题改为 **"Trust Gate：让 AI 输出有证据可追溯"**

**5. fig2-vera-overall-architecture.html — 架构重新叙事**

- 标题从"一分钟可信研报，是如何诞生的？"改为 **"可信是如何建成的"**
- 副标题改为 **"每一份输出背后，都是一条完整的证据链"**

### B. 重构 index.html slides 数组

**完整替换为 10 页：**

```javascript
const slides = [
  {src:"fig-cover-vera-portraits.html",        name:"天玑"},
  {src:"fig-hook-why-not-trust.html",           name:"为什么不敢相信 AI"},
  {src:"fig-pain-triangle.html",               name:"AI 幻觉的成本"},
  {src:"fig1-cover.html",                      name:"Vera 管理幻觉"},
  {src:"fig3-trust-gate-flow.html",            name:"Trust Gate"},
  {src:"fig-trust-contrast.html",              name:"诚实 vs 编造"},
  {src:"fig-speed-benchmark.html",             name:"Vera vs 通用Bot"},
  {src:"fig2-vera-overall-architecture.html",  name:"可信如何建成"},
  {src:"fig-vera-three-views.html",            name:"可信能力"},
  {src:"fig-enterprise-architecture-v1.html",  name:"商业路径"},
  {src:"fig7-closing.html",                    name:"收官"},
];
```

其他页面从数组中移除，文件保留在磁盘上。

### C. 验证

1. 打开 `index.html`
2. 从封面翻到最后，确认 10 页顺序正确
3. 确认文案改动生效
4. 确认无 404

---

## 叙事线

```
封面 → 为什么不敢相信 → 幻觉的成本 → 管理幻觉 → Trust Gate → 诚实vs编造 → 速度证明 → 如何建成 → 可信能力 → 商业路径 → 收官
```

## 不做

- 不改布局/CSS/结构
- 不删磁盘文件
- 不动封面页
