# DAY23: Runtime Trust Gap — Freshness / Memory / Governance Principle

**Status:** CLOSED (Governance Finding) — G 签署 2026-07-26

```
Type:            Governance Architecture
Principles:      Defined · Documented
Evidence:        Governance Finding Completed
Code Change:     None
Implementation:  NOT STARTED
Runtime:         NOT PROVEN
Production:      NOT CLAIMED
Next Window:     Trust Runtime Implementation Design v0.1
```

> ### ⚠️ 措辞边界（不可违反）
> 本文档定义的是 **Principles，不是 Capabilities**。
> 当前状态：`Principles Defined ✅ / Documented ✅ / Runtime Proven ❌`
> - ❌ 不得写：「Vera 已具备六层可信治理能力」
> - ✅ 只能写：「Vera 采用六项运行可信治理原则」
>
> 这条边界本身就是公理 1 的自指应用 —— 写下原则等于配置存在，不等于运行能力存在。
**Domain:** finance-suite / claude-code-infra
**Date:** 2026-07-26
**Severity:** Finding-01 HIGH（治理边界失效，静默判为可信）/ Finding-02 MEDIUM（可靠性，非安全）
**Scope:** 仅记录与冻结。不改 schema、不改 gateway、不改 hook。
**Origin:** EigenFlux 外部调研（Hanyu Research Agent）→ 反向自查 Finance Suite 链路

---

## Finding-01 · Freshness Capability Gap

### 事实（读文件确认，非推断）

**Consumer 侧存在且逻辑正确** — `research_runtime/evidence_bundle.py:72-82`

```python
freshness = (gateway_response.get("freshness") or "").lower()
tier = gateway_response.get("provider_tier")
if freshness == "mock" or "stub" in provider or provider == "":
    return ProviderClass.MOCK
if tier == 3 or freshness in ("stale", "cached"):
    return ProviderClass.FALLBACK
return ProviderClass.REAL
```

`ProviderClass` 会进一步收窄 `allowed_use`（MOCK → 仅 workflow_smoke/runtime_test；FALLBACK → 仅 fundamental_overview/historical_context）。这套降级机制本身是对的。

**Producer 侧缺失** — 全仓库写入 `freshness` 的位置：

| 文件 | 写入值 | 类型 |
|---|---|---|
| `smoke_trust_gate_session_guard.py:22` | `"realtime"` | 测试 |
| `smoke_trust_gate_runtime_integration_v1.py:21` | `"delayed"` | 测试 |
| `smoke_trust_gate_workflow_v1.py:27,47,67,85,104` | `delayed/stale/mock` | 测试 |
| `smoke_trust_gate_runtime_v0.py:16` | `delayed/realtime` | 测试 |
| `smoke_trust_gate_premerge.py:47,100,154` | `delayed/mock` | 测试 |
| `scripts/finance_data_gateway.py` | **零命中** | 生产 |

### 失效路径

```
真实 provider 调用
      ↓
gateway_response 无 freshness 键
      ↓
.get("freshness") → None → "" (or 兜底)
      ↓
"" != "mock"  且  "" not in ("stale","cached")
      ↓
return ProviderClass.REAL     ← 默认判为最新鲜
```

**根因：缺省语义倒置。** 缺少新鲜度证据时，系统默认自己 fresh，而不是默认未证明。

### 为什么 smoke 全绿掩盖了它

smoke 验的是 `_classify_provider` 这个分类函数在给定输入下的行为，**不验 gateway 会不会产出该输入**。测试自己喂了 `freshness=`，于是测的是"如果有 freshness 会怎样"，而非"生产路径有没有 freshness"。

### 结论

```
Freshness Validation:
  LOGIC        IMPLEMENTED  ✅
  PRODUCER     ABSENT       ❌
  SMOKE        PASS (但不覆盖 producer)
  PRODUCTION   NOT PROVEN
```

**Status:**
- `CONFIRMED` — static implementation gap（consumer/producer 不一致，代码静态确认）
- `PARTIAL` — production impact（真实 provider 运行时返回值未复现）

---

