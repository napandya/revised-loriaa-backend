"""Vapi assistant management and configuration."""

from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.integrations.vapi.client import vapi_client


# Default system prompt for leasing assistant
DEFAULT_LEASING_PROMPT = """You are a friendly and professional leasing agent AI assistant. Your role is to:

1. Greet callers warmly and ask how you can help them today
2. Answer questions about available units, pricing, and amenities
3. Qualify leads by understanding their needs:
   - Budget/price range
   - Number of bedrooms needed
   - Desired move-in date
   - Any special requirements
4. Schedule property tours when interested
5. Transfer to a human agent when requested or for complex situations

Guidelines:
- Be conversational and natural
- Ask clarifying questions to understand needs
- Provide accurate information
- Be enthusiastic about the property
- Handle objections professionally
- Always confirm important details

Use the available functions to check availability, schedule tours, and qualify leads.
"""


# Function definitions for Vapi assistant
def get_assistant_functions() -> List[Dict[str, Any]]:
    """Get function definitions for Vapi assistant.
    
    Returns:
        List of function definitions
    """
    return [
        {
            "name": "check_availability",
            "description": "Check if units are available for given criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID to check availability for"
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Number of bedrooms needed"
                    },
                    "move_in_date": {
                        "type": "string",
                        "description": "Desired move-in date (YYYY-MM-DD)"
                    }
                },
                "required": ["property_id", "bedrooms"]
            }
        },
        {
            "name": "schedule_tour",
            "description": "Schedule a property tour for a prospect",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_id": {
                        "type": "string",
                        "description": "Property ID"
                    },
                    "lead_name": {
                        "type": "string",
                        "description": "Name of the person scheduling the tour"
                    },
                    "lead_phone": {
                        "type": "string",
                        "description": "Phone number of the person"
                    },
                    "preferred_date": {
                        "type": "string",
                        "description": "Preferred tour date and time"
                    }
                },
                "required": ["property_id", "lead_name", "lead_phone", "preferred_date"]
            }
        },
        {
            "name": "qualify_lead",
            "description": "Qualify a lead based on their requirements",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget": {
                        "type": "number",
                        "description": "Monthly budget for rent"
                    },
                    "move_in_timeline": {
                        "type": "string",
                        "description": "When they plan to move in",
                        "enum": ["immediately", "1-2 weeks", "1 month", "2-3 months", "3+ months"]
                    },
                    "bedrooms": {
                        "type": "integer",
                        "description": "Number of bedrooms needed"
                    }
                },
                "required": ["budget", "move_in_timeline", "bedrooms"]
            }
        },
        {
            "name": "transfer_to_human",
            "description": "Transfer the call to a human leasing agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for transfer"
                    }
                },
                "required": ["reason"]
            }
        }
    ]


async def create_property_assistant(
    property_id: str,
    property_name: str,
    system_prompt: Optional[str] = None,
    first_message: Optional[str] = None,
    voice_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a Vapi assistant for a property.
    
    Args:
        property_id: Property/bot ID
        property_name: Name of the property
        system_prompt: Optional custom system prompt
        first_message: Optional custom first message
        voice_id: Optional custom voice ID
        
    Returns:
        Created assistant data with assistant_id
    """
    # Use defaults if not provided
    if not system_prompt:
        system_prompt = DEFAULT_LEASING_PROMPT
    
    if not first_message:
        first_message = f"Hello! Thank you for calling {property_name}. I'm your AI leasing assistant. How can I help you today?"
    
    if not voice_id:
        # Use different voices based on provider
        if settings.ELEVENLABS_API_KEY:
            voice_id = "EXAVITQu4vr4xnSDxMaL"  # ElevenLabs Sarah voice
        else:
            voice_id = "en-US-Neural2-F"  # Google Cloud female voice
    
    # Get function definitions
    functions = get_assistant_functions()
    
    # Create assistant via Vapi client
    assistant = await vapi_client.create_assistant(
        name=f"{property_name} Leasing Assistant",
        first_message=first_message,
        system_prompt=system_prompt,
        model="gpt-4",
        voice_id=voice_id,
        functions=functions
    )
    
    return assistant


async def configure_assistant_functions(assistant_id: str) -> Dict[str, Any]:
    """Configure or update function calling for an assistant.
    
    Args:
        assistant_id: Assistant ID to configure
        
    Returns:
        Updated assistant configuration
    """
    functions = get_assistant_functions()
    
    return await vapi_client.update_assistant(
        assistant_id=assistant_id,
        functions=functions
    )


async def update_assistant_knowledge(
    assistant_id: str,
    knowledge_base_text: str
) -> Dict[str, Any]:
    """Update assistant's knowledge base with property information.
    
    Args:
        assistant_id: Assistant ID to update
        knowledge_base_text: Knowledge base content (amenities, pricing, etc.)
        
    Returns:
        Updated assistant configuration
    """
    # Enhance system prompt with knowledge base
    enhanced_prompt = f"""{DEFAULT_LEASING_PROMPT}

Property Information:
{knowledge_base_text}

Use this information to answer questions about the property accurately.
"""
    
    return await vapi_client.update_assistant(
        assistant_id=assistant_id,
        system_prompt=enhanced_prompt
    )


def get_default_voice_config(provider: str = "auto") -> Dict[str, Any]:
    """Get default voice configuration.
    
    Args:
        provider: Voice provider ("elevenlabs", "playht", or "auto")
        
    Returns:
        Voice configuration
    """
    if provider == "auto":
        if settings.ELEVENLABS_API_KEY:
            provider = "elevenlabs"
        else:
            provider = "playht"
    
    if provider == "elevenlabs":
        return {
            "provider": "11labs",
            "voiceId": "EXAVITQu4vr4xnSDxMaL",  # Sarah - professional female voice
            "stability": 0.5,
            "similarityBoost": 0.75
        }
    else:  # playht
        return {
            "provider": "playht",
            "voiceId": "en-US-Neural2-F",
            "speed": 1.0
        }


async def clone_assistant(
    source_assistant_id: str,
    new_property_name: str
) -> Dict[str, Any]:
    """Clone an existing assistant for a new property.
    
    Args:
        source_assistant_id: ID of assistant to clone
        new_property_name: Name of the new property
        
    Returns:
        New assistant data
    """
    # Get source assistant
    source = await vapi_client.get_assistant(source_assistant_id)
    
    # Create new assistant with same configuration
    new_assistant = await vapi_client.create_assistant(
        name=f"{new_property_name} Leasing Assistant",
        first_message=source.get("firstMessage", "").replace(
            source.get("name", ""),
            new_property_name
        ),
        system_prompt=source.get("model", {}).get("messages", [{}])[0].get("content", DEFAULT_LEASING_PROMPT),
        model=source.get("model", {}).get("model", "gpt-4"),
        voice_id=source.get("voice", {}).get("voiceId", "en-US-Neural2-F"),
        functions=source.get("model", {}).get("functions", get_assistant_functions())
    )
    
    return new_assistant


async def test_assistant(
    assistant_id: str,
    test_phone_number: str
) -> Dict[str, Any]:
    """Make a test call to verify assistant configuration.
    
    Args:
        assistant_id: Assistant ID to test
        test_phone_number: Phone number to call for testing
        
    Returns:
        Test call result
    """
    return await vapi_client.make_outbound_call(
        assistant_id=assistant_id,
        customer_number=test_phone_number,
        customer_name="Test Call",
        metadata={"test": True}
    )
