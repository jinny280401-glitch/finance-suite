# Evidence Verification Report — 分公司线（福州分公司）

> **窗口**：Evidence Verification Mini-Window
> **日期**：2026-07-04 ~ 2026-07-05
> **角色**：Evidence Gatekeeper（只读验证 + 登记，不改材料/不 push/不 deploy）
> **收口状态**：`PARTIAL / LOCAL VERIFIED / E2E GATED`
> **明确否定**：NOT Production Ready / NOT 完整 Demo PASS

---

## 状态锁定

```
Evidence Map = PARTIAL / LOCAL VERIFIED / E2E GATED

接收:
- Demo accounts    = Verified_DB_ONLY
- Research runtime = Verified_LOCAL_SMOKE
- Trust Gate       = Verified_LOCAL_GUARD

不得升级:
- Login E2E                          → Unknown
- Production /api/analyze E2E        → Unknown
- Production Trust Gate participation → Unknown
- Production Ready                    → NOT CLAIMED
```

---

## Evidence Map（当前）

### 🟢 Verified（本地/DB 边界内）

| 检查项 | 状态标签 | 证据 |
|---|---|---|
| 3 个演示账号 | Verified_DB_ONLY | demo/demo2/demo3 均 tier=vip, is_active=1（只读 DB，未打印 hash，未改账号）|
| 一分钟研报主流程 | Verified_LOCAL_SMOKE | smoke DONE / qc_passed=true / 16 events / evidence_count=2 |
| Evidence Bundle 生成 | Verified_LOCAL_SMOKE | smoke evidence_count=2；`build_evidence_bundle` 运行级验证 |
| Trust Gate 参与 | Verified_LOCAL_GUARD | `_run_trust_gate` 分类 blocked/allowed/passthrough 正确 |
| QC 拦截不合格证据 | Verified_LOCAL_GUARD | failure quote → blocked_fields=['all'], evidence={} |
| 报告避免越界建议 | LOCAL_GUARD / LOCAL_ONLY | 禁止行为清单一致（短线/仓位/交易/资金流 BLOCKED）|

### ⚪ Unknown（E2E Gated，不得升级）

| 检查项 | 原因 |
|---|---|
| Login E2E | 未做登录 E2E，无凭据授权 |
| 生产 /api/analyze E2E | 未跑，需 deploy/生产调用授权 + 真实数据源 |
| 生产报告中 Trust Gate 真实参与 | 仅本地验证，生产链路未证 |
| 2 份年报 PDF 下载 | 仓库 PDF 总数=0，无实体/链接 |
| 2 份年报 PDF 解析 | 无 PDF 实体 |
| trust_gate payload 缺失分支行为 | 见下方 Guard Behavior Finding |

---

## Evidence Sample Registration

**Verified_LOCAL_SMOKE 的运行样本**（暂不清理，登记后可只留 sha256 + 摘要）：

| 字段 | 值 |
|---|---|
| sample_path | `/tmp/research_runtime_events.jsonl` |
| sha256 | `e1d1ea7aed83e28ba5863f88f9e844dcb3f212cf23eeb070b510ac9af2c9ed60` |
| timestamp | `2026-07-04T16:01:18Z`（events created_at）|
| line_count | 16 |
| final_state | `DONE` |
| evidence_count | 2 |
| qc_passed | `true` |
| provider | **local**（`local_research_stub`，NOT production）|
| symbol | 300750.SZ |
| smoke_script | `smoke_research_runtime.py` |

> 清理策略：登记完成后，如需清 /tmp，可只保留本表（sha256 + 摘要），不保留原始 16 行样本。

---

## Guard Behavior Finding（单独登记，不忽略）

**trust_gate payload 缺失分支**：

- **现象**：`_run_trust_gate` 遍历 raw evidence 时，若 `kind` 以 `gateway_` 开头但 `item["payload"]` 缺失/非 dict，走 `trust_gate_error` 分支——**既不 block 也不 allow**，静默跳过。
- **来源**：本轮 C TEST 2 首次把 gateway_response 错放在 `item["data"]`（应放 `item["payload"]`），暴露此分支。
- **判定**：这**不是 Trust Gate 缺陷**（我的测试输入结构错误），但暴露一个真实边界——**error 分支不是 fail-closed**。
- **风险**：如果生产链路某处产生 payload 缺失的 gateway 证据，Trust Gate 不会拦截也不会放行，该证据"消失"，可能导致报告缺证据但不报错。
- **待办**：后续单独评估是否应改成 **fail-closed**（payload 缺失即 block），而非当前的静默 error。**本窗口只登记，不改代码。**

---

## What Still Requires E2E

| 需 E2E 的项 | 前提/授权 |
|---|---|
| Login E2E（demo/demo2/demo3 真能登录）| 凭据授权 + 显式许可 |
| 生产 /api/analyze 一分钟研报全链路 | Deploy/生产调用授权 + 真实数据源（非 stub）|
| Trust Gate 在生产报告里真实拦截 | 生产 E2E + 真实 gateway 响应样本 |
| 年报 PDF 下载 + 解析 | 见下方 PDF 来源限定 |

---

## 年报 PDF 验证限定（用户拍板）

年报 PDF 仍保持 **Unknown**。后续补 Evidence 目标限定为：

1. 宝钢股份 2023 年年度报告全文 PDF
2. 宝钢股份 2024 年年度报告全文 PDF

**合法来源优先级**：
1. 上交所公告原始 PDF
2. 巨潮资讯原始 PDF
3. 公司官网 IR 原始 PDF

**禁止**：
- ❌ 年报摘要替代全文
- ❌ 新闻稿替代年报
- ❌ 搜索结果摘要 / 截图 / 网页正文替代 PDF

**升级条件**：只有拿到 PDF 实体并完成下载 + 解析后，才允许从 Unknown → Verified。

---

## 边界确认

- 未改材料（F1/F2/C1/C3 只登记，未处理）
- 未批量替换「林妹妹」
- 未改「已上线模块」文案
- 未 push / 未 deploy / 未创建或修改账号
- 未宣称 Production Ready
- Evidence Map = PARTIAL / LOCAL VERIFIED / E2E GATED
