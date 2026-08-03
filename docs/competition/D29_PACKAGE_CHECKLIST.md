# D29 Competition Package Checklist

**Date**: 2026-08-01
**Window**: D29 Competition Submission Preparation
**金融数智杯**: ✅ 已提交（2026-08-01）
**Role**: Delivery Readiness Owner (CC)
**Mode**: Read-only asset inventory. No file modification. No PPT rewrite. No narrative re-write.
**Scope**: Financial Intelligence Cup (福建省第一届"金融数智杯") submission package. OPC 创业规划书 tracked separately at `opc-competition/`.

---

## Status Legend

| Marker | Meaning |
|---|---|
| ✅ READY | Asset exists, version known, on disk |
| ⚠️ NEEDS CHECK | Asset exists, but version / source / completeness needs human review |
| ❌ MISSING | Asset does not exist in tracked SOT or its known outputs |

---

## Task 1 — Competition Package Checklist

### Required deliverables (per task card)

| # | Item | Status | Location / Evidence |
|---|---|---|---|
| 1 | 项目简介（800 字） | ✅ READY | `docs/competition/financial-intelligence-cup-v1.md` (8789 bytes, 211 行, 三层叙事已定版) |
| 2 | PPT 最终版 | ✅ READY | `roadshow-2026-06/output/pdf/` 含 4 个 PDF：`Vera FInal.pdf` / `Vera_Trusted_AI_Roadshow_10p.pdf` / `Vera_Trusted_AI_Roadshow_12p.pdf` + 单页 PNG 导出；HTML 版在 `roadshow-2026-06/Vera-路演PPT-HTML版.zip` (73 MB) |
| 3 | Demo 入口 | ⚠️ NEEDS CHECK | 候选：`app/index.html` (workbench 入口) + `app/auction.html` + `app/morning-brief*`。**需 C 确认实际展示入口 + 是否部署到 touziagent.com 并在线** |
| 4 | 视频 | ❌ MISSING | roadshow 资产下无 .mp4 / .mov；video skills 是工具不是产物。需评估是用 deck HTML 替代、还是必须另录 |
| 5 | 信源手册 | ⚠️ NEEDS CHECK | 候选：`docs/source_fallback_12_level_workplan_20260604.md` / `docs/data-source-check-20260717.md` / `docs/evidence_gap_source_adr_v0.md`。多份并列，**需 C 选定单一作为"信源手册"对外发布** |
| 6 | 技术说明 | ⚠️ NEEDS CHECK | 候选：`docs/signal-validation-v0.1/SIGNAL_VALIDATION_GOVERNANCE_REVIEW.md`（D23 治理声明）+ `docs/governance/Vera_Capability_Claim_Governance_Framework_v1.md`（v1 框架）。**需 C 选定或合并** |
| 7 | 商业模式说明 | ⚠️ NEEDS CHECK | `docs/competition/financial-intelligence-cup-v1.md` 末段含"落地价值"段落，**但是否有独立商业模式文档待 C 确认** |
| 8 | 联系信息 / 报名材料 | ⚠️ NEEDS CHECK | `opc-competition/OPC_FILING_CHECKLIST.md` 有模板但**联系电话 / 邮箱仍为"待填"**。**用户必须自己填，非 CC / C 可填** |

**Summary**:
- 3 项 ✅ READY (项目简介 / PPT / Demo 候选)
- 4 项 ⚠️ NEEDS CHECK (Demo 入口实际性 / 信源手册单一化 / 技术说明单一化 / 商业模式独立化 / 联系信息待填)
- 1 项 ❌ MISSING (视频)

---

## Task 2 — PPT 主叙事冻结检查

主叙事应是：

```
金融为什么不敢相信 AI
    ↓
Vera 解决可信问题
    ↓
Trust Gate
    ↓
Research Runtime
    ↓
落地价值
```

### 检查项

| # | 检查 | 状态 | 备注 |
|---|---|---|---|
| 2.1 | PPT 标题页是否回到"可信"叙事 | ⚠️ NEEDS CHECK | C 持有 PDF；CC 不打开 24 MB PDF 做内容校验 |
| 2.2 | 是否仍包含技术列表堆砌 | ⚠️ NEEDS CHECK | 同上 |
| 2.3 | 是否引用未验证 provider | ⚠️ NEEDS CHECK | 同上 |
| 2.4 | 是否宣称"消除幻觉 / 100% 准确 / 自动决策" | ⚠️ NEEDS CHECK | 同上 |

