# Execution Package Consistency Check

> 目的：防止 PPT、Demo、ASCII 指令、Image2 Prompt、Vera vs 豆包 表之间出现定位漂移。
> 当前唯一出图结构源头（SSOT）：`ASCII架构图指令-v2.md`。

---

## 1. 固定定位

所有材料必须统一使用：

```text
Vera = 面向证券行业的 Agent 员工平台
```

差异层统一使用：

```text
豆包 解决 Agent Capability Problem；Vera 解决 Agent Trust Problem。
```

禁止作为主定位使用：

```text
Trust Architecture
证券行业第一个 豆包
```

可作为解释使用：

```text
正在构建证券行业的 豆包
受到 豆包 这类 Agent 员工体系启发
```

---

## 2. 5 张图固定清单

所有 ASCII、Image2、PPT 图页必须是这 5 张：

1. Vera Overall Architecture
2. Trust Gate Contract Flow
3. Research Runtime Workflow
4. Skill Ecosystem
5. Vera vs 豆包

禁止替换：

```text
图5 不得换成 JIEZHU Memory Loop
不得新增第 6 张主架构图
不得回退到三层产品架构做图1
```

---

## 3. 文件责任边界

| 文件 | 责任 |
|------|------|
| `Vera-GC执行包-20260618.md` | 内容包、口径、任务分工，不作为出图定义源头 |
| `ASCII架构图指令-v2.md` | 唯一出图结构源头（SSOT） |
| `ASCII架构图指令.md` | 入口文件，只跳转到 v2 |
| `Image2液态玻璃架构图指令.md` | 从 v2 派生的视觉生成 prompt |
| `AI大赛成果-Vera-完整版.md` | 参赛正文 |
| `Vera-路演Demo逐字稿.md` | 口播和 Demo 脚本 |

---

## 4. 材料检查项

### PPT

- [ ] P1 标题使用“面向证券行业的 Agent 员工平台”
- [ ] P3 放 Vera vs 豆包
- [ ] 图 1-5 名称与 v2 完全一致
- [ ] 不把 Trust Architecture 放成第一层身份
- [ ] 不出现“证券行业第一个 豆包”

### Demo

- [ ] 开场先讲身份，再讲 Capability vs Trust
- [ ] Demo 2 必须出现 Trust Gate 拒答
- [ ] Demo 2 必须出现 source / time / citation / allowed_use
- [ ] Demo 3 JIEZHU 只放真实录屏或附录，不占主图位

### ASCII 指令

- [ ] 使用 `ASCII架构图指令-v2.md`
- [ ] 图5 是 Vera vs 豆包
- [ ] 图1 是 Overall Architecture
- [ ] 每张图都体现 Agent Trust Problem

### Image2 Prompt

- [ ] 从 v2 图结构派生，不另定图内容
- [ ] 统一 Liquid Glass / Dark Mode / Apple WWDC 风格
- [ ] 图5 是 Vera vs 豆包
- [ ] Trust Gate 和 Allowed Use 高亮

### Vera vs 豆包 表

- [ ] 豆包 链路：Task -> Plan -> Code -> Execute -> Feedback
- [ ] Vera 链路：Intent -> Trust Gate -> Evidence -> Research Runtime -> Allowed Use -> Output
- [ ] 不比较 Tool 数量
- [ ] 比较金融可信度、合规、追溯

---

## 5. 最终裁决

```text
Q1 = B：用 v2 指令作为唯一源头
Q2 = C：C 的图作为参考，G 按最终指令重画展示版
Q3 = A：增加 Execution Package Consistency Check
```

