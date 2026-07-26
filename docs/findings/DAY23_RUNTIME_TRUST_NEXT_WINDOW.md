# Runtime Trust Next Window — Implementation Design v0.1

**日期**: 2026-07-26
**前置**: D23 Runtime Trust Governance CLOSED（六公理 + 三轴模型定版）
**状态**: Design Only — 不开代码，只写 Spec
**下窗口触发条件**: 金融数智杯提交完成 + 显式开窗授权

---

## 三轴回顾（D23 定版）

| 轴 | 问题 | 载体 | 当前成熟度 |
|---|---|---|---|
| Provenance | 这是什么？为什么可信？ | Evidence Manifest v1 | L3 Implemented（消费端）/ L4 ❌ |
| Durability | 曾经是否真实存在？ | Memory Receipt | L1 Declared |
| Validity | 现在是否仍然有效？ | Freshness Contract | L1 Declared |

实现顺序不可交换：Provenance → Durability → Validity。

本窗口聚焦 **Durability（Memory Receipt v0）** + **Recall Trust Gate 定位** + **Freshness Model 设计**。不开大改造。

---

## P1: Memory Receipt v0

### 为什么先做 Receipt

当前链路：

```
Memory → Recall → Agent → Answer
```

Agent 使用记忆时，无法证明：
- 这条记忆是什么时候写的
- 写入是否成功持久化
- 召回时内容是否完整

缺 Receipt 的后果：Agent 基于记忆做决策，但记忆的可靠性无从验证。

### 目标链路

```
Memory Write
  ↓
Receipt（写入确认）
  ↓
Memory Store
  ↓
Recall
  ↓
Recall Validation（召回时验 receipt）
  ↓
Agent
  ↓
Answer
```

### Receipt 最小字段（v0）

```json
{
  "memory_id": "engram://abc123def456",
  "source": "user_input | agent_generated | system_event",
  "created_at": "2026-07-26T23:47:00+08:00",
  "retrieved_at": "2026-07-26T23:50:00+08:00",
  "confidence": "verified | unverified | stale",
  "scope": "session | project | global",
  "stale_after": "2026-08-02T23:47:00+08:00",
  "allowed_use": ["fundamental_overview", "historical_context"]
}
```

**字段说明**：

| 字段 | 为什么需要 | 不填的后果 |
|---|---|---|
| `memory_id` | 唯一标识，可追溯 | 无法区分不同记忆 |
| `source` | 区分记忆来源（用户说的 / Agent 生成的 / 系统事件） | 把 Agent 推测当成用户事实 |
| `created_at` | 记忆写入时间 | 无法判断时效 |
| `retrieved_at` | 召回时间（**≠ created_at**） | D23 已证明：有 `retrieved_at` 不等于结论会自动过期 |
| `confidence` | 记忆可靠性分级 | 所有记忆同等对待，低质量记忆污染决策 |
| `scope` | 记忆适用范围 | 跨项目误用 |
| `stale_after` | 过期时间（**这是 D23 4a 的答案**） | 陈旧证据静默支撑当下结论 |
| `allowed_use` | 允许的使用层级 | 基本面数据被用于短期价格预测 |

### `stale_after` 为什么是关键

D23 Finding-01 证明了：**记了 `retrieved_at` 不等于结论会过期**。

`retrieved_at` 只回答了"什么时候拿到的"。
`stale_after` 回答的是"拿到之后还能用多久"。

没有 `stale_after`：
- 集合竞价数据（9:25 有效）在 14:00 仍被判 REAL
- 昨天的财报数据在今天仍被视为"最新"
- freshness 门形同虚设

四种 freshness class（来自 byteseek/mira 的 Routing Card 设计）：

| Class | 含义 | 示例 |
|---|---|---|
| `live` | 实时数据，当前有效 | 当前盘口价 |
| `delayed` | 延迟数据，仍在窗口内 | 15 分钟延迟行情（对长线分析仍有效） |
| `stale` | 已过期，不可支撑结论 | 昨日集合竞价数据用于今日盘中判断 |
| `unavailable` | 无法获取，标记为缺失 | 信源断连 |

### Receipt 验证规则

Agent 召回记忆时：
1. 查 `stale_after`：如果 `now > stale_after` → 标记 `confidence=stale`，降级使用
2. 查 `allowed_use`：如果用户请求的结论层级超出允许范围 → 阻断或降级
3. 查 `source`：如果 `source=agent_generated` 且无人工确认 → 标记 `confidence=unverified`

### 验收标准

能回答这条问题就算 v0 完成：

> "AI 为什么知道这个？"

回答格式：

