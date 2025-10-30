from app.models.database import AnalysisHistory
from app.services.database_service import AnalysisHistoryService


def test_create_and_get_analysis_history(db_session) -> None:
    service = AnalysisHistoryService(db_session)

    suggestions = [
        {
            "rule_id": "test_rule",
            "message": "Mensagem",
            "severity": "info",
            "line": 1,
            "column": None,
            "metadata": {},
        }
    ]

    created = service.create(
        code_hash="hash",
        code_snippet="print('hello')",
        suggestions=suggestions,
        analysis_time_ms=5,
        language_version="3.11",
    )

    assert created.id is not None
    assert created.code_hash == "hash"

    fetched = service.get_by_code_hash("hash")
    assert fetched is not None
    assert fetched.id == created.id
    assert len(db_session.query(AnalysisHistory).all()) == 1

