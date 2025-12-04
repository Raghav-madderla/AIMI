from typing import Dict
from app.utils.langgraph_state import InterviewState
from app.services.local_llm_service import local_llm_service


async def evaluation_agent(state: InterviewState) -> Dict:
    """
    Evaluation Agent - Uses local Qwen model to evaluate user answers
    
    Receives context from Orchestrator:
    - question: The question that was asked
    - answer: User's answer
    - domain: Domain/skill of the question
    - round: technical or behavioral
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
    domain = evaluation_context.get("domain", "")
    round_type = evaluation_context.get("round", "technical")
    difficulty = evaluation_context.get("difficulty", "medium")
    
    # Build evaluation prompt
    evaluation_prompt = f"""You are an expert interview evaluator. Evaluate the candidate's answer to an interview question.

Job Role: {state.get('job_role', 'Unknown')}
Round: {round_type.capitalize()}
Domain/Skill: {domain}
Difficulty: {difficulty}

Question:
{question}

Candidate's Answer:
{answer}

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is excellent)
2. Detailed feedback on the answer
3. Strengths of the answer
4. Areas for improvement

Format your response as JSON with the following structure:
{{
    "score": <float between 0.0 and 1.0>,
    "feedback_text": "<detailed feedback>",
    "strengths": ["<strength1>", "<strength2>"],
    "improvements": ["<improvement1>", "<improvement2>"]
}}"""
    
    try:
        messages = [
            {"role": "system", "content": "You are an expert interview evaluator. Always respond with valid JSON in the exact format specified."},
            {"role": "user", "content": evaluation_prompt}
        ]
        
        evaluation_result = local_llm_service.generate_json(messages, max_new_tokens=800, temperature=0.3)
        
        if not evaluation_result:
            # Fallback if JSON parsing fails
            response_text = local_llm_service.generate(messages, max_new_tokens=800, temperature=0.3)
            evaluation_result = {
                "score": 0.7,
                "feedback_text": response_text,
                "strengths": [],
                "improvements": []
            }
        
        evaluation_data = {
            "score": float(evaluation_result.get("score", 0.7)),
            "feedback": {
                "feedback_text": evaluation_result.get("feedback_text", ""),
                "strengths": evaluation_result.get("strengths", []),
                "improvements": evaluation_result.get("improvements", [])
            },
            "domain": domain,
            "question": question
        }

        return {
            "evaluation_agent_response": {
                "score": evaluation_data["score"],
                "feedback": evaluation_data["feedback"],
                "error": None
            },
            "evaluation_history": [evaluation_data],
            "next_action": "orchestrate"
        }
    
    except Exception as e:
        # Add a placeholder evaluation to avoid infinite loops
        evaluation_data = {
            "score": 0.0,
            "feedback": {"error": str(e)},
            "domain": domain,
            "question": question
        }
        return {
            "evaluation_agent_response": {
                "error": f"Error evaluating answer: {str(e)}",
                "feedback": None,
                "score": None
            },
            "evaluation_history": [evaluation_data],
            "next_action": "orchestrate"
        }
