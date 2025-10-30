from __future__ import annotations

import ast
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List


SNAKE_CASE_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass
class AnalysisResult:
    suggestions: List[Dict[str, Any]]
    analysis_time_ms: int


class CodeAnalyzer:
    def analyze(self, code: str) -> AnalysisResult:
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

        self._check_imports(tree, suggestions)
        self._check_unused_variables(tree, suggestions)
        self._check_function_metrics(tree, suggestions)
        self._check_naming_conventions(tree, suggestions)
        self._check_docstrings(tree, suggestions)
        self._check_print_statements(tree, suggestions)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return AnalysisResult(suggestions=suggestions, analysis_time_ms=elapsed_ms)

    def _check_imports(self, tree: ast.AST, suggestions: List[Dict[str, Any]]) -> None:
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
                        "rule_id": "unused_import",
                        "message": f"Importação '{name}' não é utilizada.",
                        "severity": "warning",
                        "line": lineno,
                        "column": None,
                        "metadata": {"symbol": name},
                    }
                )

    def _check_unused_variables(
        self, tree: ast.AST, suggestions: List[Dict[str, Any]]
    ) -> None:
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
                        "rule_id": "unused_variable",
                        "message": f"Variável '{name}' é atribuída mas nunca utilizada.",
                        "severity": "info",
                        "line": lineno,
                        "column": None,
                        "metadata": {"symbol": name},
                    }
                )

    def _check_function_metrics(
        self, tree: ast.AST, suggestions: List[Dict[str, Any]]
    ) -> None:
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

    def _check_naming_conventions(
        self, tree: ast.AST, suggestions: List[Dict[str, Any]]
    ) -> None:
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

    def _check_docstrings(
        self, tree: ast.AST, suggestions: List[Dict[str, Any]]
    ) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                docstring = ast.get_docstring(node)
                if not docstring:
                    suggestions.append(
                        {
                            "rule_id": "missing_docstring",
                            "message": f"Função '{node.name}' deveria conter docstring.",
                            "severity": "info",
                            "line": node.lineno,
                            "column": None,
                            "metadata": {},
                        }
                    )

    def _check_print_statements(
        self, tree: ast.AST, suggestions: List[Dict[str, Any]]
    ) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    suggestions.append(
                        {
                            "rule_id": "print_statement",
                            "message": "Considere utilizar logging em vez de print para saída em produção.",
                            "severity": "info",
                            "line": getattr(node, "lineno", None),
                            "column": getattr(node, "col_offset", None),
                            "metadata": {},
                        }
                    )
