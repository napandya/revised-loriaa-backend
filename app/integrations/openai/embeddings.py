"""
OpenAI Embeddings for Loriaa AI CRM.

Provides embedding generation for:
- Document vectorization (RAG)
- Semantic search
- Lead matching

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.integrations.openai.client import get_openai_client
from app.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)

# Default embedding model
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
LARGE_EMBEDDING_MODEL = "text-embedding-3-large"


def generate_embedding(
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL
) -> list[float]:
    """
    Generate embedding vector for text.
    
    Args:
        text: Text to embed
        model: Embedding model to use
        
    Returns:
        Embedding vector as list of floats
        
    Raises:
        IntegrationError: On API errors
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    # Clean and truncate text
    text = text.strip()
    if not text:
        raise IntegrationError(
            integration_name="OpenAI",
            message="Cannot generate embedding for empty text"
        )
    
    # Truncate to max token limit (roughly 8000 tokens for embedding models)
    max_chars = 30000  # Approximate limit
    if len(text) > max_chars:
        logger.warning(f"Text truncated from {len(text)} to {max_chars} chars")
        text = text[:max_chars]
    
    try:
        response = client.client.embeddings.create(
            model=model,
            input=text
        )
        
        embedding = response.data[0].embedding
        
        logger.debug(
            f"Generated embedding",
            extra={
                "model": model,
                "dimensions": len(embedding),
                "text_length": len(text)
            }
        )
        
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Embedding generation failed: {str(e)}",
            cause=e
        )


def generate_embeddings_batch(
    texts: list[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = 100
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Number of texts per API call
        
    Returns:
        List of embedding vectors
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    if not texts:
        return []
    
    # Clean texts
    cleaned_texts = [t.strip() for t in texts if t.strip()]
    if not cleaned_texts:
        return []
    
    all_embeddings = []
    
    try:
        # Process in batches
        for i in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[i:i + batch_size]
            
            response = client.client.embeddings.create(
                model=model,
                input=batch
            )
            
            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            logger.debug(
                f"Generated batch embeddings",
                extra={
                    "batch_number": i // batch_size + 1,
                    "batch_size": len(batch)
                }
            )
        
        logger.info(
            f"Generated {len(all_embeddings)} embeddings",
            extra={"model": model}
        )
        
        return all_embeddings
        
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Batch embedding failed: {str(e)}",
            cause=e
        )


async def async_generate_embedding(
    text: str,
    model: str = DEFAULT_EMBEDDING_MODEL
) -> list[float]:
    """
    Async version of embedding generation.
    
    Args:
        text: Text to embed
        model: Embedding model to use
        
    Returns:
        Embedding vector
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    text = text.strip()
    if not text:
        raise IntegrationError(
            integration_name="OpenAI",
            message="Cannot generate embedding for empty text"
        )
    
    try:
        response = await client.async_client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"Async embedding generation failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Async embedding failed: {str(e)}",
            cause=e
        )
