import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before importing app modules
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.database import init_db, SessionLocal, User
from app.auth import hash_password
from app.routers import pages, api, admin, intel, watchlist

# Create FastAPI app
app = FastAPI(title="Finance Suite", docs_url="/docs" if os.getenv("DEBUG", "false").lower() == "true" else None)

# Mount static files
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Register routers
app.include_router(pages.router)
app.include_router(api.router)
app.include_router(admin.router)
app.include_router(intel.router)
app.include_router(watchlist.router)


@app.on_event("startup")
async def startup():
    """Initialize database and create default admin on startup."""
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
                print("[Startup] Default admin account created: admin / admin123")
            except Exception:
                db.rollback()
        else:
            print("[Startup] Admin account already exists")
    finally:
        db.close()

    # Preload stock name map in background (takes ~2min first time)
    import threading
    def _preload():
        try:
            from app.stock_data import _load_stock_cache
            print("[Startup] Preloading stock name map...")
            m = _load_stock_cache()
            print(f"[Startup] Stock map loaded: {len(m)} entries")
        except Exception as e:
            print(f"[Startup] Stock map preload failed: {e}")
    threading.Thread(target=_preload, daemon=True).start()


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
