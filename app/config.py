from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    crewai_api_key: Optional[str] = Field(None, alias="CREWAI_API_KEY")
    model_provider: Literal["openai", "gemini", "anthropic", "azure_openai"] = Field(
        "openai", alias="MODEL_PROVIDER"
    )
    model_name: Optional[str] = Field(None, alias="MODEL_NAME")
    azure_endpoint: Optional[str] = Field(None, alias="AZURE_OPENAI_ENDPOINT")
    deployment_name: Optional[str] = Field(None, alias="AZURE_OPENAI_DEPLOYMENT")
    request_timeout: int = Field(30, alias="REQUEST_TIMEOUT")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
