"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="analytics-service")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # PostgreSQL
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="energy_platform")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_pool_size: int = Field(default=10)
    
    # AWS S3
    s3_bucket_name: str = Field(default="energy-platform-datasets")
    s3_region: str = Field(default="us-east-1")
    s3_access_key_id: str = Field(default="")
    s3_secret_access_key: str = Field(default="")
    
    # ML Configuration
    default_train_test_split: float = Field(default=0.8)
    max_dataset_size_mb: int = Field(default=500)
    supported_models: List[str] = Field(
        default=[
            "isolation_forest",
            "autoencoder",
            "random_forest",
            "gradient_boosting",
            "prophet",
            "arima",
        ]
    )
    
    # Job Worker
    max_concurrent_jobs: int = Field(default=3)
    job_timeout_seconds: int = Field(default=3600)
    
    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL DSN."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def postgres_sync_dsn(self) -> str:
        """Build synchronous PostgreSQL DSN for migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
