"""
OpenAI Integration Module for Loriaa AI CRM.

This module provides:
- OpenAI client initialization
- Chat completions (GPT-4, GPT-3.5)
- Embeddings generation
- Text-to-Speech and Speech-to-Text
- Error handling with retries

Python 3.13 Compatible.
"""

from app.integrations.openai.client import (
    OpenAIClient,
    get_openai_client,
)
from app.integrations.openai.chat import (
    chat_completion,
    chat_completion_stream,
    generate_lead_response,
    generate_property_description,
    summarize_conversation,
)
from app.integrations.openai.embeddings import (
    generate_embedding,
    generate_embeddings_batch,
)
from app.integrations.openai.assistants import (
    create_leasing_assistant,
    create_marketing_assistant,
    run_assistant,
)

__all__ = [
    # Client
    "OpenAIClient",
    "get_openai_client",
    
    # Chat
    "chat_completion",
    "chat_completion_stream",
    "generate_lead_response",
    "generate_property_description",
    "summarize_conversation",
    
    # Embeddings
    "generate_embedding",
    "generate_embeddings_batch",
    
    # Assistants
    "create_leasing_assistant",
    "create_marketing_assistant",
    "run_assistant",
]
