"""
Evaluation Agent

Uses the dedicated evaluation service with two-step approach:
1. Generate reference (expert) answer
2. Judge candidate's answer against reference

Returns structured scores: technical_accuracy, completeness, clarity, overall_score
"""

from typing import Dict
from app.utils.langgraph_state import InterviewState
from app.services.evaluation_service import evaluation_service


async def evaluation_agent(state: InterviewState) -> Dict:
    """
    Evaluation Agent - Uses dedicated evaluation model for answer assessment
    
    Receives context from Orchestrator:
    - question: The question that was asked
    - answer: User's answer
    - domain: Domain/skill of the question
    - round: technical or behavioral
    - difficulty: easy/medium/hard
    """
    
    evaluation_context = state.get("evaluation_context")
    if not evaluation_context:
        return {
            "evaluation_agent_response": {
                "error": "No evaluation context provided",
                "feedback": None,
                "score": None
            }
        }
    
    question = evaluation_context.get("question", "")
    answer = evaluation_context.get("answer", "")
    domain = evaluation_context.get("domain", "General")
    job_role = state.get("job_role", "Data Scientist")
    
    # Validate inputs
    if not question or not answer:
        return {
            "evaluation_agent_response": {
                "error": "Missing question or answer",
                "feedback": None,
                "score": None
            }
        }
    
    try:
        # Use the dedicated evaluation service with two-step approach
        result = await evaluation_service.evaluate_answer(
            domain=domain,
            question=question,
            user_answer=answer,
            job_role=job_role
        )
        
        # Extract scores and feedback
        overall_score = result.get("overall_score", 0.5)
        
        return {
            "evaluation_agent_response": {
                "score": float(overall_score),
                "feedback": {
                    "feedback_text": result.get("feedback", ""),
                    "analysis": result.get("analysis", ""),
                    "technical_accuracy": result.get("technical_accuracy", overall_score),
                    "completeness": result.get("completeness", overall_score),
                    "clarity": result.get("clarity", overall_score),
                    "strengths": [],  # Can be extracted from analysis if needed
                    "improvements": [result.get("feedback", "")]
                },
                "reference_answer": result.get("reference_answer", ""),
                "error": None
            }
        }
    
    except Exception as e:
        print(f"Evaluation agent error: {e}")
        return {
            "evaluation_agent_response": {
                "error": f"Error evaluating answer: {str(e)}",
                "feedback": None,
                "score": None
            }
        }
