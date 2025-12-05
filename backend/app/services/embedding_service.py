"""
Embedding Service using Hugging Face API

This service generates embeddings using Hugging Face Inference API
for faster inference compared to local models.
"""

from typing import List
import httpx
from app.core.config import settings


class EmbeddingService:
    """Service for generating embeddings using Hugging Face API"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not EmbeddingService._initialized:
            self.api_url = settings.HUGGINGFACE_EMBEDDING_API_URL
            self.api_key = settings.HUGGINGFACE_EMBEDDING_API_KEY
            self.use_api = bool(self.api_url and self.api_key)
            
            # Fallback to local model if API not configured
            if not self.use_api:
                print("Warning: Hugging Face Embedding API not configured. Will attempt to load local model.")
                self.model_name = settings.EMBEDDING_MODEL
            self._model = None
            
            self._dimension = settings.EMBEDDING_DIMENSION
            EmbeddingService._initialized = True
    
    def _ensure_loaded(self):
        """Lazy load the local model only when needed (fallback)"""
        if not self.use_api and self._model is None:
            print(f"Loading embedding model: {self.model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                print(f"Embedding model loaded (dimension: {self._dimension})")
            except Exception as e:
                print(f"Failed to load local embedding model: {e}")
                raise
    
    @property
    def dimension(self):
        """Return embedding dimension"""
        if self.use_api:
            return self._dimension
        else:
            self._ensure_loaded()
            return self._dimension
    
    async def _embed_api(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Hugging Face API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # HF embedding API expects {"inputs": text or list of texts}
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={"inputs": texts}
            )
            response.raise_for_status()
            embeddings = response.json()
            
            # Handle different response formats
            # Format 1: Direct list of embeddings [[...], [...]]
            if isinstance(embeddings, list) and len(embeddings) > 0:
                if isinstance(embeddings[0], list):
                    return embeddings
                # Format 2: Single embedding returned as list
                elif isinstance(embeddings[0], (int, float)):
                    return [embeddings]
            
            raise ValueError(f"Unexpected embedding API response format: {type(embeddings)}")
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model (fallback)"""
        self._ensure_loaded()
        embeddings = self._model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        if self.use_api:
            embeddings = await self._embed_api([text])
            return embeddings[0]
        else:
            # Run local model in executor to avoid blocking
            import asyncio
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, self._embed_local, [text]
            )
            return embeddings[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if self.use_api:
            return await self._embed_api(texts)
        else:
            # Run local model in executor to avoid blocking
            import asyncio
            return await asyncio.get_event_loop().run_in_executor(
                None, self._embed_local, texts
            )
    
    def embed_text_sync(self, text: str) -> List[float]:
        """
        Synchronous version for embedding (blocking)
        Used when async is not available
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.embed_text(text))
    
    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous batch embedding
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.embed_texts(texts))


embedding_service = EmbeddingService()
