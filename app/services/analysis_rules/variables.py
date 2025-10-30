"""Rule for detecting unused variables."""

from __future__ import annotations

from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


class UnusedVariableRule(BaseAnalysisRule):
    """Detects unused variables in code."""

    rule_id = "unused_variable"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        assigned: Dict[str, int] = {}
        used_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if not node.id.startswith("_"):
                    assigned[node.id] = node.lineno
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        for name, lineno in assigned.items():
            if name not in used_names:
                suggestions.append(
                    {
                        "rule_id": self.rule_id,
                        "message": f"Variável '{name}' é atribuída mas nunca utilizada.",
                        "severity": "info",
                        "line": lineno,
                        "column": None,
                        "metadata": {"symbol": name},
                    }
                )

