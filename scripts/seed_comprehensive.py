"""
Comprehensive seed script for Loriaa AI CRM.
This script populates all the data needed for each frontend screen.

Run this script in your backend Docker container:
    python scripts/seed_comprehensive.py

Or with docker-compose:
    docker-compose exec backend python scripts/seed_comprehensive.py

Features:
- Idempotent: Can be run multiple times safely
- Proper error handling with rollback
- Comprehensive data for all UI screens
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import random
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, create_tables
from app.models.user import User
from app.models.bot import Bot, BotStatus
from app.models.call_log import CallLog, CallType, CallStatus
from app.models.team import TeamMember, TeamRole
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection
from app.models.agent_activity import AgentActivity, AgentType
from app.models.document import Document, DocumentCategory
from app.models.integration_config import IntegrationConfig, IntegrationName
from app.models.billing import BillingRecord
from app.models.lead_activity import LeadActivity, ActivityType
from app.models.knowledge_base import KnowledgeBase
from app.core.security import get_password_hash


def seed_comprehensive():
    """Seed database with comprehensive demo data for all screens."""
    db = SessionLocal()
    
    try:
        print("Creating database tables...")
        create_tables()
        
        # ============================================================
        # 1. USER & AUTHENTICATION
        # ============================================================
        print("\n[1/10] Creating users...")
        demo_user = db.query(User).filter(User.email == "demo@loriaa.ai").first()
        
        if not demo_user:
            demo_user = User(
                email="demo@loriaa.ai",
                hashed_password=get_password_hash("password123"),
                full_name="Admin User",
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"  Created demo user: {demo_user.email}")
        else:
            print(f"  Demo user already exists: {demo_user.email}")

        # ============================================================
        # 2. BOTS (Properties)
        # ============================================================
        print("\n[2/10] Creating bots/properties...")
        
        # Check if bots already exist
        existing_bots = db.query(Bot).filter(Bot.user_id == demo_user.id).all()
        if existing_bots:
            print(f"  Bots already exist ({len(existing_bots)} found), skipping...")
            bot1 = existing_bots[0]
        else:
            bot1 = Bot(
                user_id=demo_user.id,
                name="Village Green Apartments",
                hipaa_compliant=False,
                language="en-US",
                status=BotStatus.active,
                greeting_text="Hi, this is Loriaa AI. How can I help you today?",
                prompt="You are Loriaa, an AI leasing assistant for Village Green Apartments.",
                voice="Shimmer",
                model="gpt-4o",
                cost_per_minute=0.18,
                phone_number="+15551234567"
            )
            bot2 = Bot(
                user_id=demo_user.id,
                name="Sunset Ridge Community",
                hipaa_compliant=False,
                language="en-US",
                status=BotStatus.active,
                greeting_text="Welcome to Sunset Ridge! How may I assist you?",
                prompt="You are Loriaa, an AI leasing assistant for Sunset Ridge Community.",
                voice="Shimmer",
                model="gpt-4o",
                cost_per_minute=0.18,
                phone_number="+15559876543"
            )
            db.add_all([bot1, bot2])
            db.commit()
            db.refresh(bot1)
            print(f"  Created 2 bots/properties")

        # ============================================================
        # 3. LEADS (for Leads Page & Leasing Agent Funnel)
        # ============================================================
        print("\n[3/10] Creating leads...")
        
        existing_leads = db.query(Lead).filter(Lead.user_id == demo_user.id).all()
        if existing_leads:
            print(f"  Leads already exist ({len(existing_leads)} found), skipping...")
            leads = existing_leads
        else:
            leads_data = [
                # Inquiry Stage (2 leads)
                {"name": "John Doe", "email": "john.doe@email.com", "phone": "(555) 123-4567", "source": LeadSource.facebook_ads, "status": LeadStatus.new, "score": 92, "interest": "2 Bed", "ai_insight": "High intent buyer, mentioned move-in date within 30 days"},
                {"name": "Lisa Anderson", "email": "lisa.a@email.com", "phone": "(555) 234-5678", "source": LeadSource.phone, "status": LeadStatus.new, "score": 78, "interest": "2 Bed", "ai_insight": "Answering questions about pet policy"},
                
                # Touring Stage (2 leads)
                {"name": "Jane Smith", "email": "jane.smith@email.com", "phone": "(555) 345-6789", "source": LeadSource.google_ads, "status": LeadStatus.touring, "score": 85, "interest": "1 Bed", "ai_insight": "Self-guided tour scheduled for Unit 404"},
                {"name": "Robert Chen", "email": "robert.chen@email.com", "phone": "(555) 456-7890", "source": LeadSource.website, "status": LeadStatus.touring, "score": 88, "interest": "2 Bed", "ai_insight": "Agent assisted tour at 4:30 PM today"},
                
                # Application Stage (1 lead)
                {"name": "Mike Ross", "email": "mike.ross@email.com", "phone": "(555) 567-8901", "source": LeadSource.referral, "status": LeadStatus.application, "score": 74, "interest": "1 Bed", "ai_insight": "Needs approval, Score 740"},
                
                # Lease Stage (2 leads)
                {"name": "Sarah Johnson", "email": "sarah.j@email.com", "phone": "(555) 678-9012", "source": LeadSource.facebook_ads, "status": LeadStatus.lease, "score": 95, "interest": "2 Bed", "ai_insight": "Awaiting signature for Unit 101"},
                {"name": "David Martinez", "email": "david.m@email.com", "phone": "(555) 789-0123", "source": LeadSource.google_ads, "status": LeadStatus.lease, "score": 91, "interest": "3 Bed", "ai_insight": "Awaiting countersign for Unit 508"},
                
                # Move-In Stage (1 lead)
                {"name": "Emily Rodriguez", "email": "emily.r@email.com", "phone": "(555) 890-1234", "source": LeadSource.website, "status": LeadStatus.move_in, "score": 98, "interest": "2 Bed", "ai_insight": "Moving in 3 days, renters insurance pending"},
                
                # Additional leads for stats
                {"name": "Alex Turner", "email": "alex.t@email.com", "phone": "(555) 901-2345", "source": LeadSource.facebook_ads, "status": LeadStatus.contacted, "score": 82, "interest": "Studio", "ai_insight": "Budget conscious, comparing properties"},
                {"name": "Maria Garcia", "email": "maria.g@email.com", "phone": "(555) 012-3456", "source": LeadSource.referral, "status": LeadStatus.qualified, "score": 87, "interest": "1 Bed", "ai_insight": "Ready to tour, prefers weekends"},
            ]
            
            leads = []
            for ld in leads_data:
                lead = Lead(
                    property_id=bot1.id,
                    user_id=demo_user.id,
                    name=ld["name"],
                    email=ld["email"],
                    phone=ld["phone"],
                    source=ld["source"],
                    status=ld["status"],
                    score=ld["score"],
                    extra_data={
                        "unit_interest": ld["interest"],
                        "ai_insight": ld["ai_insight"],
                        "budget_min": random.randint(900, 1200),
                        "budget_max": random.randint(1400, 2000)
                    }
                )
                db.add(lead)
                leads.append(lead)
            
            db.commit()
            for lead in leads:
                db.refresh(lead)
            print(f"  Created {len(leads)} leads")

        # ============================================================
        # 3b. LEAD ACTIVITIES (for lead timeline & scoring)
        # ============================================================
        print("\n[3b] Creating lead activities...")
        
        existing_lead_activities = db.query(LeadActivity).all()
        if existing_lead_activities:
            print(f"  Lead activities already exist ({len(existing_lead_activities)} found), skipping...")
        else:
            lead_activities_data = []
            for i, lead in enumerate(leads[:8]):
                # Every lead gets a creation note
                lead_activities_data.append({
                    "lead_id": lead.id, "user_id": demo_user.id,
                    "activity_type": ActivityType.note,
                    "description": f"Lead created from {lead.source.value}",
                    "hours_ago": 72 + i * 12
                })
                # Contacted leads get an SMS/Email
                if lead.status.value not in ("new",):
                    lead_activities_data.append({
                        "lead_id": lead.id, "user_id": demo_user.id,
                        "activity_type": ActivityType.sms if i % 2 == 0 else ActivityType.email,
                        "description": f"Sent initial outreach message to {lead.name}",
                        "hours_ago": 48 + i * 6
                    })
                # Touring leads get a tour_scheduled
                if lead.status.value in ("touring", "application", "lease", "move_in"):
                    lead_activities_data.append({
                        "lead_id": lead.id, "user_id": demo_user.id,
                        "activity_type": ActivityType.tour_scheduled,
                        "description": f"Tour scheduled for {lead.name} at Village Green Apartments",
                        "hours_ago": 36 + i * 4
                    })
                # Application+ leads get a call
                if lead.status.value in ("application", "lease", "move_in"):
                    lead_activities_data.append({
                        "lead_id": lead.id, "user_id": demo_user.id,
                        "activity_type": ActivityType.call,
                        "description": f"Follow-up call with {lead.name} about application status",
                        "hours_ago": 24 + i * 2
                    })
                # Lease+ leads get a status change
                if lead.status.value in ("lease", "move_in"):
                    lead_activities_data.append({
                        "lead_id": lead.id, "user_id": demo_user.id,
                        "activity_type": ActivityType.status_change,
                        "description": f"Lead status changed to {lead.status.value}",
                        "hours_ago": 12 + i
                    })
            
            for act_data in lead_activities_data:
                activity = LeadActivity(
                    lead_id=act_data["lead_id"],
                    user_id=act_data["user_id"],
                    activity_type=act_data["activity_type"],
                    description=act_data["description"],
                    created_at=datetime.utcnow() - timedelta(hours=act_data["hours_ago"])
                )
                db.add(activity)
            
            db.commit()
            print(f"  Created {len(lead_activities_data)} lead activities")

        # ============================================================
        # 4. CONVERSATIONS & MESSAGES (for Inbox Page)
        # ============================================================
        print("\n[4/10] Creating conversations and messages...")
        
        existing_convos = db.query(Conversation).all()
        if existing_convos:
            print(f"  Conversations already exist ({len(existing_convos)} found), skipping...")
        else:
            conversations_data = [
                {
                    "lead": leads[0],  # John Doe
                    "channel": ConversationChannel.sms,
                    "messages": [
                        {"direction": MessageDirection.inbound, "sender": "John Doe", "content": "Hi, I am interested in the 2-bed apartment. Is it still available?"},
                        {"direction": MessageDirection.outbound, "sender": "Loriaa AI", "content": "Yes! The 2-bedroom apartment at Unit 404 is still available. It features hardwood floors, a modern kitchen, and natural light. Would you like to schedule a tour?", "extra_data": {"source_document": "Unit 404 Listing.pdf"}},
                    ]
                },
                {
                    "lead": leads[2],  # Jane Smith
                    "channel": ConversationChannel.email,
                    "messages": [
                        {"direction": MessageDirection.inbound, "sender": "Jane Smith", "content": "What is the pet policy?"},
                        {"direction": MessageDirection.outbound, "sender": "Loriaa AI", "content": "We welcome pets! We allow cats and dogs up to 50 lbs. There's a $300 pet deposit and $25/month pet rent. Would you like more details?", "extra_data": {"source_document": "Pet Policy.pdf"}},
                    ]
                },
                {
                    "lead": leads[3],  # Robert Chen
                    "channel": ConversationChannel.voice,
                    "messages": [
                        {"direction": MessageDirection.inbound, "sender": "Robert Chen", "content": "I'd like to know about parking options."},
                        {"direction": MessageDirection.outbound, "sender": "Loriaa AI", "content": "We offer covered parking at $50/month and uncovered at $25/month. Each unit also comes with one assigned spot included in rent."},
                    ]
                },
            ]
            
            for conv_data in conversations_data:
                conversation = Conversation(
                    lead_id=conv_data["lead"].id,
                    channel=conv_data["channel"],
                    status=ConversationStatus.open,
                    last_message_at=datetime.utcnow()
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
                
                for msg_data in conv_data["messages"]:
                    message = Message(
                        conversation_id=conversation.id,
                        direction=msg_data["direction"],
                        content=msg_data["content"],
                        sender=msg_data["sender"],
                        recipient="System" if msg_data["direction"] == MessageDirection.inbound else conv_data["lead"].name,
                        extra_data=msg_data.get("extra_data")
                    )
                    db.add(message)
            
            db.commit()
            print(f"  Created {len(conversations_data)} conversations with messages")

        # ============================================================
        # 5. AGENT ACTIVITIES (for Dashboard & Agent Pages)
        # ============================================================
        print("\n[5/10] Creating agent activities...")
        
        existing_activities = db.query(AgentActivity).all()
        if existing_activities:
            print(f"  Agent activities already exist ({len(existing_activities)} found), skipping...")
        else:
            activities_data = [
                # Marketing Agent Activities
                {"agent_type": AgentType.marketing, "action": "Synced John Doe (Lead) from Facebook Form #442 to CRM Leads Table", "lead_id": leads[0].id},
                {"agent_type": AgentType.marketing, "action": "Published Facebook Campaign for Unit 102 - 12 Leads generated", "lead_id": None},
                {"agent_type": AgentType.marketing, "action": "Detected vacancy: Unit 402 (2 Bed / 1 Bath) - $1200/mo", "lead_id": None},
                {"agent_type": AgentType.marketing, "action": "Campaign 'Village Green' is performing 20% better than average", "lead_id": None},
                
                # Leasing Agent Activities
                {"agent_type": AgentType.leasing, "action": "Scheduled tour for Unit 404 with prospect Jane Smith", "lead_id": leads[2].id if len(leads) > 2 else None},
                {"agent_type": AgentType.leasing, "action": "Qualified lead Mike Ross - Score 740, ready for application", "lead_id": leads[4].id if len(leads) > 4 else None},
                {"agent_type": AgentType.leasing, "action": "Sent lease agreement to Sarah Johnson for Unit 101", "lead_id": leads[5].id if len(leads) > 5 else None},
                {"agent_type": AgentType.leasing, "action": "Move-in scheduled for Emily Rodriguez - Unit 210", "lead_id": leads[7].id if len(leads) > 7 else None},
                
                # Property Manager Activities
                {"agent_type": AgentType.property_manager, "action": "Uploaded new document: Pet Policy 2024 Update", "lead_id": None},
                {"agent_type": AgentType.property_manager, "action": "Updated maintenance request priority for Unit 305", "lead_id": None},
            ]
            
            for i, act_data in enumerate(activities_data):
                activity = AgentActivity(
                    agent_type=act_data["agent_type"],
                    action=act_data["action"],
                    lead_id=act_data["lead_id"],
                    result="success",
                    created_at=datetime.utcnow() - timedelta(hours=i)
                )
                db.add(activity)
            
            db.commit()
            print(f"  Created {len(activities_data)} agent activities")

        # ============================================================
        # 6. DOCUMENTS (for Property Manager Knowledge Base)
        # ============================================================
        print("\n[6/10] Creating documents...")
        
        existing_docs = db.query(Document).filter(Document.user_id == demo_user.id).all()
        if existing_docs:
            print(f"  Documents already exist ({len(existing_docs)} found), skipping...")
        else:
            documents_data = [
                # Leasing Policies
                {"title": "Pet Policy", "category": DocumentCategory.policy, "content": "Village Green Apartments welcomes pets! We allow cats and dogs up to 50 pounds. Pet deposit of $300 required, plus $25/month pet rent. Aggressive breeds are not permitted."},
                {"title": "Lease Agreement Template", "category": DocumentCategory.policy, "content": "Standard 12-month lease agreement template with terms and conditions for Village Green Apartments residents."},
                {"title": "Move-In Checklist", "category": DocumentCategory.procedure, "content": "Complete checklist for new resident move-in including key pickup, utility setup, and inspection walkthrough."},
                {"title": "Parking Policy", "category": DocumentCategory.policy, "content": "Parking options: Covered parking $50/month, Uncovered $25/month. Each unit includes one assigned spot."},
                
                # FAQs
                {"title": "Application Requirements FAQ", "category": DocumentCategory.faq, "content": "Applicants must provide: Valid ID, proof of income (3x rent), rental history, and application fee of $50."},
                {"title": "Maintenance Request Guide", "category": DocumentCategory.faq, "content": "How to submit maintenance requests: Online portal, phone, or in-person at leasing office. Emergency line available 24/7."},
                
                # Training
                {"title": "Leasing Agent Training Manual", "category": DocumentCategory.training, "content": "Comprehensive guide for leasing agents including lead qualification, tour best practices, and closing techniques."},
                {"title": "AI Assistant Guidelines", "category": DocumentCategory.training, "content": "Guidelines for AI assistant interactions including tone, compliance, and escalation procedures."},
                
                # Procedures
                {"title": "Eviction Procedures", "category": DocumentCategory.procedure, "content": "Legal procedures for eviction including notice requirements, court filings, and compliance with local laws."},
                {"title": "Emergency Protocols", "category": DocumentCategory.procedure, "content": "Emergency response procedures for fire, flood, and security incidents at Village Green Apartments."},
            ]
            
            for doc_data in documents_data:
                document = Document(
                    user_id=demo_user.id,
                    property_id=bot1.id,
                    title=doc_data["title"],
                    content=doc_data["content"],
                    category=doc_data["category"],
                    file_url=None,
                    embedding=None  # Would be populated by RAG system
                )
                db.add(document)
            
            db.commit()
            print(f"  Created {len(documents_data)} documents")

        # ============================================================
        # 6b. KNOWLEDGE BASE (RAG entries for bot Q&A)
        # ============================================================
        print("\n[6b] Creating knowledge base entries...")
        
        existing_kb = db.query(KnowledgeBase).all()
        if existing_kb:
            print(f"  Knowledge base already has {len(existing_kb)} entries, skipping...")
        else:
            kb_entries = [
                {"title": "Pet Policy Summary", "content": "Village Green Apartments allows cats and dogs up to 50 lbs. A $300 pet deposit and $25/month pet rent are required. Aggressive breeds (pitbulls, rottweilers) are not permitted. Service animals are exempt from pet fees per ADA requirements."},
                {"title": "Rent & Payment Info", "content": "Rent is due on the 1st of each month. A 5-day grace period is provided. Late fee of $75 applies after the 5th. Payments accepted via online portal, check, or money order. No cash payments accepted at the office."},
                {"title": "Parking Details", "content": "Each unit comes with one assigned parking spot included in rent. Additional covered parking is $50/month and uncovered parking is $25/month. Guest parking is available in designated visitor spots. No commercial vehicles or trailers allowed."},
                {"title": "Amenities Overview", "content": "Community amenities include: 24-hour fitness center, resort-style pool (open May-September), clubhouse with kitchen, dog park, business center with free WiFi, package lockers, and on-site laundry in select buildings."},
                {"title": "Lease Terms", "content": "Standard lease terms are 12 months. Short-term leases (6-9 months) available at premium rate (+$100/month). Month-to-month available after initial lease term at +$200/month. 60-day written notice required for non-renewal. Early termination fee equals 2 months rent."},
                {"title": "Maintenance Procedures", "content": "Submit maintenance requests through the resident portal or call the office. Emergency maintenance available 24/7 for issues like water leaks, no heat/AC, or lockouts. Standard requests handled within 48 business hours. Entry notice provided 24 hours in advance except for emergencies."},
                {"title": "Move-In Requirements", "content": "Required before move-in: security deposit (one month rent), first month rent, renter's insurance (minimum $100K liability), utility setup confirmation. Move-in inspection conducted jointly with management. Key pickup at leasing office during business hours."},
                {"title": "Noise & Quiet Hours", "content": "Quiet hours are 10 PM to 8 AM Sunday-Thursday, and 11 PM to 9 AM Friday-Saturday. Music, TV, and conversations should be kept at reasonable levels. Construction and power tool use only allowed 9 AM to 7 PM weekdays. Violations may result in lease violation notices."},
            ]
            
            for kb_data in kb_entries:
                kb = KnowledgeBase(
                    bot_id=bot1.id,
                    title=kb_data["title"],
                    content=kb_data["content"],
                    embedding=None,  # Would be populated by embedding pipeline
                    document_metadata={"source": "seed_data", "version": "1.0"}
                )
                db.add(kb)
            
            db.commit()
            print(f"  Created {len(kb_entries)} knowledge base entries")

        # ============================================================
        # 7. INTEGRATION CONFIGS (for Settings Page)
        # ============================================================
        print("\n[7/10] Creating integration configs...")
        
        existing_integrations = db.query(IntegrationConfig).filter(IntegrationConfig.user_id == demo_user.id).all()
        if existing_integrations:
            print(f"  Integrations already exist ({len(existing_integrations)} found), skipping...")
        else:
            integrations_data = [
                {"name": IntegrationName.resman, "is_active": True, "config": {"api_key": "***", "property_id": "12345"}},
                {"name": IntegrationName.facebook, "is_active": True, "config": {"page_id": "***", "access_token": "***"}},
                {"name": IntegrationName.twilio, "is_active": False, "config": {"account_sid": "", "auth_token": ""}},
                {"name": IntegrationName.google_ads, "is_active": True, "config": {"customer_id": "***", "developer_token": "***"}},
            ]
            
            for int_data in integrations_data:
                integration = IntegrationConfig(
                    user_id=demo_user.id,
                    integration_name=int_data["name"],
                    is_active=int_data["is_active"],
                    config=int_data["config"]
                )
                db.add(integration)
            
            db.commit()
            print(f"  Created {len(integrations_data)} integration configs")

        # ============================================================
        # 8. BILLING RECORDS (for Settings Page)
        # ============================================================
        print("\n[8/10] Creating billing records...")
        
        existing_billing = db.query(BillingRecord).filter(BillingRecord.user_id == demo_user.id).all()
        if existing_billing:
            print(f"  Billing records already exist ({len(existing_billing)} found), skipping...")
        else:
            # Create billing records for past 3 months
            for i in range(3):
                month = (datetime.utcnow() - timedelta(days=30*i)).strftime("%Y-%m")
                billing = BillingRecord(
                    user_id=demo_user.id,
                    month=month,
                    total_cost=random.uniform(150, 300),
                    total_calls=random.randint(50, 150),
                    total_duration_minutes=random.uniform(200, 500)
                )
                db.add(billing)
            
            db.commit()
            print("  Created 3 billing records")

        # ============================================================
        # 9. CALL LOGS (for Dashboard & Analytics)
        # ============================================================
        print("\n[9/10] Creating call logs...")
        
        existing_calls = db.query(CallLog).all()
        if existing_calls:
            print(f"  Call logs already exist ({len(existing_calls)} found), skipping...")
        else:
            call_logs_data = [
                {"date": datetime.utcnow() - timedelta(hours=2), "phone": "+15551234567", "type": CallType.outbound, "duration": 84},
                {"date": datetime.utcnow() - timedelta(hours=5), "phone": "+15559876543", "type": CallType.inbound, "duration": 187},
                {"date": datetime.utcnow() - timedelta(days=1), "phone": "+15553456789", "type": CallType.outbound, "duration": 57},
                {"date": datetime.utcnow() - timedelta(days=1, hours=3), "phone": "+15557654321", "type": CallType.inbound, "duration": 173},
                {"date": datetime.utcnow() - timedelta(days=2), "phone": "+15558765432", "type": CallType.outbound, "duration": 145},
                {"date": datetime.utcnow() - timedelta(days=2, hours=6), "phone": "+15554321098", "type": CallType.inbound, "duration": 98},
                {"date": datetime.utcnow() - timedelta(days=3), "phone": "+15552109876", "type": CallType.outbound, "duration": 122},
                {"date": datetime.utcnow() - timedelta(days=4), "phone": "+15550987654", "type": CallType.outbound, "duration": 156},
                {"date": datetime.utcnow() - timedelta(days=5), "phone": "+15558765432", "type": CallType.inbound, "duration": 201},
                {"date": datetime.utcnow() - timedelta(days=6), "phone": "+15556543210", "type": CallType.outbound, "duration": 89},
            ]
            
            for log_data in call_logs_data:
                call_log = CallLog(
                    bot_id=bot1.id,
                    bot_name=bot1.name,
                    start_time=log_data["date"],
                    phone_number=log_data["phone"],
                    call_type=log_data["type"],
                    duration_seconds=log_data["duration"],
                    status=CallStatus.completed,
                    recording_url=None,
                    transcript=None
                )
                db.add(call_log)
            
            db.commit()
            print(f"  Created {len(call_logs_data)} call logs")

        # ============================================================
        # 10. TEAM MEMBERS (for Team Management Page)
        # ============================================================
        print("\n[10/10] Creating team members...")
        
        existing_team = db.query(TeamMember).filter(TeamMember.user_id == demo_user.id).all()
        if existing_team:
            print(f"  Team members already exist ({len(existing_team)} found), skipping...")
        else:
            team_members_data = [
                {"name": "Admin User", "email": "admin@loriaa.ai", "role": TeamRole.Admin},
                {"name": "Sarah Miller", "email": "sarah.miller@loriaa.ai", "role": TeamRole.Admin},
                {"name": "John Developer", "email": "john.dev@loriaa.ai", "role": TeamRole.Developer},
                {"name": "Jane Support", "email": "jane.support@loriaa.ai", "role": TeamRole.Support},
                {"name": "Mike Manager", "email": "mike.mgr@loriaa.ai", "role": TeamRole.Support},
            ]
            
            for member_data in team_members_data:
                team_member = TeamMember(
                    user_id=demo_user.id,
                    name=member_data["name"],
                    email=member_data["email"],
                    role=member_data["role"],
                    active=True
                )
                db.add(team_member)
            
            db.commit()
            print(f"  Created {len(team_members_data)} team members")

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETE!")
        print("="*60)
        print("\nData created for all screens:")
        print("  - Dashboard: Portfolio health, leads by source, AI activity")
        print("  - Leads Page: 10 leads across all funnel stages")
        print("  - Lead Activities: Timeline events (calls, SMS, tours, status changes)")
        print("  - Inbox: 3 conversations with messages")
        print("  - Leasing Agent: Leads in inquiry/touring/application/lease/move-in")
        print("  - Marketing Agent: Agent activities for campaigns")
        print("  - Property Manager: 10 knowledge base documents + 8 RAG entries")
        print("  - Settings: 4 integrations, billing records")
        print("  - Team: 5 team members")
        print("  - Call Logs: 10 call records for analytics")
        print("\n" + "-"*60)
        print("LOGIN CREDENTIALS:")
        print("  Email: demo@loriaa.ai")
        print("  Password: password123")
        print("="*60)
        
    except Exception as e:
        print(f"\nError seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_comprehensive()