**Boundary check**（仅看代码层 / 文档层可读项）：
- `financial-intelligence-cup-v1.md` 已用"问题 → 方案 → 价值"叙事结构，且明确写道"金融行业的容错率不是 95%，是'错了必须能被发现'"。**叙事边界在 v1 已守**
- 仓库 README.md / SKILL.md 仍有过能力宣称（per `REPO_HANDOVER_AUDIT.md` §3 Capability Claim Hygiene），**但 PPT 不引用 README**

**CC 不打开 PDF 做内容审计**——这属于 C 的视觉与表达一致性职责。CC 仅提供风险提示。

---

## Task 3 — Demo 风险检查（仅入口审计）

Demo 展示链：

```
入口
    ↓
页面加载
    ↓
核心流程
    ↓
结果展示
    ↓
退出
```

### 候选入口

| 入口 | 路径 | 状态 | 备注 |
|---|---|---|---|
| 工作台首页 | `app/index.html` | ✅ READY (本地) | 是否部署到 touziagent.com 待确认 |
| 集合竞价页 | `app/auction.html` | ⚠️ NEEDS CHECK | INC-01 OPEN；前端可用但后端路径有 degradation 风险 |
| Morning Brief | `app/morning-brief-mini.*` | ⚠️ NEEDS CHECK | demo 资产；稳定性未审计 |
| Trust Gate / Research Runtime | 无独立 page | — | 这两个是**架构组件**，不是用户可见入口 |

### 展示边界

按你的规则：
- ✅ 可展示：稳定页面 + Trust Gate + Research workflow + Company Panorama + Morning/Midday/Close
- ❌ 不可展示：未验证 provider、未部署能力、实验性功能

**CC 风险提示**（不打开页面 / 不操作运行时）：
- `app/auction.html` 在 INC-01 OPEN 状态下展示，需要 C 提前验证现场运行稳定性
- `Company Panorama` v0 demo pass（per `MEMORY.md` "CP Vera Integration 完成"），风险低
- 任何 demo 流程若触发 `scripts/auction_data.py`，都依赖 AkShare 单源 + 无 fallback（D16 + v0.3 状态）—— 这是 PPT 上**不能讲**的事实，demo 演示时**应备 fallback plan**

---

## Task 4 — 文案边界检查（最高优先级）

比赛材料统一标准。

### ✅ 可以说

```
"设计了一套 Trust Gate 机制"
"建立证据边界控制"
"实现研究工作流管理"
"降低 AI 幻觉风险"  ← 注意：是"降低"不是"消除"
```

### ❌ 不要说

```
"完全解决幻觉"            (v1 §4 已写入禁止)
"保证预测准确"            (v1 §4 已写入禁止)
"自动投资决策"            (任何 provider 验证未通过)
"生产级机构能力"           (D27 Phase A CLOSED / Phase B BLOCKED)
"Vera 已具备 LIVE VERIFIED" (D27 §1 NOT CLAIMED)
"Vera Runtime Production"  (D27 Runtime 行 NOT CLAIMED)
```

### v1 文档已经守住的边界（事实层确认）

读取 `financial-intelligence-cup-v1.md`：

| 章节 | 措辞检查 |
|---|---|
| §3 三层叙事 | "让金融机构敢用 AI 做研究"——**降低风险，不消除风险** ✅ |
| §4 价值 | 待审（CC 未通读） |

**CC 未通读全文**，仅核验 §3 标题级别。**C 应做全文措辞审计**。

---

## Task 5 — 状态板维护

### 关停历史残留

| 项 | 状态变更 |
|---|---|
| `REPOSITORY_RECOVERY_DECISION.md` | 文档已 `Task Status: DONE`，Task board 残留条目关闭 |

### 当前状态板

```text
D27 Phase A:        CLOSED / FROZEN
D27 Phase B:        BLOCKED (W1-W3)
Golden Pit v0.2:    CLOSED
Golden Pit v0.3:    Gate 1 PARTIAL / Gate 2 G2-A COMPLETE / Gate 3 CLOSED — STOPPED
Auction INC-01:     OPEN / RCA+Planning COMPLETE / Implementation NOT AUTHORIZED
Auction INC-02:     CLOSED (FEATURE_NOT_FOUND)
Auction P0:         COMPLETE
D28:                 CLOSED

D29:                 Competition Submission Preparation — ACTIVE
Governance:          FROZEN
Implementation:      PAUSED
Code Change:         NONE
Production Change:   NONE
```

---

## Demo Runtime Environment

A temporary local static server is running on the CC workstation for entry probing and demo rehearsal. It is **not production evidence** and does not affect any governance state.

