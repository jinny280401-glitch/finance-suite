import os
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing app modules
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# 日志最早初始化：在任何业务 import 之前
from backend.app.logging_config import setup_logging

_log_dir = os.getenv("LOG_DIR", str(Path(__file__).resolve().parent.parent.parent / "logs"))
setup_logging(log_dir=_log_dir)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.database import init_db, SessionLocal, User
from backend.app.auth import hash_password
from backend.app.routers import pages, api, admin, intel, watchlist, auth_routes, export

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, create admin, preload stock cache."""
    init_db()

    # Create default admin account if it doesn't exist
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            try:
                admin_user = User(
                    username="admin",
                    email="admin@financesuite.com",
                    hashed_password=hash_password("admin123"),
                    tier="admin",
                    is_active=True,
                )
                db.add(admin_user)
                db.commit()
                logger.info("[Startup] Default admin account created: admin / admin123")
            except Exception:
                db.rollback()
        else:
            logger.debug("[Startup] Admin account already exists")
    finally:
        db.close()

    # Preload stock name map in background (takes ~2min first time)
    def _preload():
        try:
            from backend.engine.skills.stock_skill import _load_stock_cache
            logger.debug("[Startup] Preloading stock name map...")
            m = _load_stock_cache()
            logger.info("[Startup] Stock map loaded: %d entries", len(m))
        except Exception as e:
            logger.warning("[Startup] Stock map preload failed: %s", e)
    threading.Thread(target=_preload, daemon=True).start()

    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(title="Finance Suite", docs_url="/docs" if settings.DEBUG else None, lifespan=lifespan)

# Mount static files
settings.STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Note: /app/* routes are handled by pages.router.serve_app_page()

# Register routers
app.include_router(pages.router)
app.include_router(auth_routes.router)   # auth: register/login/logout/check-auth/usage
app.include_router(api.router)           # analyze
app.include_router(export.router)        # export-pdf
app.include_router(admin.router)
app.include_router(intel.router)
app.include_router(watchlist.router)


@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    """Redirect to login on 401 for page requests."""
    if not request.url.path.startswith("/api/"):
        return RedirectResponse(url="/login", status_code=302)
    from fastapi.responses import JSONResponse as _JR; return _JR(status_code=401, content={"detail": str(exc)})



@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
