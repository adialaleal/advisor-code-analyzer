from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_analysis_service,
    get_cache_service,
    get_code_analyzer,
    get_db,
)
from app.config import Settings, get_settings
from app.crewai_integration.agent import AdvisorCrewIntegration
from app.models.schemas import (
    CodeAnalysisRequest,
    CodeAnalysisResponse,
    LLMAnalysisResponse,
    Suggestion,
)
from app.services.analysis_service import CodeAnalysisService
from app.services.cache_service import CacheService
from app.services.code_analyzer import CodeAnalyzer


router = APIRouter()


@router.post(
    "/analyze-code", response_model=CodeAnalysisResponse, status_code=status.HTTP_200_OK
)
def analyze_code(
    payload: CodeAnalysisRequest,
    analysis_service: CodeAnalysisService = Depends(get_analysis_service),
) -> CodeAnalysisResponse:
    """Analyze code with caching and persistence."""
    result = analysis_service.analyze_code(
        code=payload.code,
        language_version=payload.language_version,
    )
    return CodeAnalysisResponse(**result)


@router.get("/health")
def healthcheck(
    db: Session = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
    settings: Settings = Depends(get_settings),
) -> Dict[str, str]:
    status_map: Dict[str, str] = {"status": "ok"}

    try:
        db.execute(text("SELECT 1"))
        status_map["database"] = "ok"
    except SQLAlchemyError as exc:
        status_map["database"] = "error"
        status_map["status"] = "degraded"
        status_map["database_error"] = str(exc)

    status_map["cache"] = "ok" if cache.is_available() else "fallback"
    status_map["model_provider"] = settings.model_provider

    return status_map


@router.post(
    "/analyze-code-llm",
    response_model=LLMAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_code_with_llm(
    payload: CodeAnalysisRequest,
    analyzer: CodeAnalyzer = Depends(get_code_analyzer),
    settings: Settings = Depends(get_settings),
    analysis_service: CodeAnalysisService = Depends(get_analysis_service),
) -> LLMAnalysisResponse:
    """
    Analisa código Python usando CrewAI com LLM para gerar relatório priorizado.
    Este endpoint simula a integração do agente com a plataforma CrewAI.
    """
    import hashlib
    import time

    start = time.perf_counter()
    code_hash = hashlib.sha256(payload.code.encode("utf-8")).hexdigest()

    # Integração com CrewAI
    integration = AdvisorCrewIntegration(settings, analyzer)
    workflow = integration.build_sample_workflow()

    # Executa o workflow CrewAI com proteção de erros para evitar 500
    try:
        result = workflow["crew"].kickoff(inputs={"code_snippet": payload.code})
        report = str(result) if result else "Nenhuma recomendação adicional."
    except Exception as exc:  # pragma: no cover - robustez em runtime
        report = f"LLM execution failed: {exc}"

    # Obtém as sugestões brutas do analisador e persiste no banco
    raw_result = analyzer.analyze(payload.code)
    raw_suggestions = [Suggestion(**item) for item in raw_result.suggestions]

    # Persiste a análise no banco de dados usando o serviço de análise
    analysis_service.analyze_code(
        code=payload.code,
        language_version=payload.language_version,
        use_cache=False,  # Não usar cache para análise com LLM
        persist=True,
    )

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    # Extrai o modelo usado
    model_info = workflow.get("model", {})
    model_used = model_info.get("provider", "unknown")

    return LLMAnalysisResponse(
        code_hash=code_hash,
        raw_suggestions=raw_suggestions,
        prioritized_report=report,
        model_used=model_used,
        analysis_time_ms=elapsed_ms,
        cached=False,
    )
