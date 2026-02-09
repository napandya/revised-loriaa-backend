"""Analytics service for COO Command Center metrics and insights."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, distinct

from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.conversation import Conversation, ConversationStatus
from app.models.lead_activity import LeadActivity, ActivityType
from app.models.agent_activity import AgentActivity, AgentType
from app.models.call_log import CallLog
from app.models.bot import Bot
from app.schemas.dashboard import (
    DashboardMetrics,
    MarketingFunnelData,
    LeasingVelocityData,
    LeasingVelocityDataPoint,
    AgentActivityFeed,
    AgentActivityItem,
    PortfolioHealthScore,
    PropertyHealthMetrics
)
from app.core.exceptions import DatabaseError


class AnalyticsService:
    """Analytics service class wrapper for agent tools."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_lead_metrics(
        self,
        start_date: datetime,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get lead metrics for a time period."""
        query = self.db.query(Lead).filter(Lead.created_at >= start_date)
        
        if property_id:
            query = query.filter(Lead.property_id == UUID(property_id))
        
        total_leads = query.count()
        new_leads = query.filter(Lead.status == LeadStatus.new).count()
        contacted_leads = query.filter(Lead.status == LeadStatus.contacted).count()
        qualified_leads = query.filter(Lead.status == LeadStatus.qualified).count()
        touring_leads = query.filter(Lead.status == LeadStatus.touring).count()
        application_leads = query.filter(Lead.status == LeadStatus.application).count()
        leased_leads = query.filter(Lead.status == LeadStatus.lease).count()
        lost_leads = query.filter(Lead.status == LeadStatus.lost).count()
        
        return {
            "total_leads": total_leads,
            "new": new_leads,
            "contacted": contacted_leads,
            "qualified": qualified_leads,
            "touring": touring_leads,
            "application": application_leads,
            "leased": leased_leads,
            "lost": lost_leads,
            "conversion_rate": (leased_leads / total_leads * 100) if total_leads > 0 else 0
        }
    
    def get_conversion_rate(
        self,
        funnel_stage: str,
        start_date: datetime,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversion rate for a funnel stage."""
        query = self.db.query(Lead).filter(Lead.created_at >= start_date)
        
        if property_id:
            query = query.filter(Lead.property_id == UUID(property_id))
        
        # Define funnel stage mappings
        stage_mappings = {
            "lead_to_tour": (
                [LeadStatus.touring, LeadStatus.application, LeadStatus.lease, LeadStatus.move_in],
                [LeadStatus.new, LeadStatus.contacted, LeadStatus.qualified, LeadStatus.touring, 
                 LeadStatus.application, LeadStatus.lease, LeadStatus.move_in, LeadStatus.lost]
            ),
            "tour_to_app": (
                [LeadStatus.application, LeadStatus.lease, LeadStatus.move_in],
                [LeadStatus.touring, LeadStatus.application, LeadStatus.lease, LeadStatus.move_in]
            ),
            "app_to_lease": (
                [LeadStatus.lease, LeadStatus.move_in],
                [LeadStatus.application, LeadStatus.lease, LeadStatus.move_in]
            )
        }
        
        if funnel_stage not in stage_mappings:
            return {"rate": 0, "converted": 0, "total": 0}
        
        converted_statuses, total_statuses = stage_mappings[funnel_stage]
        converted = query.filter(Lead.status.in_(converted_statuses)).count()
        total = query.filter(Lead.status.in_(total_statuses)).count()
        
        return {
            "rate": (converted / total * 100) if total > 0 else 0,
            "converted": converted,
            "total": total
        }
    
    def get_campaign_performance(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get campaign performance metrics."""
        query = self.db.query(Lead)
        
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        
        # Group by source
        campaigns = []
        for source in LeadSource:
            count = query.filter(Lead.source == source).count()
            if count > 0:
                campaigns.append({
                    "source": source.value,
                    "leads": count,
                    "cost_per_lead": 0,  # Would need campaign cost data
                    "conversion_rate": 0  # Would calculate from lease status
                })
        
        return campaigns
    
    def get_property_performance(
        self,
        property_id: str,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific property."""
        query = self.db.query(Lead).filter(Lead.property_id == UUID(property_id))
        
        if start_date:
            query = query.filter(Lead.created_at >= start_date)
        
        total = query.count()
        leased = query.filter(Lead.status == LeadStatus.lease).count()
        
        return {
            "property_id": property_id,
            "total_leads": total,
            "leased": leased,
            "conversion_rate": (leased / total * 100) if total > 0 else 0
        }
    
    def compare_periods(
        self,
        metric: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare metrics between two time periods."""
        base_query = self.db.query(Lead)
        if property_id:
            base_query = base_query.filter(Lead.property_id == UUID(property_id))
        
        period1_count = base_query.filter(
            and_(Lead.created_at >= period1_start, Lead.created_at <= period1_end)
        ).count()
        
        period2_count = base_query.filter(
            and_(Lead.created_at >= period2_start, Lead.created_at <= period2_end)
        ).count()
        
        change = period2_count - period1_count
        change_percent = (change / period1_count * 100) if period1_count > 0 else 0
        
        return {
            "metric": metric,
            "period1_value": period1_count,
            "period2_value": period2_count,
            "change": change,
            "change_percent": change_percent
        }


async def get_dashboard_metrics(
    db: Session,
    user_id: Optional[UUID] = None,
    property_id: Optional[UUID] = None
) -> DashboardMetrics:
    """
    Calculate comprehensive dashboard metrics for COO Command Center.
    
    Args:
        db: Database session
        user_id: Filter by user
        property_id: Filter by property
        
    Returns:
        DashboardMetrics with all key performance indicators
        
    Raises:
        DatabaseError: If calculation fails
    """
    try:
        # Base query for leads
        lead_query = db.query(Lead)
        if user_id:
            lead_query = lead_query.filter(Lead.user_id == user_id)
        if property_id:
            lead_query = lead_query.filter(Lead.property_id == property_id)
        
        # Total leads
        total_leads = lead_query.count()
        
        # Active conversations
        conv_query = db.query(Conversation).join(Lead)
        if user_id:
            conv_query = conv_query.filter(Lead.user_id == user_id)
        if property_id:
            conv_query = conv_query.filter(Lead.property_id == property_id)
        active_conversations = conv_query.filter(
            Conversation.status == ConversationStatus.open
        ).count()
        
        # Tours scheduled (leads in touring status or tour_scheduled activities)
        tours_scheduled = lead_query.filter(
            Lead.status == LeadStatus.touring
        ).count()
        
        # Applications pending
        applications_pending = lead_query.filter(
            Lead.status == LeadStatus.application
        ).count()
        
        # Leases signed (this month)
        now = datetime.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        leases_signed = lead_query.filter(
            and_(
                Lead.status.in_([LeadStatus.lease, LeadStatus.move_in]),
                Lead.updated_at >= first_day_of_month
            )
        ).count()
        
        # Occupancy rate (mock calculation - would integrate with PMS in production)
        occupancy_rate = 92.5  # TODO: Get from ResMan integration
        
        # Revenue this month (mock - would come from billing/PMS)
        revenue_this_month = leases_signed * 1800.0  # Average rent estimate
        
        # AI call minutes (from call logs this month)
        call_query = db.query(CallLog)
        if property_id:
            call_query = call_query.filter(CallLog.bot_id == property_id)
        
        total_duration = call_query.filter(
            CallLog.created_at >= first_day_of_month
        ).with_entities(
            func.sum(CallLog.duration)
        ).scalar() or 0
        
        ai_call_minutes = int(total_duration / 60) if total_duration else 0
        
        # Average response time (in hours)
        # Calculate time between inbound messages and first outbound response
        response_times = []
        recent_convs = conv_query.limit(100).all()
        for conv in recent_convs:
            # Simple estimation based on conversation data
            if conv.last_message_at and conv.created_at:
                time_diff = (conv.last_message_at - conv.created_at).total_seconds() / 3600
                if time_diff > 0 and time_diff < 48:  # Filter outliers
                    response_times.append(time_diff)
        
        average_response_time = sum(response_times) / len(response_times) if response_times else 2.5
        
        # Conversion rate (leads that converted to lease)
        converted = lead_query.filter(
            Lead.status.in_([LeadStatus.lease, LeadStatus.move_in])
        ).count()
        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0.0
        
        return DashboardMetrics(
            total_leads=total_leads,
            active_conversations=active_conversations,
            tours_scheduled=tours_scheduled,
            applications_pending=applications_pending,
            leases_signed=leases_signed,
            occupancy_rate=occupancy_rate,
            revenue_this_month=revenue_this_month,
            ai_call_minutes=ai_call_minutes,
            average_response_time=average_response_time,
            conversion_rate=conversion_rate
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to calculate dashboard metrics: {str(e)}")


async def get_marketing_funnel(
    db: Session,
    property_id: Optional[UUID] = None,
    days: int = 30
) -> List[MarketingFunnelData]:
    """
    Calculate marketing funnel conversion data.
    
    Args:
        db: Database session
        property_id: Filter by property
        days: Number of days to look back
        
    Returns:
        List of MarketingFunnelData for each stage
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        last_month_cutoff = datetime.now() - timedelta(days=days*2)
        
        # Build query
        query = db.query(Lead).filter(Lead.created_at >= last_month_cutoff)
        current_query = db.query(Lead).filter(Lead.created_at >= cutoff_date)
        
        if property_id:
            query = query.filter(Lead.property_id == property_id)
            current_query = current_query.filter(Lead.property_id == property_id)
        
        # Get totals
        total_current = current_query.count()
        total_previous = query.filter(
            Lead.created_at < cutoff_date
        ).count()
        
        # Define funnel stages
        stages = [
            ("New Leads", [LeadStatus.new]),
            ("Contacted", [LeadStatus.contacted]),
            ("Qualified", [LeadStatus.qualified]),
            ("Tours", [LeadStatus.touring]),
            ("Applications", [LeadStatus.application]),
            ("Leases", [LeadStatus.lease, LeadStatus.move_in])
        ]
        
        funnel_data = []
        
        for stage_name, statuses in stages:
            # Current period count
            current_count = current_query.filter(
                Lead.status.in_(statuses)
            ).count()
            
            # Previous period count
            previous_count = query.filter(
                and_(
                    Lead.status.in_(statuses),
                    Lead.created_at < cutoff_date
                )
            ).count()
            
            # Conversion rate (percentage of total leads that reached this stage)
            conversion_rate = (current_count / total_current * 100) if total_current > 0 else 0.0
            
            # Change from last period
            change_pct = 0.0
            if previous_count > 0:
                change_pct = ((current_count - previous_count) / previous_count) * 100
            elif current_count > 0:
                change_pct = 100.0
            
            funnel_data.append(MarketingFunnelData(
                stage=stage_name,
                count=current_count,
                conversion_rate=conversion_rate,
                change_from_last_month=change_pct
            ))
        
        return funnel_data
        
    except Exception as e:
        raise DatabaseError(f"Failed to calculate marketing funnel: {str(e)}")


async def get_leasing_velocity(
    db: Session,
    property_id: Optional[UUID] = None,
    days: int = 30
) -> LeasingVelocityData:
    """
    Calculate leasing velocity over time.
    
    Args:
        db: Database session
        property_id: Filter by property
        days: Number of days to analyze
        
    Returns:
        LeasingVelocityData with time series and metrics
    """
    try:
        # Get daily data points
        data_points = []
        start_date = datetime.now() - timedelta(days=days)
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            next_date = current_date + timedelta(days=1)
            
            query = db.query(Lead).filter(
                and_(
                    Lead.created_at >= current_date,
                    Lead.created_at < next_date
                )
            )
            
            if property_id:
                query = query.filter(Lead.property_id == property_id)
            
            # Count by status for this day
            tours = query.filter(Lead.status == LeadStatus.touring).count()
            applications = query.filter(Lead.status == LeadStatus.application).count()
            leases = query.filter(Lead.status.in_([LeadStatus.lease, LeadStatus.move_in])).count()
            
            data_points.append(LeasingVelocityDataPoint(
                date=current_date,
                tours=tours,
                applications=applications,
                leases=leases
            ))
        
        # Calculate average days to lease
        lease_query = db.query(Lead).filter(
            and_(
                Lead.status.in_([LeadStatus.lease, LeadStatus.move_in]),
                Lead.created_at >= start_date
            )
        )
        
        if property_id:
            lease_query = lease_query.filter(Lead.property_id == property_id)
        
        leased_leads = lease_query.all()
        days_to_lease = []
        for lead in leased_leads:
            days = (lead.updated_at - lead.created_at).days
            if days > 0:
                days_to_lease.append(days)
        
        avg_days = sum(days_to_lease) / len(days_to_lease) if days_to_lease else 15.0
        
        # Determine trend
        first_half = data_points[:days//2]
        second_half = data_points[days//2:]
        
        first_half_avg = sum(dp.leases for dp in first_half) / len(first_half) if first_half else 0
        second_half_avg = sum(dp.leases for dp in second_half) / len(second_half) if second_half else 0
        
        if second_half_avg > first_half_avg * 1.1:
            trend = "up"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "down"
        else:
            trend = "stable"
        
        return LeasingVelocityData(
            data_points=data_points,
            average_days_to_lease=avg_days,
            trend=trend
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to calculate leasing velocity: {str(e)}")


async def get_agent_activity_feed(
    db: Session,
    limit: int = 50,
    agent_type: Optional[AgentType] = None
) -> AgentActivityFeed:
    """
    Get recent AI agent activity feed.
    
    Args:
        db: Database session
        limit: Maximum number of activities to return
        agent_type: Filter by agent type
        
    Returns:
        AgentActivityFeed with recent activities and stats
    """
    try:
        # Build query
        query = db.query(AgentActivity)
        
        if agent_type:
            query = query.filter(AgentActivity.agent_type == agent_type)
        
        # Get recent activities
        activities = query.order_by(
            AgentActivity.created_at.desc()
        ).limit(limit).all()
        
        # Format activities
        activity_items = []
        for activity in activities:
            activity_items.append(AgentActivityItem(
                id=activity.id,
                agent_type=activity.agent_type.value,
                action=activity.action,
                lead_name=activity.lead.name if activity.lead else None,
                result=activity.result,
                timestamp=activity.created_at
            ))
        
        # Get stats
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = datetime.now() - timedelta(days=7)
        
        total_today = db.query(AgentActivity).filter(
            AgentActivity.created_at >= today_start
        ).count()
        
        total_week = db.query(AgentActivity).filter(
            AgentActivity.created_at >= week_start
        ).count()
        
        return AgentActivityFeed(
            activities=activity_items,
            total_actions_today=total_today,
            total_actions_this_week=total_week
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to get agent activity feed: {str(e)}")


async def get_portfolio_health(
    db: Session,
    user_id: Optional[UUID] = None
) -> PortfolioHealthScore:
    """
    Calculate portfolio-wide health metrics.
    
    Args:
        db: Database session
        user_id: Filter by user
        
    Returns:
        PortfolioHealthScore with property-level breakdown
    """
    try:
        # Get all properties
        property_query = db.query(Bot)
        if user_id:
            property_query = property_query.filter(Bot.user_id == user_id)
        
        properties = property_query.all()
        
        property_metrics = []
        total_units = 0
        occupied_units = 0
        at_risk_count = 0
        
        for prop in properties:
            # Get lead count
            lead_count = db.query(Lead).filter(
                Lead.property_id == prop.id
            ).count()
            
            # Get active conversations
            active_convs = db.query(Conversation).join(Lead).filter(
                and_(
                    Lead.property_id == prop.id,
                    Conversation.status == ConversationStatus.open
                )
            ).count()
            
            # Get tours this week
            week_ago = datetime.now() - timedelta(days=7)
            tours_this_week = db.query(Lead).filter(
                and_(
                    Lead.property_id == prop.id,
                    Lead.status == LeadStatus.touring,
                    Lead.updated_at >= week_ago
                )
            ).count()
            
            # Calculate property health score
            # Based on lead activity, tours, response rate
            health_score = 50.0  # Base score
            
            if lead_count > 10:
                health_score += 15
            elif lead_count > 5:
                health_score += 10
            
            if active_convs > 5:
                health_score += 15
            elif active_convs > 2:
                health_score += 10
            
            if tours_this_week > 3:
                health_score += 20
            elif tours_this_week > 0:
                health_score += 10
            
            health_score = min(health_score, 100)
            
            # Mock occupancy (would come from PMS)
            occupancy = 90.0 + (hash(str(prop.id)) % 10)
            
            # Count as at-risk if health score is low
            if health_score < 60:
                at_risk_count += 1
            
            property_metrics.append(PropertyHealthMetrics(
                property_id=prop.id,
                property_name=prop.name,
                occupancy_rate=occupancy,
                lead_count=lead_count,
                active_conversations=active_convs,
                tours_this_week=tours_this_week,
                health_score=health_score
            ))
            
            # Mock unit counts
            prop_units = 50 + (hash(str(prop.id)) % 100)
            total_units += prop_units
            occupied_units += int(prop_units * occupancy / 100)
        
        # Calculate overall score
        if property_metrics:
            overall_score = sum(pm.health_score for pm in property_metrics) / len(property_metrics)
        else:
            overall_score = 0.0
        
        portfolio_occupancy = (occupied_units / total_units * 100) if total_units > 0 else 0.0
        
        return PortfolioHealthScore(
            overall_score=overall_score,
            properties=property_metrics,
            total_units=total_units,
            occupied_units=occupied_units,
            portfolio_occupancy=portfolio_occupancy,
            properties_at_risk=at_risk_count
        )
        
    except Exception as e:
        raise DatabaseError(f"Failed to calculate portfolio health: {str(e)}")
