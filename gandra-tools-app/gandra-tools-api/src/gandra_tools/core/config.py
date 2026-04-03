"""Application configuration via Pydantic BaseSettings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    env: str = "local"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Default user
    default_user_email: str = "dragan.mijatovic@cramick-it.com"
    default_user_password: str = "topsecret"

    # LLM defaults
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4o"

    # BYOK API keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Database
    database_url: str = "sqlite+aiosqlite:///./gandra_tools.db"

    # Output
    output_default_dir: str = "gandra-output/"

    # Server
    host: str = "0.0.0.0"
    port: int = 8095
    allowed_origins: str = "http://localhost:3001,http://localhost:8095"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def output_path(self) -> Path:
        return Path(self.output_default_dir)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
