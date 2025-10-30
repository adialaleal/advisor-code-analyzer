"""Rule for checking print statements."""

from __future__ import annotations

from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


class PrintStatementRule(BaseAnalysisRule):
    """Detects print statements that should use logging."""

    rule_id = "print_statement"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    suggestions.append(
                        {
                            "rule_id": self.rule_id,
                            "message": "Considere utilizar logging em vez de print para saída em produção.",
                            "severity": "info",
                            "line": getattr(node, "lineno", None),
                            "column": getattr(node, "col_offset", None),
                            "metadata": {},
                        }
                    )