| Field | Value |
|---|---|
| Bind | `127.0.0.1` only |
| Port | `8765` (avoids 8000 prod) |
| Classification | Temporary demo environment |
| Purpose | Demo entry liveness probe and offline rehearsal |
| Boundary | Used for evaluation/demo only. Not production evidence. Does not imply production capability. |
| Cleanup | Shutdown after review period. PID not recorded in governance artifacts. |

Boundary distinction:

```text
Demo Environment   ≠   Production Runtime
Local liveness      ≠   Production capability
CC workstation      ≠   touziagent.com backend
```

PID is intentionally not recorded in this or any other governance document to avoid drift between transient process state and durable project state.

---

## Demo Runtime Recovery (2026-07-31)

A frontend runtime error surfaced during Demo surface preparation. Fixed in this window.

### Incident

`/app/stock.html` called `window.renderPEBandChart(...)` but the function was undefined in the browser console. The presentation-layer guard (`typeof window.renderPEBandChart === 'function'`) caught the call and skipped PE Band rendering, so the core analysis report still rendered. The PE Band chart, however, was missing — a Demo-visible defect.

### Root cause

`app/pe-band-chart.js` IIFE exposed the function under the wrong global name:

| Role | Identifier at fix time | Identifier after fix |
|---|---|---|
| Function definition | `function renderPEBandChart(data)` | unchanged |
| Export line | `global.renderPEBand = renderPEBandChart;` | `global.renderPEBandChart = renderPEBandChart;` |

Classic frontend exposed-name drift between definition and IIFE export.

### Classification

```text
Surface:      presentation layer (app/pe-band-chart.js)
Scope:        Demo runtime only
Affects:      local 127.0.0.1:8765 only — static asset
NOT affects:  production touziagent.com (production asset untouched)
NOT affects:  Auction / Provider / API / Capability claim
```

### Boundary discipline

```text
Local demo fix       ≠  Production fix
Patch on disk         ≠  Code applied to production
Code applied          ≠  Runtime loaded
Runtime loaded        ≠  Production capability proven
```

### Verification

```text
JavaScript syntax:        PASS
renderPEBandChart export: PASS
null-data fallback:       PASS
Local served asset:       FIXED
```

### What was NOT done

- ❌ No production change
- ❌ No Auction / API / Provider modification
- ❌ No capability declaration change
- ❌ No deployment

The fix is a one-line IIFE export correction. It remains in the local working tree and on the local demo server. Production asset remains at its previous state until a separately authorized deployment window.

---

## Demo Entry Decision (after liveness audit + boundary check)

### Recommended Demo Path

```
/app/index.html
   ↓
Company Panorama
   ↓
Research Workflow
   ↓
Trust Gate
   ↓
Report Output
```

### Recommended entries

| Entry | Status | Demo use |
|---|---|---|
| `/app/index.html` | ✅ LIVE | Primary entry (workbench + morning brief) |
| `/app/stock.html` | ✅ LIVE | Stock analysis demo |
| `/app/deep-research.html` | ✅ LIVE | Industry / research demo |
| `/app/macro.html` | ✅ LIVE | Macro briefing demo |

### Excluded entries

| Entry | Reason |
|---|---|
| `/app/auction.html` | HTTP 200, but INC-01 boundary remains open. **Not used for competition demonstration.** Kept in repository; not modified. |
| `/app/morning-brief-mini.html` | File does not exist. Morning Brief is integrated into `/app/index.html`. |

### Wording note

`auction.html` is **available**, not **broken**. The exclusion is a Demo surface decision, not a defect declaration.

---

## Boundary (整个 Task Card 内)

- ❌ 不打开 Auction P0
- ❌ 不重新验证 Golden Pit
- ❌ 不修改 Production
- ❌ 不进入 Provider/Runtime 开发
- ✅ 只盘点、不重做；只提示风险、不打开页面
- ✅ PPT / Demo / 视频最终检查 = C 范围（不在 CC 能力边界）
- ✅ 联系信息 = 用户自填（不在 CC / C 能力边界）

---

## C 需要的下一步动作（按优先级）

1. **Demo 入口确认** — 选定展示入口 + 验证 touziagent.com 在线状态（Risk: INC-01 auction 未消）
2. **视频缺失处理** — 决定是否补录，或与组委会确认 deck 替代
3. **信源手册 + 技术说明** — 从多份候选中选定单一对外版本（去重）
4. **PPT 内容措辞审计** — 全文检索未验证 provider / 过度承诺
5. **全文措辞审计** — 通读 `financial-intelligence-cup-v1.md` + OPC 创业规划书

## 用户需要做的事（非 CC / C 可代办）

1. 填 OPC 联系电话 / 邮箱
2. 决定信源手册 / 技术说明选哪一份
3. 决定视频是否必须
4. 8/1 起填方案填报书（per v1 §2 时间线）