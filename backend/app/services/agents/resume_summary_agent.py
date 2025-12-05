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
    
    # Simplified approach - create a basic summary without LLM
    # The LLM often fails to return proper JSON for complex summaries
    print(f"Generating resume summary for {job_role}")
    
    # Extract key points from resume text
    lines = resume_text[:2000].split('\n')
    experience_keywords = ['experience', 'work', 'project', 'developed', 'built', 'designed', 'implemented']
    skill_keywords = ['python', 'machine learning', 'data', 'sql', 'nlp', 'deep learning', 'ai']
    
    # Find relevant lines
    key_points = []
    skills_found = set()
    
    for line in lines:
        line_lower = line.lower()
        # Check for experience mentions
        if any(kw in line_lower for kw in experience_keywords) and len(line.strip()) > 20:
            key_points.append(line.strip()[:200])
        
        # Check for skills
        for skill in skill_keywords:
            if skill in line_lower:
                skills_found.add(skill.title())
    
    # Create structured summary
    summary_points = []
    for i, point in enumerate(key_points[:5]):  # Limit to 5 points
        summary_points.append({
            "point": point,
            "domains": list(skills_found)[:3] if skills_found else ["General"],
            "significance": "high" if i < 2 else "medium",
            "talking_angle": f"Tell me more about this experience"
        })
    
    # If no points found, create generic one
    if not summary_points:
        summary_points = [
                    {
                "point": "Professional experience and background",
                "domains": list(skills_found)[:3] if skills_found else ["General"],
                        "significance": "medium",
                "talking_angle": "Tell me about your key experiences"
                    }
        ]
    
    result = {
        "summary_points": summary_points,
        "overall_impression": f"Candidate with background relevant to {job_role}",
        "key_strengths": list(skills_found)[:5] if skills_found else ["Technical skills", "Problem solving"]
    }
    
    print(f"Resume summary generated: {len(summary_points)} points found")
    return result
