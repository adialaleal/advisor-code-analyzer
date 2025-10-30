"""Interfaces for code analysis services."""

from dataclasses import dataclass
from typing import Any, Dict, List
from typing_extensions import Protocol


@dataclass
class AnalysisResult:
    """Result of code analysis."""

    suggestions: List[Dict[str, Any]]
    analysis_time_ms: int


class IAnalysisRule(Protocol):
    """Protocol defining a single analysis rule."""

    rule_id: str
    """Unique identifier for this rule."""

    def analyze(self, tree: Any, suggestions: List[Dict[str, Any]]) -> None:
        """
        Analyze code and add suggestions.

        Args:
            tree: Parsed AST tree of the code
            suggestions: List to append suggestions to
        """
        ...


class ICodeAnalyzer(Protocol):
    """Protocol defining the contract for code analyzers."""

    def analyze(self, code: str) -> AnalysisResult:
        """
        Analyze code and return results.

        Args:
            code: The source code to analyze

        Returns:
            AnalysisResult with suggestions and timing information
        """
        ...