## Finding-02 · Memory Reliability Gap

### 事实

`~/.claude/hooks/engram-sync/stop.sh` — Stop 事件的 async hook：

- `urllib.request.urlopen(req, timeout=5)` 写 Engram `/lessons`
- 异常被 `except Exception: pass` 吞掉
- 无 receipt、无日志、无重试

Engram 未启动 / 5 秒内未响应 / 进程先退出 → 该会话记录静默丢失，用户与后续 session 均不知情。

### 分类

**不是安全漏洞**（该 hook 不承担 blocking 责任，4 个 hook 全 `async:true` 但均为通知/记录用途，无安全暴露面）。
**是可靠性漏洞**：`write()` 之后没有 `receipt` 与 `verify`，无法区分"成功"与"静默失败"。

### 与 Finding-01 同构

两者形状相同：**缺少回执 → 无法区分成功与静默失败 → 默认按成功处理。**

**Status: RELIABILITY GAP**

---

## Finding-03 · Governance Principle

### Vera Trust Architecture 五条公理（本窗口固定）

| # | 公理 | 中文 | 层 | 来源 |
|---|---|---|---|---|
| 1 | Configuration Exists ≠ Runtime Capability Exists | 配置存在 ≠ 运行能力存在 | runtime | D23 新增 |
| 2 | Credential Exists ≠ Capability Proven | 凭证存在 ≠ 能力验证通过 | provider | Wind D19 |
| 3 | HTTP Success ≠ Business Success | 传输成功 ≠ 业务成功 | transport | 部署证据链 |
| 4a | Evidence Exists ≠ Evidence Valid | 证据存在 ≠ 仍具支撑当前结论的有效性 | **设计层** | Mira（外部输入） |
| 4b | Freshness Logic Exists ≠ Freshness Evidence Exists | 存在 freshness 判断逻辑 ≠ 运行时已获得 freshness 证据输入 | **运行层** | D23 Finding-01 |
| 5 | Memory Written ≠ Memory Durable | 写入记忆 ≠ 记忆可靠保存 | memory | D23 Finding-02 |

### 4a / 4b 必须分开（G 签署 2026-07-26）

不拆会导致一个危险误解：**「我们已经有 freshness 字段，所以 freshness 问题解决了。」**
D23 证明的恰恰是：字段存在，不代表生产链路会产生字段。

**4a · Evidence Exists ≠ Evidence Valid**（设计层）
证据存在，不代表证据仍具备支撑当前结论的有效性。
问题形态：`retrieved_at` → 不知道还能用多久。
解决方向：Freshness Window / Validity Policy。

**4b · Freshness Logic Exists ≠ Freshness Evidence Exists**（运行层）
系统存在 freshness 判断逻辑，不代表运行时已获得 freshness 证据输入。
问题形态：
```
Consumer:  读取 freshness
              ↑
              |  ← 断层
Producer:  不生成 freshness
```
判断逻辑存在 + 输入缺失 = 默认放行。

**4b 比 4a 更危险**，因为它制造「已治理假象」：审计者看到降级逻辑会认为该风险已被覆盖。
**4b 也比 4a 更有产品价值** —— 对外讲 Vera 时，「你怎么解决 AI 幻觉」的普通回答是"我们增加引用"；Vera 的回答是"我们不只验证证据来源，还验证证据是否由真实运行链路产生、是否仍处于有效窗口、以及它是否允许支撑当前结论"。这是 RAG 与 Trust Runtime 的分界。

治理哲学落点：不问「代码有没有？」，问「运行时有没有真实证据证明它发生？」

### 验证层级链（本窗口补充最后一层）

```
Smoke ≠ Integration ≠ Production ≠ Business
                  +
        Schema ≠ Data Contract          ← 新增
```

> Test data proving a field exists is not equivalent to production data proving the field is populated.
> 测试数据证明字段存在，不等于生产链路证明字段会被填充。

---

## Capability Maturity Chain（G 定版 2026-07-26 · D23 最大产出）

任何新能力，套这条链定位当前级别。**六公理说明断层发生在哪里，这条链说明现在站在第几级。**

