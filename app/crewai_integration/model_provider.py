from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.config import Settings


class BaseModelProvider(ABC):
    provider_name: str

    def __init__(
        self, *, model_name: Optional[str], api_key: Optional[str], **extra: Any
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.extra = extra
        self.validate()

    def validate(self) -> None:
        if not self.api_key:
            raise ValueError(
                f"Chave de API não configurada para o provedor {self.provider_name}. Defina CREWAI_API_KEY ou variável específica."
            )

    @abstractmethod
    def get_llm_config(self) -> Dict[str, Any]:
        """Retorna a configuração utilizada pelo CrewAI para instanciar o LLM."""

    def get_observability_metadata(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
        }


class OpenAIModelProvider(BaseModelProvider):
    provider_name = "openai"

    def get_llm_config(self) -> Dict[str, Any]:
        model = self.model_name or "gpt-4o-mini"
        return {
            "provider": self.provider_name,
            "config": {
                "model": model,
                "api_key": self.api_key,
                **self.extra,
            },
        }


class GeminiModelProvider(BaseModelProvider):
    provider_name = "gemini"

    def get_llm_config(self) -> Dict[str, Any]:
        model = self.model_name or "gemini-2.0-flash"

        # CrewAI (via LiteLLM) espera apenas um dict simples com 'model'
        # e usa GOOGLE_API_KEY do ambiente para autenticação do Gemini.
        google_api_key = self.extra.get("google_api_key", self.api_key)
        os.environ["GOOGLE_API_KEY"] = google_api_key

        # Retorne somente o que o Agent aceita como llm config: {'model': 'gemini/<model>'}
        # Sem o wrapper provider/config.
        return {
            "model": f"gemini/{model}",
            "api_key": google_api_key,
            "litellm_params": {"custom_llm_provider": "gemini"},
        }


class AnthropicModelProvider(BaseModelProvider):
    provider_name = "anthropic"

    def get_llm_config(self) -> Dict[str, Any]:
        model = self.model_name or "claude-3-sonnet-20240229"
        return {
            "provider": self.provider_name,
            "config": {
                "model": model,
                "api_key": self.api_key,
                **self.extra,
            },
        }


class AzureOpenAIModelProvider(BaseModelProvider):
    provider_name = "azure_openai"

    def get_llm_config(self) -> Dict[str, Any]:
        if not self.extra.get("azure_endpoint"):
            raise ValueError(
                "É necessário informar 'azure_endpoint' para usar Azure OpenAI."
            )
        model = self.model_name or self.extra.get("deployment_name")
        if not model:
            raise ValueError("Informe MODEL_NAME ou deployment_name para Azure OpenAI.")
        return {
            "provider": self.provider_name,
            "config": {
                "api_key": self.api_key,
                "azure_endpoint": self.extra["azure_endpoint"],
                "deployment_name": model,
                **self.extra,
            },
        }


class ModelProviderFactory:
    provider_map = {
        "openai": OpenAIModelProvider,
        "gemini": GeminiModelProvider,
        "anthropic": AnthropicModelProvider,
        "azure_openai": AzureOpenAIModelProvider,
    }

    @classmethod
    def from_settings(cls, settings: Settings) -> BaseModelProvider:
        provider_name = settings.model_provider.lower()
        provider_cls = cls.provider_map.get(provider_name)
        if not provider_cls:
            raise ValueError(
                f"Provedor de modelo '{settings.model_provider}' não suportado."
            )

        extra = {}
        if provider_name == "gemini":
            extra["google_api_key"] = settings.crewai_api_key
        if provider_name == "azure_openai":
            extra.update(
                {
                    "azure_endpoint": getattr(settings, "azure_endpoint", None),
                    "deployment_name": getattr(settings, "deployment_name", None),
                }
            )

        return provider_cls(
            model_name=settings.model_name, api_key=settings.crewai_api_key, **extra
        )
