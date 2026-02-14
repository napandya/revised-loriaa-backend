"""Marketing AI agent for campaign optimization and analytics."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.prompts.marketing_prompt import MARKETING_AGENT_PROMPT
from app.agents.tools import analytics_tools, integration_tools
from app.models.agent_activity import AgentType


class MarketingAgent(BaseAgent):
    """
    Marketing AI agent specialized in campaign optimization, performance analysis,
    lead source analytics, and budget recommendations.
    """
    
    def __init__(self):
        """Initialize the marketing agent with appropriate tools."""
        tools = [
            analytics_tools.get_lead_metrics,
            analytics_tools.get_conversion_rate,
            analytics_tools.get_campaign_performance,
            analytics_tools.get_property_stats,
            analytics_tools.get_lead_source_breakdown,
            analytics_tools.calculate_roi,
            integration_tools.update_facebook_campaign,
            integration_tools.track_google_ads_conversion,
            integration_tools.get_facebook_campaign_insights,
            integration_tools.generate_facebook_ad_copy,
            integration_tools.generate_social_ad_copy,
        ]
        
        super().__init__(
            agent_name="MarketingAgent",
            system_prompt=MARKETING_AGENT_PROMPT,
            tools=tools,
            agent_type=AgentType.marketing
        )
    
    def analyze_campaign_performance(
        self,
        campaign_id: Optional[str] = None,
        period: str = "30d",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Analyze marketing campaign performance.
        
        Args:
            campaign_id: Optional specific campaign ID
            period: Time period for analysis
            db: Database session
        
        Returns:
            Dict with analysis results
        """
        task = f"""Analyze marketing campaign performance for the last {period}.
        
        {f'Campaign ID: {campaign_id}' if campaign_id else 'All campaigns'}
        
        Steps:
        1. Get campaign performance metrics
        2. Calculate conversion rates at each funnel stage
        3. Analyze ROI and cost efficiency
        4. Compare to previous period if possible
        5. Identify top performing and underperforming campaigns
        6. Provide specific recommendations for optimization
        
        Provide a comprehensive analysis with actionable insights."""
        
        context = {
            "campaign_id": campaign_id,
            "period": period
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def optimize_lead_sources(
        self,
        property_id: Optional[str] = None,
        period: str = "30d",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Analyze and optimize lead sources.
        
        Args:
            property_id: Optional property ID filter
            period: Time period for analysis
            db: Database session
        
        Returns:
            Dict with optimization recommendations
        """
        task = f"""Analyze lead sources and provide optimization recommendations.
        
        {f'Property ID: {property_id}' if property_id else 'All properties'}
        Period: {period}
        
        Steps:
        1. Get lead source breakdown
        2. Analyze cost per lead by source
        3. Review lead quality scores by source
        4. Calculate conversion rates by source
        5. Identify best and worst performing sources
        6. Recommend budget reallocation
        7. Suggest improvements for underperforming sources
        
        Provide data-driven recommendations for optimizing lead source strategy."""
        
        context = {
            "property_id": property_id,
            "period": period
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def recommend_budget_allocation(
        self,
        total_budget: float,
        property_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Recommend budget allocation across channels.
        
        Args:
            total_budget: Total budget to allocate
            property_id: Optional property ID
            db: Database session
        
        Returns:
            Dict with budget recommendations
        """
        task = f"""Recommend budget allocation for ${total_budget:.2f} marketing budget.
        
        {f'Property ID: {property_id}' if property_id else 'All properties'}
        
        Steps:
        1. Get historical performance by channel
        2. Calculate ROI for each channel
        3. Analyze cost per lease by channel
        4. Consider seasonality and current occupancy
        5. Recommend percentage allocation by channel
        6. Provide rationale for recommendations
        7. Suggest expected outcomes
        
        Provide a detailed budget allocation plan with expected results."""
        
        context = {
            "total_budget": total_budget,
            "property_id": property_id
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def analyze_conversion_funnel(
        self,
        property_id: Optional[str] = None,
        period: str = "30d",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Analyze the lead conversion funnel.
        
        Args:
            property_id: Optional property ID filter
            period: Time period for analysis
            db: Database session
        
        Returns:
            Dict with funnel analysis
        """
        task = f"""Analyze the lead conversion funnel for the last {period}.
        
        {f'Property ID: {property_id}' if property_id else 'All properties'}
        
        Steps:
        1. Get conversion rates at each stage (lead → tour → application → lease)
        2. Identify drop-off points in the funnel
        3. Compare to industry benchmarks if available
        4. Calculate time-to-convert at each stage
        5. Identify bottlenecks and issues
        6. Recommend improvements for low-converting stages
        
        Provide a comprehensive funnel analysis with specific improvement recommendations."""
        
        context = {
            "property_id": property_id,
            "period": period
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def generate_marketing_report(
        self,
        property_id: Optional[str] = None,
        period: str = "30d",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive marketing report.
        
        Args:
            property_id: Optional property ID filter
            period: Time period for report
            db: Database session
        
        Returns:
            Dict with marketing report
        """
        task = f"""Generate a comprehensive marketing performance report.
        
        {f'Property ID: {property_id}' if property_id else 'All properties'}
        Period: {period}
        
        Include:
        1. Executive summary of key metrics
        2. Lead generation performance
        3. Campaign performance breakdown
        4. Lead source analysis
        5. Conversion funnel analysis
        6. ROI analysis
        7. Top wins and challenges
        8. Recommendations for next period
        
        Provide a detailed, executive-ready marketing report."""
        
        context = {
            "property_id": property_id,
            "period": period
        }
        
        return self.execute(task=task, context=context, db=db)
    
    def track_conversion_event(
        self,
        lead_id: str,
        conversion_type: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Track a conversion event in advertising platforms.
        
        Args:
            lead_id: Lead ID that converted
            conversion_type: Type of conversion
            db: Database session
        
        Returns:
            Dict with tracking result
        """
        task = f"""Track conversion event for lead {lead_id}.
        
        Conversion type: {conversion_type}
        
        Steps:
        1. Get lead information and source
        2. Track conversion in Google Ads if applicable
        3. Track conversion in Facebook if applicable
        4. Log the tracking activity
        
        Confirm the conversion has been tracked."""
        
        context = {
            "conversion_type": conversion_type
        }
        
        return self.execute(task=task, context=context, db=db, lead_id=lead_id)
    
    def _get_agent_specific_context(self) -> Dict[str, Any]:
        """Get marketing-specific context."""
        return {
            "agent_type": "marketing",
            "capabilities": [
                "campaign_optimization",
                "performance_analysis",
                "lead_source_analytics",
                "budget_recommendations",
                "roi_analysis"
            ]
        }
