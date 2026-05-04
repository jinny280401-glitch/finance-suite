from flask import Blueprint, request, jsonify, session
import sqlite3
import hashlib
from pathlib import Path

auth_bp = Blueprint('auth', __name__)
DB_PATH = Path(__file__).parent.parent / "finance_suite.db"

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
    """登录接口"""
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
