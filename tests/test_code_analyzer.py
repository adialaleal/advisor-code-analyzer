from app.services.code_analyzer import CodeAnalyzer


def test_analyze_handles_syntax_errors() -> None:
    analyzer = CodeAnalyzer()

    result = analyzer.analyze("def broken(:\n    pass")

    assert len(result.suggestions) == 1
    suggestion = result.suggestions[0]
    assert suggestion["rule_id"] == "syntax_error"
    assert suggestion["severity"] == "error"


def test_analyze_detects_style_issues() -> None:
    analyzer = CodeAnalyzer()

    code = """
import math


def CamelCaseFunction():
    unused_var = 10
    print("hello")
    return 42
"""

    result = analyzer.analyze(code)
    rule_ids = {item["rule_id"] for item in result.suggestions}

    assert "unused_import" in rule_ids
    assert "unused_variable" in rule_ids
    assert "function_naming" in rule_ids
    assert "print_statement" in rule_ids
    assert "missing_docstring" in rule_ids

