from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional
from app.core.config import settings
import os


class VectorStore:
    def __init__(self):
        self._pc = None
        self._index = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only connect when actually needed"""
        if self._initialized:
            return
        
        # Check if Pinecone API key is configured
        if not settings.PINECONE_API_KEY:
            raise ValueError(
                "Pinecone API key not configured. Please set PINECONE_API_KEY in app/core/config.py"
            )
        
        # Initialize Pinecone
        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Get or create index
        index_name = settings.PINECONE_INDEX_NAME
        
        # Check if index exists, create if not
        existing_indexes = [index.name for index in self._pc.list_indexes()]
        
        if index_name not in existing_indexes:
            # Create index with configured dimensions
            self._pc.create_index(
                name=index_name,
                dimension=settings.PINECONE_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.PINECONE_ENVIRONMENT
                )
            )
        
        self._index = self._pc.Index(index_name)
        self._initialized = True
    
    @property
    def pc(self):
        self._ensure_initialized()
        return self._pc
    
    @property
    def index(self):
        self._ensure_initialized()
        return self._index
    
    @property
    def dimension(self):
        return settings.PINECONE_DIMENSION  # Embedding model dimension
    
    def add_documents(
        self, 
        documents: List[str], 
        ids: List[str], 
        metadatas: List[Dict],
        embeddings: List[List[float]]
    ):
        """
        Add documents to the vector store
        
        Args:
            documents: List of text documents
            ids: List of unique IDs for each document
            metadatas: List of metadata dictionaries for each document
            embeddings: List of embedding vectors (must be provided)
        """
        if not embeddings:
            raise ValueError("Embeddings are required for Pinecone")
        
        # Prepare vectors for upsert
        vectors = []
        for i, (doc_id, embedding, metadata) in enumerate(zip(ids, embeddings, metadatas)):
            # Pinecone expects metadata values to be strings, numbers, booleans, or lists
            # Convert any complex types to strings
            cleaned_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    cleaned_metadata[key] = value
                elif isinstance(value, list):
                    # Handle lists - if it's a list of strings, keep it, otherwise convert
                    cleaned_metadata[key] = value if all(isinstance(x, (str, int, float, bool)) for x in value) else str(value)
                else:
                    cleaned_metadata[key] = str(value)
            
            vectors.append({
                "id": doc_id,
                "values": embedding,
                "metadata": {
                    **cleaned_metadata,
                    "text": documents[i]  # Store text in metadata for retrieval
                }
            })
        
        # Upsert in batches (Pinecone limit is 100 vectors per batch)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
    
    def query(
        self, 
        query_texts: List[str], 
        n_results: int = 3,
        where: Optional[Dict] = None,
        query_embeddings: Optional[List[List[float]]] = None
    ) -> Dict:
        """
        Query the vector store
        
        Args:
            query_texts: List of query texts (if query_embeddings not provided)
            n_results: Number of results to return
            where: Filter metadata (e.g., {"resume_id": "123"})
            query_embeddings: Pre-computed query embeddings (optional)
        
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        # If embeddings not provided, need to compute them (but this should be done by caller)
        if query_embeddings is None:
            raise ValueError("query_embeddings must be provided for Pinecone queries")
        
        results = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        
        for query_embedding in query_embeddings:
            # Query Pinecone
            query_result = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                filter=where,  # Pinecone uses 'filter' instead of 'where'
                include_metadata=True
            )
            
            # Format response to match ChromaDB-style format
            batch_ids = []
            batch_docs = []
            batch_metadatas = []
            batch_distances = []
            
            for match in query_result.matches:
                batch_ids.append(match.id)
                # Extract text from metadata if stored
                batch_docs.append(match.metadata.get("text", ""))
                batch_metadatas.append(match.metadata)
                batch_distances.append(match.score)
            
            results["ids"].append(batch_ids)
            results["documents"].append(batch_docs)
            results["metadatas"].append(batch_metadatas)
            results["distances"].append(batch_distances)
        
        return results
    
    def get_by_resume_id(self, resume_id: str, n_results: int = 5) -> Dict:
        """
        Get all chunks for a specific resume by filtering metadata
        
        Note: Pinecone doesn't support fetching all documents easily,
        so we use a query with a dummy vector or fetch by metadata filter.
        For better performance, store resume_id in metadata and query with filter.
        """
        # Use query with filter to get documents by resume_id
        # We need a dummy embedding - use zero vector
        dummy_vector = [0.0] * self.dimension
        
        query_result = self.index.query(
            vector=dummy_vector,
            top_k=n_results,
            filter={"resume_id": resume_id},
            include_metadata=True
        )
        
        # Format response
        documents = []
        metadatas = []
        ids = []
        
        for match in query_result.matches:
            ids.append(match.id)
            documents.append(match.metadata.get("text", ""))
            metadatas.append(match.metadata)
        
        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
    
    def query_by_domain(
        self,
        domain: str,
        resume_id: str,
        query_embedding: List[float],
        n_results: int = 3
    ) -> Dict:
        """
        Query chunks by domain and resume_id
        
        Args:
            domain: Domain name to filter by
            resume_id: Resume ID to filter by
            query_embedding: Query embedding vector
            n_results: Number of results
        
        Returns:
            Dictionary with matching chunks
        """
        # First try filtering by primary_domain (faster)
        # But we also need to check chunks where domain is in the domains list
        # So we query more results and filter in Python for better accuracy
        filter_dict = {
            "resume_id": resume_id
        }
        
        # Query more results to account for filtering by domain list membership
        query_result = self.index.query(
            vector=query_embedding,
            top_k=n_results * 3,  # Get more results, then filter
            filter=filter_dict,
            include_metadata=True
        )
        
        documents = []
        metadatas = []
        ids = []
        
        # Filter by domain: check if domain is in the domains list or matches primary_domain
        for match in query_result.matches:
            metadata = match.metadata
            chunk_domains = metadata.get('domains', [])
            primary_domain = metadata.get('primary_domain', '')
            
            # Check if domain matches primary_domain or is in domains list
            if domain == primary_domain or (isinstance(chunk_domains, list) and domain in chunk_domains):
                ids.append(match.id)
                documents.append(metadata.get("text", ""))
                metadatas.append(metadata)
                
                # Stop when we have enough results
                if len(documents) >= n_results:
                    break
        
        return {
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas
        }
    
    def clear_all(self):
        """Clear all vectors from the index"""
        index_name = settings.PINECONE_INDEX_NAME
        
        # Delete the index
        self.pc.delete_index(index_name)
        
        # Recreate the index
        self._pc.create_index(
            name=index_name,
            dimension=settings.PINECONE_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=settings.PINECONE_ENVIRONMENT
            )
        )
        
        # Reinitialize the index connection
        self._index = self._pc.Index(index_name)


vector_store = VectorStore()
