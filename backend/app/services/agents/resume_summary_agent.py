"""
Resume Summary Agent

Purpose: Analyzes resume text using LLM and creates a structured summary 
that the orchestrator uses to plan the interview domains and flow.
"""

from typing import Dict, List
from app.services.local_llm_service import local_llm_service


async def resume_summary_agent(resume_text: str, job_role: str) -> Dict:
    """
    Creates a structured summary of the resume using LLM
    
    Args:
        resume_text: Full resume text or concatenated chunks
        job_role: Target job role for context
    
    Returns:
        {
            "candidate_overview": "Brief professional summary",
            "key_experiences": [
                {
                    "experience": "Description of the experience",
                    "technologies": ["tech1", "tech2"],
                    "impact": "What was achieved"
                }
            ],
            "technical_skills": ["skill1", "skill2", ...],
            "recommended_domains": ["Domain1", "Domain2", ...],  # LLM-recommended domains to cover
            "experience_level": "junior/mid/senior"
        }
    """
    
    print(f"Generating LLM-based resume summary for {job_role}")
    
    # Truncate resume to reasonable size for LLM
    resume_excerpt = resume_text[:4000] if len(resume_text) > 4000 else resume_text
    
    # Define available domains for the LLM to choose from
    available_domains = [
        "Python",
        "SQL", 
        "Data Engineering",
        "Data Analysis",
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "System Design",
        "Statistics"
    ]
    
    prompt = f"""You are an expert technical recruiter analyzing a resume for a {job_role} position.

RESUME:
{resume_excerpt}

TASK:
Analyze this resume and provide a structured summary in JSON format.

AVAILABLE TECHNICAL DOMAINS (choose from these only):
{', '.join(available_domains)}

OUTPUT FORMAT (valid JSON only):
{{
    "candidate_overview": "2-3 sentence professional summary of the candidate",
    "key_experiences": [
        {{
            "experience": "Brief description of a key project/role",
            "technologies": ["relevant", "technologies", "used"],
            "impact": "What was achieved or delivered"
        }}
    ],
    "technical_skills": ["list", "of", "technical", "skills", "mentioned"],
    "recommended_domains": ["Domain1", "Domain2", "Domain3", "Domain4", "Domain5"],
    "experience_level": "junior OR mid OR senior"
}}

IMPORTANT INSTRUCTIONS:
1. For "recommended_domains", select 4-6 domains from the AVAILABLE TECHNICAL DOMAINS list that are most relevant to this candidate's experience
2. Order the domains by relevance - most relevant first
3. Only include domains where the candidate has demonstrated experience
4. Return ONLY the JSON object, no additional text
5. Ensure all JSON is properly formatted with double quotes

JSON Output:"""

    try:
        messages = [
            {
                "role": "system", 
                "content": "You are a technical recruiter expert. Analyze resumes and output structured JSON summaries. Return only valid JSON, no explanations."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        result = await local_llm_service.generate_json_async(
            messages, 
            max_new_tokens=1500, 
            temperature=0.3
        )
        
        if result and isinstance(result, dict):
            # Validate and clean the response
            summary = {
                "candidate_overview": result.get("candidate_overview", f"Candidate applying for {job_role}"),
                "key_experiences": result.get("key_experiences", []),
                "technical_skills": result.get("technical_skills", []),
                "recommended_domains": _validate_domains(result.get("recommended_domains", []), available_domains),
                "experience_level": result.get("experience_level", "mid")
            }
            
            # Ensure we have at least some domains
            if not summary["recommended_domains"]:
                summary["recommended_domains"] = _extract_fallback_domains(resume_text, available_domains)
            
            print(f"LLM Resume summary generated successfully")
            print(f"  - Candidate overview: {summary['candidate_overview'][:100]}...")
            print(f"  - Recommended domains: {summary['recommended_domains']}")
            print(f"  - Experience level: {summary['experience_level']}")
            
            return summary
        else:
            print(f"LLM returned invalid response, using fallback")
            return _generate_fallback_summary(resume_text, job_role, available_domains)
            
    except Exception as e:
        print(f"Resume summary generation failed: {str(e)}")
        return _generate_fallback_summary(resume_text, job_role, available_domains)


def _validate_domains(domains: List[str], available_domains: List[str]) -> List[str]:
    """Validate that domains are from the available list"""
    if not domains or not isinstance(domains, list):
        return []
    
    validated = []
    for domain in domains:
        # Check for exact match or close match
        if domain in available_domains:
            validated.append(domain)
        else:
            # Try to find a close match
            domain_lower = domain.lower()
            for available in available_domains:
                if available.lower() in domain_lower or domain_lower in available.lower():
                    if available not in validated:
                        validated.append(available)
                    break
    
    return validated[:6]  # Max 6 domains


def _extract_fallback_domains(resume_text: str, available_domains: List[str]) -> List[str]:
    """Extract domains using keyword matching as fallback"""
    resume_lower = resume_text.lower()
    
    domain_keywords = {
        "Python": ["python", "pandas", "numpy", "django", "flask", "fastapi"],
        "SQL": ["sql", "mysql", "postgresql", "database", "query", "nosql", "mongodb"],
        "Data Engineering": ["data pipeline", "etl", "airflow", "spark", "kafka", "data warehouse"],
        "Data Analysis": ["data analysis", "analytics", "visualization", "tableau", "powerbi", "excel"],
        "Machine Learning": ["machine learning", "ml", "sklearn", "model training", "classification", "regression"],
        "Deep Learning": ["deep learning", "neural network", "tensorflow", "pytorch", "cnn", "rnn", "lstm"],
        "Artificial Intelligence": ["ai", "artificial intelligence", "nlp", "computer vision", "llm", "gpt"],
        "System Design": ["system design", "architecture", "scalability", "microservices", "distributed"],
        "Statistics": ["statistics", "statistical", "hypothesis", "a/b test", "probability"]
    }
    
    found_domains = []
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in resume_lower:
                if domain not in found_domains:
                    found_domains.append(domain)
                break
    
    # Default domains if none found
    if not found_domains:
        found_domains = ["Python", "SQL", "Data Analysis"]
    
    return found_domains[:6]


def _generate_fallback_summary(resume_text: str, job_role: str, available_domains: List[str]) -> Dict:
    """Generate a basic summary when LLM fails"""
    domains = _extract_fallback_domains(resume_text, available_domains)
    
    return {
        "candidate_overview": f"Candidate with technical background applying for {job_role} position.",
        "key_experiences": [],
        "technical_skills": domains,
        "recommended_domains": domains,
        "experience_level": "mid"
    }
