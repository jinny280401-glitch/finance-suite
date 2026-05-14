# Finance Suite 宏观内参最小闭环补丁归档

**日期**：2026-05-14
**作者**：Claude / Codex
**版本**：生产侧最小闭环补丁

---

## 1. 补丁 Diff 摘要

| 改动 | 说明 |
|------|------|
| `_summarize_record_value()` | 新 helper，从 macro record 提取关键数值做摘要展示，避免旧 record 全量灌给模型当实时证据 |
| `_format_macro_indicators_with_freshness()` | fresh 指标全量保留，非 fresh 指标只注入 1 行摘要 + 非实时背景数据标注 |
| `context` 头部新增数据层级规则 | 明确职责边界：`event_facts` > `macro_indicators` > `search_results` |
| `event_facts` 标题改为优先级最高 | 强化结构化信号，确保事件事实驱动分析 |
| `consistency_error` 分支 | 先 strip macro_indicators 重试 LLM；仍冲突才返回 error，防止旧指标干扰事件判断 |

---

## 2. Smoke 输出（示例）

### 数据时间边界

- 事件事实
  - status: confirmed/official
  - event_time: 2026-05-11
  - source_time: 2026-05-11
  - basis: confirmed Bloomberg / Reuters / AP News

- 背景宏观数据
  - GDP: background_periodic
  - CPI: background_non_realtime
  - PMI: background_non_realtime
  - LPR: fresh

- 说明：事件事实用于确认当前事件；背景宏观数据仅用于分析宏观环境，不能否定事件真实性。

### 正文关键段示例

> "所有宏观指标均严重滞后——最新GDP数据停留在2006年…对判断当前形势毫无参考价值。唯一尚属新鲜的数据是LPR利率"

---

## 3. _qc 字段示例

```json
{
  "status": "success",
  "completeness": 1.0,
  "used_timeline_context": true,
  "event_status": "confirmed/official"
}
```

---

## 4. 缓存策略

- `macro` 查询仍关闭缓存：`cached = None if req.skill_type == "macro"`
- 目的：保证每次宏观内参都重新拉取最新 `event_facts`，并重新执行 freshness gate。
- 其他 `skill_type` 不受影响，仍沿用原缓存策略。

---

## 5. 说明与后续

本次补丁仅修复事件事实驱动链路及宏观指标背景化，防止旧指标误导事件分析。

未覆盖范围：

- `macro_data` 本身指标可能滞后（GDP/PMI/M2 fetcher 疑似静默坏掉，返回 2006-2008 年数据），未在本次最小闭环内修复。
- 建议另开低优先级 issue，记录 `macro_data` 数据源更新、fallback 或定期刷新计划。
