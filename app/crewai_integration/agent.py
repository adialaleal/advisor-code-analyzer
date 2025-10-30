from __future__ import annotations

import json
import hashlib
from typing import Any, Dict

from app.config import Settings
from app.crewai_integration.model_provider import ModelProviderFactory
from app.services.code_analyzer import CodeAnalyzer

try:
    from crewai import Agent, Crew, Process, Task, LLM as CrewLLM
    from crewai.tools import tool
except ImportError:  # pragma: no cover - fallback em ambientes sem CrewAI instalado
    Agent = Crew = Process = Task = None  # type: ignore[assignment]

    def tool(*_args: Any, **_kwargs: Any):  # type: ignore
        def decorator(func):
            return func

        return decorator


class CrewAIIntegrationError(RuntimeError):
    pass


def create_analyze_tool(analyzer: CodeAnalyzer) -> Any:
    """
    Create a CrewAI tool that uses the provided analyzer.

    Args:
        analyzer: The code analyzer instance to use

    Returns:
        A CrewAI tool function
    """
    @tool("analyze_python_code")
    def analyze_python_code(code_snippet: str) -> str:
        """
        Analisa um trecho de código Python e retorna sugestões de melhoria em formato JSON.

        Args:
            code_snippet: O código Python a ser analisado.

        Returns:
            Um JSON com code_hash, suggestions e analysis_time_ms.
        """
        result = analyzer.analyze(code_snippet)
        code_hash = hashlib.sha256(code_snippet.encode("utf-8")).hexdigest()
        payload = {
            "code_hash": code_hash,
            "suggestions": result.suggestions,
            "analysis_time_ms": result.analysis_time_ms,
        }
        return json.dumps(payload, ensure_ascii=False)

    return analyze_python_code


class AdvisorCrewIntegration:
    def __init__(self, settings: Settings, analyzer: CodeAnalyzer) -> None:
        self.settings = settings
        self.analyzer = analyzer
        self.model_provider = ModelProviderFactory.from_settings(settings)

    def build_agent(self) -> Agent:
        if Agent is None:
            raise CrewAIIntegrationError(
                "Biblioteca CrewAI não está disponível. Instale crewai para utilizar esta integração."
            )

        llm_config = self.model_provider.get_llm_config()
        # Constrói a instância do LLM diretamente para evitar passar dict como "model"
        # Ex.: {"model": "gemini/gemini-2.0-flash", ...}
        llm_instance = CrewLLM(**llm_config)

        # Create tool with injected analyzer
        analyze_tool = create_analyze_tool(self.analyzer)

        return Agent(
            role="Code Optimization Advisor",
            goal=(
                "Avaliar trechos de código Python e fornecer recomendações práticas de melhoria "
                "seguindo boas práticas e PEP 8."
            ),
            backstory=(
                "Engenheiro de software experiente focado em revisão de código, com conhecimento "
                "em design patterns, performance e mantenabilidade."
            ),
            allow_delegation=False,
            llm=llm_instance,
            tools=[analyze_tool],
        )

    def build_sample_workflow(self) -> Dict[str, Any]:
        if Agent is None or Crew is None or Task is None or Process is None:
            raise CrewAIIntegrationError(
                "Biblioteca CrewAI não está disponível. Instale crewai para utilizar esta integração."
            )

        agent = self.build_agent()

        task = Task(
            description=(
                "Sempre responda em Português Brasileiro"
                "Receba um trecho de código Python, invoque a tool 'analyze_python_code' e sintetize "
                "as principais oportunidades de melhoria em formato de lista priorizada."
            ),
            expected_output=(
                "Uma lista priorizada contendo até 5 recomendações de melhoria, cada uma com "
                "justificativa e impacto esperado."
            ),
            agent=agent,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        return {
            "crew": crew,
            "instructions": "Execute crew.kickoff(inputs={'code_snippet': '<trecho_a_ser_analisado>'})",
            "model": self.model_provider.get_observability_metadata(),
        }
