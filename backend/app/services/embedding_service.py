"""
Embedding Service using Qwen3-Embedding-0.6B

This service generates embeddings using a local SentenceTransformer model.
"""

from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    """Service for generating embeddings using local Qwen model"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not EmbeddingService._initialized:
            self._model = None
            self.model_name = settings.EMBEDDING_MODEL
            EmbeddingService._initialized = True
    
    def _ensure_loaded(self):
        """Lazy load the model only when needed"""
        if self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(f"Embedding model loaded")
    
    @property
    def model(self):
        self._ensure_loaded()
        return self._model
    
    @property
    def dimension(self):
        """Return embedding dimension"""
        self._ensure_loaded()
        return self._model.get_sentence_embedding_dimension()
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        self._ensure_loaded()
        embedding = self._model.encode(text)
        return embedding.tolist()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        self._ensure_loaded()
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    
    def embed_text_sync(self, text: str) -> List[float]:
        """
        Synchronous version for embedding (blocking)
        Used when async is not available
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        self._ensure_loaded()
        embedding = self._model.encode(text)
        return embedding.tolist()
    
    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous batch embedding
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        self._ensure_loaded()
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]


embedding_service = EmbeddingService()