```
L0 Unknown → L1 Declared → L2 Documented → L3 Implemented → L4 Runtime Proven → L5 Production Proven
   无证据       设计/配置声明     文档·契约·定义      代码路径存在        真实运行证据          生产持续验证
```

每一级到下一级都需要**新的**证据，**上一级不构成下一级的证据**：

| L | 级别 | 证据要求 | 常见误判 |
|---|---|---|---|
| 0 | Unknown | 无任何证据 | 未被提出 ≠ 不存在风险 |
| 1 | Declared | 有设计声明 / 配置声明 | 「配置有」当成「能用」← 公理 1 |
| 2 | Documented | 有文档 / 契约 / 定义 | 「写了 schema」当成「实现了」← Schema ≠ Data Contract |
| 3 | Implemented | 代码路径存在 | 「代码有」当成「跑起来了」← 公理 4b |
| 4 | Runtime Proven | 真实运行证据可复现 | 「smoke 绿」当成「运行时证明」 |
| 5 | Production Proven | 生产环境持续验证 | 「能跑」当成「业务成功」← 公理 3 |

### 审计方法（正式表述）

> **审计能力时，必须拆解 capability components；任何组件等级低于消费者依赖等级的位置，即为治理缺口。**

这比 checklist 高一层：checklist 问「做了没有」，本判据问「消费者依赖的级别，供给方到了没有」。

F-01 按此判据拆解：

| 组件 | 等级 | 说明 |
|---|---|---|
| freshness schema | L2 Documented | 字段已定义 |
| freshness consumer logic | L3 Implemented | `evidence_bundle.py:72-82` 代码路径存在 |
| freshness producer | **L1 Declared** | 生产 gateway 零产出 |
| production freshness verification | **L0 Unknown** | 无证据 |

consumer 在 L3 却依赖一个 L1 的 producer → **maturity mismatch = 治理缺口位置**。
所以正确表述不是「Freshness = Implemented」，而是「**Freshness capability chain contains maturity mismatch**」。

**D23 三条 Finding 定位**：F-01 存在 L3/L1 错位（见上表）；F-02 Memory Receipt = L2（本文档定义了字段，未实现）；F-03 六公理+三轴 = L2。

**自指测试**：Trust Runtime 的第一个测试对象是 Trust Runtime 自己。本文档处于 **L2 Documented**，`Runtime Proven ❌` —— 不得对外表述为已具备能力。

---

## Trust Runtime 三轴模型（G 提出 2026-07-26）

六条公理底层统一，但**实现维度是三轴**，不是一个问题：

| 轴 | 问的问题 | 语义 | 当前载体 | 成熟度 |
|---|---|---|---|---|
| **Provenance** | 这是什么？为什么可信？ | 来源可追溯 | Evidence Manifest v1 | 最高（schema DEFINED） |
| **Durability** | 曾经是否真实存在？有没有可靠保存？ | 写入可证明 | Engram Receipt | 未实现 |
| **Validity** | 现在是否仍然有效？还能不能支撑当前判断？ | 时效可判定 | Freshness | 刚进入设计 |

```
              Provenance
                  |
   Durability ——— + ——— Validity
                  |
            Trust Runtime
```

**实现顺序：Provenance → Durability → Validity。** 依赖是单向的：
- 没有 provenance，freshness 没有意义（不知道来源，谈不上来源的时效）
- 没有 durability，freshness 记录本身可能丢失（判定写了但没落地）

三轴共同回答一句话：**AI 的每一次判断，都必须知道 —— 证据从哪里来、是否保存成功、现在是否仍然有效、是否允许支撑这个结论。**

---

## 修复路线（已排序，不在本窗口执行）

顺序是刻意的：**写入端先于 schema 扩展**。否则新增字段同样悬空，而 smoke 同样会绿。

### Phase 1 · Producer Contract
先回答「**谁负责产生 freshness？**」。Gateway 必须输出 `retrieved_at` + `freshness_status`（建议含 `age_seconds`）。
**没有 producer，就不要谈 consumer。**

