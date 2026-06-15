"""Конфигурация приложения, читается из переменных окружения / .env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Общее
    warn_days: int = 3
    digest_hour: int = 9
    database_url: str = "sqlite:///./data/holodilnik.db"

    # Telegram
    telegram_token: str = ""
    telegram_chat_id: str = ""

    # OpenRouter (vision)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_vision_model: str = "qwen/qwen-2-vl-7b-instruct"

    # Groq (STT)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_stt_model: str = "whisper-large-v3-turbo"

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_token and self.telegram_chat_id)

    @property
    def vision_enabled(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def stt_enabled(self) -> bool:
        return bool(self.groq_api_key)


settings = Settings()
