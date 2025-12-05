import logging
from typing import Dict
from app.utils.langgraph_state import InterviewState
from app.services.question_gen_service import question_gen_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def question_agent(state: InterviewState) -> Dict:
    """
    Question Agent - Uses the fine-tuned question generation model.
    
    Receives context from Orchestrator:
    - domain: Skill/domain for the question
    - difficulty: easy/medium/hard
    - resume_context: Relevant resume chunks (optional context)
    - job_role: Target job role
    """
    question_context = state.get("question_context")
    if not question_context:
        return {
            "question_agent_response": {
                "error": "No question context provided",
                "question": None
            }
        }
    
    domain = question_context.get("domain", "general")
    difficulty = question_context.get("difficulty", "medium")
    job_role = state.get("job_role", "Software Engineer")
    
    # Create Alpaca-style instruction prompt
    instruction = f"Generate a technical interview question for a {job_role} position about {domain} at {difficulty} difficulty level."
    
    input_text = f"""Domain: {domain}
Difficulty: {difficulty}
Job Role: {job_role}

Output only the interview question. Do not include explanations, answers, or formatting."""

    try:
        # Format as Alpaca prompt
        alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:
{input_text}

### Response:"""

        messages = [
            {"role": "user", "content": alpaca_prompt}
        ]
        
        # Use the fine-tuned question generation service
        question = await question_gen_service.generate_question(
            messages=messages,
            max_new_tokens=150,
            temperature=0.7
        )
        
        # Handle None or empty response
        if question is None or not question.strip():
            logger.error(f"Question gen returned None or empty for domain={domain}, difficulty={difficulty}")
            return {
                "question_agent_response": {
                    "question": None,
                    "domain": domain,
                    "difficulty": difficulty,
                    "error": "Question generation returned empty response"
                }
            }
        
        # Clean up the response
        question = question.strip()
        # Remove quotes if the model added them
        question = question.strip('"\'')
        
        # Final validation - ensure we have a substantive question
        if len(question) < 10:
            logger.error(f"Question too short after cleaning: '{question}'")
            return {
                "question_agent_response": {
                    "question": None,
                    "domain": domain,
                    "difficulty": difficulty,
                    "error": f"Generated question too short: '{question}'"
                }
            }
        
        logger.info(f"Generated question for {domain} ({difficulty}): {question}")
            
        return {
            "question_agent_response": {
                "question": question,
                "domain": domain,
                "difficulty": difficulty,
                "error": None
            }
        }
    
    except Exception as e:
        error_msg = f"Question generation error: {str(e)}"
        logger.error(error_msg)
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }
