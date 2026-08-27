"""
Centralized application settings, loaded from environment variables / .env.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = "sqlite:///./rexplore.db"
    max_upload_mb: int = 50
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    kaggle_username: str = ""
    kaggle_key: str = ""
    tesseract_cmd: str = ""
    external_api_timeout: int = 12

    # Authentication
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    upload_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    generated_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated")
    index_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "indexes")

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self):
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> "Settings":
    settings = Settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.generated_dir, exist_ok=True)
    os.makedirs(settings.index_dir, exist_ok=True)
    return settings
