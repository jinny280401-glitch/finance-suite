from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_optional_user, get_current_user
from app.database import get_db, User, check_usage_allowed, get_today_usage_count
from app.skills import get_skill_list, get_skill

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.head("/")
async def index_head():
    return Response(
        status_code=200,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User | None = Depends(get_optional_user)):
    skills = get_skill_list()
    response = templates.TemplateResponse(
        "index.html",
        {"request": request, "current_user": user, "skills": skills},
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "current_user": None})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = get_skill_list()
    usage_today = get_today_usage_count(db, user.id)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": user,
            "skills": skills,
            "usage_today": usage_today,
        },
    )


@router.get("/skill/{skill_type}", response_class=HTMLResponse)
async def skill_page(
    skill_type: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skill_data = get_skill(skill_type)
    if not skill_data:
        return RedirectResponse(url="/dashboard", status_code=302)
    # Add type key for template compatibility
    skill_data = {**skill_data, "type": skill_type}
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    return templates.TemplateResponse(
        "skill.html",
        {
            "request": request,
            "current_user": user,
            "skill": skill_data,
            "skill_type": skill_type,
            "usage_today": used,
            "usage_allowed": allowed,
        },
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(
        "pricing.html", {"request": request, "current_user": user}
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: User = Depends(get_current_user)):
    if user.tier != "admin":
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        "admin.html", {"request": request, "current_user": user}
    )


@router.get("/app")
@router.get("/app/")
async def app_entry(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)
