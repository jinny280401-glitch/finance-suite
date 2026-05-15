# Finance Suite 账号管理参考（脱敏安全版）

> 安全说明：
> 历史版本曾包含明文测试/生产密码。
> 当前 runbook 完全脱敏，密码仅保存在生产服务器数据库 hash 与远端 handoff 文件中。
> 所有示例仅为占位，不可用于真实登录。

## 数据库位置

- 服务器：`119.28.156.125`（`ubuntu` 用户）
- 路径：`/home/ubuntu/finance-suite-web/finance_suite.db`
- 表结构：`users` 表包含 `id`, `username`, `email`, `hashed_password`, `tier`, `created_at`, `is_active`

## 密码管理位置

| 位置 | 用途 |
|---|---|
| `finance_suite.db`（生产 DB，bcrypt hash） | 验证登录的唯一权威源 |
| `/home/ubuntu/.finance-suite/rotated_passwords_<TIMESTAMP>.json`（远端，`0600`） | 轮换后 handoff 文件，明文仅在轮换窗口期临时保留 |
| 运维内部文档 / 1Password 等保密渠道 | 长期归档 |

任何 memory / git / 公开文档都禁止写入明文密码，统一使用 `<PASSWORD>` / `<NEW_PASSWORD>` / `<rotated YYYY-MM-DD>` / `请通过运维安全渠道获取`。

## 当前账号列表（截至 2026-05-16）

### VIP 账号（15 个）

| 账号 | 邮箱 | 密码状态 | 权限 | 备注 |
|---|---|---|---|---|
| hfzq | hfzq@touziagent.com | `<rotated 2026-05-15>` | vip | 华福证券 |
| linzuxi | linzuxi@touziagent.com | `<rotated 2026-05-15>` | vip | 内测用户 |
| danny | danny@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| ivan | ivan@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| shengwei | shengwei@touziagent.com | `<rotated 2026-05-15>` | vip | 内测用户 |
| demo | demo@touziagent.com | `<rotated 2026-05-15>` | vip | 演示账号 |
| zhuanz | zhuanz@touziagent.com | `<rotated 2026-05-15>` | vip | 管理员 |
| vanilla | vanilla@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| nanjian | nanjian@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| fengzhijie | fengzhijie@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| lianghailin | lianghailin@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 待轮换 |
| yudi | yudi@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 原密码未知，建议纳入轮换 |
| yuwen388 | yuwen388@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 原密码未知，建议纳入轮换 |
| jiliwong | jiliwong@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 原密码未知，建议纳入轮换 |
| huangsi | huangsi@touziagent.com | 待轮换 / 请通过运维安全渠道获取 | vip | 原密码未知，建议纳入轮换 |

### Admin 账号（1 个）

| 账号 | 邮箱 | 密码状态 | 权限 | 备注 |
|---|---|---|---|---|
| admin | admin@financesuite.com | 待轮换 / 请通过运维安全渠道获取 | admin | 系统管理员，最高权限优先轮换 |

### reset / add / bcrypt 示例（脱敏）

```bash
# 添加账号
python3 server_scripts/manage_users.py add <USERNAME> <PASSWORD> <TIER>

# 更新或新增账号
python3 server_scripts/manage_users.py upsert <USERNAME> <PASSWORD> <TIER>

# 重置密码
python3 server_scripts/manage_users.py reset <USERNAME> <NEW_PASSWORD>
```

### 登录测试示例（脱敏）

```bash
curl -X POST https://www.touziagent.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<USERNAME>","password":"<PASSWORD>"}'
```

### SECRET_KEY 示例（脱敏）

```python
app.secret_key = os.environ.get("SECRET_KEY", "<SECRET_KEY>")
```

## 备注

- 所有密码均为占位或状态说明。
- grep 不应命中任何历史明文密码。
- 内部团队使用此文件仅作账号管理参考 / 文档示例，不可用于生产登录。
- 真实密码仅存在生产数据库 hash、远端 handoff 文件（`0600` 权限）和运维安全渠道。
