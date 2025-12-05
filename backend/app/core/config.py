"""
Application Configuration

All settings are defined here directly in this file.
Modify the values below to configure your application.
No .env file or environment variables needed.
"""

from pydantic import BaseModel, field_validator
from typing import List, Union, Optional


class Settings(BaseModel):
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL: str = "sqlite:///./interview.db"
    
    # ============================================
    # PINECONE VECTOR DB CONFIGURATION
    # ============================================
    # Set your Pinecone API key here (or via env variable)

    PINECONE_API_KEY: str = "pcsk_4bYQVD_CnMZXDcLUXPxycHYqiLdd1H75HcTKpXast41tp2GHyGnUkeJykT15372BhHvKVo"  # TODO: Set your Pinecone API key here 
    PINECONE_ENVIRONMENT: str = "us-east-1"  # or "us-west1" depending on your index
    PINECONE_INDEX_NAME: str = "resumes"
    PINECONE_DIMENSION: int = 1024  # Dimension for Qwen3-Embedding-0.6B (will be auto-detected)
    
    # ============================================
    # EMBEDDING MODEL CONFIGURATION
    # ============================================
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"  # Only used if HF API not configured
    EMBEDDING_DIMENSION: int = 1024  # Dimension for embeddings (will be auto-detected)
    
    # ============================================
    # HUGGING FACE API CONFIGURATION
    # ============================================
    # Question generation model (fine-tuned for interview questions)
    HUGGINGFACE_API_URL: str = ""  # TODO: Set your HF endpoint for question generation
    HUGGINGFACE_API_KEY: str = ""  # TODO: Set your HF API key
    
    # LLM API (for evaluation, cleaning, orchestrator, etc.)
    HUGGINGFACE_LLM_API_URL: str = ""  # TODO: Set your HF endpoint for LLM
    HUGGINGFACE_LLM_API_KEY: str = ""  # TODO: Set your HF API key
    
    # Embedding API
    HUGGINGFACE_EMBEDDING_API_URL: str = ""  # TODO: Set your HF endpoint for embeddings
    HUGGINGFACE_EMBEDDING_API_KEY: str = ""  # TODO: Set your HF API key
    
    # ============================================
    # LOCAL LLM MODEL CONFIGURATION (Deprecated - using HF API instead)
    # ============================================
    LOCAL_LLM_MODEL: str = "Qwen/Qwen3-0.6B"  # Only used if HF API not configured
    
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
    

# Create settings instance - all configuration is in this file
settings = Settings()
