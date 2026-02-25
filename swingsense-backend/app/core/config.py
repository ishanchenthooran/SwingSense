from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/swingsense"
    OPENAI_API_KEY: str = ""
    SUPABASE_JWKS_URL: str = ""
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()


def debug_print_settings() -> None:
    has_openai_key = bool(settings.OPENAI_API_KEY)
    print(f"OPENAI_API_KEY set: {has_openai_key}")
