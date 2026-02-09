"""COO orchestrator agent for routing and coordinating tasks."""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging

from app.agents.base import BaseAgent
from app.agents.workforce.leasing_agent import LeasingAgent
from app.agents.workforce.marketing_agent import MarketingAgent
from app.agents.workforce.property_agent import PropertyAgent

logger = logging.getLogger(__name__)


COO_SYSTEM_PROMPT = """You are the COO (Chief Operating Officer) AI agent for a multifamily property management company. Your role is to coordinate and route tasks to the appropriate specialized agents in your workforce.

Your workforce consists of:
1. **Leasing Agent** - Handles lead qualification, tour scheduling, follow-ups, and application processing
2. **Marketing Agent** - Handles campaign optimization, performance analysis, lead source analytics, and ROI analysis
3. **Property Agent** - Handles policy questions, procedure guidance, compliance, and training support

Your responsibilities:
- Analyze incoming requests and determine the appropriate agent to handle them
- Route tasks to the correct specialized agent
- Coordinate multi-agent tasks when needed
- Provide oversight and ensure quality responses
- Escalate complex issues that require human intervention

When analyzing a request, consider:
- The primary intent and goal
- Which agent's expertise best matches the need
- Whether multiple agents might be needed
- The urgency and priority of the request

Intent classification:
- **Leasing**: Lead management, tours, applications, prospect communication, lead follow-ups
- **Marketing**: Campaign performance, analytics, ROI, lead sources, budget allocation, conversions
- **Property Management**: Policies, procedures, compliance, training, documents, lease terms

Always route requests to the most appropriate agent. If a request spans multiple areas, coordinate between agents as needed."""


