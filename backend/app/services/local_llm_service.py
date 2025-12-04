"""
Local LLM Service using Qwen/Qwen3-0.6B

This service provides text generation using a local Qwen model
instead of OpenAI API calls.
"""

from typing import List, Dict, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import re
from app.core.config import settings


class LocalLLMService:
    """Service for text generation using local Qwen model"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not LocalLLMService._initialized:
            self.model_name = settings.LOCAL_LLM_MODEL
            self._tokenizer = None
            self._model = None
            self._device = None
            LocalLLMService._initialized = True
    
    def _ensure_loaded(self):
        """Lazy load the model only when needed"""
        if self._model is None:
            print(f"Loading local LLM: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model = self._model.to(self._device)
            print(f"Model loaded on {self._device}")
    
    @property
    def tokenizer(self):
        self._ensure_loaded()
        return self._tokenizer
    
    @property
    def model(self):
        self._ensure_loaded()
        return self._model
    
    @property
    def device(self):
        self._ensure_loaded()
        return self._device
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text from a list of messages (chat format)
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Generated text string
        """
        self._ensure_loaded()
        
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else None,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode only the new tokens (exclude input)
        generated_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True
        )
        
        # FIX: Remove <think>...</think> blocks from the output
        if "<think>" in generated_text:
            # First try to remove closed blocks
            generated_text = re.sub(r'<think>.*?</think>', '', generated_text, flags=re.DOTALL)
            
            # If <think> remains (unclosed tag), remove everything from <think> onwards
            if "<think>" in generated_text:
                generated_text = re.sub(r'<think>.*', '', generated_text, flags=re.DOTALL)
        
        return generated_text.strip()
    
    def generate_json(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict:
        """
        Generate JSON response from messages
        
        Args:
            messages: List of message dicts
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Returns:
            Parsed JSON dict or empty dict on failure
        """
        response_text = self.generate(messages, max_new_tokens, temperature)
        
        # Try to extract JSON from the response
        try:
            # First try direct parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON array
            array_match = re.search(r'\[[\s\S]*\]', response_text)
            if array_match:
                try:
                    return {"data": json.loads(array_match.group())}
                except json.JSONDecodeError:
                    pass
        
        return {}


# Singleton instance
local_llm_service = LocalLLMService()

