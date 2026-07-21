# Truthfulness & Reliability Probe Candidate Pack v0

> **Status:** DELIVERED / NOT APPROVED / NOT AUTHORIZED
> **Type:** Candidate Pack (与 Rule Candidate Pack #26 同型资产, 非 Gate / Contract / L0 变更)
> **Track:** Strategic Track (对话框 2), 不消费 #25/#26/#27, 不启动 Session 2
> **Created:** 2026-06-13
> **Owner:** CC (per orchestrator 选"中")
> **Boundary:** 这是 asset 不是 execution。任一 probe 要落地仍需另开 Window 显式授权。

---

## 0. 一句话

```
Finance Suite 下一阶段最缺的不是功能, 是「系统知道自己真的会什么」(真实性)
和「真的会的东西持续会」(稳定性)。
本 Pack 把散落在 memory 的 6 个病灶聚成 3 个类别 + 4 个探针候选, 排优先级。
它是候选清单, 不是已批准的探针。
```

---

## 1. 三个病灶类别 (per orchestrator 三分法)

### Category A — Truthfulness Failure (真实性失败)

```
定义: 系统从来不会, 却表现得像会。
特征: 真实能力 = 0, 表现能力 > 0
病灶 (memory 实证):
  - stub 冒充 capability   → Live Upstream Stub (/api/intel/research 返回 "not connected")
  - fallback 冒充 real     → Backend Intel Drift (intel_api.py stale, 2 条 404)
  - health 冒充 business   → Operational Readiness Layers 4-6
暴露速度: 快 (用户一试就知道, 完全不会)
```

### Category B — Reliability Failure (稳定性失败)

```
定义: 系统真的会, 但经常坏。
特征: 真实能力 > 0, 稳定能力不足
病灶 (memory 实证):
  - launchd 睡眠         → Task #21 Mac sleep/hibernate, 09:24 漏跑 13:49 补
  - deploy 偶发失败       → Sidebar P0 / deploy.sh 6/1 未同步
  - warmup race          → Morning Brief warmup/smoke 时序
可监控性: 高 (成功率 / 失败率 / MTTR 都能测)
```

### Category C — Authenticity Drift (真实性漂移) ⭐ 最危险

```
定义: 系统真的会, 但无法证明"当前这一次"走的是哪条路径。
特征: 真实能力 > 0, 但路径不可证 (不是不会, 是不知道自己现在是不是在会)
病灶 (memory 实证):
  - 90% live / 10% fallback
  - 95% fresh / 5% stale cache   → Morning Brief 36 天 cache 混在 live 里
  - 大部分 deployed / 少部分 drift
为什么最危险:
  A 类一试就穿, B 类能测成功率,
  C 类唯独要看「路径分布」, 而没人看路径分布 ——
  因为每次单看都是「真的」:
    昨天是真的 → 前天也是真的 → 默认今天也是真的
    → 今天偷偷走 fallback, 没人知道
```

---

## 2. 探针候选 (4 个, 按优先级)

> **格式说明 (CC 增补):** 每个 probe 多一行 **Probe 自身诚实性**。
> 因为探针若只返回 `{"probe": "ok"}` 而不暴露它实际探到了什么,
> 探针本身就成了新的 Category A 自欺源。探针必须先对自己诚实, 才能验别人。
> 这是「真实性」主题的递归应用 —— 也是 Serenity 的 Evidence Traceable 搬到自检层。

### Tier 1 (P0)

#### Probe 1 — Source Authenticity Marker

```
目标:    我拿到的数据到底来自 live / cache / fallback / stub
解决:    Category A (cache 冒充 live, fallback 冒充 real)
形态:    每个 API response 强制带
           data_source ∈ {live, cache, fallback, stub}
           freshness_age (秒/天)
可证伪断言: "这条 response 是 live 且 age < 阈值"
失败长什么样: data_source=cache 但调用方以为是 live → marker 把它点亮
Probe 自身诚实性:
           marker 不能由返回方"自报", 要由数据获取层在源头打戳,
           否则 fallback 路径会给自己贴 live 标签 (自欺套娃)
```

#### Probe 2 — Capability Honesty Test

```
目标:    系统声称会 X, 实际是否真的走到 X
解决:    Category A (stub 冒充 capability)
形态:    对每个声称的 capability 跑端到端,
           断言它走的是 real path 不是 fallback/stub
可证伪断言: "capability X 的 happy path 真实可达, 不是预留位"
失败长什么样: research 声称能调研, 实际命中 stub "not connected" → 断言 FAIL
Probe 自身诚实性:
           测试必须断言"走到了哪一层", 不能只断言"返回非空"
           (stub 也返回非空) —— 对标 Vera Router 的 layer_quality
```

### Tier 2 (P0.5) ⭐ 新增类别

#### Probe 4 — Authenticity Drift Probe (Category C 专属)

```
目标:    同一 capability 最近 N 次请求, 分别走了什么路径
解决:    Category C (偶发 fallback / 偶发 stale / 偶发 drift)
形态:    路径分布统计, 例:
           research:  live 93 / fallback 7 / stub 0
           market:    fresh 85 / cache 15
可证伪断言: "最近 N 次, real path 占比 ≥ 阈值 且 无 silent fallback"
失败长什么样: live 占比从 99% 掉到 80% 而无人告警 → drift 曲线点亮
为什么 P0.5 而非 P1:
           同时具备真实性问题 + 稳定性问题, 且最难被发现
           A 快暴露 / B 可监控 / C 会骗过人
Probe 自身诚实性:
           依赖 Probe 1 的 marker 作为数据源 (无 marker 则无分布),
           所以 Probe 1 是 Probe 4 的前置 —— 这条依赖必须显式
```

### Tier 3 (P1)

#### Probe 3 — Deployment Contract Probe

```
目标:    main HEAD vs production HEAD
解决:    demonstrated ≠ deployed (Deployment Contract Drift)
形态:    生产实际跑的 commit hash vs main HEAD, 输出 gap
可证伪断言: "production HEAD == main HEAD (或显式记录 N commits behind)"
失败长什么样: 04d5f7d 在 main 但生产跑的是更早的 → gap = N commits
Probe 自身诚实性:
           要读"生产实际加载的代码"而非"生产目录的代码",
           uvicorn 不重启则磁盘新 ≠ 运行新 (对标 Backend Intel Drift 真因)
```

---

## 3. 优先级总表 (per orchestrator 微调)

| Priority | Probe | Category | 杀死的自欺 |
|---|---|---|---|
| **P0** | Probe 1 Source Authenticity Marker | A | cache/fallback 冒充 live/real |
| **P0** | Probe 2 Capability Honesty Test | A | stub 冒充 capability |
| **P0.5** | Probe 4 Authenticity Drift Probe ⭐ | **C** | 偶发 fallback/stale/drift (最阴险) |
| **P1** | Probe 3 Deployment Contract Probe | B/A | demonstrated ≠ deployed |

```
P0    Truthfulness        (系统是不是在骗"我会")
P0.5  Authenticity Drift  (系统是不是在骗"我这次也会")  ← 同时是真实性+稳定性
P1    Reliability         (系统会的东西是不是持续会)
```

依赖关系: **Probe 1 是 Probe 4 的前置** (无 source marker 则无路径分布)。

---

## 4. 与现有方法论的同构 (为什么这个 Pack 不是空中楼阁)

```
方法论层 (已锁) ──────────────── 基础设施层 (本 Pack)
不许 narrative 冒充 verdict   →   不许 fallback 冒充 real      (Probe 1/2)
Method DEMONSTRATED≠PROVEN    →   Feature Demonstrated≠Reliable (Probe 3/4)
Evidence Traceable           →   Probe 自身诚实性 (源头打戳)
Verified Loop 需跨时点/跨实体  →   Drift 需看 N 次路径分布        (Probe 4)
```

北方华创 Session 2 是真实性纪律在**方法论层**的成功样本 (PARTIAL_PLUS 没偷升 VERIFIED)。
本 Pack 是把同一套免疫系统移植到**基础设施层**。

---

## 5. 边界声明 (与 Completion ⊥ Authorization 一致)

```
本 Pack = Asset (Complete)
        ≠ Authority (Granted)

允许 (已做):
  ✅ 病灶归类 / 探针候选 / 优先级排序

禁止 (未授权):
  ❌ 实现任何 probe
  ❌ 改任何 API response 格式 (Probe 1 要碰)
  ❌ 改 deploy 流程 (Probe 3 要碰)
  ❌ 升 Candidate → Approved Probe
  ❌ 开新 Gate / Contract / L0

任一 probe 落地 = 另开 Window 显式授权
Strategic Track 讨论 Complete ≠ 授权改基础设施
```

---

## 6. Changelog

- 2026-06-13: v0 产出。orchestrator 选"中"。三分法 (A Truthfulness / B Reliability / C Authenticity Drift) + 4 probe + P0/P0.5/P1。CC 增补「Probe 自身诚实性」一行 (防探针自欺) + Probe1→Probe4 依赖。DELIVERED / NOT APPROVED / NOT AUTHORIZED。
