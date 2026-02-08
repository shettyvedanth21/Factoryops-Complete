"""Configuration settings for the Reporting Service.

This module loads configuration from environment variables
and provides typed settings for the application.
"""

from typing import List, Optional
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Service Configuration
    service_name: str = Field(default="reporting-service", alias="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", alias="SERVICE_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8085, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: str = Field(default="energy-platform-datasets", alias="S3_BUCKET_NAME")
    s3_prefix: str = Field(default="datasets", alias="S3_PREFIX")
    
    # PostgreSQL Configuration (for analytics results)
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="energy_platform", alias="POSTGRES_DB")
    postgres_pool_size: int = Field(default=10, alias="POSTGRES_POOL_SIZE")
    
    # Report Generation Settings
    max_report_size_mb: int = Field(default=100, alias="MAX_REPORT_SIZE_MB")
    default_page_size: int = Field(default=1000, alias="DEFAULT_PAGE_SIZE")
    report_timeout_seconds: int = Field(default=300, alias="REPORT_TIMEOUT_SECONDS")
    cleanup_interval_seconds: int = Field(default=3600, alias="CLEANUP_INTERVAL_SECONDS")
    
    # Temporary Storage
    temp_dir: str = Field(default="/tmp/reports", alias="TEMP_DIR")
    
    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def postgres_async_url(self) -> str:
        """Build async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


# Global settings instance
settings = Settings()