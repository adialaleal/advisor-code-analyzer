"""Rule for checking docstrings."""

from __future__ import annotations

from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


class DocstringRule(BaseAnalysisRule):
    """Checks for missing docstrings."""

    rule_id = "missing_docstring"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                docstring = ast.get_docstring(node)
                if not docstring:
                    suggestions.append(
                        {
                            "rule_id": self.rule_id,
                            "message": f"Função '{node.name}' deveria conter docstring.",
                            "severity": "info",
                            "line": node.lineno,
                            "column": None,
                            "metadata": {},
                        }
                    )

