"""
Question Cleaning Agent

Purpose: 
1. Retrieves relevant resume chunks from VDB by domain
2. Blends the raw question with candidate's experience
3. Produces a natural, personalized interview question
"""

from typing import Dict, List
from app.services.local_llm_service import local_llm_service
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service


async def question_cleaning_agent(
    generated_question: str,
    domain: str,
    resume_id: str,
    orchestrator_intent: str
) -> Dict:
    """
    Cleans and personalizes the generated question using resume context from VDB
    
    Args:
        generated_question: Raw question from question agent
        domain: Technical domain for the question
        resume_id: ID to retrieve relevant chunks from VDB
        orchestrator_intent: What the interviewer wants to assess
    
    Returns:
        {
            "cleaned_question": "The final polished question",
            "success": bool,
            "resume_context_used": "The resume context that was used",
            "error": str or None
        }
    """
    
    print(f"Cleaning question for domain: {domain}")
    print(f"Original question: {generated_question[:100]}...")
    
    # Step 1: Retrieve relevant resume chunks by domain from VDB
    resume_context = await _retrieve_resume_context_by_domain(
        domain=domain,
        resume_id=resume_id,
        query=generated_question,
        top_k=3
    )
    
    print(f"Retrieved resume context: {len(resume_context)} characters")
    
    # Step 2: Generate personalized question using LLM
    cleaned_question = await _blend_question_with_context(
        raw_question=generated_question,
        resume_context=resume_context,
        domain=domain,
        orchestrator_intent=orchestrator_intent
    )
    
    if cleaned_question:
        print(f"Cleaned question: {cleaned_question[:100]}...")
        return {
            "cleaned_question": cleaned_question,
            "success": True,
            "resume_context_used": resume_context[:500] if resume_context else "",
            "error": None
        }
    else:
        print("Question cleaning failed, using original question")
        return {
            "cleaned_question": generated_question,
            "success": False,
            "resume_context_used": "",
            "error": "Failed to generate cleaned question"
        }


async def _retrieve_resume_context_by_domain(
    domain: str,
    resume_id: str,
    query: str,
    top_k: int = 3
) -> str:
    """
    Retrieve relevant resume chunks from VDB filtered by domain
    Uses semantic search with domain filtering for better relevance
    """
    
    if not resume_id:
        print("No resume_id provided, skipping VDB retrieval")
        return ""
    
    try:
        # Generate embedding for the query (the question)
        query_embedding = await embedding_service.embed_text(query)
        
        # Query VDB with domain filter
        results = vector_store.query_by_domain(
            domain=domain,
            resume_id=resume_id,
            query_embedding=query_embedding,
            n_results=top_k
        )
        
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])
        
        if not documents:
            print(f"No chunks found for domain: {domain}, trying broader search")
            # Fallback: Get any chunks for this resume
            results = vector_store.get_by_resume_id(resume_id, n_results=top_k)
            documents = results.get("documents", [])
        
        if documents:
            # Combine top chunks with separator
            context_parts = []
            for i, doc in enumerate(documents[:top_k]):
                if doc and doc.strip():
                    context_parts.append(f"[Experience {i+1}]: {doc.strip()}")
            
            combined_context = "\n".join(context_parts)
            print(f"Retrieved {len(context_parts)} chunks for domain {domain}")
            return combined_context
        
        print(f"No resume chunks found for resume_id: {resume_id}")
        return ""
        
    except Exception as e:
        print(f"Error retrieving resume context: {str(e)}")
        return ""


