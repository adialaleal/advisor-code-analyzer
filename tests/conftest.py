import os
import sys
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, compiler, **kw):  # noqa: D401, ANN001
    return "JSON"

# Override UUID default for SQLite
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(_type, compiler, **kw):  # noqa: D401, ANN001
    return "TEXT"

# Override the default value for UUID in SQLite
def _compile_uuid_default_sqlite(element, compiler, **kw):  # noqa: D401, ANN001
    return "hex(randomblob(16))"

# Ensure required environment variables exist before importing application modules
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.dependencies import get_cache_service, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import database as database_module  # noqa: E402
from app.models.database import AnalysisHistory  # noqa: E402


test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# Rebind the global engine/session factory used by the application to the test database
database_module.engine = test_engine
database_module.SessionLocal = TestingSessionLocal
database_module.Base.metadata.create_all(bind=test_engine)


class InMemoryCacheService:
    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    def get(self, key: str):  # type: ignore[override]
        return self.store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:  # noqa: ARG002
        self.store[key] = value

    def is_available(self) -> bool:
        return True


@pytest.fixture
def cache_service() -> InMemoryCacheService:
    return InMemoryCacheService()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.query(AnalysisHistory).delete()
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session, cache_service: InMemoryCacheService) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_cache():
        return cache_service

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache_service] = override_get_cache

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


