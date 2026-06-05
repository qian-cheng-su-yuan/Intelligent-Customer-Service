from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    dashscope_api_key: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="qwen-plus", validation_alias="LLM_MODEL")
    database_path: Path = Field(default=Path("data/customer_service.db"), validation_alias="DATABASE_PATH")
    refund_review_threshold: float = Field(default=500.0, validation_alias="REFUND_REVIEW_THRESHOLD")

    @property
    def api_key(self) -> str:
        return self.llm_api_key or self.dashscope_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
