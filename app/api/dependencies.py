from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.database import get_db_session
from app.services.analysis_service import CodeAnalysisService
from app.services.cache_service import CacheService
from app.services.code_analyzer import CodeAnalyzer
from app.services.database_service import AnalysisHistoryService


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


def get_database_service(db: Session = Depends(get_db)) -> AnalysisHistoryService:
    """Provide database service instance."""
    return AnalysisHistoryService(db)


def get_analysis_service(
    analyzer: CodeAnalyzer = Depends(get_code_analyzer),
    cache: CacheService = Depends(get_cache_service),
    db_service: AnalysisHistoryService = Depends(get_database_service),
) -> CodeAnalysisService:
    """Provide analysis service instance."""
    return CodeAnalysisService(analyzer, cache, db_service)
