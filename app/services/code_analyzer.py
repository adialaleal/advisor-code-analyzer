from __future__ import annotations

import ast
import time
from typing import Any, Dict, List, Optional

from app.interfaces.analyzer import AnalysisResult
from app.services.analysis_rules import (
    DocstringRule,
    FunctionMetricsRule,
    ImportAnalysisRule,
    NamingConventionRule,
    PrintStatementRule,
    UnusedVariableRule,
)


class CodeAnalyzer:
    """Code analyzer that applies multiple analysis rules."""

    def __init__(
        self,
        rules: Optional[List[Any]] = None,
    ) -> None:
        """
        Initialize analyzer with rules.

        Args:
            rules: List of analysis rules. Defaults to all standard rules.
        """
        self._rules = rules or self._get_default_rules()

    def _get_default_rules(self) -> List[Any]:
        """Get default analysis rules."""
        return [
            ImportAnalysisRule(),
            UnusedVariableRule(),
            FunctionMetricsRule(),
            NamingConventionRule(),
            DocstringRule(),
            PrintStatementRule(),
        ]

    def analyze(self, code: str) -> AnalysisResult:
        """
        Analyze code and return results.

        Args:
            code: The source code to analyze

        Returns:
            AnalysisResult with suggestions and timing information
        """
        start = time.perf_counter()
        suggestions: List[Dict[str, Any]] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            suggestions.append(
                {
                    "rule_id": "syntax_error",
                    "message": f"Erro de sintaxe: {exc.msg}",
                    "severity": "error",
                    "line": exc.lineno,
                    "column": exc.offset,
                    "metadata": {},
                }
            )
            return AnalysisResult(
                suggestions=suggestions,
                analysis_time_ms=int((time.perf_counter() - start) * 1000),
            )

        # Apply all rules
        for rule in self._rules:
            rule.analyze(tree, suggestions)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return AnalysisResult(suggestions=suggestions, analysis_time_ms=elapsed_ms)
