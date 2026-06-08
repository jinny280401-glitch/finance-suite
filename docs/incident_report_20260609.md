# Finance Suite 运维恢复与安全加固报告（2026-06-09）

## 一、事件背景

本轮事件最初表现为：

- `touziagent.com` 出现访问异常
- 部分页面反馈“抓取失败”
- SSH 无法进入后端机器
- 本地排查过程中出现 Clash fake-IP、SSH KEX 失败等干扰信号

初期怀疑包括：

- DNS / Clash 路由问题
- 云防火墙规则问题
- SSH 配置问题
- GitHub 抓取链路问题

最终经过多轮证据收集与假设推翻，确认根因并完成恢复。

## 二、最终确认的系统拓扑

生产链路：

```text
用户
  ↓
touziagent.com
  ↓
119.28.156.125
(Tencent Cloud / nginx)
  ↓
8.138.2.55
(OpenClaw Backend)
```

运维链路：

```text
Mac
  ↓ SSH
8.138.2.55
  ↓ SSH Jump
119.28.156.125
```

## 三、故障排查过程

### Phase 1：错误假设

最初怀疑：

1. Clash fake-IP 导致 DNS 异常
2. GitHub raw.githubusercontent 抓取失败
3. SSH Key 配置错误
4. SSH KEX 配置错误

随后逐项验证：

- `raw.githubusercontent.com` 正常
- GitHub API 正常
- HTTP 服务部分正常
- DNS fake-IP 属于 Clash 正常行为

上述假设全部被排除。

### Phase 2：收敛到后端节点

确认 `8.138.2.55` 出现：

- SSH 不可用
- 业务服务不可用
- nginx 上游异常

影响链路：

```text
8.138.2.55 不可用
    ↓
119.28.156.125 反代失败
    ↓
touziagent.com 异常
```

### Phase 3：推翻“云防火墙未放行”假设

检查腾讯云轻量服务器规则后发现已放行：

- TCP 22
- TCP 80
- TCP 443
- ICMP

因此，故障不是云防火墙导致 SSH 不通，排查方向转向系统内部。

### Phase 4：VNC 救援

通过腾讯云控制台远程连接（VNC）进入实例，确认：

- `sshd` 服务异常
- 业务链路异常
- 服务恢复后重新开放 SSH

## 四、SSH 恢复结果

`8.138.2.55` 当前可通过 `admin@8.138.2.55` 正常登录。

验证通过：

```text
SSH_OK
```

`119.28.156.125` 当前可通过跳板进入：

```text
admin@8.138.2.55
    ↓
ubuntu@119.28.156.125
```

验证通过：

```text
VIA_JUMPBOX_OK
```

## 五、安全加固结果

### sshd 配置

已生效：

```text
MaxAuthTries 3
MaxSessions 10
MaxStartups 3:50:10
PermitRootLogin no
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
```

验证结果：root 登录已被拒绝，符合预期。

### Fail2Ban

已安装并启用。

验证：

```text
fail2ban-client status sshd
```

结果：

```text
Currently banned: 0
Total banned: 2
```

说明：

- 已成功识别并封禁过攻击源
- 当前无残留封禁

### authorized_keys

已补充：

- OpenClaw 跳板机 Key
- Mac 本机 Key

Mac 已成功直接 SSH 登录。

验证：

```text
MAC_SSH_OK
```

## 六、防火墙状态

### 当前策略

22 端口当前以 `0.0.0.0/0` 作为临时中间态保留。

原因：当前公网出口 `203.10.99.11` 虽然连续三次测试稳定：

```text
203.10.99.11
203.10.99.11
203.10.99.11
```

但尚未确认属于长期固定出口，因此暂不收窄。

### 后续建议

当出口稳定确认后：

```text
22
↓
203.10.99.11/32
```

进一步收窄。

### 8000 端口

待后续维护窗口执行：

```text
8000
↓
仅允许 119.28.156.125/32
```

## 七、生产状态确认

网站：

```text
https://touziagent.com
```

状态：正常。

API：

```text
/api/health
```

返回：

```json
{"status":"ok"}
```

登录接口返回：

```text
401 用户名或密码错误
```

符合未登录预期。

## 八、项目管理状态

已完成：

- SSH 恢复
- VNC 救援
- Fail2Ban 部署
- `sshd` 加固
- Mac 公钥接入
- 跳板链路恢复
- 生产站点恢复

未完成：

```text
Task #10: 8000 收窄到 119.28.156.125/32
状态: Pending
```

```text
Task #5: P0a push ahead 28 commits
状态: Pending
说明: 发现此前误在 feature 分支执行检查。
当前确认: main ahead 28, behind 0, 尚未 push。
```

Tailscale 状态：Proposal。

目的：消除公网出口 IP 变化这一长期不确定因素。

## 九、最终结论

本次事件根因并非 DNS、Clash、GitHub 抓取链路或 SSH Key 本身，而是后端节点 `8.138.2.55` 出现服务失效，导致：

```text
8.138.2.55
    ↓
119.28.156.125 反代失败
    ↓
touziagent.com 异常
```

目前：

- 生产站点恢复
- API 恢复
- SSH 恢复
- Jump Host 恢复
- `sshd` 已加固
- Fail2Ban 已启用

系统已恢复到可运维、可发布、可继续开发状态。

当前建议：不继续修改生产系统，保留稳定状态，下一阶段处理：

1. 8000 收窄
2. P0a Push Review
3. Tailscale 长期方案

## 十、收尾审核备注

本报告归档时，生产系统不再继续变更；后续只处理代码仓库归档、GitHub push 和安全 follow-up。

仍需保留的未竣工项：

- 防火墙 Task #10：`8.138.2.55:8000` 收窄到仅允许 `119.28.156.125/32`。
- 出口 IP 稳定性复核：当前不应急于把 SSH 22 收窄到单一公网出口。
- Tailscale 长期方案：仍处于 Proposal。

本次 push review 发现的本地验证风险：

- `smoke_research_runtime_gateway.py` 在本机返回 `qc_passed=false`，同时本机缺少 `tushare`。
- `smoke_trust_gate_runtime_integration_v1.py` 存在 `_run_trust_gate()` 调用签名不匹配问题。

这些风险不影响本次运维恢复事实归档，但不能把当前 `finance-suite main` 描述为 smoke 全绿状态。
