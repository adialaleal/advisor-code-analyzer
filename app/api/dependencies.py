from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.database import get_db_session
from app.services.cache_service import CacheService
from app.services.code_analyzer import CodeAnalyzer


@lru_cache
def get_code_analyzer() -> CodeAnalyzer:
    return CodeAnalyzer()


@lru_cache
def _build_cache_service(redis_url: str) -> CacheService:
    return CacheService(redis_url)


def get_cache_service(settings: Settings = Depends(get_settings)) -> CacheService:
    return _build_cache_service(settings.redis_url)


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()
