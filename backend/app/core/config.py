"""
Application Configuration

All settings are loaded from environment variables (.env file).
This keeps sensitive data out of version control.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union, Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Create a .env file in the backend directory with all required values.
    """
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL: str
    
    # ============================================
    # PINECONE VECTOR DB CONFIGURATION
    # ============================================
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str
    PINECONE_DIMENSION: int
    
    # ============================================
    # EMBEDDING MODEL CONFIGURATION
    # ============================================
    EMBEDDING_MODEL: str
    EMBEDDING_DIMENSION: int
    
    # ============================================
    # HUGGING FACE API CONFIGURATION
    # ============================================
    HUGGINGFACE_API_URL: str
    HUGGINGFACE_API_KEY: str
    
    HUGGINGFACE_LLM_API_URL: str
    HUGGINGFACE_LLM_API_KEY: str
    
    HUGGINGFACE_EMBEDDING_API_URL: str
    HUGGINGFACE_EMBEDDING_API_KEY: str
    
    HUGGINGFACE_EVALUATION_API_URL: str
    HUGGINGFACE_EVALUATION_API_KEY: str
    
    # ============================================
    # LOCAL LLM MODEL CONFIGURATION
    # ============================================
    LOCAL_LLM_MODEL: str
    
    # ============================================
    # OPENAI API CONFIGURATION
    # ============================================
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    
    # ============================================
    # FILE STORAGE CONFIGURATION
    # ============================================
    UPLOAD_DIR: str
    MAX_FILE_SIZE: int
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    DEBUG: bool
    SECRET_KEY: str
    CORS_ORIGINS: Union[str, List[str]]
    
    # ============================================
    # JWT AUTHENTICATION CONFIGURATION
    # ============================================
    JWT_ALGORITHM: str
    JWT_EXPIRATION_HOURS: int
    
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins string into list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Create settings instance - loads from .env file automatically
settings = Settings()
