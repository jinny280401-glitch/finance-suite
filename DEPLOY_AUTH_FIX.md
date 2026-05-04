# Finance Suite 账号系统修复 - 部署指南

## 问题说明
- 前端硬编码账号密码，后端有数据库，两边不同步
- 内测账号密码失效，无法登录
- 需要添加华福证券账号

## 解决方案
将前端硬编码改为调用后端 API，统一使用数据库管理账号

---

## 服务器端部署步骤

### 1. 上传文件到服务器

将以下文件上传到服务器 `/home/ubuntu/finance-suite-web/`：

```bash
# 在本地执行
cd /Users/Zhuanz/finance-suite
scp server_scripts/manage_users.py ubuntu@touziagent.com:/home/ubuntu/finance-suite-web/server_scripts/
scp server_scripts/import_accounts.sh ubuntu@touziagent.com:/home/ubuntu/finance-suite-web/server_scripts/
scp server_scripts/auth.py ubuntu@touziagent.com:/home/ubuntu/finance-suite-web/app/
```

### 2. 登录服务器

```bash
ssh ubuntu@touziagent.com
cd /home/ubuntu/finance-suite-web
```

### 3. 检查现有数据库

```bash
# 查看数据库是否存在
ls -lh finance_suite.db

# 如果存在，查看现有用户
sqlite3 finance_suite.db "SELECT username, tier FROM users;"
```

### 4. 初始化/导入账号

```bash
# 给脚本添加执行权限
chmod +x server_scripts/import_accounts.sh

# 执行导入（如果用户已存在会跳过）
bash server_scripts/import_accounts.sh
```

### 5. 添加华福证券账号

```bash
# 手动添加华福证券账号（替换为实际用户名和密码）
python3 server_scripts/manage_users.py add huafu01 实际密码 vip
python3 server_scripts/manage_users.py add huafu02 实际密码 vip

# 查看所有账号
python3 server_scripts/manage_users.py list
```

### 6. 检查 Flask 应用配置

确保主应用文件（通常是 `app.py` 或 `main.py`）已注册 auth blueprint：

```python
from app.auth import auth_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 必须设置 session 密钥
app.register_blueprint(auth_bp)
```

如果没有，需要添加。查看主应用文件：

```bash
cat app.py  # 或 main.py
```

### 7. 重启 Flask 应用

```bash
# 查找 Flask 进程
ps aux | grep python | grep -E "app.py|main.py|uvicorn"

# 重启（根据实际启动方式）
sudo systemctl restart finance-suite  # 如果用 systemd
# 或
pkill -f "python.*app.py" && nohup python3 app.py &
```

---

## 本地前端部署步骤

### 1. 更新前端文件到服务器

```bash
cd /Users/Zhuanz/finance-suite

# 使用现有的部署脚本
ssh ubuntu@touziagent.com 'bash -s' < deploy.sh
```

### 2. 验证部署

访问 https://touziagent.com/ 测试登录：

- 账号：demo
- 密码：demo2026

---

## 账号管理命令

### 列出所有用户
```bash
python3 server_scripts/manage_users.py list
```

### 添加新用户
```bash
python3 server_scripts/manage_users.py add 用户名 密码 权限
# 权限: free / vip / admin
```

### 重置密码
```bash
python3 server_scripts/manage_users.py reset 用户名 新密码
```

### 删除用户
```bash
python3 server_scripts/manage_users.py delete 用户名
```

---

## 当前账号列表

| 用户名 | 密码 | 权限 | 备注 |
|--------|------|------|------|
| linzuxi | lzx123456 | vip | 内测用户 |
| danny | danny123456 | vip | 内测用户 |
| ivan | ivan123456 | vip | 内测用户 |
| shengwei | 86869945 | vip | 内测用户 |
| vanilla | lemon123456 | vip | 内测用户 |
| nanjian | nj123456 | vip | 内测用户 |
| fengzhijie | fzj123456 | vip | 内测用户 |
| lianghailin | lhl123456 | vip | 内测用户 |
| demo | demo2026 | free | 演示账号 |
| zhuanz | zhuanz0405 | admin | 管理员 |
| hfzq | hf1234 | vip | 华福证券 |

---

## 故障排查

### 登录失败
1. 检查数据库中是否有该用户：
   ```bash
   sqlite3 finance_suite.db "SELECT * FROM users WHERE username='用户名';"
   ```

2. 检查 Flask 日志：
   ```bash
   tail -f /var/log/finance-suite.log  # 或实际日志路径
   ```

3. 测试 API：
   ```bash
   curl -X POST https://touziagent.com/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"demo","password":"demo2026"}'
   ```

### Session 问题
确保 Flask 应用设置了 `secret_key`：
```python
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
```

### 数据库权限
```bash
chmod 644 finance_suite.db
chown ubuntu:ubuntu finance_suite.db
```

---

## 下一步优化建议

1. **密码加盐**：当前使用 SHA256，建议改用 bcrypt
2. **密码策略**：强制定期修改密码
3. **登录日志**：记录登录失败次数，防止暴力破解
4. **Token 认证**：考虑使用 JWT 替代 session
5. **HTTPS Only**：确保 cookie 设置 secure 标志
