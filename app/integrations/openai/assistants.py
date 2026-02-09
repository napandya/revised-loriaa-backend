"""
OpenAI Assistants API for Loriaa AI CRM.

Provides AI assistants for:
- Leasing Agent assistant
- Marketing Agent assistant
- Property Manager assistant

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.integrations.openai.client import get_openai_client
from app.core.exceptions import IntegrationError

logger = logging.getLogger(__name__)


# Assistant configurations
LEASING_ASSISTANT_CONFIG = {
    "name": "Loriaa Leasing Agent",
    "instructions": """You are Loriaa, an AI leasing assistant for property management.

Your responsibilities:
1. Answer prospect inquiries about available units, pricing, and amenities
2. Schedule property tours and follow up on leads
3. Qualify leads based on their requirements and budget
4. Provide information about lease terms, policies, and move-in procedures
5. Handle objections and address concerns professionally

Guidelines:
- Be friendly, professional, and responsive
- Always try to move prospects toward scheduling a tour
- Collect contact information when appropriate
- Escalate complex issues to human agents
- Never make promises about pricing or availability without verification""",
    "model": "gpt-4o",
    "tools": [
        {"type": "code_interpreter"},
        {"type": "file_search"}
    ]
}


MARKETING_ASSISTANT_CONFIG = {
    "name": "Loriaa Marketing Agent",
    "instructions": """You are Loriaa, an AI marketing assistant for property management.

Your responsibilities:
1. Create compelling property listings and descriptions
2. Generate social media content for property promotion
3. Analyze marketing campaign performance
4. Suggest targeting strategies for different demographics
5. Create email marketing content for lead nurturing

Guidelines:
- Write engaging, professional copy
- Highlight unique property features and benefits
- Use data-driven insights for recommendations
- Maintain brand voice consistency
- Follow fair housing guidelines in all content""",
    "model": "gpt-4o",
    "tools": [
        {"type": "code_interpreter"}
    ]
}


def create_leasing_assistant(
    property_files: Optional[list[str]] = None
) -> dict:
    """
    Create or retrieve the leasing assistant.
    
    Args:
        property_files: Optional list of file IDs to attach
        
    Returns:
        Assistant object dict
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    try:
        # Create assistant
        config = LEASING_ASSISTANT_CONFIG.copy()
        
        if property_files:
            config["file_ids"] = property_files
        
        assistant = client.client.beta.assistants.create(**config)
        
        logger.info(f"Created leasing assistant: {assistant.id}")
        
        return {
            "id": assistant.id,
            "name": assistant.name,
            "model": assistant.model,
            "created_at": assistant.created_at
        }
        
    except Exception as e:
        logger.error(f"Failed to create leasing assistant: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Failed to create assistant: {str(e)}",
            cause=e
        )


def create_marketing_assistant() -> dict:
    """
    Create or retrieve the marketing assistant.
    
    Returns:
        Assistant object dict
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    try:
        assistant = client.client.beta.assistants.create(**MARKETING_ASSISTANT_CONFIG)
        
        logger.info(f"Created marketing assistant: {assistant.id}")
        
        return {
            "id": assistant.id,
            "name": assistant.name,
            "model": assistant.model,
            "created_at": assistant.created_at
        }
        
    except Exception as e:
        logger.error(f"Failed to create marketing assistant: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Failed to create assistant: {str(e)}",
            cause=e
        )


def run_assistant(
    assistant_id: str,
    user_message: str,
    thread_id: Optional[str] = None,
    additional_instructions: Optional[str] = None
) -> dict:
    """
    Run an assistant with a user message.
    
    Args:
        assistant_id: The assistant ID to use
        user_message: User's message
        thread_id: Optional existing thread ID
        additional_instructions: Optional additional context
        
    Returns:
        Dict with response and thread_id
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    try:
        # Create or use existing thread
        if thread_id:
            thread = client.client.beta.threads.retrieve(thread_id)
        else:
            thread = client.client.beta.threads.create()
        
        # Add user message to thread
        client.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        
        # Run the assistant
        run = client.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            additional_instructions=additional_instructions
        )
        
        if run.status == "completed":
            # Get the assistant's response
            messages = client.client.beta.threads.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            response_message = messages.data[0]
            response_text = response_message.content[0].text.value
            
            logger.info(
                f"Assistant run completed",
                extra={
                    "assistant_id": assistant_id,
                    "thread_id": thread.id,
                    "run_id": run.id
                }
            )
            
            return {
                "response": response_text,
                "thread_id": thread.id,
                "run_id": run.id,
                "status": "completed"
            }
        else:
            logger.warning(f"Assistant run failed with status: {run.status}")
            return {
                "response": None,
                "thread_id": thread.id,
                "run_id": run.id,
                "status": run.status,
                "error": getattr(run, 'last_error', None)
            }
            
    except Exception as e:
        logger.error(f"Assistant run failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Assistant run failed: {str(e)}",
            cause=e
        )


async def async_run_assistant(
    assistant_id: str,
    user_message: str,
    thread_id: Optional[str] = None
) -> dict:
    """
    Async version of run_assistant.
    """
    client = get_openai_client()
    
    if not client.is_configured():
        raise IntegrationError(
            integration_name="OpenAI",
            message="OpenAI API key not configured"
        )
    
    try:
        # Create or use existing thread
        if thread_id:
            thread = await client.async_client.beta.threads.retrieve(thread_id)
        else:
            thread = await client.async_client.beta.threads.create()
        
        # Add user message
        await client.async_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )
        
        # Run assistant
        run = await client.async_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        if run.status == "completed":
            messages = await client.async_client.beta.threads.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            response_text = messages.data[0].content[0].text.value
            
            return {
                "response": response_text,
                "thread_id": thread.id,
                "run_id": run.id,
                "status": "completed"
            }
        else:
            return {
                "response": None,
                "thread_id": thread.id,
                "status": run.status
            }
            
    except Exception as e:
        logger.error(f"Async assistant run failed: {e}")
        raise IntegrationError(
            integration_name="OpenAI",
            message=f"Async assistant run failed: {str(e)}",
            cause=e
        )
