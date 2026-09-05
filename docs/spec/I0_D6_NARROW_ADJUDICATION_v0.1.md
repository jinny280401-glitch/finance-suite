# I0 — D6 Narrow Adjudication v0.1

**卡：** Implementation Plan — I0（唯一 blocker 收口）
**状态：** CLOSED — M25 已裁决
**日期：** 2026-08-13
**范围锁死：** 只回答一格：D6 `search_result × unclassified × research` 的行为语义。不重开 I0、不动其它 taxonomy、不改 CR1–CR6、不重跑/新增无关 fixture。

**DECISION:** M25 = INF — `search_result × unclassified × research = INFORMATIONAL`
**HUMAN_DECISION:** 2026-08-13
**语义：** 可作为 research background information；必须保留 `unclassified/search_external` marker；不得单独支撑 claim；claim-strength ceiling = INF；trading counterpart 保持 NC。

---

## 0. 为什么这不是 ACR

填补已冻结 D6 表内的 TBD 格 — 不改变 CR1–CR6 语义、不动 Target Architecture 不变量（lattice / 单调性 / freeze clause 均未触及）。与 OPC 四类参数同级：用户裁决即可，M 编号（M25）登记。不重开 Architecture Review。

## 1. 冻结锚点（裁决受此约束，选项空间已被收窄）

1. **单调性（OBS-4 推导链冻结）**：trading ≤ research 的同源上限 → trading = NC ⇒ research ∈ {NC, INF, AC, AO, DI, OF}
2. **unclassified < classified 降级语义**（trading 行 precedent：classified AC → unclassified NC）：research classified = AC ⇒ research unclassified < AC ⇒ research ∈ {NC, INF}
3. **§1.7 裁决表（冻结）**：research × P2 = `ALLOW_WITH_MARKER`（marker=`unclassified/search_external`）— 本格必须与 marker 语义自洽

**⇒ 选项空间 = {NC, INF}。AC 违反降级语义，排除。**

## 2. 两选项

| | A：INFORMATIONAL | B：NO_CLAIM |
|---|---|---|
| 行为 | 进入 research context，必须携带 unclassified marker；可作为背景信息存在，不可作为主张/结论的 claim 基础 | 进入 research context，仅提示人工核验；不得影响研究判断（与 trading 同严格） |
| 论证 | ① 单调性下 research 允许的最紧一致值之一，且保持"research 比 trading 松一档"的既有模式（media_transcript AC/INF、excerpt INF/NC 同构）② marker 语义 = "进入但标注"，INF = 其 claim-strength 对应物 ③ 与 excerpt research=INF 同构（片段、需追溯原件）④ trading=NC 的 fail-closed 理由（不得影响交易判断）不适用于 research ⑤ Coverage 记录 search 类 "unclassified in practice" 是常态 → NC 会把 research context 的搜索材料整体清空，等于用 ceiling 架空 §1.7 已冻结的 ALLOW_WITH_MARKER admission | ① 与 trading 对称，最保守 ② 未分类材料未经人工核验前不得影响任何判断，research 不例外 ③ 与"事实进 Evidence、观点进 Research Context"纪律一致——未分类片段既非已核实事实也非明确观点 |
| 代价 | 未分类片段可影响研究过程（受 marker + 不可成 claim 约束；经 synthesis 时 glb ≤ INF，不可能升级为 claim） | research 场景搜索材料基本不可用；§1.7 research 列的 ALLOW_WITH_MARKER 退化为仅买到一个核验提示 |
| 与 §1.7 自洽性 | 自洽：marker admission + INF 背景存在 | 张力：admitted 但 ceiling=NC，admission 的实际收益最小 |
| downstream 安全 | 合成含 INF 的 bundle：glb ≤ INF | 合成含 NC 的 bundle：glb = NC |

## 3. 推荐

**A：INFORMATIONAL** — 与冻结的 marker admission 自洽，保持 research 松一档的既有模式，downstream 经 glb 单调性天然封顶（不可升级为 claim）。B 可行但会架空 §1.7 已冻结的 research admission。

## 4. 裁决后的落地（已锁定，选 A 或 B 相同）

1. §1.6 行改写：`TBD` → 裁决值（登记 M25，来源 = 用户裁决 2026-08-1X）
2. validator：`d6_ceiling` 移除 None 跳过 → 实现该格
3. 2 个判别 fixture：
   - valid：research + search_result + unclassified + strength = 裁决值 → PASS
   - invalid：research + search_result + unclassified + strength = 裁决值上一级 → L3-I5
4. 全量 regression（29 + 2 = 31/31）
5. 全 PASS → Task #10：I0 SCHEMA CONTRACT PROVEN 裁决
6. 三个禁止外推不变：≠ Evidence Layer implemented / ≠ Production enforcement proven / ≠ Coverage > 0/15

## 5. Coverage 传播位点定位结论（本卡附带）

Coverage Contract 无 D6 格子副本 — 其 claim-strength 语义是 per-family prose 否定约束（P2 行："search_external evidence CANNOT be sole basis for: valuation judgment, trading signal, management assessment"），verdict/use 级、无 research/trading 分列、无 lattice 值。本格裁决**不产生 Coverage 传播**：M25 传播范围 = I0 §1.6 + validator + fixtures。两选项均满足该 prose 约束。

---

## States

```
D6 Narrow Adjudication:      CLOSED — M25 = INF（Human Decision 2026-08-13；选项空间 {NC, INF} → 选 A=INF）
I0 Schema Contract:          FROZEN / OPEN PARAMETERS CLOSED
I0 Validation Evidence:      PASS — Regression 31/31（2026-08-13）
I0 SCHEMA CONTRACT PROVEN:   PROVEN — M25 COMMITTED（research×search_result×unclassified = INF）
OBS-8:                       ACCEPTED / NON-BLOCKING TAXONOMY DEBT（不 amendment）
```
