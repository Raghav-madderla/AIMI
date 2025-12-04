import httpx
import json
import re
from typing import Dict, List
from app.utils.langgraph_state import InterviewState
from app.core.config import settings
from app.services.local_llm_service import local_llm_service


async def question_agent(state: InterviewState) -> Dict:
    """
    Question Agent - Uses YOUR Hugging Face fine-tuned model to generate questions.
    Now enhanced to generate "Dynamic Ground Truth" (Key Points) for evaluation.
    
    Receives context from Orchestrator:
    - domain: Skill/domain for the question
    - difficulty: easy/medium/hard
    - resume_context: Relevant resume chunks
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
    resume_context = question_context.get("resume_context", "")
    job_role = question_context.get("job_role", "")
    
    # Build prompt in Alpaca format (matching fine-tuning format)
    instruction = """You are an expert interview question generator. Generate an interview question based on the parameters provided.
    
Return the response in strict JSON format with the following keys:
- "question_text": The interview question.
- "key_points": A list of 3-5 specific technical concepts or keywords required in a correct answer.
- "complexity": The difficulty level (Easy/Medium/Hard).
"""
    
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
                        "max_new_tokens": 300,  # Increased for JSON
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
            clean_text = generated_text.strip()
            if "### Response:" in clean_text:
                clean_text = clean_text.split("### Response:")[-1].strip()
            
            # Attempt to parse JSON
            question_data = {}
            try:
                # Try direct JSON parsing
                question_data = json.loads(clean_text)
            except json.JSONDecodeError:
                # Try to find JSON block
                json_match = re.search(r'\{[\s\S]*\}', clean_text)
                if json_match:
                    try:
                        question_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
            
            question_text = question_data.get("question_text")
            key_points = question_data.get("key_points", [])
            complexity = question_data.get("complexity", difficulty)
            
            # Fallback: If JSON parsing failed or no question text
            if not question_text:
                print("Question Agent: Failed to parse JSON, treating output as raw text.")
                # Treat the raw text as the question
                question_text = clean_text
                
                # Remove special tokens
                special_tokens = ["<|end_of_text|>", "<|endoftext|>", "</s>", "<eos>", "[END]", "<|im_end|>", "###"]
            for token in special_tokens:
                    question_text = question_text.replace(token, "")
                    question_text = question_text.strip()

            # Dynamic Ground Truth Generation (Fallback if missing)
            if not key_points:
                print("Question Agent: Generating key points using Local LLM.")
                key_points_prompt = f"""For the interview question below, identify 3-5 key technical concepts or keywords that a correct answer MUST include.
                
Question: "{question_text}"
Domain: {domain}
Job Role: {job_role}

Return ONLY a JSON object with a "key_points" list.
Example: {{"key_points": ["Concept A", "Concept B", "Concept C"]}}"""

                messages = [
                    {"role": "system", "content": "You are an expert technical interviewer."},
                    {"role": "user", "content": key_points_prompt}
                ]
                
                kp_result = local_llm_service.generate_json(messages, max_new_tokens=200)
                key_points = kp_result.get("key_points", [])
            
            # Final safety check
            final_question = question_text
            if not final_question or not final_question.strip():
                final_question = "Could you describe a challenging technical problem you solved recently?"
                print("Question Agent: Generated empty question, using fallback.")

            return {
                "question_agent_response": {
                    "question": final_question,
                    "domain": domain,
                    "difficulty": complexity,
                    "error": None
                },
                "current_question_key_points": key_points
            }
    
    except httpx.HTTPError as e:
        error_msg = f"Hugging Face model error: {str(e)}"
        print(f"Question generation failed: {error_msg}")
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }
    except Exception as e:
        error_msg = f"Question generation error: {str(e)}"
        print(f"Question generation failed: {error_msg}")
        return {
            "question_agent_response": {
                "error": error_msg,
                "question": None
            }
        }

