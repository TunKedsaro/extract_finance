from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or ``.env``."""

    app_name: str = "Financial Statement Extraction API"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    input_dir: Path = Path("resources/input")
    output_dir: Path = Path("outputs")
    save_output: bool = True
    max_input_file_size_bytes: int = 20 * 1024 * 1024
    max_llm_request_size_bytes: int = 30 * 1024 * 1024

    litellm_proxy_url: str | None = None
    litellm_master_key: str | None = None
    anthropic_base_url: str | None = None
    anthropic_auth_token: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def input_directory(self) -> Path:
        return self._absolute_from_project_root(self.input_dir)

    @property
    def output_directory(self) -> Path:
        return self._absolute_from_project_root(self.output_dir)

    @staticmethod
    def _absolute_from_project_root(path: Path) -> Path:
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
