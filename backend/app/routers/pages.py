from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from backend.app.auth import get_optional_user, get_current_user
from backend.app.database import get_db, User, check_usage_allowed, get_today_usage_count
from backend.engine.registry import ScenarioRegistry
from backend.app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


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
    skills = ScenarioRegistry().list_metadata()
    response = templates.TemplateResponse(
        request,
        "index.html",
        {"current_user": user, "skills": skills},
    )
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"current_user": None})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "register.html", {"current_user": None})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = ScenarioRegistry().list_metadata()
    usage_today = get_today_usage_count(db, user.id)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
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
    skill_data = ScenarioRegistry().get_metadata(skill_type)
    if not skill_data:
        return RedirectResponse(url="/dashboard", status_code=302)
    # Add type key for template compatibility
    skill_data = {**skill_data, "type": skill_type}
    allowed, used, limit = check_usage_allowed(db, user.id, user.tier)
    return templates.TemplateResponse(
        request,
        "skill.html",
        {
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
        request, "pricing.html", {"current_user": user}
    )


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: User = Depends(get_current_user)):
    if user.tier != "admin":
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        request, "admin.html", {"current_user": user}
    )


@router.get("/app")
async def app_index(user: User | None = Depends(get_optional_user)):
    """Redirect /app to dashboard (main entry point)."""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


@router.get("/app/{filename}")
async def serve_app_page(filename: str, user: User | None = Depends(get_optional_user)):
    """Serve frontend pages from scenarios/ or frontend/pages/ directories."""
    # Map scenario pages
    scenario_pages = {
        "stock.html": "backend/scenarios/stock/page.html",
        "macro.html": "backend/scenarios/macro/page.html",
        "auction.html": "backend/scenarios/auction/page.html",
        "industry.html": "backend/scenarios/industry/page.html",
        "meeting.html": "backend/scenarios/meeting/page.html",
        "video.html": "backend/scenarios/video/page.html",
        "deep-research.html": "backend/scenarios/deep-research/page.html",
    }
    
    # Check if it's a scenario page
    if filename in scenario_pages:
        file_path = settings.BASE_DIR / scenario_pages[filename]
        if file_path.exists():
            return FileResponse(file_path, media_type="text/html")
    
    # Check frontend/pages/
    frontend_path = settings.BASE_DIR / "frontend" / "pages" / filename
    if frontend_path.exists():
        return FileResponse(frontend_path, media_type="text/html")
    
    # Check for JS/CSS files in frontend subdirectories
    for subdir in ["scripts", "styles", "shared", "lib"]:
        resource_path = settings.BASE_DIR / "frontend" / subdir / filename
        if resource_path.exists():
            media_type = "text/javascript" if filename.endswith(".js") else "text/css"
            return FileResponse(resource_path, media_type=media_type)
    
    raise HTTPException(status_code=404, detail=f"Page not found: {filename}")
