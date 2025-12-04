"""
Application Configuration

All settings are defined here with defaults. You can:
1. Modify values directly in this file
2. Override via environment variables (optional)
3. Create a .env file (optional)

No environment variables are required - everything has defaults.
"""

from pydantic_settings import BaseSettings
from typing import List, Union, Optional
from pydantic import field_validator
from pathlib import Path
import os

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL: str = "sqlite:///./interview.db"
    
    # ============================================
    # PINECONE VECTOR DB CONFIGURATION
    # ============================================
    # Set your Pinecone API key here (or via env variable)
    PINECONE_API_KEY: str = ""  # TODO: Set your Pinecone API key here 
    PINECONE_ENVIRONMENT: str = "us-east-1"  # or "us-west1" depending on your index
    PINECONE_INDEX_NAME: str = "resumes"
    PINECONE_DIMENSION: int = 1024  # Dimension for Qwen3-Embedding-0.6B (will be auto-detected)
    
    # ============================================
    # EMBEDDING MODEL CONFIGURATION (Local Qwen)
    # ============================================
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"  # Local Qwen embedding model
    EMBEDDING_DIMENSION: int = 1024  # Dimension for Qwen3-Embedding-0.6B (will be auto-detected)
    
    # ============================================
    # HUGGING FACE API CONFIGURATION (Question Agent)
    # ============================================
    # Optional: Only needed if using HuggingFace API for question generation
    # If empty, the system will use local models instead
    HUGGINGFACE_API_URL: str = ""  # TODO: Set your HuggingFace API URL here if needed
    HUGGINGFACE_API_KEY: str = ""  # TODO: Set your HuggingFace API key here if needed
    
    # ============================================
    # LOCAL LLM MODEL CONFIGURATION
    # ============================================
    LOCAL_LLM_MODEL: str = "Qwen/Qwen3-0.6B"  # Local Qwen model for text generation
    
    # ============================================
    # OPENAI API (DEPRECATED - No longer used)
    # ============================================
    # Kept for backward compatibility only
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # ============================================
    # FILE STORAGE CONFIGURATION
    # ============================================
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"  # TODO: Change this in production!
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001"
    
    # ============================================
    # JWT AUTHENTICATION CONFIGURATION
    # ============================================
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins string into list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    class Config:
        # Optional: Load from .env if it exists, but don't require it
        env_file = str(BACKEND_DIR / ".env") if (BACKEND_DIR / ".env").exists() else None
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars without validation errors


settings = Settings()
