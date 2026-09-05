from datetime import datetime, date
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

DATABASE_URL = "sqlite:///./finance_suite.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Daily usage limits per tier
TIER_LIMITS = {
    "free": 3,
    "vip": None,  # unlimited
    "admin": None,  # unlimited
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    tier = Column(String(10), default="free", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    usages = relationship("Usage", back_populates="user")


class Usage(Base):
    __tablename__ = "usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_type = Column(String(30), nullable=False)
    query = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="usages")


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_today_usage_count(db: Session, user_id: int) -> int:
    """Count how many analyses a user has run today."""
    today_start = datetime.combine(date.today(), datetime.min.time())
    return (
        db.query(func.count(Usage.id))
        .filter(Usage.user_id == user_id, Usage.created_at >= today_start)
        .scalar()
    )


def check_usage_allowed(db: Session, user_id: int, tier: str) -> tuple[bool, int, int | None]:
    """
    Check if user can perform analysis.
    Returns (allowed, used_count, limit_or_none).
    """
    limit = TIER_LIMITS.get(tier)
    used = get_today_usage_count(db, user_id)
    if limit is None:
        return True, used, None
    return used < limit, used, limit


# ---------------------------------------------------------------------------
# CC Phase 1 instrumentation (added 2026-07-30, observability only).
# Purpose: attribute QueuePool checkouts to requests to confirm the
# long-hold hypothesis in KAN_PIAO_ANALYSIS_RCA.md. No behaviour change.
# Remove or gate this block once the ownership question is closed.
# ---------------------------------------------------------------------------

import os as _cc_os
import threading as _cc_threading
import time as _cc_time

from sqlalchemy import event as _cc_event

_CC_POOL_LOG = _cc_os.environ.get(
    "CC_POOL_LOG", "/home/ubuntu/finance-suite-web/logs/pool_instrument.log"
)
_cc_lock = _cc_threading.Lock()
_cc_checkout_started: dict[int, float] = {}


def _cc_emit(action: str, extra: str = "") -> None:
    """Append one pool event line. Never raise into the request path."""
    try:
        pool = engine.pool
        line = (
            f"{_cc_time.strftime('%Y-%m-%dT%H:%M:%S')} "
            f"pid={_cc_os.getpid()} "
            f"tid={_cc_threading.get_ident()} "
            f"action={action} "
            f"checkedout={pool.checkedout()} "
            f"size={pool.size()} "
            f"overflow={pool.overflow()} "
            f"{extra}\n"
        )
        with _cc_lock:
            _cc_os.makedirs(_cc_os.path.dirname(_CC_POOL_LOG), exist_ok=True)
            with open(_CC_POOL_LOG, "a") as fh:
                fh.write(line)
    except Exception:
        pass


@_cc_event.listens_for(engine, "checkout")
def _cc_on_checkout(dbapi_conn, conn_record, conn_proxy):
    _cc_checkout_started[id(conn_record)] = _cc_time.monotonic()
    _cc_emit("checkout")


@_cc_event.listens_for(engine, "checkin")
def _cc_on_checkin(dbapi_conn, conn_record):
    started = _cc_checkout_started.pop(id(conn_record), None)
    held = f"held_s={_cc_time.monotonic() - started:.3f}" if started else "held_s=unknown"
    _cc_emit("checkin", held)
