# Warm Up 检查指令（给 C 执行）

> **给 C**：执行以下 7 步检查，输出"可以关"或"继续跑"的明确结论
> **来源**：妈妈 6/18 下午问"这个 Warm Up 从 12 号一直跑到现在的意义和效果是什么？要不要检查是不是已经可以关闭 Warm Up？"
> **优先级**：高（妈妈最初关心的真问题）
> **截止**：6/19 上午

---

## 🎯 任务定义（不要再误解）

**Warm Up** = 生产环境的预热进程，从 6 月 12 日启动至今一直在跑。

**这次检查的目标**：判断这个进程**是否还有保留价值**，还是已经可以安全关闭。

**注意**：
- 这不是 Sandbox 任务
- 这不是 Demo Validation 任务
- 这不是 Vera 测试任务
- 这只是"一个跑了 6 天的预热进程是否还在有效工作"的检查

---

## 📋 C 必须执行的 7 步检查

### Step 1：Warm Up 当前 PID
```bash
# 找到 Warm Up 进程的 PID
ps aux | grep -i warm | grep -v grep
# 或者
ps -ef | grep warm
```

**输出**：`Warm Up PID = XXXX`

### Step 2：CPU 占用
```bash
# 查看进程 CPU 占用
top -p <PID>
# 或者
ps -p <PID> -o %cpu,%mem,etime,cmd
```

**输出**：`CPU 占用 = X%`

### Step 3：内存占用
```bash
# 查看内存详情
ps -p <PID> -o vsz,rss,etime,cmd
```

**输出**：`内存占用 = X MB（虚拟 X MB）`

### Step 4：最近一次有效工作时间
```bash
# 查看进程最后活跃时间
ps -p <PID> -o etime,start,etime
# 或者看日志
ls -lt /var/log/warmup.log 2>/dev/null
tail -100 /var/log/warmup.log 2>/dev/null | head -20
```

**输出**：
- 进程已运行：`X 天 Y 小时`
- 日志最后写入：`X 小时前` 或 `X 分钟前`

### Step 5：是否还有新缓存写入
```bash
# 检查 Warm Up 相关的缓存目录最近修改时间
ls -lt /var/cache/warmup/ 2>/dev/null
ls -lt /tmp/warmup/ 2>/dev/null
find / -name "warmup*" -mmin -60 2>/dev/null | head -5
```

**输出**：
- 缓存目录最近写入：`X 分钟前` 或 `X 小时前` 或 `已 X 天未写入`

### Step 6：当前生产链路是否仍依赖 Warm Up
```bash
# 1. 找 Warm Up 产出的文件被谁引用
grep -r "warmup" /etc/ 2>/dev/null | head -10
# 2. 找生产配置里有没有引用 warmup
find /etc -name "*.conf" 2>/dev/null | xargs grep -l "warmup" 2>/dev/null
# 3. 找代码里有没有引用 warmup 文件
find /opt -name "*.py" -o -name "*.js" 2>/dev/null | xargs grep -l "warmup" 2>/dev/null | head -5
```

**输出**：
- `有 N 个文件引用 warmup`（列出路径）
- 或 `无任何生产链路引用 warmup`

### Step 7：如果停止 Warm Up，会影响什么
```bash
# 1. 找 Warm Up 进程的所有子进程
pstree -p <PID>
# 2. 找 Warm Up 监听的端口
lsof -p <PID> 2>/dev/null | grep LISTEN
# 3. 找 Warm Up 创建的 socket/文件描述符
lsof -p <PID> 2>/dev/null | head -20
```

**输出**：
- 子进程数：`X`
- 监听端口：`X`（如 0 端口表示纯本地）
- 打开文件数：`X`

---

## 🎯 最终结论（必须给出二选一）

**根据以上 7 步检查结果，C 必须给出明确结论**：

### 选项 A：SAFE TO STOP（可以安全关闭）
**判定条件**（满足任意 3 条以上）：
- [ ] CPU 占用 < 1%
- [ ] 内存占用 < 100MB
- [ ] 日志/缓存 X 小时未写入
- [ ] 无生产链路引用
- [ ] 无子进程、无监听端口

**关闭命令**（仅在 SAFE TO STOP 时执行）：
```bash
kill -TERM <PID>
# 等待 30 秒观察
sleep 30
# 确认无影响
ps -p <PID> 2>/dev/null
```

**如果妈妈确认关闭，给最终报告**：
```
Warm Up PID: XXXX
最终状态: SAFE TO STOP ✅
执行动作: kill -TERM XXXX
影响评估: 无任何生产链路受影响
建议: 关闭后继续观察 1 小时
```

### 选项 B：KEEP（继续跑）
**判定条件**（满足任意 2 条以上）：
- [ ] CPU 占用 > 5%
- [ ] 内存占用 > 500MB
- [ ] 日志/缓存持续写入
- [ ] 有生产链路引用
- [ ] 有子进程在跑

**给最终报告**：
```
Warm Up PID: XXXX
最终状态: KEEP ⚠️
继续理由: [具体引用点]
优化建议: [如调整启动频率、清理缓存等]
```

---

## 🚨 C 执行红线

- ❌ 不要问"妈妈 Warm Up 是什么"（已经定义清楚：生产环境预热进程）
- ❌ 不要扩展到其他任务（Trust Gate / 四层降级 / JIEZHU 等是其他任务）
- ❌ 不要脑补"也许 Vera 在用"（除非 Step 6 真的找到引用证据）
- ❌ 不要直接 kill 进程（先给结论，妈妈确认后再 kill）
- ❌ 不要写超过 200 字的报告（妈妈只要二选一）

---

## ✅ 报告模板（直接给妈妈）

```markdown
# Warm Up 检查报告

**执行人**：C
**执行时间**：2026-06-19 XX:XX
**检查目标**：判断 Warm Up 进程（6/12 启动）是否还有保留价值

## 7 步检查结果

| Step | 项目 | 结果 |
|------|------|------|
| 1 | PID | XXXX |
| 2 | CPU 占用 | X% |
| 3 | 内存占用 | X MB |
| 4 | 最后活跃 | X 小时前 |
| 5 | 缓存写入 | X 分钟前 |
| 6 | 生产依赖 | 有 N 个引用 / 无引用 |
| 7 | 子进程/端口 | X 子进程 / X 端口 |

## 最终结论

**状态**：✅ SAFE TO STOP  /  ⚠️ KEEP

**理由**：[一句话]

**建议动作**：
- SAFE TO STOP：执行 `kill -TERM <PID>`，观察 1 小时
- KEEP：[具体优化建议]
```

---

## 📁 报告输出位置

```
/Users/Zhuanz/finance-suite/roadshow-2026-06/reports/warmup-check-20260619.md
```

写完报告同步给妈妈，等妈妈决定是否执行 kill。
