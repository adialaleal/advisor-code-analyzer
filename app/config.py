from functools import lru_cache
from typing import Any, Dict, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    model_provider: str = Field("openai", alias="MODEL_PROVIDER")
    model_name: Optional[str] = Field(None, alias="MODEL_NAME")
    request_timeout: int = Field(30, alias="REQUEST_TIMEOUT")
    
    # Optional API keys - users can configure any or all of these
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    claude_api_key: Optional[str] = Field(None, alias="CLAUDE_API_KEY")
    azure_openai_api_key: Optional[str] = Field(None, alias="AZURE_OPENAI_API_KEY")
    azure_endpoint: Optional[str] = Field(None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_endpoint: Optional[str] = Field(None, alias="AZURE_ENDPOINT")  # Alternative name
    deployment_name: Optional[str] = Field(None, alias="AZURE_OPENAI_DEPLOYMENT")

    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, v: str) -> str:
        return v.lower()

    def get_api_key(self) -> Optional[str]:
        """
        Get the appropriate API key for the configured provider.
        Supports: google_api_key, openai_api_key, anthropic_api_key, azure_openai_api_key, etc.
        """
        provider_lower = self.model_provider.lower().replace("-", "_").replace(".", "_")
        
        # Try provider-specific key first (e.g., GOOGLE_API_KEY for gemini)
        provider_key = getattr(self, f"{provider_lower}_api_key", None)
        if provider_key:
            return provider_key
        
        # Try common aliases for this provider
        provider_aliases = {
            "openai": ["openai_api_key"],
            "gemini": ["google_api_key", "gemini_api_key"],
            "anthropic": ["anthropic_api_key", "claude_api_key"],
            "azure_openai": ["azure_openai_api_key"],
        }
        
        aliases = provider_aliases.get(provider_lower, [])
        for alias in aliases:
            key_value = getattr(self, alias.lower(), None)
            if key_value:
                return key_value
        
        return None
    
    def get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration with all env vars available."""
        provider_lower = self.model_provider.lower().replace("-", "_").replace(".", "_")
        
        config = {
            "model_name": self.model_name,
            "api_key": self.get_api_key(),
        }
        
        # Add provider-specific configs from env
        if provider_lower == "azure_openai":
            azure_endpoint = getattr(self, "azure_endpoint", None) or getattr(self, "azure_openai_endpoint", None)
            deployment_name = getattr(self, "deployment_name", None) or getattr(self, "azure_openai_deployment", None)
            if azure_endpoint:
                config["azure_endpoint"] = azure_endpoint
            if deployment_name:
                config["deployment_name"] = deployment_name
        
        elif provider_lower in ("gemini", "google"):
            # Gemini needs GOOGLE_API_KEY in environment
            google_key = getattr(self, "google_api_key", None) or getattr(self, "gemini_api_key", None)
            if google_key and config["api_key"] != google_key:
                config["google_api_key"] = google_key
        
        # Pass through any other provider-specific config from env
        # This allows users to add any arbitrary config via env vars
        return config
    
    def get_extra_config(self, key: str, default: Any = None) -> Any:
        """Get any additional configuration from environment variables."""
        key_lower = key.lower()
        return getattr(self, key_lower, default)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
