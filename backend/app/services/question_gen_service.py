"""
Question Generation Service using fine-tuned Hugging Face model
Separate from the general LLM service
"""

from typing import List, Dict
from huggingface_hub import AsyncInferenceClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class QuestionGenService:
    """Service specifically for generating interview questions using fine-tuned model"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not QuestionGenService._initialized:
            self.api_url = settings.HUGGINGFACE_API_URL
            self.api_key = settings.HUGGINGFACE_API_KEY
            
            if self.api_url and self.api_key:
                # Initialize client with the fine-tuned question generation endpoint
                self.async_client = AsyncInferenceClient(base_url=self.api_url, token=self.api_key)
                self.model_id = "fine-tuned-question-model"  # Your fine-tuned model
                logger.info(f"QuestionGenService initialized with endpoint: {self.api_url}")
            else:
                raise ValueError("Question generation API URL and key must be configured!")
            
            QuestionGenService._initialized = True
    
    async def generate_question(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 150,
        temperature: float = 0.7
    ) -> str:
        """Generate a question using the fine-tuned model"""
        try:
            logger.info(f"Calling question gen API: {self.api_url}")
            
            # Convert messages to a single prompt string
            prompt = self._format_prompt(messages)
            
            # Use standard text generation (not chat completions)
            response = await self.async_client.text_generation(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                return_full_text=False,  # Only return generated text, not the prompt
                do_sample=True
            )
            
            if response is None or response == "":
                logger.error(f"Question gen API returned empty response")
                return ""
            
            # Clean special tokens
            content = self._clean_special_tokens(response)
            
            # Clean formatting from the model's response
            content = self._clean_question_formatting(content)
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"Question generation API failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e
    
    def _format_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages format to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt = "\n".join(prompt_parts)
        prompt += "\nAssistant:"  # Prompt the model to generate
        return prompt
    
    def _clean_special_tokens(self, text: str) -> str:
        """Remove special tokens from generated text"""
        special_tokens = [
            "<|end_of_text|>",
            "<|endoftext|>",
            "</s>",
            "<eos>",
            "[END]",
            "<|im_end|>",
            "<|end|>",
            "<|system|>",
            "<|user|>",
            "<|assistant|>",
            "<s>",
            "[INST]",
            "[/INST]",
        ]
        
        cleaned_text = text
        for token in special_tokens:
            cleaned_text = cleaned_text.replace(token, "")
        
        return cleaned_text.strip()
    
    def _clean_question_formatting(self, text: str) -> str:
        """Remove common prefixes and formatting from generated questions"""
        import re
        
        # Remove common prefixes (case insensitive, multiline)
        prefixes_to_remove = [
            r"^Got it\.?\s*Here is your interview question:\s*",
            r"^Here is your interview question:\s*",
            r"^Your interview question:\s*",
            r"^Question:\s*",
            r"^Interview Question:\s*",
            r"^Technical Question:\s*",
            r"^\d+\.\s*",  # Remove leading numbers like "1. "
            r"^###\s*",    # Remove markdown headers
            r"^##\s*",
            r"^#\s*",
        ]
        
        cleaned = text.strip()
        for pattern in prefixes_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
            cleaned = cleaned.strip()
        
        # Check for generic/invalid responses
        generic_responses = [
            "Your request has been processed",
            "I understand",
            "Got it",
            "Understood",
            "Request processed",
            "Task completed",
        ]
        
        # If the response is just a generic message, log warning and return empty
        for generic in generic_responses:
            if cleaned.lower().startswith(generic.lower()):
                logger.warning(f"Question gen returned generic response: '{cleaned}' - returning empty")
                return ""
        
        # Clean up extra whitespace and newlines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Remove multiple newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
        cleaned = cleaned.strip()
        
        return cleaned


# Create singleton instance
question_gen_service = QuestionGenService()

