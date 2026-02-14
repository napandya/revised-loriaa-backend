"""
Content generation service using OpenAI ChatGPT.

Generates marketing ad copy for Facebook, Instagram, Google Ads,
and other social media platforms for apartment leasing campaigns.

Python 3.13 Compatible.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class AdPlatform(str, Enum):
    """Supported advertising platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    GOOGLE_ADS = "google_ads"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class AdObjective(str, Enum):
    """Campaign objectives for ad copy generation."""
    LEAD_GENERATION = "lead_generation"
    BRAND_AWARENESS = "brand_awareness"
    TOUR_SCHEDULING = "tour_scheduling"
    LEASE_SIGNING = "lease_signing"
    OPEN_HOUSE = "open_house"
    SEASONAL_PROMOTION = "seasonal_promotion"
    MOVE_IN_SPECIAL = "move_in_special"


# Platform-specific constraints and best practices
PLATFORM_SPECS: Dict[str, Dict[str, Any]] = {
    AdPlatform.FACEBOOK: {
        "headline_max_chars": 40,
        "primary_text_max_chars": 125,
        "description_max_chars": 30,
        "cta_options": [
            "Learn More", "Sign Up", "Book Now",
            "Contact Us", "Get Offer", "Apply Now"
        ],
    },
    AdPlatform.INSTAGRAM: {
        "caption_max_chars": 2200,
        "hashtag_count": 15,
        "cta_options": [
            "Learn More", "Sign Up", "Book Now",
            "Contact Us", "Shop Now"
        ],
    },
    AdPlatform.GOOGLE_ADS: {
        "headline_max_chars": 30,
        "headline_count": 3,
        "description_max_chars": 90,
        "description_count": 2,
        "cta_options": ["Call Now", "Visit Site", "Get Directions"],
    },
    AdPlatform.TIKTOK: {
        "caption_max_chars": 150,
        "hashtag_count": 5,
        "cta_options": ["Learn More", "Sign Up", "Contact Us"],
    },
    AdPlatform.LINKEDIN: {
        "headline_max_chars": 70,
        "intro_text_max_chars": 150,
        "cta_options": ["Learn More", "Sign Up", "Apply Now"],
    },
}


def _get_openai_client() -> AsyncOpenAI:
    """Create an OpenAI async client instance.

    Returns:
        AsyncOpenAI client configured with the API key from settings.

    Raises:
        ValueError: If OPENAI_API_KEY is not configured.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not configured. "
            "Set it in your .env file to enable ad copy generation."
        )
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_ad_copy(
    property_name: str,
    platform: AdPlatform | str,
    objective: AdObjective | str = AdObjective.LEAD_GENERATION,
    property_details: Optional[Dict[str, Any]] = None,
    tone: str = "professional yet friendly",
    target_audience: Optional[str] = None,
    special_offer: Optional[str] = None,
    num_variations: int = 3,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """
    Generate advertising copy for a specific platform using ChatGPT.

    Args:
        property_name: Name of the apartment property.
        platform: Target ad platform (facebook, instagram, google_ads, etc.).
        objective: Campaign objective.
        property_details: Dict with property info (amenities, pricing, location, etc.).
        tone: Desired tone of the ad copy.
        target_audience: Description of the target audience.
        special_offer: Any special promotions or move-in deals.
        num_variations: Number of ad copy variations to generate.
        model: OpenAI model to use.

    Returns:
        Dict with generated ad copy variations and metadata.
    """
    client = _get_openai_client()

    platform_str = platform.value if isinstance(platform, AdPlatform) else platform
    objective_str = objective.value if isinstance(objective, AdObjective) else objective
    specs = PLATFORM_SPECS.get(platform_str, PLATFORM_SPECS[AdPlatform.FACEBOOK])

    # Build property context
    details_text = ""
    if property_details:
        parts = []
        if property_details.get("location"):
            parts.append(f"Location: {property_details['location']}")
        if property_details.get("bedrooms"):
            parts.append(f"Unit types: {property_details['bedrooms']}")
        if property_details.get("price_range"):
            parts.append(f"Price range: {property_details['price_range']}")
        if property_details.get("amenities"):
            amenities = property_details["amenities"]
            if isinstance(amenities, list):
                amenities = ", ".join(amenities)
            parts.append(f"Amenities: {amenities}")
        if property_details.get("pet_policy"):
            parts.append(f"Pet policy: {property_details['pet_policy']}")
        if property_details.get("unique_selling_points"):
            usp = property_details["unique_selling_points"]
            if isinstance(usp, list):
                usp = ", ".join(usp)
            parts.append(f"Unique selling points: {usp}")
        details_text = "\n".join(parts)

    audience_text = target_audience or "young professionals and families looking for apartments"
    offer_text = f"\nSpecial offer to highlight: {special_offer}" if special_offer else ""

    system_prompt = """You are an expert digital marketing copywriter specializing in apartment \
and multifamily real estate advertising. You create compelling, high-converting ad copy that \
drives leads and tours. You understand Fair Housing laws and NEVER include discriminatory language \
based on race, color, religion, sex, national origin, disability, or familial status. \
Always comply with platform advertising policies."""

    user_prompt = f"""Generate {num_variations} ad copy variations for the following:

**Property:** {property_name}
**Platform:** {platform_str.replace('_', ' ').title()}
**Campaign Objective:** {objective_str.replace('_', ' ').title()}
**Tone:** {tone}
**Target Audience:** {audience_text}
{f"**Property Details:**{chr(10)}{details_text}" if details_text else ""}
{offer_text}

**Platform Specifications:**
{_format_specs(specs)}

**Requirements:**
- Each variation should have a distinct angle/hook
- Include a clear call-to-action from the allowed CTAs: {', '.join(specs.get('cta_options', ['Learn More']))}
- Respect character limits for the platform
- Use emotional triggers relevant to apartment hunting (home, community, lifestyle)
- Include relevant keywords for apartment leasing
- Comply with Fair Housing guidelines

**Output Format (JSON):**
Return a JSON array of variations, where each variation is an object with these keys:
{_get_platform_output_keys(platform_str)}

Return ONLY the JSON array, no markdown formatting or extra text."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        import json

        # Parse the response — handle both {"variations": [...]} and bare [...]
        parsed = json.loads(content)
        if isinstance(parsed, list):
            variations = parsed
        elif isinstance(parsed, dict):
            # Look for the array in common keys
            for key in ("variations", "ads", "ad_copy", "results", "data"):
                if key in parsed and isinstance(parsed[key], list):
                    variations = parsed[key]
                    break
            else:
                variations = [parsed]
        else:
            variations = [{"raw": content}]

        return {
            "success": True,
            "property_name": property_name,
            "platform": platform_str,
            "objective": objective_str,
            "num_variations": len(variations),
            "variations": variations,
            "model_used": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }

    except Exception as e:
        logger.error(f"ChatGPT ad copy generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "property_name": property_name,
            "platform": platform_str,
            "objective": objective_str,
        }


async def generate_social_media_post(
    property_name: str,
    platform: AdPlatform | str,
    topic: str,
    property_details: Optional[Dict[str, Any]] = None,
    tone: str = "engaging and casual",
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """
    Generate an organic social media post (not paid ad) for a property.

    Args:
        property_name: Name of the apartment property.
        platform: Target social media platform.
        topic: Post topic (e.g., "community event", "amenity spotlight", "resident testimonial").
        property_details: Dict with property info.
        tone: Desired tone.
        model: OpenAI model to use.

    Returns:
        Dict with generated social media post.
    """
    client = _get_openai_client()

    platform_str = platform.value if isinstance(platform, AdPlatform) else platform

    system_prompt = """You are a social media manager for a luxury apartment community. \
You create engaging, authentic posts that build community and attract prospects. \
Always comply with Fair Housing guidelines."""

    user_prompt = f"""Create a social media post for {platform_str.replace('_', ' ').title()}:

**Property:** {property_name}
**Topic:** {topic}
**Tone:** {tone}
{_format_property_details(property_details) if property_details else ""}

Include:
- Engaging caption text
- Relevant hashtags (5-10 for Instagram, 3-5 for others)
- Suggested image/visual description
- Best time to post suggestion

Return a JSON object with keys: "caption", "hashtags", "image_suggestion", "best_time_to_post"
Return ONLY the JSON, no markdown."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        import json
        content = response.choices[0].message.content
        post_data = json.loads(content)

        return {
            "success": True,
            "property_name": property_name,
            "platform": platform_str,
            "topic": topic,
            "post": post_data,
            "model_used": model,
        }

    except Exception as e:
        logger.error(f"Social media post generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "property_name": property_name,
            "platform": platform_str,
        }


async def improve_ad_copy(
    existing_copy: str,
    platform: AdPlatform | str,
    feedback: Optional[str] = None,
    performance_data: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """
    Improve existing ad copy based on feedback or performance data.

    Args:
        existing_copy: The current ad copy text.
        platform: Target platform.
        feedback: Human feedback on what to change.
        performance_data: Campaign metrics (CTR, CPC, conversion rate, etc.).
        model: OpenAI model.

    Returns:
        Dict with improved ad copy and explanation of changes.
    """
    client = _get_openai_client()

    platform_str = platform.value if isinstance(platform, AdPlatform) else platform

    perf_text = ""
    if performance_data:
        perf_parts = []
        for k, v in performance_data.items():
            perf_parts.append(f"- {k}: {v}")
        perf_text = f"\n**Performance Data:**\n" + "\n".join(perf_parts)

    user_prompt = f"""Improve this {platform_str.replace('_', ' ').title()} ad copy:

**Current Copy:**
{existing_copy}

{f"**Feedback:** {feedback}" if feedback else ""}
{perf_text}

Provide an improved version with an explanation of what was changed and why.

Return a JSON object with keys: "improved_copy", "changes_made", "expected_improvement"
Return ONLY the JSON, no markdown."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a performance marketing expert who optimizes ad copy "
                    "for better conversion rates. Always comply with Fair Housing guidelines.",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        import json
        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "success": True,
            "platform": platform_str,
            "original_copy": existing_copy,
            **result,
            "model_used": model,
        }

    except Exception as e:
        logger.error(f"Ad copy improvement failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "platform": platform_str,
        }


async def generate_campaign_strategy(
    property_name: str,
    budget: float,
    platforms: List[str],
    property_details: Optional[Dict[str, Any]] = None,
    goals: Optional[str] = None,
    timeline: str = "30 days",
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    """
    Generate a comprehensive multi-platform ad campaign strategy.

    Args:
        property_name: Property name.
        budget: Total campaign budget in dollars.
        platforms: List of target platforms.
        property_details: Property information.
        goals: Campaign goals description.
        timeline: Campaign timeline.
        model: OpenAI model.

    Returns:
        Dict with full campaign strategy, budget allocation, and ad copy per platform.
    """
    client = _get_openai_client()

    platforms_text = ", ".join(p.replace("_", " ").title() for p in platforms)
    goals_text = goals or "maximize qualified leads for apartment tours"

    user_prompt = f"""Create a comprehensive advertising campaign strategy:

**Property:** {property_name}
**Budget:** ${budget:,.2f}
**Timeline:** {timeline}
**Platforms:** {platforms_text}
**Goals:** {goals_text}
{_format_property_details(property_details) if property_details else ""}

Include:
1. Budget allocation across platforms (percentage and dollar amounts)
2. Campaign structure (campaigns, ad sets, audiences)
3. Ad copy for each platform (2 variations each)
4. Targeting recommendations for each platform
5. A/B testing suggestions
6. KPI targets and benchmarks
7. Optimization schedule

Return a JSON object with keys:
"budget_allocation", "platform_strategies", "kpi_targets", "optimization_plan", "executive_summary"

Return ONLY the JSON, no markdown."""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior digital marketing strategist specializing "
                    "in multifamily real estate. You create data-driven campaign strategies "
                    "that maximize ROI. Always comply with Fair Housing guidelines.",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        import json
        content = response.choices[0].message.content
        strategy = json.loads(content)

        return {
            "success": True,
            "property_name": property_name,
            "budget": budget,
            "platforms": platforms,
            "timeline": timeline,
            "strategy": strategy,
            "model_used": model,
        }

    except Exception as e:
        logger.error(f"Campaign strategy generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "property_name": property_name,
        }


# ── Helper functions ───────────────────────────────────────────────

def _format_specs(specs: Dict[str, Any]) -> str:
    """Format platform specs for the prompt."""
    lines = []
    for key, value in specs.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            lines.append(f"- {label}: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def _get_platform_output_keys(platform: str) -> str:
    """Get the expected output JSON keys per platform."""
    keys_map = {
        "facebook": '"headline", "primary_text", "description", "cta"',
        "instagram": '"caption", "hashtags", "cta"',
        "google_ads": '"headlines" (array of 3), "descriptions" (array of 2), "cta"',
        "tiktok": '"caption", "hashtags", "hook_text"',
        "linkedin": '"headline", "intro_text", "cta"',
    }
    return keys_map.get(platform, '"headline", "body_text", "cta"')


def _format_property_details(details: Dict[str, Any]) -> str:
    """Format property details for the prompt."""
    if not details:
        return ""
    parts = ["\n**Property Details:**"]
    for key, value in details.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        parts.append(f"- {label}: {value}")
    return "\n".join(parts)
