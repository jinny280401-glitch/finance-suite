# Loop Budget — Finance Suite

## Daily limits

| Loop | Max runs/day | Max tokens/day | Max sub-agent spawns/run |
|------|--------------|----------------|--------------------------|
| Morning Brief | 1 | 50k | 0 (L1 report-only) |
| Intelligence Loop | 1 | 100k | 2 (A/B/C analysis) |
| Golden Pit Scan | 1 | 80k | 1 (verification) |
| Provider Health Check | 4 | 20k | 0 (smoke only) |

## Freeze Rules

### Pre-Event Freeze (T-12h)
开盘前 12 小时窗口（T-12h 到 T+5min）冻结所有非稳定性工作。

**冻结范围**：
- 新 skill 安装
- ADR/架构文档撰写
- 探索性研究
- 非生产 bug 修复
- 任何"明天能做的事"

**保留范围**：
- 生产端点存活检查
- 关键路径保活
- cron 预检
- 缓存/数据新鲜度修复（如直接影响明早）

**恢复触发**：开盘后 30 分钟 + cron log 看到关键端点 HTTP 200

**来源**: [[feedback_pre_event_freeze]]

### Explicit Freeze (User STOP)
用户显式下达 STOP 时，所有窗口冻结到**明确新窗口开启**。

**冻结期硬规则（绝对不可破）**：
- ❌ `git push`
- ❌ deploy（任何工具任何路径）
- ❌ cleanup / 重构 / 顺手改
- ❌ Engram write
- ❌ production claims（任何"已上线"声明都禁止）
- ✅ read-only / smoke / 探活可以（前提是不写任何状态）

**破例计数规则**：一 session 破例 ≥2 次立即重置 freeze

**来源**: [[project_freeze_20260702]]

## On budget exceed

1. Pause all schedulers (cron/launchd)
2. Append event to Engram (`POST http://127.0.0.1:8766/lessons`)
3. Notify human (update Memory MEMORY.md High Priority section)

## Kill switch

- Command: User explicit "STOP" or "FREEZE"
- Resume: Only after user explicitly opens a numbered window (e.g., "窗口 #1 开启")
- Detection: Any `git push`, `deploy`, `ssh production`, or Engram write during freeze = violation

## Token cost monitoring

**实际成本追踪**：
- Morning Brief automation: ~15k tokens/run (measured 2026-07)
- Intelligence Loop v1 (A/B/C): ~80k tokens/run
- Provider smoke checks: ~5k tokens/run

**预算分配理由**：
- Morning Brief 设 50k 留 3.3x buffer（考虑异常重试）
- Intelligence Loop 设 100k 留 1.25x buffer
- 总日预算：250k tokens/day（平稳运行约 100k/day）

**超预算处理**：
1. 立即停止当前 loop
2. 写入 Engram lesson（标记异常原因）
3. 人工审查是否为异常数据或 loop 逻辑错误

## Related

- Automation alignment: See `docs/d20_automation_alignment_audit.md`
- Evidence chain: See `feedback_deployment_evidence_chain.md` in Memory
- Freeze erosion rules: See `feedback_freeze_erosion.md` in Memory