> "第 3 次 sync 的 receipt，memory_id=abc123，status=success，source=user_input，created_at=2026-07-26，stale_after=2026-08-02，当前仍在有效窗口内。"

**不做**：
- ❌ 不改 Engram API
- ❌ 不改 recall 机制
- ❌ 不写 Gate 代码
- ❌ 不宣称"Memory 已可靠"

---

## P2: Recall Trust Gate 定位

### 问题

当前 Recall→Agent 链路没有 Gate。记忆被召回后直接进入 Context Injection。

### 先定位，不实现

当前任务只有一个：**找到 Recall 的真正入口函数，画调用链，标记 Gate 应该插在哪里**。

### 调用链（待填充 — 需实际代码定位）

```
用户输入
  ↓
???（Prompt 组装入口）
  ↓
???（Memory recall 触发点）       ← 需要定位
  ↓
???（Context injection 点）       ← 需要定位
  ↓
LLM
```

### Gate 插入点（设计，非实现）

Trust Gate 应该插在 **Recall 之后、Context Injection 之前**：

```
Recall
  ↓
═══ Recall Trust Gate ═══
  │ - 验 receipt 存在
  │ - 验 stale_after 未过期
  │ - 验 allowed_use 覆盖
  ↓
Context Injection
```

**不是**插在 LLM 输出后做 QC（那是后置审查，D23 已证明后置审查不可靠）。

### Gate 判定逻辑（设计）

```
For each recalled memory:
  if no receipt:
    → mark confidence=unverified
    → restrict allowed_use to []
  if receipt exists and now > receipt.stale_after:
    → mark confidence=stale
    → restrict allowed_use to ["historical_context"]
  if receipt.confidence == "unverified" and receipt.source == "agent_generated":
    → require human confirmation before use
```

### 当前 Unknown

- 生产环境中 Memory recall 的入口函数是哪个？
- Recall 结果的结构是什么？是否携带元数据？
- Context injection 在哪个函数/模块？

这些必须定位后才能设计 Gate 的实际插入代码。**当前只做定位，不做实现**。

### 与 Bad Memory 论文的对齐

arXiv 2607.14611（Bad Memory）的核心发现：记忆系统本身可能成为攻击面。这进一步支持"Recall 也必须过 Trust Gate"——不只是信源数据要过门，记忆召回也要过门。

---

## P3: Freshness Model

### 两个独立问题（D23 4a vs 4b）

**4a · Evidence Exists ≠ Evidence Valid（设计层）**
- 问题：`retrieved_at` 存在，但没有定义"多久后过期"
- 答案（本窗口设计）：`stale_after` + `must_refresh_if`

**4b · Freshness Logic Exists ≠ Freshness Evidence Exists（运行层）**
- 问题：consumer 有 freshness 降级逻辑，producer 不产出 freshness
- 答案：需要先定义谁负责产生 freshness（Producer Contract），再实现

### Freshness Producer Contract（设计）

生产 gateway 每次数据调用后，必须在 response 中写入：

```json
{
  "data": {...},
  "_qc": {
    "status": "success",
    "freshness": {
      "retrieved_at": "2026-07-26T14:35:00+08:00",
      "stale_after": "2026-07-26T14:40:00+08:00",
      "class": "delayed",
      "must_refresh_if": ["market_close", "major_news"]
    }
  }
}
```

### `must_refresh_if` 事件触发词表（v0 草案）

| 事件 | 影响范围 |
|---|---|
| `market_open` | 所有行情类数据 |
| `market_close` | 日频汇总数据 |
| `major_news` | 个股基本面判断 |
| `earnings_release` | 该股所有财务数据 |
| `index_rebalance` | 指数成分数据 |

### 当前不做

- ❌ 不实现 Producer Contract
- ❌ 不改 gateway 代码
- ❌ 不扩展 `_qc` schema

---

## 下窗口实施顺序

```
本窗口（现在）:
  ✅ 写 Memory Receipt v0 Spec
  ✅ 标记 Recall Gate 定位任务（只定位，不实现）
  ✅ 写 Freshness Model 设计

下一窗口（授权后）:
  1. 定位生产 Memory recall 入口函数 → 画完整调用链
  2. Receiver v0 字段落地（不改 Engram，先在 Evidence Manifest 层加）
  3. Consumer 端 recalled memory validation 逻辑
  4. Freshness Producer Contract 在 gateway 最小落地（1 个 provider 试点）
```

---

## 不动的项（本窗口锁定）

- D23 Finding Document — CLOSED，不改
- Evidence Manifest v1 schema — 冻结，不在本窗口改
- Engram API — 不改
- Recall 机制 — 不改
- Gateway 代码 — 不改
