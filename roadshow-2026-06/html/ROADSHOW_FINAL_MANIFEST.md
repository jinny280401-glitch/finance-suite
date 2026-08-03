# Roadshow Final Manifest

**Date**: 2026-07-23
**Status**: Competition Final Candidate

---

## SSOT

**唯一来源**: `/Users/Zhuanz/finance-suite/roadshow-2026-06/html/index.html`

不要引用作为当前状态：
- Vera V4 16 页封板（`project_vera_v4_closed_20260721.md`，2026-07-21）— 历史资产，已被后续迭代取代
- Codex handoff 10 页重构计划（`vera-architecture-ppt-handoff.md`）— 过程资产，未完全按此执行
- 任何早于本文件日期的页数描述

以上均为过程资产，不代表当前生效版本。当前生效版本以磁盘 `index.html` 的 `slides` 数组为唯一事实来源。

---

## Current Version

**Slides**: 14

| # | 文件 | 翻页名（name） |
|---|---|---|
| 1 | fig-cover-vera-portraits.html | 天玑 |
| 2 | fig-contents.html | 目录 |
| 3 | fig-hook-why-not-trust.html | 为什么不敢相信 AI |
| 4 | fig-pain-triangle.html | AI 幻觉的成本 |
| 5 | fig1-cover.html | Vera 管理幻觉 |
| 6 | fig-general-ai-vs-vera.html | 通用 AI vs Vera |
| 7 | fig3-trust-gate-flow.html | Trust Gate |
| 8 | fig-daily-research-loop.html | 持续研究闭环 |
| 9 | fig-company-panorama.html | 公司拜访速查卡 |
| 10 | fig-workbench.html | 真实工作台 |
| 11 | fig2-vera-overall-architecture.html | 可信如何建成 |
| 12 | fig4-research-runtime.html | Research Runtime |
| 13 | fig-enterprise-architecture-v1.html | 业务验证与行业开放 |
| 14 | fig7-closing.html | 收官 |

**2026-07-23 变更**：新增第 6 页（图片插入，通用 AI vs Vera 对比图，放在"Vera 管理幻觉"之后、"Trust Gate"之前），原第 6-13 页顺延为第 7-14 页。第 12 页 name 同步修正为"业务验证与行业开放"（此前记录为"降本增效与生态增长"，与磁盘当前 name 不一致，已按磁盘为准更新）。

---

## Verified（2026-07-23）

| 检查项 | 结果 |
|---|---|
| ✓ slide existence | PASS — 14/14 文件存在，无 404 |
| ✓ title consistency | PASS — 14/14 `name` 标签与页面实际 h1/title 一致 |
| ✓ asset loading | PASS — `assets/` 28 个资源文件（新增 general-ai-vs-vera.png）、`deck.css` 存在，未见缺失引用 |
| ✓ navigation | PASS — `index.html` 翻页逻辑（prev/next/dots/keyboard）读取自单一 `slides` 数组，无硬编码页数冲突 |
| PDF export | NOT VERIFIED — 本次未执行，见下方 Known Deviations |
| Demo path | NOT VERIFIED — 本次未执行，属于下一阶段（Demo 彩排）范围 |

---

## Known Deviations

**None blocking.**

- 2026-07-23 本次更新新增 Slide 6（通用 AI vs Vera 对比图），触发结构性调整（13 → 14 页），属于用户明确要求的图片插入，已在 Cue Card 和 Manifest 中同步更新。
- PDF export 与 Demo path 尚未在本轮验证范围内，标记为下一步待办，非本 Manifest 的阻塞项。

---

## Historical Versions

以下版本已归档，**非当前生效状态**，仅供追溯参考：

- **V4 / 16 页**（2026-07-21 封板）— 记录于 `project_vera_v4_closed_20260721.md`
- **Codex handoff / 10 页重构计划**（`vera-architecture-ppt-handoff.md`）— 叙事方向（"管理幻觉"文案）已部分吸收进当前 13 页版本，但页数与页面清单未按此计划最终落地

---

## Next Authorized Window

本 Manifest 锁定的是**检查结果**，不锁定文件本身——后续对 `index.html` 或任一 `fig-*.html` 的调整不需要撤销此 Manifest，但任何结构性改动（增删页/改变页序/改变 SSOT 路径）后应重新执行本清单并更新本文件。

**下一步优先级**：
1. Demo 彩排（8–10 分钟路径演练）
2. 评委追问准备
3. 视频录制（Optional）