### Phase 2 · Trust Gate Enforcement（缺省语义翻转）
```
现在危险逻辑：  missing → assume fresh
未来应该：      missing → UNKNOWN → unproven → 不得升级 REAL
```
默认不能是「不知道 = 最新」，必须是「不知道 = 未证明」。这是金融 AI 与普通 agent 的分界。

### Phase 3 · Freshness Schema Expansion（Mira 形态）
`valid_until` / `expiry_reason` / `freshness_class`。**仅在 Phase 1-2 完成后进入**，否则再次制造 `schema complete but runtime empty`。

### Phase 4 · Memory Reliability Evidence v0 — **下窗口 Priority 1（G+C 定版）**

> **改名原因**：C 审核指出「Receipt 容易被实现成写入尝试日志而非存储确认」，Rule B 要求回执必须证明「写入确认 + 未来可检索性」。

**三部件**（不可拆开交付）：

**Part 1 · Write Receipt**  
证明 `sync attempted`。字段：`session_id / timestamp / status / memory_id`。

**Part 2 · Durability Verification**  
证明 `stored and retrievable`。区分两个语义：
- `write_acknowledged` — 数据库返回 OK
- `verified_retrievable` — 写入后立刻读回成功

验收标准：`status=success` 必须同时具备 `memory_id` + `verified_retrievable=true`。

**Part 3 · Trust Metadata**  
证明记忆来源可追溯。字段：`source_scope / trust_label`。

```json
{
  "event": "memory_sync",
  "session_id": "",
  "timestamp": "",
  "status": "success|failed",
  "memory_id": "",
  "verified_retrievable": true,
  "source_scope": "user_input|tool_output|external_web",
  "trust_label": "trusted|untrusted|mixed"
}
```

`source_scope` / `trust_label` 是 C 判断最容易被省略的两个字段，因为它们需要来源分类、继承规则、默认策略，容易实现成空值或固定 `trusted`。**Part 3 缺失 → Receipt 退化为成功写日志，失去判断记忆可信度的能力。**

**P1 最小 Evidence Schema**（G 2026-07-26 —— 不做"大 Memory 系统"，只证明一条 Write 是否可验证成功）：

```json
{
  "memory_id": "",
  "write_request_time": "",
  "write_receipt_time": "",
  "storage_target": "",
  "content_hash": "",
  "receipt_hash": "",
  "verification_status": "PASS|FAIL|UNKNOWN",
  "verification_scope": "durability_only"
}
```

**明确排除的字段**（不加，否则边界膨胀）：
- ❌ `recall_accuracy` — 属 Recall Trust Gate（P3）
- ❌ `semantic_correctness` — 属 Evidence Trust Gate
- ❌ `freshness_score` — 属 Freshness（P2）
- ❌ `importance_ranking` — 属个性化，非可靠性

**P1 只回答一个问题**：系统声称已经记住了一件事，这个声称有没有证据？
**不回答**：系统记住的是不是正确？（后者属 Recall Trust Gate）

**正确路线**（G 2026-07-26）：
```
Write Durability → Evidence Receipt → Recall Validity → Freshness → Trust Runtime
```
先证明「存进去是真的」，再谈其他。这很像金融基础设施建设：**先做清算系统，再做交易策略。**

in。** 当前 Trust Runtime 实际状态：

```
Trust Runtime      L1 Declared ✅  L2 Documented ✅  L3 Implemented Partial  L4 Runtime ❌  L5 Production ❌
Evidence Manifest  L2 Documented（Design PASS）
```

- ❌ 不得写：「Vera 已具备 Trust Runtime」
- ✅ 应当写：「Vera 正在构建 Trust Runtime Architecture，目前 Evidence Manifest 已完成设计验证，并持续推进 Runtime 验证」

后者稳的原因：每个分句都能指向具体证据级别，经得起追问「凭什么」。前者一旦被追问 runtime 证据即失守。

**Vera 治理体系三层**（本窗口成型）：

