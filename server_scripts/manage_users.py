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

DB_PATH = Path(__file__).parent.parent / "finance_suite.db"

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
