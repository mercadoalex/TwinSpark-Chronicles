"""
TwinSpark Chronicles - Configuration Management

Centralized configuration using pydantic settings for type safety and validation.
Supports both local development and GCP Cloud SQL production deployment.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google AI API
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_project_id: str = Field(default="", alias="GOOGLE_PROJECT_ID")
    
    # Hugging Face API
    huggingface_api_key: str = Field(default="", alias="HUGGINGFACE_API_KEY")
    
    # Application
    app_env: Literal["development", "production"] = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    
    # Database - supports SQLite (dev) and PostgreSQL (prod)
    database_url: str = Field(default="sqlite:///./data/twinspark.db", alias="DATABASE_URL")
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    
    # Cloud SQL specific (GCP)
    use_cloud_sql_proxy: bool = Field(default=False, alias="USE_CLOUD_SQL_PROXY")
    db_connection_name: str = Field(default="", alias="DB_CONNECTION_NAME")  # project:region:instance
    db_name: str = Field(default="twinspark", alias="DB_NAME")
    db_user: str = Field(default="twinspark_app", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    
    # Cloud Storage (GCP)
    gcs_bucket: str = Field(default="", alias="GCS_BUCKET")  # For family photos, voice recordings
    gcs_project_id: str = Field(default="", alias="GCS_PROJECT_ID")
    use_cloud_storage: bool = Field(default=False, alias="USE_CLOUD_STORAGE")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    
    # Feature Flags
    enable_video_generation: bool = Field(default=True, alias="ENABLE_VIDEO_GENERATION")
    enable_emotion_detection: bool = Field(default=True, alias="ENABLE_EMOTION_DETECTION")
    enable_dual_perspective: bool = Field(default=True, alias="ENABLE_DUAL_PERSPECTIVE")
    
    # Story Settings
    max_story_length: int = Field(default=20, alias="MAX_STORY_LENGTH")
    default_age_group: int = Field(default=6, alias="DEFAULT_AGE_GROUP")
    session_timeout_minutes: int = Field(default=30, alias="SESSION_TIMEOUT_MINUTES")
    
    # Safety
    enable_content_filter: bool = Field(default=True, alias="ENABLE_CONTENT_FILTER")
    store_video_locally: bool = Field(default=True, alias="STORE_VIDEO_LOCALLY")
    enable_analytics: bool = Field(default=False, alias="ENABLE_ANALYTICS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
