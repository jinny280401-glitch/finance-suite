from flask import Blueprint, request, jsonify, session
import sqlite3
import hashlib
import time
from collections import defaultdict
from pathlib import Path

auth_bp = Blueprint('auth', __name__)
DB_PATH = Path(__file__).parent.parent / "finance_suite.db"

# In-memory rate limiter: 5 attempts per IP per 60s window
_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_RATE_LIMIT = 5
_LOGIN_RATE_WINDOW = 60


def _check_login_rate(ip: str) -> bool:
    """Return True if under limit, False if rate-limited."""
    now = time.time()
    window = [t for t in _login_attempts[ip] if now - t < _LOGIN_RATE_WINDOW]
    _login_attempts[ip] = window
    if len(window) >= _LOGIN_RATE_LIMIT:
        return False
    _login_attempts[ip].append(now)
    return True

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password: str):
    """验证用户名密码，返回 (user_id, tier) 或 None"""
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
    """登录接口（含速率限制：每 IP 每分钟最多 5 次尝试）"""
    client_ip = request.remote_addr or '127.0.0.1'
    if not _check_login_rate(client_ip):
        return jsonify({'success': False, 'message': '登录尝试过于频繁，请稍后再试'}), 429

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
    """登出接口"""
    session.clear()
    return jsonify({'success': True})

@auth_bp.route('/api/check-auth', methods=['GET'])
def check_auth():
    """检查登录状态"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'tier': session.get('tier')
        })
    else:
        return jsonify({'authenticated': False})
