"""Service layer for code analysis orchestration."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.interfaces.analyzer import AnalysisResult, ICodeAnalyzer
from app.interfaces.cache import ICacheService
from app.models.schemas import Suggestion
from app.services.database_service import AnalysisHistoryService


class CodeAnalysisService:
    """Orchestrates code analysis, caching, and persistence."""

    def __init__(
        self,
        analyzer: ICodeAnalyzer,
        cache: ICacheService,
        db_service: AnalysisHistoryService,
    ) -> None:
        """
        Initialize the service.

        Args:
            analyzer: Code analyzer instance
            cache: Cache service instance
            db_service: Database service instance
        """
        self._analyzer = analyzer
        self._cache = cache
        self._db_service = db_service

    def analyze_code(
        self,
        code: str,
        language_version: str | None = None,
        *,
        use_cache: bool = True,
        persist: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze code with caching and persistence.

        Args:
            code: The source code to analyze
            language_version: Optional Python version
            use_cache: Whether to use cache (default: True)
            persist: Whether to persist to database (default: True)

        Returns:
            Dictionary with analysis results including cached flag
        """
        code_hash = self._generate_hash(code)
        cache_key = f"analysis:{code_hash}"

        # Try cache first
        if use_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                suggestions = [self._dict_to_suggestion(item) for item in cached["suggestions"]]
                return {
                    "code_hash": cached["code_hash"],
                    "suggestions": suggestions,
                    "analysis_time_ms": cached["analysis_time_ms"],
                    "cached": True,
                }

        # Perform analysis
        result = self._analyzer.analyze(code)

        # Persist to database
        if persist:
            self._db_service.create(
                code_hash=code_hash,
                code_snippet=code,
                suggestions=result.suggestions,
                analysis_time_ms=result.analysis_time_ms,
                language_version=language_version,
            )

        # Cache the result
        if use_cache:
            response_payload = {
                "code_hash": code_hash,
                "suggestions": result.suggestions,
                "analysis_time_ms": result.analysis_time_ms,
            }
            self._cache.set(cache_key, response_payload)

        # Convert to response format
        suggestions = [self._dict_to_suggestion(item) for item in result.suggestions]
        return {
            "code_hash": code_hash,
            "suggestions": suggestions,
            "analysis_time_ms": result.analysis_time_ms,
            "cached": False,
        }

    @staticmethod
    def _generate_hash(code: str) -> str:
        """Generate SHA-256 hash of code."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def _dict_to_suggestion(data: Dict[str, Any]) -> Suggestion:
        """Convert dictionary to Suggestion model."""
        return Suggestion(**data)

