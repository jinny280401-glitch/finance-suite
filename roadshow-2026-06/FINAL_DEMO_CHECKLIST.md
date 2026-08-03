# D23 Competition Final Demo Checklist
**Generated**: 2026-07-23 09:22 UTC+8  
**Status**: 🔒 FREEZE - No new features / providers / runtime extensions

---

## ✅ PPT 视觉审查

### PDF 交付物
- ✅ `Vera FInal.pdf` — 13 pages, 26MB (主交付)
- ✅ `Vera_Trusted_AI_Roadshow_12p.pdf` — 12 pages, 24MB (备用)
- ✅ `Vera_Trusted_AI_Roadshow_10p.pdf` — 10 pages, 22MB (简化版)

### 视觉完整性
- ✅ 液态玻璃设计系统已统一 (index.html 已应用)
- ✅ Trust Gate 页面用户语言改写完成
- ✅ 工作台页面金句卡片化完成
- ✅ Vera 定位页面底部金句玻璃卡片化

**Action Required**: 
- [ ] 打开 `Vera FInal.pdf` 进行最终人工审查
- [ ] 确认页面顺序、字体渲染、图片清晰度

---

## ✅ Demo 演示路径

### 13 页 Slide 完整性检查
```
1. ✅ fig-cover-vera-portraits.html       天玑
2. ✅ fig-contents.html                   目录
3. ✅ fig-hook-why-not-trust.html         为什么不敢相信 AI
4. ✅ fig-pain-triangle.html              AI 幻觉的成本
5. ✅ fig1-cover.html                     Vera 管理幻觉
6. ✅ fig3-trust-gate-flow.html           Trust Gate
7. ✅ fig-daily-research-loop.html        持续研究闭环
8. ✅ fig-company-panorama.html           公司拜访速查卡
9. ✅ fig-workbench.html                  真实工作台
10. ✅ fig2-vera-overall-architecture.html 可信如何建成
11. ✅ fig4-research-runtime.html          Research Runtime
12. ✅ fig-enterprise-architecture-v1.html 未来展望
13. ✅ fig7-closing.html                   收官
```

### 演示脚本推荐
```
开场 (1-2)  → 痛点 (3-4)  → 解决方案核心 (5-6) 
         → 产品能力 (7-9) → 架构支撑 (10-11) → 收官 (12-13)
```

**Action Required**:
- [ ] 彩排一遍完整演示路径 (13 页约 8-10 分钟)
- [ ] 准备 3 个关键页的备用话术：
  - Trust Gate (评委可能问「和别人有什么不同」)
  - 工作台 (评委可能问「已上线了吗」)
  - 未来展望 (评委可能问「多久能做」)

---

## ✅ HTML 页面访问链路

### 文件结构完整性
```
roadshow-2026-06/html/
├── index.html              ✅ 主入口 (液态玻璃控制台)
├── deck.css                ✅ 样式表
├── assets/                 ✅ 26 个 PNG 资源
│   ├── vera-portrait-closeup.png   ✅ 用于 fig1-cover
│   ├── workbench.png               ✅ 用于 fig-workbench
│   └── (其他 24 个资源)
└── fig-*.html (28 个)      ✅ 全部页面存在
```

