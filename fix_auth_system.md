# Finance Suite 账号系统修复方案

## 问题诊断
1. **前端硬编码**：`index.html` 中有 `_accounts` 对象，纯前端验证
2. **后端数据库**：服务器上有 `finance_suite.db` 和 `app/auth.py`
3. **不同步**：前后端账号列表不一致，导致登录失败
4. **密码失效**：现有密码已过期，需要重置

## 解决方案

### 第一步：服务器端 - 创建账号管理脚本

在服务器上创建 `/home/ubuntu/finance-suite-web/manage_users.py`：

```python
#!/usr/bin/env python3
"""
Finance Suite 用户管理脚本
用法：
  python manage_users.py list                    # 列出所有用户
  python manage_users.py add <username> <password> <tier>  # 添加用户
  python manage_users.py reset <username> <password>       # 重置密码
  python manage_users.py delete <username>                 # 删除用户
"""

import sqlite3
import hashlib
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "finance_suite.db"

def hash_password(password: str) -> str:
    """使用 SHA256 哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def list_users():
    """列出所有用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, tier, created_at, last_login FROM users ORDER BY username")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        print("数据库中没有用户")
        return
    
    print(f"\n{'用户名':<20} {'权限':<10} {'创建时间':<20} {'最后登录':<20}")
    print("-" * 80)
    for username, tier, created, last_login in users:
        print(f"{username:<20} {tier:<10} {created or 'N/A':<20} {last_login or '从未登录':<20}")
    print(f"\n总计: {len(users)} 个用户\n")

def add_user(username: str, password: str, tier: str = "free"):
    """添加新用户"""
    if tier not in ["free", "vip", "admin"]:
        print(f"错误：权限必须是 free/vip/admin，当前值: {tier}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, tier) VALUES (?, ?, ?)",
            (username, hash_password(password), tier)
        )
        conn.commit()
        print(f"✓ 用户 {username} 添加成功 (权限: {tier})")
        return True
    except sqlite3.IntegrityError:
        print(f"✗ 用户 {username} 已存在")
        return False
    finally:
        conn.close()

def reset_password(username: str, new_password: str):
    """重置用户密码"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hash_password(new_password), username)
    )
    if cursor.rowcount == 0:
        print(f"✗ 用户 {username} 不存在")
        conn.close()
        return False
    conn.commit()
    conn.close()
    print(f"✓ 用户 {username} 密码已重置")
    return True

def delete_user(username: str):
    """删除用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    if cursor.rowcount == 0:
        print(f"✗ 用户 {username} 不存在")
        conn.close()
        return False
    conn.commit()
    conn.close()
    print(f"✓ 用户 {username} 已删除")
    return True

def main():
    init_db()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    elif command == "add":
        if len(sys.argv) < 5:
            print("用法: python manage_users.py add <username> <password> <tier>")
            return
        add_user(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "reset":
        if len(sys.argv) < 4:
            print("用法: python manage_users.py reset <username> <password>")
            return
        reset_password(sys.argv[2], sys.argv[3])
    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法: python manage_users.py delete <username>")
            return
        delete_user(sys.argv[2])
    else:
        print(f"未知命令: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
```

### 第二步：服务器端 - 批量导入现有账号

创建 `/home/ubuntu/finance-suite-web/import_accounts.sh`：

```bash
#!/bin/bash
# 批量导入所有内测账号

cd /home/ubuntu/finance-suite-web

echo "开始导入账号..."

# 内测账号（从前端硬编码迁移）
python3 manage_users.py add linzuxi lzx123456 vip
python3 manage_users.py add danny danny123456 vip
python3 manage_users.py add ivan ivan123456 vip
python3 manage_users.py add shengwei 86869945 vip
python3 manage_users.py add demo demo2026 free
python3 manage_users.py add zhuanz zhuanz0405 admin
python3 manage_users.py add vanilla lemon123456 vip
python3 manage_users.py add nanjian nj123456 vip
python3 manage_users.py add fengzhijie fzj123456 vip
python3 manage_users.py add lianghailin lhl123456 vip

# 华福证券账号（请补充实际用户名和密码）
# python3 manage_users.py add huafu_user1 password1 vip
# python3 manage_users.py add huafu_user2 password2 vip

echo ""
echo "导入完成！当前用户列表："
python3 manage_users.py list
```

### 第三步：服务器端 - 检查/创建 auth.py

确保 `/home/ubuntu/finance-suite-web/app/auth.py` 存在且正确：

