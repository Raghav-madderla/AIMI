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
    
    # Build evaluation prompt with Implicit Rubric Generation
    evaluation_prompt = f"""You are a Senior Technical Interviewer. Perform a two-step evaluation process:

**Step 1: Implicit Rubric Generation**
Analyze the interview question and identify 3-5 Key Technical Concepts (Ground Truth) that a perfect answer MUST include. These are the essential concepts, principles, or knowledge areas required for a correct answer.

**Step 2: Evaluation**
Evaluate the candidate's answer strictly against the key points you identified in Step 1.

Job Role: {state.get('job_role', 'Unknown')}
Round: {round_type.capitalize()}
Domain/Skill: {domain}
Difficulty: {difficulty}

Question:
{question}

Candidate's Answer:
{answer}

### Evaluation Rubric:
1. Accuracy (0-10): Are the identified key points mentioned and used correctly in the answer?
2. Completeness (0-10): Did the candidate cover all identified key concepts?
3. Clarity (0-10): Is the answer structured and easy to understand?

Format your response as a strict JSON object:
{{
    "identified_key_points": ["<concept1>", "<concept2>", "<concept3>", "<concept4>", "<concept5>"],
    "score": <float between 0.0 and 1.0>,
    "feedback_text": "<detailed feedback explaining the score and how the answer relates to the key points>",
    "strengths": ["<strength1>", "<strength2>"],
    "improvements": ["<improvement1>", "<improvement2>"],
    "metrics": {{
        "accuracy": <int 0-10>,
        "completeness": <int 0-10>,
        "clarity": <int 0-10>
    }}
}}"""
    
    try:
        messages = [
            {"role": "system", "content": "You are a Senior Technical Interviewer. Always respond with valid JSON."},
            {"role": "user", "content": evaluation_prompt}
        ]
        
        evaluation_result = local_llm_service.generate_json(messages, max_new_tokens=1000, temperature=0.3)
        
        if not evaluation_result:
            # Fallback if JSON parsing fails
            response_text = local_llm_service.generate(messages, max_new_tokens=1000, temperature=0.3)
            evaluation_result = {
                "identified_key_points": ["Technical Correctness", "Problem Solving", "Communication"],
                "score": 0.5,
                "feedback_text": response_text,
                "strengths": [],
                "improvements": [],
                "metrics": {"accuracy": 5, "completeness": 5, "clarity": 5}
            }
        
        # Extract identified key points (from implicit rubric generation)
        identified_key_points = evaluation_result.get("identified_key_points", [])
        
        evaluation_data = {
            "score": float(evaluation_result.get("score", 0.7)),
            "feedback": {
                "feedback_text": evaluation_result.get("feedback_text", ""),
                "strengths": evaluation_result.get("strengths", []),
                "improvements": evaluation_result.get("improvements", [])
            },
            "metrics": evaluation_result.get("metrics", {"accuracy": 7, "completeness": 7, "clarity": 7}),
            "identified_key_points": identified_key_points,  # Store the implicitly generated rubric
            "domain": domain,
            "question": question
        }

        return {
            "evaluation_agent_response": {
                "score": evaluation_data["score"],
                "feedback": evaluation_data["feedback"],
                "metrics": evaluation_data["metrics"],
                "identified_key_points": identified_key_points,  # Include in response
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
            "identified_key_points": [],
            "domain": domain,
            "question": question
        }
        return {
            "evaluation_agent_response": {
                "error": f"Error evaluating answer: {str(e)}",
                "feedback": None,
                "score": None,
                "identified_key_points": []
            },
            "evaluation_history": [evaluation_data],
            "next_action": "orchestrate"
        }
