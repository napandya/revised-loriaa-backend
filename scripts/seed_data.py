"""Seed database with demo data matching screenshots."""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, create_tables
from app.models.user import User
from app.models.bot import Bot, BotStatus
from app.models.call_log import CallLog, CallType, CallStatus
from app.models.team import TeamMember, TeamRole
from app.core.security import get_password_hash


def seed_database():
    """Seed database with demo data."""
    db = SessionLocal()
    
    try:
        print("Creating database tables...")
        create_tables()
        
        print("Checking for demo user...")
        # Check if demo user already exists
        demo_user = db.query(User).filter(User.email == "demo@loriaa.ai").first()

        if not demo_user:
            print("Creating demo user...")
            # Create demo user
            demo_user = User(
                email="demo@loriaa.ai",
                hashed_password=get_password_hash("password123"),
                full_name="Demo User",
                is_active=True
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"Demo user created: {demo_user.email}")
        else:
            print(f"Demo user already exists: {demo_user.email}")

        print("Creating bots...")
        # Bot 1: Rental and Delinquency Outbound
        bot1_prompt = """Role & Identity
* You are Emily, a Rent Payment Support Representative from Prop Pal.
* Do not change your name or company identity.
* You always know (or are given) the rent amount (spoken in words) and the due date (spoken as "the {ordinal} of {Month}").
* Never ask the resident to confirm the rent amount or due date—you already know them.

Non-Negotiables (Guardrails)
1. Language: English only.
2. Tone Control:
   * First reminder: warm, friendly, supportive.
   * Second reminder: calm, clear, and firm; mention lease consequences respectfully (no threats).
3. Human Delivery:
   * Short, clear sentences.
   * One question at a time, pause and listen.
   * Light fillers sparingly (e.g., "alright", "okay", "sure"), never overuse.
4. No Speculation:
   * Only state facts you have or the resident confirms.
   * Never assume reasons for late payment unless the resident shares them.
5. Compliance:
   * No misleading statements.
   * No threats of illegal eviction or harm.
   * No harassment or aggressive language.

Call Structure
1. Greeting:
   * "Hi, this is Emily with Prop Pal. Could you confirm your name please?"
   * Wait for resident confirmation.

2. Identify Reason:
   * "I'm calling because your rent payment of [amount in words] was due on [date] and we haven't received it yet."
   * Pause. Let the resident respond.

3. Listening & Options:
   * If resident explains a situation, acknowledge empathetically.
   * Offer solutions:
     - "We can set up a payment plan if that helps."
     - "You can pay online at [website] or call our office at [number]."
   * If resident is unclear or evasive, gently remind them of lease terms.

4. Closing:
   * Summarize next steps clearly.
   * "Thank you for your time. Please reach out if you have questions."

Examples of Good Behavior:
* "I understand things can be tight. Let's see how we can work this out together."
* "Just to confirm, your rent of eight hundred dollars was due on the fifth. Is that correct?"

Examples of Bad Behavior (Avoid):
* "Why didn't you pay?"
* "You'll be evicted if you don't pay now."
* Interrupting the resident or talking over them.

If Resident is Hostile or Uncooperative:
* Stay calm, respectful, and professional.
* "I hear your frustration. I'm here to help find a solution."
* If they refuse to engage, politely end: "I understand. Please contact us when you're ready to discuss this further."

Always prioritize clarity, empathy, and compliance with fair debt collection practices."""

        bot1 = Bot(
            user_id=demo_user.id,
            name="Rental and Delinquency Outbound",
            hipaa_compliant=False,
            language="en-US",
            status=BotStatus.active,
            greeting_text="Hi, this is Emily with Prop Pal. Could you confirm your name please ?",
            prompt=bot1_prompt,
            voice="Shimmer",
            model="gpt-4o",
            cost_per_minute=0.18,
            phone_number=None
        )
        db.add(bot1)
        
        # Bot 2: Rental and Delinquency Inbound
        bot2 = Bot(
            user_id=demo_user.id,
            name="Rental and Delinquency Inbound",
            hipaa_compliant=False,
            language="en-US",
            status=BotStatus.active,
            greeting_text="Hi, thank you for calling Prop Pal. How can I help you today?",
            prompt="You are a helpful customer service representative for Prop Pal, a property management company. Assist callers with their rent payment inquiries, account questions, and general property management concerns. Be professional, empathetic, and solution-oriented.",
            voice="Shimmer",
            model="gpt-4o",
            cost_per_minute=0.18,
            phone_number=None
        )
        db.add(bot2)
        db.commit()
        db.refresh(bot1)
        db.refresh(bot2)
        print(f"Bots created: {bot1.name}, {bot2.name}")
        
        print("Creating call logs...")
        # Call logs from screenshot
        call_logs_data = [
            {"date": "2025-10-17 15:14:00", "phone": "+14787221002", "type": CallType.outbound, "duration": 84, "bot": bot1},
            {"date": "2025-10-15 12:52:00", "phone": "+14693281415", "type": CallType.outbound, "duration": 187, "bot": bot1},
            {"date": "2025-10-04 18:08:00", "phone": "+19453876906", "type": CallType.outbound, "duration": 57, "bot": bot1},
            {"date": "2025-09-22 11:32:00", "phone": "https://interacts.ai", "type": CallType.inbound, "duration": 173, "bot": bot2},
            {"date": "2025-09-15 09:45:00", "phone": "+15551234567", "type": CallType.outbound, "duration": 145, "bot": bot1},
            {"date": "2025-09-10 14:20:00", "phone": "+15559876543", "type": CallType.inbound, "duration": 98, "bot": bot2},
            {"date": "2025-09-05 16:30:00", "phone": "+15558765432", "type": CallType.outbound, "duration": 122, "bot": bot1},
            {"date": "2025-08-28 10:15:00", "phone": "+15557654321", "type": CallType.outbound, "duration": 156, "bot": bot1},
            {"date": "2025-08-20 13:45:00", "phone": "+15556543210", "type": CallType.inbound, "duration": 201, "bot": bot2},
            {"date": "2025-08-15 11:00:00", "phone": "+15555432109", "type": CallType.outbound, "duration": 89, "bot": bot1},
            {"date": "2025-08-10 15:25:00", "phone": "+15554321098", "type": CallType.inbound, "duration": 167, "bot": bot2},
            {"date": "2025-08-05 09:30:00", "phone": "+15553210987", "type": CallType.outbound, "duration": 134, "bot": bot1},
        ]
        
        for log_data in call_logs_data:
            call_log = CallLog(
                bot_id=log_data["bot"].id,
                bot_name=log_data["bot"].name,
                start_time=datetime.strptime(log_data["date"], "%Y-%m-%d %H:%M:%S"),
                phone_number=log_data["phone"],
                call_type=log_data["type"],
                duration_seconds=log_data["duration"],
                status=CallStatus.completed,
                recording_url=None,
                transcript=None
            )
            db.add(call_log)
        
        db.commit()
        print(f"Created {len(call_logs_data)} call logs")
        
        print("Creating team members...")
        # Team members
        team_members_data = [
            {"name": "Nandan Pandya", "email": "pandyanandan@gmail.com", "role": TeamRole.Admin},
            {"name": "John Doe", "email": "john@loriaa.ai", "role": TeamRole.Developer},
            {"name": "Jane Smith", "email": "jane@loriaa.ai", "role": TeamRole.Support},
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
        print(f"Created {len(team_members_data)} team members")
        
        print("\n" + "="*60)
        print("Database seeded successfully!")
        print("="*60)
        print("\nDemo Credentials:")
        print("  Email: demo@loriaa.ai")
        print("  Password: password123")
        print("\nYou can now login and access the API.")
        print("="*60)
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
