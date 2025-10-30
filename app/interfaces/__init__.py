"""Protocols and interfaces for dependency inversion."""

from app.interfaces.analyzer import IAnalysisRule, ICodeAnalyzer
from app.interfaces.cache import ICacheService
from app.interfaces.database import IDatabaseService

__all__ = [
    "IAnalysisRule",
    "ICodeAnalyzer",
    "ICacheService",
    "IDatabaseService",
]

