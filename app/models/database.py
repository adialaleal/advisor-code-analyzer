from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Text, create_engine, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


# Override JSONB for SQLite
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, compiler, **kw):  # noqa: D401, ANN001
    return "JSON"


# Override UUID default for SQLite
@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(_type, compiler, **kw):  # noqa: D401, ANN001
    return "TEXT"


# Override the default value for UUID in SQLite
@compiles(text("gen_random_uuid()"), "sqlite")
def _compile_uuid_default_sqlite(element, compiler, **kw):  # noqa: D401, ANN001
    return "hex(randomblob(16))"


settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    __table_args__ = (
        Index("ix_analysis_history_created_at", "created_at"),
        Index("ix_analysis_history_code_hash", "code_hash"),
        Index("ix_analysis_history_suggestions", "suggestions", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    code_hash: Mapped[str] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    analysis_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


def get_db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
