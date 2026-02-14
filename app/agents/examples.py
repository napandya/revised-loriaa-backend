"""Example usage of the agent system.

This script demonstrates how to use the agent system for various tasks.
"""

from sqlalchemy.orm import Session
from app.agents import COOAgent, LeasingAgent, MarketingAgent, PropertyAgent
from app.database import get_db

# Example 1: Using COO Agent to route requests automatically
def example_coo_routing():
    """Example of using COO agent to automatically route requests."""
    db = next(get_db())
    coo = COOAgent()
    
    # Leasing request - will be routed to LeasingAgent
    result = coo.route_request(
        request="I need to schedule a tour for lead abc-123 tomorrow at 2 PM",
        db=db,
        context={"lead_id": "abc-123"}
    )
    print("Leasing request result:", result)
    
    # Marketing request - will be routed to MarketingAgent
    result = coo.route_request(
        request="Analyze our Facebook campaign performance for the last 30 days",
        db=db
    )
    print("Marketing request result:", result)
    
    # Property management request - will be routed to PropertyAgent
    result = coo.route_request(
        request="What is our policy on late rent payments?",
        db=db
    )
    print("Property request result:", result)


# Example 2: Using Leasing Agent directly
def example_leasing_agent():
    """Example of using the leasing agent directly."""
    db = next(get_db())
    leasing_agent = LeasingAgent()
    
    # Qualify a lead
    result = leasing_agent.qualify_lead(
        lead_id="abc-123",
        db=db
    )
    print("Lead qualification:", result)
    
    # Schedule a tour
    result = leasing_agent.schedule_lead_tour(
        lead_id="abc-123",
        date="2024-02-15",
        time_slot="2:00 PM",
        property_id="prop-456",
        db=db
    )
    print("Tour scheduled:", result)
    
    # Follow up with lead
    result = leasing_agent.follow_up_with_lead(
        lead_id="abc-123",
        db=db,
        follow_up_reason="Tour reminder for tomorrow"
    )
    print("Follow-up sent:", result)


# Example 3: Using Marketing Agent directly
def example_marketing_agent():
    """Example of using the marketing agent directly."""
    db = next(get_db())
    marketing_agent = MarketingAgent()
    
    # Analyze campaign performance
    result = marketing_agent.analyze_campaign_performance(
        period="30d",
        db=db
    )
    print("Campaign analysis:", result)
    
    # Optimize lead sources
    result = marketing_agent.optimize_lead_sources(
        period="30d",
        db=db
    )
    print("Lead source optimization:", result)
    
    # Generate marketing report
    result = marketing_agent.generate_marketing_report(
        period="30d",
        db=db
    )
    print("Marketing report:", result)


# Example 4: Using Property Agent directly
def example_property_agent():
    """Example of using the property agent directly."""
    db = next(get_db())
    property_agent = PropertyAgent()
    
    # Answer a policy question
    result = property_agent.answer_policy_question(
        question="What are the requirements for approving a rental application?",
        db=db
    )
    print("Policy answer:", result)
    
    # Find a procedure
    result = property_agent.find_procedure(
        procedure_name="Move-in inspection",
        db=db
    )
    print("Procedure:", result)
    
    # Explain compliance requirement
    result = property_agent.explain_compliance_requirement(
        requirement="Fair Housing Act requirements",
        db=db
    )
    print("Compliance explanation:", result)


# Example 5: Multi-agent coordination
def example_multi_agent():
    """Example of coordinating multiple agents."""
    db = next(get_db())
    coo = COOAgent()
    
    # Task that might need multiple agents
    result = coo.coordinate_multi_agent_task(
        task_description="Analyze lead quality from our marketing campaigns and provide recommendations for improving conversion",
        agents_needed=["marketing", "leasing"],
        db=db
    )
    print("Multi-agent result:", result)


if __name__ == "__main__":
    print("Agent System Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run
    # example_coo_routing()
    # example_leasing_agent()
    # example_marketing_agent()
    # example_property_agent()
    # example_multi_agent()
    
    print("\nNote: Make sure OPENAI_API_KEY is set in your environment")
    print("and the database is properly configured before running.")
