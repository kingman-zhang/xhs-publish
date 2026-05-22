from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongo_url: str = Field(..., alias="MONGO_URL")
    mongo_db_name: str = Field(..., alias="MONGO_DB_NAME")
    public_base_url: str = Field(..., alias="PUBLIC_BASE_URL")
    upload_dir: Path = Field(default=Path(__file__).resolve().parents[1] / "uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    xhs_app_key: str = Field(default="", alias="XHS_APP_KEY")
    xhs_app_secret: str = Field(default="", alias="XHS_APP_SECRET")
    xhs_access_token_url: str = Field(
        default="https://edith.xiaohongshu.com/api/sns/v1/ext/access/token",
        alias="XHS_ACCESS_TOKEN_URL",
    )
    xhs_request_timeout_ms: int = Field(default=5000, alias="XHS_REQUEST_TIMEOUT_MS")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
