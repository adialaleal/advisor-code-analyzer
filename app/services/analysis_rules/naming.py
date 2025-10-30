"""Rule for checking naming conventions."""

from __future__ import annotations

import re
from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


class NamingConventionRule(BaseAnalysisRule):
    """Checks PEP 8 naming conventions."""

    rule_id = "naming_conventions"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        def add_suggestion(name: str, lineno: int, rule: str, entity: str) -> None:
            suggestions.append(
                {
                    "rule_id": rule,
                    "message": f"{entity} '{name}' deveria seguir PEP 8 (snake_case).",
                    "severity": "info",
                    "line": lineno,
                    "column": None,
                    "metadata": {"name": name},
                }
            )

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not SNAKE_CASE_PATTERN.match(node.name):
                    add_suggestion(node.name, node.lineno, "function_naming", "Função")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        if not SNAKE_CASE_PATTERN.match(target.id):
                            add_suggestion(
                                target.id, target.lineno, "variable_naming", "Variável"
                            )

