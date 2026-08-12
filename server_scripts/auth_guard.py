"""
Shared auth guards for Flask and FastAPI endpoints.

Deny-by-default: every protected endpoint requires valid authentication.
Unauthenticated access returns 401; unauthorized role returns 403.

Contract:
- Flask endpoints: use @login_required / @admin_required decorators
- FastAPI endpoints: use require_auth / require_admin as Depends()
- SECRET_KEY must be set in environment (shared between Flask and FastAPI)
"""

from __future__ import annotations

import os
from functools import wraps

from flask import jsonify, session


# ---------------------------------------------------------------------------
# Flask guards
# ---------------------------------------------------------------------------

def login_required(f):
    """Flask decorator: reject if not logged in (401)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "请先登录"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Flask decorator: reject if not admin (401 if not logged in, 403 if wrong role)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "请先登录"}), 401
        if session.get("tier") != "admin":
            return jsonify({"success": False, "message": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# FastAPI guards (deny-by-default)
# ---------------------------------------------------------------------------

from fastapi import HTTPException, Request  # noqa: E402 (deferred to keep flask imports together)


async def require_auth(request: Request) -> dict:
    """FastAPI dependency. Returns {user_id, username, tier} or raises 401.

    Checks in order:
    1. request.state.user_id — set by app-level middleware (e.g. Starlette
       SessionMiddleware that bridges Flask sessions into FastAPI).
    2. Flask session cookie — decoded directly using the shared SECRET_KEY.
       This path works when Flask and FastAPI share the same secret key and
       the session cookie is set by auth.py's /api/login.
    """
    # Path 1: middleware already set user context on request.state
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return {
            "user_id": user_id,
            "username": getattr(request.state, "username", ""),
            "tier": getattr(request.state, "tier", "free"),
        }

    # Path 2: decode Flask session cookie directly
    session_cookie = request.cookies.get("session")
    if session_cookie:
        try:
            from flask import Flask
            from flask.sessions import SecureCookieSessionInterface

            _app = Flask(__name__)
            _app.secret_key = os.getenv(
                "FLASK_SECRET_KEY",
                os.getenv("SECRET_KEY", "finance-suite-unsafe-default"),
            )
            si = SecureCookieSessionInterface()
            data = si.get_signing_serializer(_app).loads(session_cookie)
            user_id = data.get("user_id")
            if user_id:
                return {
                    "user_id": user_id,
                    "username": data.get("username", ""),
                    "tier": data.get("tier", "free"),
                }
        except Exception:
            pass  # invalid / tampered cookie → fall through to 401

    raise HTTPException(status_code=401, detail="请先登录")


async def require_admin(request: Request) -> dict:
    """FastAPI dependency. require_auth + admin tier check (403 if not admin)."""
    user = await require_auth(request)
    if user.get("tier") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
