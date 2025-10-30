from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Suggestion(BaseModel):
    rule_id: str = Field(..., description="Identificador da regra aplicada")
    message: str = Field(..., description="Mensagem de sugestão")
    severity: Literal["info", "warning", "error"] = Field(
        "info", description="Nível de severidade"
    )
    line: Optional[int] = Field(None, description="Número da linha afetada")
    column: Optional[int] = Field(None, description="Número da coluna afetada")
    metadata: dict[str, Any] = Field(default_factory=dict)


class CodeAnalysisRequest(BaseModel):
    code: str = Field(
        ..., min_length=1, description="Trecho de código Python a ser analisado"
    )
    language_version: Optional[str] = Field(
        None, description="Versão do Python utilizada pelo código"
    )


class CodeAnalysisResponse(BaseModel):
    code_hash: str
    suggestions: list[Suggestion]
    analysis_time_ms: int
    cached: bool = False


class LLMAnalysisResponse(BaseModel):
    code_hash: str
    raw_suggestions: list[Suggestion]
    prioritized_report: str
    model_used: str
    analysis_time_ms: int
    cached: bool = False


class AnalysisHistoryRead(BaseModel):
    id: str
    code_hash: str
    code_snippet: Optional[str]
    suggestions: list[Suggestion]
    analysis_time_ms: Optional[int]
    language_version: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

