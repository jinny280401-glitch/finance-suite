from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.database import get_db, User, Usage, check_usage_allowed, get_today_usage_count
from app.search import unified_search, format_search_results
from app.llm import generate_analysis
from app.skills import get_skill, get_skill_prompt

router = APIRouter(prefix="/api")


# ---- Request models ----

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AnalyzeRequest(BaseModel):
    skill_type: str
    query: str
    extra_content: str = ""


# ---- Auth endpoints ----

@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check existing
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
    response = JSONResponse(
        content={"success": True, "message": "注册成功"},
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return response


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    token = create_access_token({"user_id": user.id, "username": user.username})
    response = JSONResponse(
        content={"success": True, "message": "登录成功"},
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"success": True, "message": "已退出登录"})
    response.delete_cookie(key="access_token")
    return response


# ---- Analysis endpoint ----

@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate skill
    skill = get_skill(req.skill_type)
    if not skill:
        raise HTTPException(status_code=400, detail="未知的分析技能")

    # Check usage
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"今日免费额度已用完（{used}/{limit}次），请升级VIP获取无限使用",
        )

    # Search for data (if skill requires it)
    search_results_text = ""
    sources = []
    search_type = skill.get("search_type")

    if search_type:
        search_query = req.query
        if req.skill_type == "stock":
            # 股票分析：多维度并发搜索
            from app.search import multi_search_stock, format_search_results_grouped
            results = await multi_search_stock(search_query)
            sources = [{"title": r["title"], "url": r["url"]} for r in results if r.get("url")]
            search_results_text = format_search_results_grouped(results)
        elif search_type == "extract" and req.extra_content:
            search_query = req.extra_content
            results = await unified_search(search_query, search_type)
            sources = [{"title": r["title"], "url": r["url"]} for r in results]
            search_results_text = format_search_results(results)
        else:
            results = await unified_search(search_query, search_type)
            sources = [{"title": r["title"], "url": r["url"]} for r in results]
            search_results_text = format_search_results(results)

    # Build user content
    user_content = f"用户查询：{req.query}"
    if req.extra_content and search_type != "extract":
        user_content += f"\n\n用户补充资料：\n{req.extra_content}"

    # Call LLM
    system_prompt = get_skill_prompt(req.skill_type)
    result = await generate_analysis(system_prompt, user_content, search_results_text)

    # Record usage
    usage = Usage(
        user_id=user.id,
        skill_type=req.skill_type,
        query=req.query[:500],
    )
    db.add(usage)
    db.commit()

    return {
        "success": True,
        "result": result,
        "sources": sources,
        "usage_used": used + 1,
        "usage_limit": limit,
    }


# ---- Usage endpoint ----

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
