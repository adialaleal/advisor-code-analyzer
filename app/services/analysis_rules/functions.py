"""Rule for checking function metrics."""

from __future__ import annotations

from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


class FunctionMetricsRule(BaseAnalysisRule):
    """Checks function length and cyclomatic complexity."""

    rule_id = "function_metrics"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                function_length = end_lineno - node.lineno + 1
                if function_length > 50:
                    suggestions.append(
                        {
                            "rule_id": "long_function",
                            "message": f"Função '{node.name}' possui {function_length} linhas (máximo recomendado: 50).",
                            "severity": "warning",
                            "line": node.lineno,
                            "column": None,
                            "metadata": {"length": function_length},
                        }
                    )

                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    suggestions.append(
                        {
                            "rule_id": "high_cyclomatic_complexity",
                            "message": f"Função '{node.name}' possui complexidade ciclomática {complexity} (máximo recomendado: 10).",
                            "severity": "warning",
                            "line": node.lineno,
                            "column": None,
                            "metadata": {"complexity": complexity},
                        }
                    )

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.With,
                    ast.AsyncWith,
                    ast.Try,
                    ast.BoolOp,
                    ast.comprehension,
                ),
            ):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity

