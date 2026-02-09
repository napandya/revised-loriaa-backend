"""AI Agents module for Loriaa platform.

This module provides the agent system for Phase 6, including:
- Base agent class with Google Gemini integration
- COO orchestrator for routing and coordination
- Workforce agents (Leasing, Marketing, Property Management)
- Tools for agent functionality
- System prompts for each agent type
"""

from app.agents.base import BaseAgent
from app.agents.orchestrator import COOAgent
from app.agents.workforce import (
    LeasingAgent,
    MarketingAgent,
    PropertyAgent
)

__all__ = [
    "BaseAgent",
    "COOAgent",
    "LeasingAgent",
    "MarketingAgent",
    "PropertyAgent"
]
