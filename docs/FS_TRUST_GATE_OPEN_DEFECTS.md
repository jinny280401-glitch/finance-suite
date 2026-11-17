# FS_TRUST_GATE_OPEN_DEFECTS

**日期：** 2026-11-18  
**模式：** STRICT_READ_ONLY（本文件为缺陷登记，不含修复）  
**FULL_SUITE：** 52/57 PASS  
**OPEN_DEFECTS：** 5  
**本轮来源：** GAP-1/GAP-4 接线后基线，5 项均为历史遗留，非本轮引入。

---

## 缺陷清单总览

| ID | 测试 | 文件:行 | 优先级 | 影响 LLM 前置准入？ |
|---|---|---|---|---|
| OD-1 | test_f04_future_timestamp_rejected | test_trust_gate_phase1a.py:650 | P1 | YES — 未来时间戳可 PASS |
| OD-2 | test_f05_stock_eod_consistency | test_trust_gate_phase1a.py:726 | P2 | NO — 契约一致性 |
| OD-3 | test_lv01_replay_tushare_t3 | test_trust_gate_phase1a.py:288 | P3 | NO — 测试数据陈旧 |
| OD-4 | test_p3_derived_valuation_caps_status | test_evidence_provenance.py:154 | P0 | YES — 派生估值可升级 QC status |
| OD-5 | test_p3_no_claim_upgrade_chain | test_evidence_provenance.py:253 | P0 | YES — 同 OD-4 根因 |

---

## OD-1: F04 未来时间戳准入

**测试位置：** `tests/test_trust_gate_phase1a.py:650` (`test_f04_future_timestamp_rejected`)  
**实现位置：** `trust_gate/boundaries/g3_freshness.py:271`

**预期行为：** 未来时间戳（含明天 date-only）必须 G3_FUTURE_TIMESTAMP BLOCK。  
**实际行为：** 明天 date-only 时间戳 PASS。2 天后的 datetime 时间戳正确 BLOCK。

**根因：** g3_freshness.py:271 容差为 `-90000`（25h）。date-only 时间戳被转为当日 23:59:59 本地时间（g3_freshness.py:95-97），明天 date-only = 明天 23:59:59，距现在最多 ~24h，落在 25h 容差内 → PASS。

**首次失败证据：** 2026-11-18 本轮基线运行，`assert_block(tomorrow_decision, "G3")` 失败，`got PASS`。datetime+2d 路径（第一断言）PASS。

**历史遗留证明：** 本轮未修改 `g3_freshness.py`（git diff HEAD 证实）。该容差 90000 在本轮前已存在。

**影响业务入口：** `wind_query` action=stock 经 `_enforce_trust_gate_or_block`。若 provider 返回未来 date-only trade_date（时钟错乱或数据错误），G3 放行 → 未来数据进入 LLM 上下文。

**影响 LLM 前置准入：** YES。未来时间戳数据可绕过 G3 进入 Evidence。

**修复方案（仅设计）：** 将 date-only 时间戳的容差收紧。date-only 转 23:59:59 是为避免"今日 EOD 被判为午夜陈旧"，但明天 date-only 应判未来。方案：date-only 时间戳若日期 > 今日日期 → 直接 G3_FUTURE_TIMESTAMP，不套用 25h 容差。

**必败负控设计：** 输入 trade_date=明天 → assert BLOCK + reason_code=G3_FUTURE_TIMESTAMP。输入 trade_date=今日 → assert PASS（EOD 允许今日）。输入 trade_date=昨日 → assert PASS（24h 内）。

**建议优先级：** P1

---

## OD-2: F05 时间戳契约一致性

**测试位置：** `tests/test_trust_gate_phase1a.py:726` (`test_f05_stock_eod_consistency`)  
**实现位置：** `trust_gate/boundaries/g3_freshness.py:56`

**预期行为：** `TIMESTAMP_REQUIRED_ACTIONS == {"stock"}`（测试断言只含 stock）。  
**实际行为：** `TIMESTAMP_REQUIRED_ACTIONS = {"stock", "daily_price"}`，含额外项。

**根因：** g3_freshness.py:56 将 `daily_price` 加入 `TIMESTAMP_REQUIRED_ACTIONS`，但测试 F05 期望只有 `stock`。两者契约不一致。需判定 `daily_price` 是否应要求时间戳：`daily_price` 是 EOD 日线（g3_freshness.py:40 注释 "EOD snapshot, same rule as stock"），逻辑上应与 stock 同等要求时间戳。

**首次失败证据：** 2026-11-18 基线，`assert TIMESTAMP_REQUIRED_ACTIONS == {"stock"}` 失败，`got {'daily_price', 'stock'}`。

**历史遗留证明：** 本轮未修改 g3_freshness.py。`daily_price` 条目在本轮前已存在。

**影响业务入口：** `wind_query` action=daily_price 若被调用，会要求时间戳（G3_TIMESTAMP_MISSING_REQUIRED）。当前 wind_query chains 字典无 daily_price action，实际不触发。

**影响 LLM 前置准入：** NO（当前无调用路径）。契约不一致本身是文档/测试维护问题。

