"""
LLM Service using Hugging Face API
"""

from typing import List, Dict, Optional
import json
import re
import asyncio
from huggingface_hub import InferenceClient, AsyncInferenceClient
from app.core.config import settings


class LocalLLMService:
    """Service for text generation using Hugging Face API"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not LocalLLMService._initialized:
            self.api_url = settings.HUGGINGFACE_LLM_API_URL
            self.api_key = settings.HUGGINGFACE_LLM_API_KEY
            self.use_api = bool(self.api_url and self.api_key)
            
            if self.use_api:
                # Initialize clients with the user's endpoint
                self.client = InferenceClient(base_url=self.api_url, token=self.api_key)
                self.async_client = AsyncInferenceClient(base_url=self.api_url, token=self.api_key)
                self.model_id = "openai/gpt-oss-20b" # Using the specific model name requested
            
            # Fallback to local model if API not configured (legacy support)
            if not self.use_api:
                print("Warning: Hugging Face LLM API not configured. Will attempt to load local model.")
                self.model_name = settings.LOCAL_LLM_MODEL
                self._tokenizer = None
                self._model = None
                self._device = None
            
            LocalLLMService._initialized = True
    
    def _ensure_loaded(self):
        """Lazy load the local model only when needed (fallback)"""
        if not self.use_api and self._model is None:
            print(f"Loading local LLM: {self.model_name}")
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = self._model.to(self._device)
                print(f"Model loaded on {self._device}")
            except Exception as e:
                print(f"Failed to load local model: {e}")
                raise
    
    async def _generate_api(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate text using Hugging Face API via AsyncInferenceClient"""
        try:
            # Use the OpenAI-compatible endpoint as requested
            response = await self.async_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=max_new_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"API generation failed: {e}")
            # Fallback or re-raise? For now re-raise to be handled by caller or caught
            raise e

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
    
    def _generate_local(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate text using local model (fallback)"""
        self._ensure_loaded()
        
        import torch
        
        inputs = self._tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._device)
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else None,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.eos_token_id
            )
        
        # Decode only the new tokens (exclude input)
        generated_text = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        )
        
        return generated_text.strip()
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text from a list of messages (chat format)
        """
        if self.use_api:
            # Use synchronous client for sync method
            try:
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    max_tokens=max_new_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Sync API generation failed: {e}")
                raise e
        else:
            # Use local model
            return self._generate_local(messages, max_new_tokens, temperature)
    
    async def generate_async(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Async version of generate (preferred)
        """
        if self.use_api:
            return await self._generate_api(messages, max_new_tokens, temperature)
        else:
            # Run local model in executor to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_local, messages, max_new_tokens, temperature
            )
    
    def generate_json(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict:
        """
        Generate JSON response from messages (sync version)
        """
        response_text = self.generate(messages, max_new_tokens, temperature)
        
        # Clean the response first
        response_text = self._clean_special_tokens(response_text)
        
        return self._parse_json_response(response_text)
    
    async def generate_json_async(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict:
        """
        Async version of generate_json (preferred)
        """
        response_text = await self.generate_async(messages, max_new_tokens, temperature)
        
        # Clean the response first
        response_text = self._clean_special_tokens(response_text)
        
        return self._parse_json_response(response_text)

    def _parse_json_response(self, response_text: str) -> Dict:
        """Helper to parse JSON from response text"""
        try:
            # First try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON array
            array_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', response_text, re.DOTALL)
            if array_match:
                try:
                    parsed = json.loads(array_match.group())
                    if isinstance(parsed, list):
                        return {"data": parsed}
                    return parsed
                except json.JSONDecodeError:
                    pass
        
        print(f"Failed to parse JSON from response: {response_text[:200]}")
        return {}


# Singleton instance
local_llm_service = LocalLLMService()
