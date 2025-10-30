"""Rule for detecting unused imports."""

from __future__ import annotations

from typing import Any, Dict, List

import ast

from app.services.analysis_rules.base import BaseAnalysisRule


class ImportAnalysisRule(BaseAnalysisRule):
    """Detects unused imports in code."""

    rule_id = "unused_import"

    def _analyze(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
        imports: Dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imports[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    key = f"{module}.{name}" if module else name
                    imports[key] = node.lineno

        used_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
        }

        for name, lineno in imports.items():
            base_name = name.split(".")[0]
            if base_name not in used_names:
                suggestions.append(
                    {
                        "rule_id": self.rule_id,
                        "message": f"Importação '{name}' não é utilizada.",
                        "severity": "warning",
                        "line": lineno,
                        "column": None,
                        "metadata": {"symbol": name},
                    }
                )

