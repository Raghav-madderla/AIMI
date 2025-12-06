"""
Evaluation Service

Dedicated service for evaluating candidate answers using a two-step approach:
1. Generate reference (expert) answer from the LLM
2. Judge candidate's answer against the reference and get scores
"""

import json
import re
from typing import Dict, Optional
from huggingface_hub import InferenceClient, AsyncInferenceClient
from app.core.config import settings


class EvaluationService:
    """Service for evaluating interview answers using dedicated HF endpoint"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not EvaluationService._initialized:
            self.api_url = settings.HUGGINGFACE_EVALUATION_API_URL
            self.api_key = settings.HUGGINGFACE_EVALUATION_API_KEY
            
            # Initialize clients
            self.client = InferenceClient(base_url=self.api_url, token=self.api_key)
            self.async_client = AsyncInferenceClient(base_url=self.api_url, token=self.api_key)
            
            EvaluationService._initialized = True
            print(f"Evaluation service initialized with endpoint: {self.api_url}")
    
    async def evaluate_answer(
        self,
        domain: str,
        question: str,
        user_answer: str,
        job_role: str = "Data Scientist"
    ) -> Dict:
        """
        Evaluate a candidate's answer using two-step approach.
        """
        print(f"Evaluating answer for domain: {domain}")
        
        # Step 1: Generate reference (expert) answer
        reference_answer = await self._generate_reference_answer(domain, question)
        
        if not reference_answer:
            print("Warning: Failed to generate reference answer, using fallback evaluation")
            return self._fallback_evaluation(user_answer)
        
        # Step 2: Judge candidate's answer against reference
        evaluation_result = await self._judge_answer(
            question=question,
            reference_answer=reference_answer,
            user_answer=user_answer,
            domain=domain
        )
        
        # Add reference answer to result for transparency
        evaluation_result["reference_answer"] = reference_answer
        
        return evaluation_result
    
    async def _generate_reference_answer(self, domain: str, question: str) -> Optional[str]:
        """
        Step A: Generate a reference (expert) answer for the question
        """
        reference_prompt = f"""You are an expert in {domain}.
Write a concise, technically perfect answer to the following interview question.
Focus on the definition and the 'why'. Do NOT use code examples unless absolutely necessary.

Question: {question}

Answer:"""

        try:
            print(f"Generating reference answer for domain: {domain}")
            
            response = await self.async_client.text_generation(
                prompt=reference_prompt,
                max_new_tokens=256,
                temperature=0.2,
                stop=["<|end_of_text|>", "Question:", "User:"], # Updated deprecated arg
                return_full_text=False  # CRITICAL FIX: Don't echo prompt
            )
            
            if response:
                reference = response.strip()
                print(f"Reference generated: {len(reference)} characters")
                return reference
            
            print("Warning: Empty reference response")
            return None
            
        except Exception as e:
            print(f"Error generating reference answer: {e}")
            return None
    
    async def _judge_answer(
        self,
        question: str,
        reference_answer: str,
        user_answer: str,
        domain: str
    ) -> Dict:
        """
        Step B: Judge candidate's answer against the reference
        """
        judge_prompt = f"""You are a strict technical interviewer.

### Question:
{question}

### Reference Answer (Truth):
{reference_answer}

### Candidate's Answer:
{user_answer}

### Evaluation Protocol:
1. *Analyze:* Compare the Candidate's answer to the Reference. Note matches and misses.
2. *Score Technical Accuracy (0.0-1.0):* Is the information factually correct? (No lies/hallucinations).
3. *Score Completeness (0.0-1.0):* Did they cover the main points? (e.g. missed "test data" in overfitting).
4. *Score Clarity (0.0-1.0):* Is the answer easy to understand?
5. *Overall Score (0.0-1.0):* A weighted average of the above.

### Instructions:
- Be objective.
- *CRITICAL:* Respond using ONLY valid JSON. Do not write anything else.

### Output Format (JSON):
{{
    "analysis": "<Short comparison of Reference vs Candidate>",
    "technical_accuracy": <float>,
    "completeness": <float>,
    "clarity": <float>,
    "overall_score": <float>,
    "feedback": "<Constructive feedback for the student>"
}}

### Response:
"""

        try:
            print("Running judge evaluation...")
            
            response = await self.async_client.text_generation(
                prompt=judge_prompt,
                max_new_tokens=512,
                temperature=0.1,
                stop=["<|end_of_text|>"], # Updated deprecated arg
                return_full_text=False    # CRITICAL FIX: Don't echo prompt
            )
            
            if not response:
                print("Warning: Empty judge response")
                return self._fallback_evaluation(user_answer)
            
            # Parse JSON from response
            result = self._parse_judge_response(response)
            
            if result:
                print(f"Evaluation complete: overall_score={result.get('overall_score', 'N/A')}")
                return result
            
            print("Warning: Failed to parse judge response")
            return self._fallback_evaluation(user_answer)
            
        except Exception as e:
            print(f"Error in judge evaluation: {e}")
            return self._fallback_evaluation(user_answer)
    
    def _parse_judge_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse JSON from judge response, handling markdown code blocks
        """
        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.strip()
            clean_text = re.sub(r'```json\s*', '', clean_text)
            clean_text = re.sub(r'```\s*', '', clean_text)
            clean_text = clean_text.strip()
            
            # Try direct JSON parsing
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError:
                pass
            
            # Try to find JSON object in response (greedy search)
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            print(f"Failed to parse JSON from response: {response_text[:200]}")
            return None
            
        except Exception as e:
            print(f"Error parsing judge response: {e}")
            return None
    
    def _fallback_evaluation(self, user_answer: str) -> Dict:
        """
        Provide a basic evaluation when LLM fails
        Based on answer length and structure as heuristics
        """
        answer_length = len(user_answer.strip())
        
        # Simple heuristic scoring based on answer length
        if answer_length < 20:
            base_score = 0.3
        elif answer_length < 50:
            base_score = 0.5
        elif answer_length < 150:
            base_score = 0.65
        else:
            base_score = 0.75
        
        return {
            "analysis": "Automatic evaluation based on response structure",
            "technical_accuracy": base_score,
            "completeness": base_score - 0.1,
            "clarity": base_score,
            "overall_score": base_score,
            "feedback": "Your answer has been recorded. Please ensure you provide detailed technical explanations with specific examples.",
            "reference_answer": ""
        }


# Singleton instance
evaluation_service = EvaluationService()