async def _blend_question_with_context(
    raw_question: str,
    resume_context: str,
    domain: str,
    orchestrator_intent: str
) -> str:
    """
    Use LLM to blend the raw question with resume context into a natural question
    """
    
    # Handle case where no resume context was found
    if not resume_context or len(resume_context.strip()) < 20:
        print("No meaningful resume context, generating standalone question")
        return await _generate_standalone_question(raw_question, domain, orchestrator_intent)
    
    prompt = f"""You are a Senior Technical Interviewer conducting an interview. Your task is to transform a raw technical question into a natural, personalized question that references the candidate's experience.

RAW TECHNICAL QUESTION:
{raw_question}

CANDIDATE'S RELEVANT EXPERIENCE (from their resume):
{resume_context}

DOMAIN: {domain}
ASSESSMENT GOAL: {orchestrator_intent}

INSTRUCTIONS:
Create a single, complete interview question that:
1. References a specific aspect of the candidate's experience
2. Tests their knowledge of {domain} concepts
3. Feels natural and conversational (like a real interviewer)
4. Is complete and grammatically correct
5. Does NOT start with "I see you..." or similar robotic phrases

STRATEGIES TO USE:
- DEEP DIVE: Connect their specific project/experience to the technical concept
  Example: "In your [specific project], how did you handle [technical concept]? What trade-offs did you consider?"

- EXPERIENCE-BASED: Ask them to explain their approach using their real work
  Example: "Walk me through how you implemented [concept] in your [specific experience]. What challenges did you face?"

- COMPARATIVE: Ask them to compare approaches based on their experience
  Example: "You mentioned using [approach A] in [project]. Have you considered [approach B]? When would you choose one over the other?"

OUTPUT:
Write ONLY the final question. Make sure it is:
- A complete sentence ending with a question mark
- Between 20-80 words
- Natural sounding
- Specific to their experience

FINAL QUESTION:"""

    try:
        messages = [
            {
                "role": "system",
                "content": "You are an expert interviewer. Output ONLY the final interview question. The question must be complete and end with a question mark."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        response = await local_llm_service.generate_async(
            messages, 
            max_new_tokens=200,  # Enough for a complete question
            temperature=0.7
        )
        
        if response:
            cleaned = _clean_question_output(response)
            if cleaned and len(cleaned) > 20:
                return cleaned
        
        print("LLM returned invalid response, using fallback")
        return await _generate_standalone_question(raw_question, domain, orchestrator_intent)
        
    except Exception as e:
        print(f"Question blending failed: {str(e)}")
        return await _generate_standalone_question(raw_question, domain, orchestrator_intent)


async def _generate_standalone_question(
    raw_question: str,
    domain: str,
    orchestrator_intent: str
) -> str:
    """
    Generate a standalone question when no resume context is available
    """
    
    prompt = f"""You are a Senior Technical Interviewer. Transform this raw question into a natural, conversational interview question.

RAW QUESTION: {raw_question}
DOMAIN: {domain}
GOAL: {orchestrator_intent}

Make the question sound natural and professional. Output ONLY the final question:"""

    try:
        messages = [
            {"role": "system", "content": "Output only the final interview question."},
            {"role": "user", "content": prompt}
        ]
        
        response = await local_llm_service.generate_async(messages, max_new_tokens=150, temperature=0.7)
        
        if response:
            cleaned = _clean_question_output(response)
            if cleaned:
                return cleaned
        
        # Final fallback: return original question
        return raw_question
        
    except Exception as e:
        print(f"Standalone question generation failed: {str(e)}")
        return raw_question


def _clean_question_output(text: str) -> str:
    """
    Clean the LLM output to ensure we have a proper, complete question
    """
    if not text:
        return ""
    
    # Remove common prefixes
    prefixes_to_remove = [
        "Here is the rewritten question:",
        "Rewritten Question:",
        "Final Question:",
        "Question:",
        "Answer:",
        "Output:",
        "Here's the question:",
        "The question is:",
    ]
    
    cleaned = text.strip()
    
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove surrounding quotes
    cleaned = cleaned.strip('"\'')
    
    # Ensure the question is complete (ends with ? or reasonable punctuation)
    # Take only the first complete question if multiple are generated
    lines = cleaned.split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 20:
            # Check if it's a question (ends with ? or contains interrogative)
            if '?' in line:
                # Take up to the first question mark and include it
                question_end = line.rfind('?') + 1
                cleaned = line[:question_end].strip()
                break
            elif len(line) > 30:  # Accept longer statements that might be questions
                cleaned = line
                if not cleaned.endswith('?'):
                    cleaned += '?'
                break
    
    # Final cleanup
    cleaned = cleaned.strip()
    
    # Ensure minimum length
    if len(cleaned) < 20:
        return ""
    
    return cleaned
