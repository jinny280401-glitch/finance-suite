"""
Auth routes — registration, login, logout, auth check, usage, cookie management.
Extracted from routers/api.py for separation of concerns.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
)
from backend.app.database import get_db, User, Usage, check_usage_allowed

router = APIRouter(prefix="/api")


# ---- Request models ----

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ---- Helpers ----

def _issue_auth_response(content: dict, token: str) -> JSONResponse:
    """Clear legacy cookie variants, then set one canonical host-only cookie."""
    response = JSONResponse(content=content)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token", path="/", domain=".touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="www.touziagent.com")
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        max_age=86400,
        path="/",
        samesite="lax",
    )
    return response


def _clear_auth_response(content: dict) -> JSONResponse:
    response = JSONResponse(content=content)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="access_token", path="/", domain=".touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="touziagent.com")
    response.delete_cookie(key="access_token", path="/", domain="www.touziagent.com")
    return response


# ---- Endpoints ----

@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {
            "success": True,
            "message": "注册成功",
            "username": user.username,
            "tier": user.tier,
            "token": token,
        },
        token,
    )


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {
            "success": True,
            "message": "登录成功",
            "username": user.username,
            "tier": user.tier,
            "token": token,
        },
        token,
    )


@router.post("/logout")
async def logout():
    return _clear_auth_response({"success": True, "message": "已退出登录"})


@router.get("/check-auth")
async def check_auth(user: User | None = Depends(get_optional_user)):
    if not user:
        raise HTTPException(status_code=401, detail="未登录，请先登录")
    return {
        "authenticated": True,
        "username": user.username,
        "tier": user.tier,
    }


@router.get("/usage")
async def get_usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    return {
        "used": used,
        "limit": limit,
        "tier": user.tier,
        "allowed": allowed,
    }


@router.post("/auth/refresh")
async def auth_refresh(
    user: User = Depends(get_current_user),
):
    """Re-issue access_token cookie with correct domain (fixes www/non-www cookie scope)."""
    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {"success": True, "username": user.username, "tier": user.tier, "token": token},
        token,
    )


@router.post("/auth/cookie-fix")
async def cookie_fix(
    user: User = Depends(get_current_user),
):
    """Delete old cookie (if any) and set fresh one with correct domain.
    Called by frontend when localStorage shows logged-in but API returns 401.
    """
    token = create_access_token({"user_id": user.id, "username": user.username})
    return _issue_auth_response(
        {"success": True, "username": user.username, "tier": user.tier, "token": token},
        token,
    )
