import httpx
from typing import Dict
from app.utils.langgraph_state import InterviewState
from app.core.config import settings


async def question_agent(state: InterviewState) -> Dict:
    """
    Question Agent - Uses YOUR Hugging Face fine-tuned model ONLY to generate questions
    
    Receives context from Orchestrator:
    - domain: Skill/domain for the question
    - difficulty: easy/medium/hard
    - resume_context: Relevant resume chunks
    - job_role: Target job role
    
    Note: No fallback to other models - uses only your HF model
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
    resume_context = question_context.get("resume_context", "")
    job_role = question_context.get("job_role", "")
    
    # Build prompt in Alpaca format (matching fine-tuning format)
    instruction = "You are an expert interview question generator. Generate an interview question based on the parameters provided in the input."
    
    # Include resume context in input if available
    if resume_context:
        input_params = f"Domain: {domain}\nDifficulty: {difficulty}\nJob Role: {job_role}\nCandidate Background: {resume_context[:500]}"
    else:
        input_params = f"Domain: {domain}\nDifficulty: {difficulty}\nJob Role: {job_role}"
    
    alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:

{instruction}

### Input:

{input_params}

### Response:

"""
    
    prompt = alpaca_prompt
    
    # Check if HuggingFace API is configured
    if not settings.HUGGINGFACE_API_URL or not settings.HUGGINGFACE_API_KEY:
        error_msg = "HuggingFace API not configured. Please set HUGGINGFACE_API_URL and HUGGINGFACE_API_KEY in config.py"
        print(f"Question generation failed: {error_msg}")
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }
    
    try:
        # Call Hugging Face API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.HUGGINGFACE_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 150,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats from Hugging Face
            if isinstance(result, list):
                generated_text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                generated_text = result.get("generated_text", "")
            else:
                generated_text = str(result)
            
            # Clean up the generated text
            # Remove the prompt if it was included in the response
            question = generated_text.strip()
            
            # Remove prompt prefix if present (some models return full text)
            if "### Response:" in question:
                question = question.split("### Response:")[-1].strip()
            
            # Remove common special tokens from fine-tuned models
            special_tokens = [
                "<|end_of_text|>",
                "<|endoftext|>",
                "</s>",
                "<eos>",
                "[END]",
                "<|im_end|>",
                "###",
            ]
            for token in special_tokens:
                question = question.replace(token, "")
            
            # Remove any leading/trailing whitespace and newlines
            question = question.strip()
            
            return {
                "question_agent_response": {
                    "question": question,
                    "domain": domain,
                    "difficulty": difficulty,
                    "error": None
                }
            }
    
    except httpx.HTTPError as e:
        # No fallback - return error if YOUR model fails
        error_msg = f"Hugging Face model error: {str(e)}"
        print(f"Question generation failed: {error_msg}")
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }
    except Exception as e:
        # No fallback - return error if YOUR model fails
        error_msg = f"Question generation error: {str(e)}"
        print(f"Question generation failed: {error_msg}")
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }

