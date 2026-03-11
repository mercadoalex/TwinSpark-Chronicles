"""
TwinSpark Chronicles - Configuration Management

Centralized configuration using pydantic settings for type safety and validation.
Supports both local development and GCP Cloud SQL production deployment.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys - UPPERCASE
    GOOGLE_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    REPLICATE_API_KEY: str = "" 
    FAL_API_KEY: str = ""
    LEONARDO_API_KEY: str = ""
    
    # Google Cloud
    GOOGLE_PROJECT_ID: Optional[str] = None
    
    # Application Settings - UPPERCASE
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"  # UPPERCASE
    
    # Database & Cache
    DATABASE_URL: Optional[str] = "sqlite:///./twinpark.db"
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    
    # Story Generation
    MAX_STORY_LENGTH: int = 500
    ENABLE_IMAGE_GENERATION: bool = True
    ENABLE_VIDEO_GENERATION: bool = True
    ENABLE_AUDIO: bool = False
    ENABLE_EMOTION_DETECTION: bool = True
    ENABLE_DUAL_PERSPECTIVE: bool = True
    
    # Session Settings
    DEFAULT_AGE_GROUP: int = 6
    SESSION_TIMEOUT_MINUTES: int = 30
    
    # Content & Safety
    ENABLE_CONTENT_FILTER: bool = True
    
    # Storage
    STORE_VIDEO_LOCALLY: bool = True
    
    # Analytics & Testing
    ENABLE_ANALYTICS: bool = False
    USE_MOCK_STORIES: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow both upper and lowercase
        extra = "allow"


# Global settings instance
settings = Settings()
