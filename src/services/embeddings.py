"""
Cloudflare AI embeddings service
"""

import os
from typing import List, Optional
from openai import OpenAI

DEFAULT_MODEL = "@cf/baai/bge-m3"


class EmbeddingsService:
    """Service for generating embeddings using Cloudflare AI"""
    
    def __init__(self, api_key: Optional[str] = None, account_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("CLOUDFLARE_API_KEY")
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        
        if not self.api_key or not self.account_id:
            raise ValueError("CLOUDFLARE_API_KEY and CLOUDFLARE_ACCOUNT_ID environment variables are required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/v1"
        )
    
    async def create_embedding(self, text: str, model: str = DEFAULT_MODEL) -> Optional[List[float]]:
        """Create embedding for a single text string."""
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embeddings creation error: {e}")
            return None
    
    async def create_embeddings(self, texts: List[str], model: str = DEFAULT_MODEL) -> Optional[List[List[float]]]:
        """Create embeddings for multiple text strings."""
        try:
            response = self.client.embeddings.create(
                model=model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            print(f"Embeddings creation error: {e}")
            return None


# Global service instance
_embeddings_service: Optional[EmbeddingsService] = None

def get_embeddings_service() -> Optional[EmbeddingsService]:
    """Get global embeddings service instance"""
    global _embeddings_service
    
    if _embeddings_service is None:
        try:
            _embeddings_service = EmbeddingsService()
        except ValueError:
            # API keys not available
            return None
    
    return _embeddings_service