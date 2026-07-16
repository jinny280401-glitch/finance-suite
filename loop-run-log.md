# Loop Run Log — Finance Suite

> **实际 run log 存储在 Engram**：`POST http://127.0.0.1:8766/lessons`  
> 本文件为 loop-audit 兼容性摘要，不替代 Engram。

## 查询完整日志

```bash
# 按 domain 查询
curl -s http://127.0.0.1:8766/lessons?domain=finance-suite | jq '.'

# 最近 20 条
curl -s http://127.0.0.1:8766/lessons?domain=finance-suite | jq -r '.[] | "\(.timestamp) - \(.lesson)"' | head -20
```

## 摘要（最近运行）

| Timestamp | Loop | Status | Tokens | Notes |
|-----------|------|--------|--------|-------|
| 2026-07-16 23:40 | loop-audit | ✅ | — | Score: 75/100 |
| 2026-07-16 23:15 | loop-audit | ✅ | — | Score: 50/100, initial integration |
| 2026-07-16 09:00 | Morning Brief | ✅ | ~15k | Daily automation |
| 2026-07-15 | D20 Audit | ✅ CLOSED | — | DRIFT-01 resolved |
| 2026-07-14 | Provider Health | ✅ | ~5k | AkShare/Choice status |
| 2026-07-10 | Intelligence Loop v1 | 🔒 | ~80k | Frozen per G directive |

## 预算使用

| Date | Total tokens | Budget | % Used |
|------|-------------|--------|--------|
| 2026-07-16 | ~25k | 250k | 10% |
| 2026-07-15 | ~105k | 250k | 42% |
| 2026-07-14 | ~90k | 250k | 36% |

## Incidents

| Date | Type | Resolution | Engram ref |
|------|------|-----------|------------|
| 2026-07-02 | Freeze (User STOP) | Awaiting window open | `project_freeze_20260702` |
| 2026-06-08 | Pre-Event Freeze | Resumed T+35min | `feedback_pre_event_freeze` |
| 2026-05-12 | "HTTP 200 = 上线" 误判 | 6-item evidence chain established | `feedback_deployment_evidence_chain` |