| Layer | 回答 | 载体 |
|---|---|---|
| 1 · Principles | 什么不能混淆？ | 六公理（4a/4b 分层） |
| 2 · Maturity Model | 现在到底做到哪一级？ | Capability Maturity Chain L0-L5 |
| 3 · Implementation Roadmap | 下一步怎么补证据？ | P1/P2/P3 |

`Principle → Maturity Assessment → Implementation Evidence` —— 比单纯架构图强的地方在于它自带证伪路径。

---

## Trust Runtime 当前状态（G 定版 2026-07-26）

```
Trust Runtime Architecture
  Principles:          Defined
  Governance:          Documented
  Evidence Layer:      Design PASS
  Memory Reliability:  Problem Defined · Design Pending
  Freshness:           Design Pending
  Recall Trust Gate:   Prerequisite Pending
  Runtime:             NOT PROVEN
  Production:          NOT CLAIMED
```

按线分列而非给整体打分 —— 「组件分别定级」判据的直接应用。

### 元原则：验证机制必须自证（Trust Runtime 第一性原则 · G 签署 2026-07-26）

> **任何用于证明能力存在的机制，自身也必须经过同等级证据验证。**

这不是一条附加规则，而是**整个治理体系的递归约束**。没有它会出现「信任套娃」：

```
AI 输出可信
   ↓ 因为
Trust Gate 说可信
   ↓ Trust Gate 为什么可信？
Audit Log 证明
   ↓ Audit Log 为什么可信？
没有证据
```

：Receipt（自身可读回）/ Monitor（进程活着且过滤器匹配）/ Audit log（未丢、已 flush）/ Trust Gate（不可绕过）/ Evaluation（数据未污染）/ Governance 文档（标注自身级别）/ Smoke（覆盖生产路径而非自喂输入）。

自检句式：**「如果这个验证机制现在坏了，我会知道吗？」** 答不出发现路径 = 该机制处于 UNKNOWN。

这条解释了 Rule B 为何必须存在，以及自指测试为何是**第一性**原则而非 Finding 的补丁：它是从 Evidence Governance（证据需可信）到 Trust Runtime（证明证据可信的机制也需可信）的分界。

---

## 对外材料表述规则（AWS 申请 / 比赛 / BP / 路演）

所有对外能力表述必须先过 Capability Maturity Chain。

- ❌ 不得写：「Vera 已具备 Trust Runtime」
- ✅ 应当写：「Vera 正在构建 Trust Runtime Architecture，目前 Evidence Manifest 已完成设计验证，并持续推进 Runtime 验证」

后者稳的原因：每个分句都能指向具体证据级别，经得起追问「凭什么」。前者一旦被追问 runtime 证据即失守。

**Vera 治理体系三层**：

| Layer | 回答 | 载体 |
|---|---|---|
| 1 · Principles | 什么不能混淆？ | 六公理（4a/4b 分层）+ Rule A/B |
| 2 · Maturity Model | 现在到底做到哪一级？ | Capability Maturity Chain L0-L5 |
| 3 · Implementation Roadmap | 下一步怎么补证据？ | P1/P2/P3 |

`Principle → Maturity Assessment → Implementation Evidence` —— 比架构图强的地方在于自带证伪路径。

---

## 下窗口：Trust Runtime Implementation Design v0.1

**不开大改造。** 只做三件事，按序：

| P | 内容 | 目标 | 轴 |
|---|---|---|---|
| **P1** | Memory Reliability Evidence v0 | 建立第一条可验证闭环（三部件见下） | Durability |
| **P2** | Freshness Producer Contract | 先回答「谁负责产生 freshness」，**不是先加 schema** | Validity |
| **P3** | Recall Trust Gate | `Recall → Trust Gate → LLM Context`，让记忆召回也过门 | Provenance × Durability |

P3 是新增项（G 2026-07-26）：目前 memory recall 直接进 LLM context，没有经过 Trust Gate。结合 Bad Memory（arXiv 2607.14611）—— 记忆是持久攻击面，召回路径应与 evidence 路径同等对待。

