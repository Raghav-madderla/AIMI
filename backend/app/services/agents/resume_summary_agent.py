"""
Resume Summary Agent

Purpose: Analyzes resume chunks and creates a structured summary with key points
that the orchestrator can use to guide the conversation.
"""

from typing import Dict, List
from app.services.local_llm_service import local_llm_service


async def resume_summary_agent(resume_text: str, job_role: str) -> Dict:
    """
    Creates a structured summary of the resume with key talking points
    
    Args:
        resume_text: Full resume text or concatenated chunks
        job_role: Target job role for context
    
    Returns:
        {
            "summary_points": [
                {
                    "point": "Brief description",
                    "domains": ["Python", "Machine Learning"],
                    "significance": "high/medium/low",
                    "talking_angle": "What to discuss about this point"
                }
            ],
            "overall_impression": "Brief professional summary",
            "key_strengths": ["strength1", "strength2", ...]
        }
    """
    
    prompt = f"""You are an expert hiring manager reviewing a resume for a {job_role} position.

Analyze the following resume and create a structured summary with key talking points for the interview.

Resume:
{resume_text[:3000]}

Create a JSON response with:
1. summary_points: Array of 5-7 key achievements/experiences to discuss
   - Each point should have: "point" (brief description), "domains" (technical areas), "significance" (high/medium/low), "talking_angle" (what to ask about it)
2. overall_impression: A brief professional summary of the candidate
3. key_strengths: 3-5 main strengths based on the resume

Format your response as valid JSON.
"""
    
    try:
        messages = [
                {
                    "role": "system",
                    "content": "You are an expert hiring manager. Analyze resumes and create structured interview talking points."
                },
                {
                    "role": "user",
                    "content": prompt
                }
        ]
        
        summary = local_llm_service.generate_json(messages, max_new_tokens=1500, temperature=0.7)
        
        if summary:
            return summary
        else:
            return {
                "success": False,
                "summary": None,
                "error": "Failed to parse JSON response"
            }
        
    except Exception as e:
        print(f"Resume summary failed: {str(e)}")
        # Fallback: Create basic summary
        return {
            "success": False,
            "summary": {
                "summary_points": [
                    {
                        "point": "General experience discussion",
                        "domains": ["General"],
                        "significance": "medium",
                        "talking_angle": "Tell me about your experience"
                    }
                ],
                "overall_impression": "Experienced candidate",
                "key_strengths": ["Technical skills", "Problem solving"]
            },
            "error": str(e)
        }
