"""Leasing AI agent for lead management and tours."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.prompts.leasing_prompt import LEASING_AGENT_PROMPT
from app.agents.tools import lead_tools, communication_tools, scheduling_tools
from app.models.agent_activity import AgentType


class LeasingAgent(BaseAgent):
    """
    Leasing AI agent specialized in lead qualification, tour scheduling,
    follow-ups, and application processing.
    """
    
    def __init__(self):
        """Initialize the leasing agent with appropriate tools."""
        tools = [
            lead_tools.get_lead_info,
            lead_tools.update_lead_status,
            lead_tools.score_lead,
            lead_tools.assign_lead,
            lead_tools.create_lead_note,
            communication_tools.send_sms,
            communication_tools.send_email,
            communication_tools.log_interaction,
            scheduling_tools.check_availability,
            scheduling_tools.schedule_tour,
            scheduling_tools.reschedule_tour,
            scheduling_tools.cancel_tour
        ]
        
        super().__init__(
            agent_name="LeasingAgent",
            system_prompt=LEASING_AGENT_PROMPT,
            tools=tools,
            agent_type=AgentType.leasing
        )
    
    def qualify_lead(
        self,
        lead_id: str,
        db: Session,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Qualify a lead by gathering key information and scoring.
        
        Args:
            lead_id: UUID of the lead
            db: Database session
            context: Optional additional context
        
        Returns:
            Dict with qualification result
        """
        task = f"""Qualify the lead with ID {lead_id}. 
        
        Steps:
        1. Get the lead information
        2. Analyze their budget, move-in date, and requirements
        3. Score the lead based on qualification criteria
        4. Update the lead status if appropriate
        5. Add a note with qualification summary
        
        Provide a summary of the lead's qualification status and any recommended next steps."""
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def schedule_lead_tour(
        self,
        lead_id: str,
        date: str,
        time_slot: str,
        property_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Schedule a tour for a lead.
        
        Args:
            lead_id: UUID of the lead
            date: Tour date (YYYY-MM-DD)
            time_slot: Time slot for tour
            property_id: Property ID
            db: Database session
        
        Returns:
            Dict with scheduling result
        """
        task = f"""Schedule a tour for lead {lead_id}.
        
        Details:
        - Date: {date}
        - Time: {time_slot}
        - Property: {property_id}
        
        Steps:
        1. Check availability for the requested time
        2. If available, schedule the tour
        3. Send confirmation SMS and email to the lead
        4. Update lead status to 'tour_scheduled'
        5. Add a note about the scheduled tour
        
        Confirm the tour is scheduled and provide the details."""
        
        context = {
            "date": date,
            "time_slot": time_slot,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def follow_up_with_lead(
        self,
        lead_id: str,
        db: Session,
        follow_up_reason: str = "general"
    ) -> Dict[str, Any]:
        """
        Follow up with a lead.
        
        Args:
            lead_id: UUID of the lead
            db: Database session
            follow_up_reason: Reason for follow-up
        
        Returns:
            Dict with follow-up result
        """
        task = f"""Follow up with lead {lead_id} for: {follow_up_reason}
        
        Steps:
        1. Get the lead information and recent activity
        2. Determine appropriate follow-up message based on their status and engagement
        3. Send follow-up via their preferred communication method
        4. Log the interaction
        5. Update lead status if needed
        
        Provide a summary of the follow-up action taken."""
        
        context = {"follow_up_reason": follow_up_reason}
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def handle_tour_request(
        self,
        lead_id: str,
        db: Session,
        preferred_dates: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle a tour request from a lead.
        
        Args:
            lead_id: UUID of the lead
            db: Database session
            preferred_dates: Optional preferred dates/times
        
        Returns:
            Dict with handling result
        """
        task = f"""Handle tour request from lead {lead_id}.
        
        {f'Preferred dates/times: {preferred_dates}' if preferred_dates else 'No specific dates provided.'}
        
        Steps:
        1. Get lead information
        2. If specific dates provided, check availability
        3. If available, schedule the tour
        4. If not available or no dates provided, offer alternative time slots
        5. Send confirmation or options via SMS/email
        6. Update lead status and add notes
        
        Confirm the tour scheduling or provide next steps."""
        
        context = {"preferred_dates": preferred_dates} if preferred_dates else {}
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def process_application(
        self,
        lead_id: str,
        db: Session,
        application_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a rental application.
        
        Args:
            lead_id: UUID of the lead
            db: Database session
            application_data: Optional application data
        
        Returns:
            Dict with processing result
        """
        task = f"""Process rental application for lead {lead_id}.
        
        Steps:
        1. Get lead information
        2. Review application completeness
        3. Update lead status to 'application_submitted'
        4. Send confirmation to the lead
        5. Notify property team about new application
        6. Add detailed notes about the application
        
        Confirm the application has been received and provide next steps."""
        
        context = {"application_data": application_data} if application_data else {}
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def _get_agent_specific_context(self) -> Dict[str, Any]:
        """Get leasing-specific context."""
        return {
            "agent_type": "leasing",
            "capabilities": [
                "lead_qualification",
                "tour_scheduling",
                "follow_ups",
                "application_processing"
            ]
        }