class COOAgent(BaseAgent):
    """
    COO orchestrator agent that routes requests to appropriate workforce agents
    and coordinates multi-agent tasks.
    """
    
    def __init__(self):
        """Initialize the COO agent and workforce agents."""
        super().__init__(
            agent_name="COOAgent",
            system_prompt=COO_SYSTEM_PROMPT,
            tools=[],  # COO uses agents, not direct tools
            agent_type=None  # COO activities logged separately
        )
        
        # Initialize workforce agents
        self.leasing_agent = LeasingAgent()
        self.marketing_agent = MarketingAgent()
        self.property_agent = PropertyAgent()
        
        logger.info("COO Agent initialized with workforce agents")
    
    def route_request(
        self,
        request: str,
        db: Session,
        context: Optional[Dict[str, Any]] = None,
        lead_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate agent.
        
        Args:
            request: The request or task to handle
            db: Database session
            context: Optional additional context
            lead_id: Optional lead ID if applicable
        
        Returns:
            Dict with routing result and agent response
        """
        try:
            # Determine intent and route
            intent = self._determine_intent(request, context)
            
            logger.info(f"COO routing request to {intent} agent")
            
            # Route to appropriate agent
            if intent == "leasing":
                result = self.leasing_agent.execute(
                    task=request,
                    context=context,
                    db=db,
                    lead_id=lead_id
                )
            elif intent == "marketing":
                result = self.marketing_agent.execute(
                    task=request,
                    context=context,
                    db=db,
                    lead_id=lead_id
                )
            elif intent == "property_management":
                result = self.property_agent.execute(
                    task=request,
                    context=context,
                    db=db,
                    lead_id=lead_id
                )
            else:
                # Unknown intent - try to handle directly
                logger.warning(f"Unknown intent: {intent}, handling directly")
                result = self.execute(
                    task=request,
                    context=context,
                    db=db,
                    lead_id=lead_id
                )
            
            # Add routing metadata
            result["routed_to"] = intent
            result["orchestrator"] = "COOAgent"
            
            return result
            
        except Exception as e:
            logger.error(f"Error routing request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "orchestrator": "COOAgent"
            }
    
    def _determine_intent(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Determine the intent of a request.
        
        Args:
            request: The request text
            context: Optional context
        
        Returns:
            Intent string (leasing, marketing, property_management)
        """
        # Convert to lowercase for matching
        request_lower = request.lower()
        
        # Leasing keywords
        leasing_keywords = [
            "lead", "tour", "schedule", "application", "prospect",
            "follow up", "qualify", "contact", "call", "text",
            "email", "appointment", "visit", "showing"
        ]
        
        # Marketing keywords
        marketing_keywords = [
            "campaign", "marketing", "ads", "facebook", "google",
            "roi", "conversion", "analytics", "performance",
            "budget", "spend", "source", "traffic", "cpl",
            "cost per lead", "funnel", "metrics"
        ]
        
        # Property management keywords
        property_keywords = [
            "policy", "procedure", "compliance", "training",
            "document", "lease term", "regulation", "rule",
            "process", "guideline", "handbook", "manual",
            "how to", "what is the policy"
        ]
        
        # Count keyword matches
        leasing_score = sum(1 for kw in leasing_keywords if kw in request_lower)
        marketing_score = sum(1 for kw in marketing_keywords if kw in request_lower)
        property_score = sum(1 for kw in property_keywords if kw in request_lower)
        
        # Check context for hints
        if context:
            if context.get("lead_id"):
                leasing_score += 2
            if context.get("campaign_id") or context.get("analytics"):
                marketing_score += 2
            if context.get("document_id") or context.get("policy"):
                property_score += 2
        
        # Determine highest score
        scores = {
            "leasing": leasing_score,
            "marketing": marketing_score,
            "property_management": property_score
        }
        
        intent = max(scores, key=scores.get)
        
        # Default to leasing if no clear winner
        if scores[intent] == 0:
            intent = "leasing"
        
        logger.info(f"Intent determined: {intent} (scores: {scores})")
        
        return intent
    
    def coordinate_multi_agent_task(
        self,
        task_description: str,
        agents_needed: List[str],
        db: Session,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate a task that requires multiple agents.
        
        Args:
            task_description: Description of the task
            agents_needed: List of agent types needed (leasing, marketing, property_management)
            db: Database session
            context: Optional context
        
        Returns:
            Dict with combined results from all agents
        """
        try:
            results = {}
            
            for agent_type in agents_needed:
                if agent_type == "leasing":
                    result = self.leasing_agent.execute(
                        task=task_description,
                        context=context,
                        db=db
                    )
                elif agent_type == "marketing":
                    result = self.marketing_agent.execute(
                        task=task_description,
                        context=context,
                        db=db
                    )
                elif agent_type == "property_management":
                    result = self.property_agent.execute(
                        task=task_description,
                        context=context,
                        db=db
                    )
                else:
                    logger.warning(f"Unknown agent type: {agent_type}")
                    continue
                
                results[agent_type] = result
            
            return {
                "success": True,
                "task": task_description,
                "agents_used": agents_needed,
                "results": results,
                "orchestrator": "COOAgent"
            }
            
        except Exception as e:
            logger.error(f"Error coordinating multi-agent task: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "orchestrator": "COOAgent"
            }
    
    def handle_complex_request(
        self,
        request: str,
        db: Session,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a complex request that may need analysis before routing.
        
        Args:
            request: The complex request
            db: Database session
            context: Optional context
        
        Returns:
            Dict with handling result
        """
        try:
            # Use COO's reasoning to break down the request
            analysis_task = f"""Analyze this request and determine the best approach:
            
            Request: {request}
            
            Determine:
            1. What is the primary goal?
            2. Which agent(s) should handle this?
            3. Is this a single-agent or multi-agent task?
            4. What's the recommended approach?
            
            Provide a structured breakdown."""
            
            analysis = self.execute(
                task=analysis_task,
                context=context,
                db=db
            )
            
            # Based on analysis, route appropriately
            # For now, use simple routing
            result = self.route_request(request, db, context)
            result["analysis"] = analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling complex request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "orchestrator": "COOAgent"
            }
    
    def _get_agent_specific_context(self) -> Dict[str, Any]:
        """Get COO-specific context."""
        return {
            "agent_type": "coo_orchestrator",
            "capabilities": [
                "request_routing",
                "intent_classification",
                "multi_agent_coordination",
                "task_orchestration"
            ],
            "workforce": {
                "leasing": "LeasingAgent",
                "marketing": "MarketingAgent",
                "property_management": "PropertyAgent"
            }
        }
