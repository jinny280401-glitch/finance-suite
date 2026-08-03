from concurrent.futures import ThreadPoolExecutor
import inspect
import sys
import time
import types

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from starlette.requests import Request

# Auth hashing is outside this hotfix; this keeps the test runnable in the
# repository venv, where bcrypt is not installed.
sys.modules.setdefault(
    "bcrypt",
    types.SimpleNamespace(
        gensalt=lambda: b"unused",
        hashpw=lambda value, _salt: value,
        checkpw=lambda value, hashed: value == hashed,
    ),
)

from app import auth, database
from app.routers import api


def _request(token: str) -> Request:
    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/analyze",
        "headers": [(b"authorization", f"Bearer {token}".encode())],
    })


@pytest.fixture()
def db_runtime(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=1,
        max_overflow=0,
        pool_timeout=0.05,
    )
    database.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(auth, "SessionLocal", factory)
    monkeypatch.setattr(api, "SessionLocal", factory)
    with factory.begin() as db:
        db.add(database.User(
            id=1,
            username="fixture-user",
            email="fixture@example.com",
            hashed_password="unused",
            tier="admin",
            is_active=True,
        ))
    yield engine, factory
    engine.dispose()


def test_auth_releases_connection_before_route_work(db_runtime):
    engine, _ = db_runtime
    token = auth.create_access_token({"user_id": 1, "username": "fixture-user"})
    user = auth.get_current_user(_request(token))
    assert user.id == 1
    assert user.tier == "admin"
    assert engine.pool.checkedout() == 0


def test_auth_pool_timeout_is_explicit_503(db_runtime):
    engine, factory = db_runtime
    token = auth.create_access_token({"user_id": 1, "username": "fixture-user"})
    held = factory()
    held.query(database.User).first()
    with pytest.raises(HTTPException) as caught:
        auth.get_current_user(_request(token))
    held.close()
    assert caught.value.status_code == 503
    assert caught.value.headers == {"Retry-After": "5"}
    assert "资源暂时不可用" in caught.value.detail
    assert engine.pool.checkedout() == 0


def test_analysis_usage_scopes_release_connection(db_runtime):
    engine, factory = db_runtime
    user = database.User(id=1, tier="admin")
    allowed, used, limit = api._analysis_usage_status(user, "test-trace")
    assert (allowed, used, limit) == (True, 0, None)
    assert engine.pool.checkedout() == 0
    api._record_analysis_usage(1, "stock", "002594", "test-trace")
    assert engine.pool.checkedout() == 0
    with factory() as db:
        assert db.query(database.Usage).count() == 1


def test_analysis_usage_pool_timeout_is_explicit_503(db_runtime):
    engine, factory = db_runtime
    user = database.User(id=1, tier="admin")
    held = factory()
    held.query(database.User).first()
    with pytest.raises(HTTPException) as caught:
        api._analysis_usage_status(user, "test-trace")
    held.close()
    assert caught.value.status_code == 503
    assert caught.value.headers == {"Retry-After": "5"}
    assert "资源暂时不可用" in caught.value.detail
    assert engine.pool.checkedout() == 0


def test_concurrent_external_waits_do_not_hold_db_connections(db_runtime):
    engine, _ = db_runtime
    user = database.User(id=1, tier="admin")

    def request_prefix_then_external_wait(_index: int) -> None:
        assert api._analysis_usage_status(user, f"test-{_index}")[0] is True
        time.sleep(0.03)

    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(request_prefix_then_external_wait, range(36)))
    assert engine.pool.checkedout() == 0


def test_analyze_route_has_no_request_scoped_db_dependency():
    assert "db" not in inspect.signature(api.analyze).parameters
