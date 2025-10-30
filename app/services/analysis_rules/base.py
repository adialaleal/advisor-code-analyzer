"""Base class for analysis rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import ast


class BaseAnalysisRule(ABC):
    """Abstract base class for code analysis rules."""

    rule_id: str
    """Unique identifier for this rule."""

    def analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        """
        Analyze code and add suggestions.

        Args:
            tree: Parsed AST tree of the code
            suggestions: List to append suggestions to
        """
        self._analyze(tree, suggestions)

    @abstractmethod
    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        """
        Internal analysis method implemented by subclasses.

        Args:
            tree: Parsed AST tree of the code
            suggestions: List to append suggestions to
        """
        ...

