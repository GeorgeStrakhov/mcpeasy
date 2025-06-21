"""
OpenRouter service for LLM API calls with structured output support
"""

import os
import json
from typing import Any, Dict, List, Optional, Type, TypeVar
from openai import OpenAI
from pydantic import BaseModel

DEFAULT_MODEL = "google/gemma-3-27b-it"

T = TypeVar('T', bound=BaseModel)


class OpenRouterService:
    """Service for making LLM calls through OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
    
    async def completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = DEFAULT_MODEL,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """Simple text completion"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenRouter completion error: {e}")
            return None
    
    async def structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        model: str = DEFAULT_MODEL, 
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> Optional[T]:
        """Structured completion with Pydantic model validation"""
        try:
            # Add JSON schema instruction to the last message
            schema = response_model.model_json_schema()
            schema_instruction = f"""
Please respond with a valid JSON object that matches this exact schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no additional text or formatting.
"""
            
            # Clone messages and add schema instruction
            enhanced_messages = messages.copy()
            if enhanced_messages:
                enhanced_messages[-1]["content"] += "\n\n" + schema_instruction
            else:
                enhanced_messages.append({"role": "user", "content": schema_instruction})
            
            response = self.client.chat.completions.create(
                model=model,
                messages=enhanced_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Try to parse JSON and validate with Pydantic model
            try:
                # Clean up response (remove markdown formatting if present)
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # Parse JSON and validate
                data = json.loads(content)

                return response_model.model_validate(data)
            except (json.JSONDecodeError, ValueError) as parse_error:
                print(f"Failed to parse structured response: {parse_error}")
                print(f"Raw response: {content}")
                return None
                
        except Exception as e:
            print(f"OpenRouter structured completion error: {e}")
            return None


# Global service instance
_openrouter_service: Optional[OpenRouterService] = None

def get_openrouter_service() -> Optional[OpenRouterService]:
    """Get global OpenRouter service instance"""
    global _openrouter_service
    
    if _openrouter_service is None:
        try:
            _openrouter_service = OpenRouterService()
        except ValueError:
            # API key not available
            return None
    
    return _openrouter_service