```python
from flask import Blueprint, request, jsonify, session
import sqlite3
import hashlib
from pathlib import Path

auth_bp = Blueprint('auth', __name__)
DB_PATH = Path(__file__).parent.parent / "finance_suite.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password: str):
    """验证用户名密码"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, tier FROM users WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    result = cursor.fetchone()
    
    if result:
        # 更新最后登录时间
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (result[0],)
        )
        conn.commit()
    
    conn.close()
    return result

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '请输入账号和密码'}), 400
    
    result = verify_user(username, password)
    
    if result:
        user_id, tier = result
        session['user_id'] = user_id
        session['username'] = username
        session['tier'] = tier
        return jsonify({
            'success': True,
            'username': username,
            'tier': tier
        })
    else:
        return jsonify({'success': False, 'message': '账号或密码不正确'}), 401

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'tier': session.get('tier')
        })
    else:
        return jsonify({'authenticated': False})
```

### 第四步：本地修改前端代码

修改 `/Users/Zhuanz/finance-suite/index.html`：

**删除硬编码账号（1055-1063行）：**
```javascript
// 删除这部分
var _accounts = {
  'linzuxi': 'lzx123456',
  // ... 其他账号
};
```

**修改 doLogin() 函数（1070-1088行）：**
```javascript
async function doLogin() {
  var u = document.getElementById('loginUser').value.trim().toLowerCase();
  var p = document.getElementById('loginPass').value;
  var errEl = document.getElementById('loginErr');
  
  if (!u || !p) {
    errEl.textContent = '请输入账号和密码';
    return;
  }
  
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    });
    
    const data = await response.json();
    
    if (data.success) {
      localStorage.setItem('fs_auth', 'ok');
      localStorage.setItem('fs_user', data.username);
      localStorage.setItem('fs_tier', data.tier);
      
      var params = new URLSearchParams(location.search);
      var redirect = params.get('redirect');
      if (redirect && /^\/[\w\-\/]*$/.test(redirect)) {
        location.href = redirect;
        return;
      }
      document.getElementById('loginGate').style.display = 'none';
      renderHeader();
    } else {
      errEl.textContent = data.message || '登录失败';
      document.getElementById('loginPass').value = '';
    }
  } catch (error) {
    errEl.textContent = '网络错误，请稍后重试';
    console.error('Login error:', error);
  }
}
```

**修改 doLogout() 函数（1109行）：**
```javascript
async function doLogout() {
  try {
    await fetch('/api/logout', { method: 'POST' });
  } catch (error) {
    console.error('Logout error:', error);
  }
  localStorage.removeItem('fs_auth');
  localStorage.removeItem('fs_user');
  localStorage.removeItem('fs_tier');
  location.reload();
}
```

同样修改 `/Users/Zhuanz/finance-suite/app/index.html` 中的登录/登出逻辑。

### 第五步：部署流程

```bash
# 1. 在服务器上执行
ssh ubuntu@8.138.2.55
cd /home/ubuntu/finance-suite-web

# 2. 创建管理脚本
nano manage_users.py  # 粘贴上面的代码
chmod +x manage_users.py

# 3. 导入账号
nano import_accounts.sh  # 粘贴上面的代码
chmod +x import_accounts.sh
./import_accounts.sh

# 4. 检查 auth.py 是否存在
ls -la app/auth.py

# 5. 确保 Flask app 注册了 auth blueprint
# 检查主应用文件（可能是 app.py 或 main.py）

# 6. 重启后端服务
sudo systemctl restart finance-suite  # 或者你的服务名称

# 7. 在本地更新前端代码
cd /Users/Zhuanz/finance-suite
# 修改 index.html 和 app/index.html

# 8. 部署到服务器
./deploy.sh
```

## 验证步骤

1. 访问 https://touziagent.com/
2. 点击"进入工作台"
3. 使用任意账号登录（如 demo / demo2026）
4. 检查是否能正常进入工作台

## 后续维护

```bash
# 添加新用户
python3 manage_users.py add 新用户名 密码 vip

# 重置密码
python3 manage_users.py reset 用户名 新密码

# 查看所有用户
python3 manage_users.py list

# 删除用户
python3 manage_users.py delete 用户名
```

## 注意事项

1. **密码安全**：当前使用 SHA256，建议后续升级为 bcrypt
2. **Session 配置**：确保 Flask app 配置了 SECRET_KEY
3. **HTTPS**：生产环境必须使用 HTTPS（已配置）
4. **备份数据库**：修改前先备份 `finance_suite.db`
