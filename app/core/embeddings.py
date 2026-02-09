"""OpenAI embedding generation utilities."""

from typing import List
import openai
from app.core.config import settings

# Configure OpenAI client
openai.api_key = settings.OPENAI_API_KEY


async def generate_embedding(text: str) -> List[float]:
    """Generate an embedding vector for the given text using OpenAI.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        A list of floats representing the embedding vector
        
    Raises:
        Exception: If OpenAI API call fails
    """
    try:
        response = await openai.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")
