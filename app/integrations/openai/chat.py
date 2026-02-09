"""
OpenAI Chat Completions for Loriaa AI CRM.

Provides specialized chat functions for:
- Lead response generation
- Property descriptions
- Conversation summarization
- General chat completions

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Optional, Generator, AsyncGenerator

from openai import OpenAI

from app.integrations.openai.client import get_openai_client
from app.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)

# Default models
DEFAULT_MODEL = "gpt-4o"
FAST_MODEL = "gpt-3.5-turbo"


def chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    Generate a chat completion.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (default: gpt-4o)
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt to prepend
        
    Returns:
        Generated response text
        
    Raises:
        IntegrationError: On API errors
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    # Prepend system prompt if provided
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        response = client.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content
        
        logger.info(
            f"Chat completion generated",
            extra={
                "model": model,
                "input_messages": len(messages),
                "output_tokens": response.usage.completion_tokens if response.usage else None
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Chat completion failed: {str(e)}",
            cause=e
        )


def chat_completion_stream(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Generate a streaming chat completion.
    
    Args:
        messages: List of message dicts
        model: Model to use
        temperature: Sampling temperature
        system_prompt: Optional system prompt
        
    Yields:
        Response text chunks
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        stream = client.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Streaming chat completion failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Streaming failed: {str(e)}",
            cause=e
        )


# ============================================================
# Specialized Chat Functions for Property Management
# ============================================================

LEASING_SYSTEM_PROMPT = """You are Loriaa, an AI leasing assistant for a property management company. 
You help prospective tenants with:
- Answering questions about available units, pricing, and amenities
- Scheduling tours and appointments
- Explaining lease terms and policies
- Providing information about the community and neighborhood

Be friendly, professional, and helpful. If you don't know something, say so and offer to connect them with a human agent.
Always encourage prospects to schedule a tour."""


def generate_lead_response(
    lead_message: str,
    lead_context: Optional[dict] = None,
    conversation_history: Optional[list[dict]] = None,
    property_info: Optional[str] = None
) -> str:
    """
    Generate a response to a lead inquiry.
    
    Args:
        lead_message: The lead's message
        lead_context: Optional lead info (name, interest, etc.)
        conversation_history: Previous messages in the conversation
        property_info: Property-specific information to include
        
    Returns:
        AI-generated response
    """
    system_prompt = LEASING_SYSTEM_PROMPT
    
    # Add property info to system prompt
    if property_info:
        system_prompt += f"\n\nProperty Information:\n{property_info}"
    
    # Add lead context
    if lead_context:
        context_str = "\n".join([f"- {k}: {v}" for k, v in lead_context.items()])
        system_prompt += f"\n\nLead Information:\n{context_str}"
    
    # Build messages
    messages = conversation_history or []
    messages.append({"role": "user", "content": lead_message})
    
    return chat_completion(
        messages=messages,
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=500
    )


PROPERTY_DESCRIPTION_PROMPT = """You are a real estate copywriter creating compelling property listings.
Write engaging, professional descriptions that highlight key features and benefits.
Use descriptive language that helps prospects visualize living in the space.
Keep descriptions concise but impactful."""


def generate_property_description(
    property_details: dict,
    style: str = "professional"
) -> str:
    """
    Generate a property listing description.
    
    Args:
        property_details: Dict with unit info (beds, baths, sqft, amenities, etc.)
        style: Writing style ('professional', 'casual', 'luxury')
        
    Returns:
        Generated property description
    """
    details_str = "\n".join([f"- {k}: {v}" for k, v in property_details.items()])
    
    user_message = f"""Create a {style} property listing description for:

{details_str}

Write 2-3 paragraphs highlighting the best features."""
    
    return chat_completion(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=PROPERTY_DESCRIPTION_PROMPT,
        temperature=0.8,
        max_tokens=400
    )


SUMMARIZATION_PROMPT = """You are an assistant that summarizes conversations between leasing agents and prospects.
Create concise summaries that capture:
- Key topics discussed
- Prospect's interests and concerns
- Any action items or next steps
- Overall sentiment (positive/neutral/negative)"""


def summarize_conversation(
    messages: list[dict],
    include_sentiment: bool = True
) -> dict:
    """
    Summarize a conversation between agent and prospect.
    
    Args:
        messages: List of conversation messages
        include_sentiment: Whether to include sentiment analysis
        
    Returns:
        Dict with summary, key_points, action_items, sentiment
    """
    # Format messages for summarization
    formatted = "\n".join([
        f"{msg.get('sender', msg.get('role', 'Unknown'))}: {msg.get('content', msg.get('text', ''))}"
        for msg in messages
    ])
    
    user_message = f"""Summarize this conversation:

{formatted}

Provide:
1. Brief summary (2-3 sentences)
2. Key points discussed (bullet points)
3. Action items or next steps
{"4. Overall sentiment (positive/neutral/negative)" if include_sentiment else ""}

Format as JSON."""
    
    response = chat_completion(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SUMMARIZATION_PROMPT,
        temperature=0.3,
        max_tokens=500
    )
    
    # Try to parse as JSON, fallback to raw text
    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "summary": response,
            "key_points": [],
            "action_items": [],
            "sentiment": "unknown"
        }


async def async_chat_completion(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    Async version of chat completion.
    
    Args:
        messages: List of message dicts
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        system_prompt: Optional system prompt
        
    Returns:
        Generated response text
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    if system_prompt:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        response = await client.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Async chat completion failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Async chat completion failed: {str(e)}",
            cause=e
        )