**P3 前置条件**（C 审核 2026-07-26）：当前仓库内**尚未定位明确的生产 memory-recall 注入函数** —— 不知道召回在哪个函数发生、用什么格式注入、进哪条 LLM 请求路径。C 指出最小可行方式是「召回边界上的元数据过滤」（检查 receipt status / memory_id / source_scope / trust_label，缺失默认 unknown 不得进可信上下文）。但这要求：(1) 知道 `Recall Result → LLM Context` 的代码路径，(2) 该路径是所有召回的必经点（不可绕过），(3) 能在该点拿到记忆元数据。

**P3 必须先执行「定位 Recall 边界」，否则只能输出设计而无法实现。** 应拆为 P3-prerequisite（定位注入点）+ P3-design（元数据过滤逻辑）。详见 [[project_recall_trust_gate_prerequisite]]。

---

## C 审核意见（2026-07-26 · APPROVE）

**Q1 · F-01 缺省落 REAL 是否认同是设计缺陷？**  
认同。`freshness=None` → `REAL` 属 fail-open。更合理缺省不是 `FALLBACK`，而是 `UNKNOWN/UNVERIFIED`：时效敏感用途应阻断，非时效用途才允许受限降级。

另指出**根本问题**：`ProviderClass` 混合了「来源真实性」与「数据新鲜度」两个维度 —— 真实 provider 同样可能返回过期数据。这两个维度后续应分离。（D23 未识别此点，记入遗留）

**Q2 · P1 Receipt 哪个字段最易被省略？**  
`trust_label`。`timestamp/status/session_id` 易记录，`memory_id` 是存储返回值，`source_scope` 能从输入路径提取；`trust_label` 需要来源分类、继承规则、默认策略，最容易实现成空值或固定 `trusted`。

第二危险是省掉 `memory_id`：缺它则 Receipt 只是"本地尝试日志"而非存储确认。**验收增补**：`status=success` 必须同时具备 `memory_id`，并区分 `write_acknowledged` 与 `verified_retrievable`。

**Q3 · P3 Recall Trust Gate 最小可行方式？**  
元数据过滤，不是文件锁或 Hook。建议链路：

```
Recall Result → Metadata Trust Filter → ALLOW/CONSTRAIN/DENY → LLM Context
```

最低检查 `receipt status / memory_id / source_scope / trust_label`；缺失默认 `unknown`，不得进可信上下文。文件锁只解决并发一致性，Hook 只触发流程，均非不可绕过的召回执行点。

**未完成项（P3 前置）**：当前仓库内尚未定位明确的生产 memory-recall 注入函数，P3 开窗前需先确认真正的 `Recall → Context` 边界。

---

## 未覆盖范围（诚实边界）

- **Trust Gate 全路径审计：PARTIAL，未穷尽。** 完整审计需跑真实 provider 调用，超出本窗口"仅治理原则输入"授权。
- Finding-01 的失效路径由代码静态阅读确认；**未在生产环境实跑验证** `freshness` 缺失时的实际 ProviderClass 取值。
- `project_evidence_manifest_v1` 记录的 Integration: BLOCKED 状态在 smoke 层补齐后未同步更新，存在被误读为整链绿灯的风险。

---

## D23 冻结口径（G+C 签署 2026-07-26）

```
D23 CLOSED
  Achieved:
    - Trust Runtime principles defined
    - Governance boundary defined
    - Evidence Layer design validated
    - Self-verification as first principle
  Not achieved（不属于本窗口）:
    - Runtime capability
    - Memory reliability proof
    - Recall trust
    - Freshness validation
    - Production readiness
  Next Window:
    P1 Memory Reliability Evidence v0
    Single Objective: Prove Write Durability before claiming Memory Trust
```

现在不是缺功能，而是在建立未来 Vera 被机构客户相信的**审计底座**。

---

## 关联

- `docs/findings/BF-JQ-01-phantom-provider.md` — 同族：provider 幽灵 vs 本次字段幽灵
- Memory: `feedback_declared_vs_effective_capability` / `feedback_async_audit_trail_flush` / `reference_financial_agent_landscape_20260726`
- Memory: `project_evidence_manifest_v1`（F2 provider_policy.refresh_frequency 已提出未实现）
