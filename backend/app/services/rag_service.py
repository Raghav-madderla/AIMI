from typing import List, Dict, Optional
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
import os
import asyncio


class RAGService:
    def __init__(self):
        pass  # Using embedding_service instead of local model
    
    async def retrieve_relevant_context(
        self, 
        query: str, 
        resume_id: str, 
        top_k: int = 3,
        domain: Optional[str] = None
    ) -> str:
        """Retrieve relevant resume chunks using RAG, optionally filtered by domain"""
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(query)
        
        # Query vector store
        if domain:
            # Query by domain using specialized method
            results = vector_store.query_by_domain(
                domain=domain,
                resume_id=resume_id,
                query_embedding=query_embedding,
                n_results=top_k
            )
            documents = results.get('documents', [])
        else:
            # Regular query
            results = vector_store.query(
                query_texts=[query],
                n_results=top_k,
                where={"resume_id": resume_id},
                query_embeddings=[query_embedding]
            )
            documents = results['documents'][0] if results.get('documents') else []
        
        # Combine retrieved chunks
        if documents:
            context = "\n\n".join(documents)
            return context
        return ""
    
    def get_resume_summary(self, resume_id: str, top_k: int = 5) -> str:
        """Get summary of resume for initial context"""
        results = vector_store.get_by_resume_id(resume_id, n_results=top_k)
        if results.get('documents'):
            return "\n\n".join(results['documents'])
        return ""
    
    def get_domains_for_resume(self, resume_id: str) -> List[str]:
        """Get all unique domains associated with a resume"""
        # Get all chunks for resume
        results = vector_store.get_by_resume_id(resume_id, n_results=100)  # Get more to find all domains
        metadatas = results.get('metadatas', [])
        
        domains = set()
        for metadata in metadatas:
            chunk_domains = metadata.get('domains', [])
            if isinstance(chunk_domains, list):
                domains.update(chunk_domains)
            elif isinstance(chunk_domains, str):
                domains.add(chunk_domains)
        
        return list(domains)
    
    async def get_chunks_by_domain(
        self,
        resume_id: str,
        domain: str,
        query: Optional[str] = None,
        top_k: int = 3
    ) -> List[str]:
        """Get chunks filtered by specific domain"""
        if query:
            query_embedding = await embedding_service.embed_text(query)
            results = vector_store.query_by_domain(
                domain=domain,
                resume_id=resume_id,
                query_embedding=query_embedding,
                n_results=top_k
            )
        else:
            # Use dummy embedding to filter by domain
            dummy_query = f"information about {domain}"
            query_embedding = await embedding_service.embed_text(dummy_query)
            results = vector_store.query_by_domain(
                domain=domain,
                resume_id=resume_id,
                query_embedding=query_embedding,
                n_results=top_k
            )
        
        return results.get('documents', [])
    
    def get_domain_relevance(self, resume_id: str) -> Dict[str, int]:
        """
        Get domain relevance scores (chunk counts per domain) from resume
        
        Returns:
            Dictionary mapping domain names to chunk counts
        """
        results = vector_store.get_by_resume_id(resume_id, n_results=100)
        metadatas = results.get('metadatas', [])
        
        domain_counts = {}
        for metadata in metadatas:
            chunk_domains = metadata.get('domains', [])
            if isinstance(chunk_domains, list):
                for domain in chunk_domains:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            elif isinstance(chunk_domains, str):
                domain_counts[chunk_domains] = domain_counts.get(chunk_domains, 0) + 1
        
        return domain_counts


rag_service = RAGService()

