"""
TwinSpark Chronicles - Configuration Management

Centralized configuration using pydantic settings for type safety and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google AI API
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")
    google_project_id: str = Field(default="", env="GOOGLE_PROJECT_ID")
    
    # Application
    app_env: Literal["development", "production"] = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(default="sqlite:///./twinpark.db", env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    # Feature Flags
    enable_video_generation: bool = Field(default=True, env="ENABLE_VIDEO_GENERATION")
    enable_emotion_detection: bool = Field(default=True, env="ENABLE_EMOTION_DETECTION")
    enable_dual_perspective: bool = Field(default=True, env="ENABLE_DUAL_PERSPECTIVE")
    
    # Story Settings
    max_story_length: int = Field(default=20, env="MAX_STORY_LENGTH")
    default_age_group: int = Field(default=6, env="DEFAULT_AGE_GROUP")
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # Safety
    enable_content_filter: bool = Field(default=True, env="ENABLE_CONTENT_FILTER")
    store_video_locally: bool = Field(default=True, env="STORE_VIDEO_LOCALLY")
    enable_analytics: bool = Field(default=False, env="ENABLE_ANALYTICS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