**修复方案（仅设计）：** 判定 `daily_price` 是否为 wind_query action。若是 → 更新测试 F05 期望为 `{"stock", "daily_price"}`。若不是 → 从集合移除 `daily_price`。需 Owner 裁决 daily_price 是否为有效 action。

**必败负控设计：** 若保留 daily_price：输入 daily_price 无时间戳 → BLOCK。若移除：`TIMESTAMP_REQUIRED_ACTIONS == {"stock"}` 断言通过。

**建议优先级：** P2

---

## OD-3: LV01 Replay 时间基准

**测试位置：** `tests/test_trust_gate_phase1a.py:288` (`test_lv01_replay_tushare_t3`)  
**实现位置：** 测试自身硬编码日期

**预期行为：** data_timestamp=2026-08-03，retrieved_at=2026-08-06，data age ~72h。  
**实际行为：** 测试用 `datetime.now()` 计算年龄，当前 2026-11-18，age=2559.8h，断言 `70 < age < 80` 失败。

**根因：** 测试硬编码绝对日期（2026-08-03/08-06），但 G3 用真实当前时间计算年龄。随时间推移，年龄增长，断言失效。G3 BLOCK 本身正确（数据确实陈旧），只是年龄断言过时。

**首次失败证据：** 2026-11-18 基线，`assert 70 < age_hours < 80` 失败，`got 2559.8h`。注意 G3 BLOCK 断言（:324）PASS——gate 逻辑正确。

**历史遗留证明：** 本轮未修改 g3_freshness.py 或该测试。硬编码日期在本轮前已存在。

**影响业务入口：** 无。G3 正确 BLOCK 陈旧数据。缺陷仅在测试断言。

**影响 LLM 前置准入：** NO。G3 行为正确，仅测试年龄断言过时。

**修复方案（仅设计）：** 测试应使用相对日期（`datetime.now() - timedelta(days=3)` 构造 data_timestamp），而非硬编码 2026-08-03。retrieved_at 同样用相对日期。

**必败负控设计：** 构造 data_timestamp=now-3d，retrieved_at=now → assert age 70-80h + assert BLOCK。

**建议优先级：** P3

---

## OD-4 / OD-5: P3 派生估值 QC 升级

**测试位置：**  
- OD-4: `tests/test_evidence_provenance.py:154` (`test_p3_derived_valuation_caps_status`)  
- OD-5: `tests/test_evidence_provenance.py:253` (`test_p3_no_claim_upgrade_chain`)  

**实现位置：** `mcp_server.py:275-278` (`_qc_stock` status 逻辑)

**预期行为：** 当 `valuation_source.type == "derived"` 时，`_qc_stock` 应将 status cap 在 "partial"，即使 completeness >= 0.8。  
**实际行为：** `_qc_stock` 不检查 `valuation_source.type`，completeness >= 0.8 + freshness_ok → status="success"。

**根因：** mcp_server.py:275-278 的 status 判断只看 completeness 和 freshness，不检查 `data["valuation"]["valuation_source"]["type"]`。测试 P3 期望该检查存在。

**首次失败证据：** 2026-11-18 基线，`assert qc["status"] == "partial"` 失败，`got 'success'`。OD-5 同根因，`assert qc["status"] != "success"` 失败。

**历史遗留证明：** 本轮未修改 `_qc_stock`（mcp_server.py:200-296）。git diff HEAD 对 mcp_server.py 的修改仅在 wind_query 接线区（L1091+）和 choke point（L66-182），未触及 `_qc_stock`。

**影响业务入口：** `stock_analysis` 工具调用 `_qc_stock`（mcp_server.py:533）。派生估值（Wind 不可用时从 AkShare 推算 PE/PB）被标为 status=success，可能被 LLM 误认为已验证能力。

**影响 LLM 前置准入：** YES。派生估值 QC status=success 可触发 `allowed_use` 升级（`_allowed_use` 在 status=success 时返回完整三用途），使派生数据获得与真实 provider 数据相同的准入权限。

**修复方案（仅设计）：** 在 `_qc_stock` status 判断前，检查 `data.get("valuation", {}).get("valuation_source", {}).get("type") == "derived"`，若是 → 强制 status="partial"（在 completeness/freshness 判断之后覆盖）。

**必败负控设计：**  
输入：所有维度 present + valuation_source.type="derived" → assert status=="partial"。  
输入：所有维度 present + valuation_source.type="real_provider" → assert status=="success"（若 freshness_ok）。  
输入：derived + 缺一维 → assert status=="partial"。

**建议优先级：** P0（OD-4 + OD-5 同根因，最高优先级——直接影响 LLM 准入等级）

---

## 优先级排序

1. **P0 — OD-4/OD-5**：派生估值 QC 升级，直接影响 LLM 准入等级，衍生数据可能获得真实 provider 权限。
2. **P1 — OD-1**：未来时间戳准入，时钟错乱数据可进入 LLM。
3. **P2 — OD-2**：契约一致性，当前无调用路径但维护债务。
4. **P3 — OD-3**：测试数据陈旧，gate 逻辑正确，仅测试断言失效。

---

**状态：** 5 项缺陷正式登记，未关闭。均经历史遗留证明（git diff 证实本轮未触及相关代码）。等待 Owner 授权修复 Sprint。
