"""
Shared test fixtures for Finance Suite test suite.
Uses in-memory SQLite to avoid touching production or local dev databases.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure test environment: use temp DB, disable external calls
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-2026"
os.environ["DEBUG"] = "true"
os.environ["QWEN_API_KEY"] = "test-qwen-key"
os.environ["TAVILY_KEYS"] = "test-tavily-key-1,test-tavily-key-2"
os.environ["BRAVE_KEYS"] = "test-brave-key-1"

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.auth import hash_password


@pytest.fixture(scope="function")
def engine():
    """Per-function in-memory SQLite engine for full test isolation."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Per-function database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(engine):
    """FastAPI TestClient with overridden DB dependency."""
    TestSession = sessionmaker(bind=engine)

    def _override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    from backend.app.main import app
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a standard free-tier test user."""
    from backend.app.database import User
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        tier="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin-tier test user."""
    from backend.app.database import User
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        tier="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """JWT auth headers for the standard test user."""
    from backend.app.auth import create_access_token
    token = create_access_token({"user_id": test_user.id, "username": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user):
    """JWT auth headers for the admin user."""
    from backend.app.auth import create_access_token
    token = create_access_token({"user_id": admin_user.id, "username": admin_user.username})
    return {"Authorization": f"Bearer {token}"}