### HTTP Server 测试
- ✅ `http://localhost:8765/index.html` 返回 200
- ✅ 预加载逻辑正常 (非 file:// 协议时自动 fetch)
- ✅ 键盘翻页 (←/→/Space/F) 正常
- ✅ 导航圆点 13 个全部生成

### 本地资源引用检查
```bash
fig1-cover.html:        <img src="assets/vera-portrait-closeup.png">
fig-workbench.html:     <img src="assets/workbench.png">
所有页面:               <link rel="stylesheet" href="deck.css">
```
所有引用均为相对路径，✅ 无外部依赖。

**Action Required**:
- [ ] 启动本地服务器验证完整演示流程：
  ```bash
  cd /Users/Zhuanz/finance-suite/roadshow-2026-06/html
  python3 -m http.server 8080
  # 访问 http://localhost:8080
  ```
- [ ] 确认所有 13 页在 iframe 中渲染无异常
- [ ] 测试全屏模式 (按 F)

---

## ⚠️ 演示风险点

### 已知问题（不修复，现场规避）
1. **Golden Pit**: 后端逻辑未修复 → 现场**不演示**黄金坑扫描功能
2. **Production Claim**: fig-workbench 页面提到「生产环境·已上线」
   - ✅ 已从 HTML 中隐藏 `.brand{display:none}`
   - 现场话术：「工作台原型已在内部测试」
3. **Mock 数据风险**: 
   - Trust Gate 页面提到「演示模式/Mock」
   - ✅ 已改为「演示模式 — 使用测试数据，仅展示功能」
   - 评委追问时明确：「我们区分真实/测试数据，透明告知用户」

### 现场规避策略
| 页面 | 风险点 | 规避话术 |
|---|---|---|
| fig-workbench | 「已上线」claim | 「工作台原型已在内部测试，核心能力可演示」 |
| fig3-trust-gate | Mock 含义 | 「四种模式让 AI 透明告知数据来源，不是所有 AI 都做到」 |
| fig-company-panorama | 公司拜访是否真用 | 「这是我们为调研场景设计的速查卡，整合公开数据」 |

---

## 📋 现场 Checklist

### 演示前 (T-30min)
- [ ] 打开 `index.html`，预加载所有 13 页
- [ ] 测试翻页 (←/→)、全屏 (F)、导航圆点点击
- [ ] 确认投影分辨率，检查文字清晰度
- [ ] 备用：PDF `Vera FInal.pdf` 打开并置顶

### 演示中 (T=0)
- [ ] 开场：fig-cover-vera-portraits（天玑画像，1 句话定位）
- [ ] 痛点：fig-hook + fig-pain-triangle（为什么不信 AI）
- [ ] 核心：fig1-cover + fig3-trust-gate（Vera 如何管理幻觉）
- [ ] 能力：fig-workbench + fig-company-panorama（真实场景）
- [ ] 架构：fig2 + fig4（可信如何建成）
- [ ] 收官：fig7-closing（金句 + 团队信息）

### 备用预案
- [ ] 如果 HTML 渲染异常 → 切换到 PDF 模式
- [ ] 如果评委要求跳页 → 使用导航圆点或键盘数字键
- [ ] 如果追问「生产数据」→ 话术：「我们区分 Real/Fallback/Mock，透明声明」

---

## 🚫 Freeze 纪律

**禁止操作（直到比赛结束）**:
- ❌ 新增功能（包括 Golden Pit 修复）
- ❌ 新增 Provider（JoinQuant/Wind/Tushare 等）
- ❌ Runtime 扩展（Skill/Tool/MCP 相关）
- ❌ Production 环境声明（不得在页面上加「已上线」「生产级」等）
- ❌ 修改已审查通过的 HTML 页面（除非发现 blocking bug）

**允许操作**:
- ✅ 现场话术优化（口头表达，不改代码）
- ✅ PDF 打印件准备（备用方案）
- ✅ 演示彩排与时间控制
- ✅ 评委 Q&A 预演

---

## 📊 交付物清单

| 类型 | 文件 | 状态 | 用途 |
|---|---|---|---|
| PDF | `Vera FInal.pdf` | ✅ | 主交付 PPT |
| PDF | `Vera_*_12p.pdf` | ✅ | 备用版本 |
| HTML | `index.html` + 13 slides | ✅ | 现场演示主力 |
| Assets | 26 个 PNG | ✅ | 页面资源 |

---

**签收确认**:
- [ ] 我已完成 PPT 视觉审查
- [ ] 我已完成演示路径彩排
- [ ] 我已测试 HTML 完整访问链路
- [ ] 我理解 Freeze 纪律，不会擅自修改交付物

**Final Sign-off**: ___________________  Date: 2026-07-__
