from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.database import AnalysisHistory


class AnalysisHistoryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code_hash(self, code_hash: str) -> Optional[AnalysisHistory]:
        return (
            self.session.query(AnalysisHistory)
            .filter(AnalysisHistory.code_hash == code_hash)
            .order_by(AnalysisHistory.created_at.desc())
            .first()
        )

    def create(
        self,
        *,
        code_hash: str,
        code_snippet: Optional[str],
        suggestions: list[dict[str, Any]],
        analysis_time_ms: Optional[int],
        language_version: Optional[str],
    ) -> AnalysisHistory:
        record = AnalysisHistory(
            code_hash=code_hash,
            code_snippet=code_snippet,
            suggestions=suggestions,
            analysis_time_ms=analysis_time_ms,
            language_version=language_version,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

