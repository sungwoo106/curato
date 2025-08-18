"""
AI Prompt Templates and Generation

This module contains two essential prompt templates:
1. Lightweight Phi-3.5 Mini prompt for selecting 4-5 locations
2. Enhanced Qwen prompt for generating descriptive, unique stories

The prompts are designed to:
- Generate optimal 4-5 location routes with minimal complexity
- Create unique, descriptive narratives that feel personal and engaging
- Maintain consistent quality across different companion types
"""

import json
import random
from constants import TONE_STYLE_MAP, LOW_BUDGET, MEDIUM_BUDGET, HIGH_BUDGET

# =============================================================================
# LIGHTWEIGHT PHI-3.5 MINI PROMPT FOR LOCATION SELECTION (4-5 PLACES)
# =============================================================================

def build_phi_location_prompt(
    start_location: tuple,
    companion_type: str,
    start_time: int,
    budget_level: str,
    recommendations_json: json,
) -> str:
    """
    Build a lightweight prompt for Phi-3.5 Mini to select 4-5 optimal locations.
    
    This prompt is designed to be simple and efficient for the lightweight model:
    - Choose 4-5 locations from different place types
    - Ensure logical flow and variety
    - Match companion type and budget preferences
    - Return structured JSON with reasoning
    
    Args:
        start_location (tuple): Starting coordinates (latitude, longitude)
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        start_time (int): Starting time in 24-hour format
        budget_level (str): Budget level (low, medium, high)
        recommendations_json (json): Formatted place recommendations from Kakao API
        
    Returns:
        str: Lightweight prompt string for Phi-3.5 Mini
    """
    
    # Simple companion guidance
    companion_guide = {
        "solo": "quiet, reflective places",
        "couple": "romantic, intimate spots",
        "friends": "fun, social locations",
        "family": "safe, educational places"
    }
    
    # Time-based guidance
    if start_time < 12:
        time_guide = "morning-friendly locations"
    elif start_time < 17:
        time_guide = "afternoon-appropriate spots"
    else:
        time_guide = "evening atmosphere places"
    
    return f"""<|system|>
You are a travel planner. Select 4-5 locations for a {companion_type.lower()} outing.
IMPORTANT: Respond ONLY with valid JSON. Do not include the prompt, system messages, or any other text.
<|end|>

<|user|>
Starting from {start_location} at {start_time}:00, choose 4-5 locations that are:
- {companion_guide.get(companion_type.lower(), "suitable for the outing")}
- {time_guide}
- Within {budget_level} budget
- Different place types for variety
- Near each other for easy flow

Return ONLY a JSON array with this exact structure:
[
  {{
    "place_name": "Location Name",
    "road_address_name": "Full Address",
    "place_type": "Category",
    "distance": "Distance from start",
    "place_url": "Kakao Map URL",
    "latitude": 37.123456,
    "longitude": 126.123456
  }}
]

Available places:
{recommendations_json}

Remember: Output ONLY the JSON array, nothing else.
<|end|>

<|assistant|>"""

# =============================================================================
# ENHANCED QWEN PROMPT FOR DESCRIPTIVE STORYTELLING
# =============================================================================

def build_qwen_story_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
) -> str:
    """
    Build an enhanced prompt for Qwen to generate descriptive, unique stories.
    
    This prompt creates immersive narratives that:
    - Transform locations into memorable experiences
    - Use rich sensory language and unique perspectives
    - Create emotional connections and personal moments
    - Avoid generic descriptions in favor of vivid storytelling
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        
    Returns:
        str: Enhanced prompt string for descriptive storytelling
    """
    
    # Enhanced emotional journey mapping
    emotional_journey = {
        "solo": {
            "opening": "quiet anticipation and self-discovery",
            "development": "growing confidence and personal insights",
            "climax": "profound moments of connection",
            "closing": "peaceful reflection and satisfaction"
        },
        "couple": {
            "opening": "warm excitement and shared anticipation",
            "development": "deepening connection and romantic moments",
            "climax": "peak emotional intimacy and joy",
            "closing": "sweet contentment and future dreams"
        },
        "friends": {
            "opening": "bubbling energy and shared enthusiasm",
            "development": "building laughter and collective memories",
            "climax": "peak fun and unforgettable moments",
            "closing": "grateful camaraderie and plans for next time"
        },
        "family": {
            "opening": "loving preparation and family bonding",
            "development": "shared learning and growing together",
            "climax": "heartwarming family moments and joy",
            "closing": "deep family connection and gratitude"
        }
    }
    
    # Sensory enhancement guide for unique descriptions
    sensory_guide = {
        "visual": "colors, lighting, architecture, people-watching, seasonal beauty, unique details",
        "auditory": "ambient sounds, music, laughter, city rhythms, nature sounds, local atmosphere",
        "tactile": "textures, temperatures, comfortable seating, smooth surfaces, seasonal sensations",
        "olfactory": "aromas, fresh air, food scents, seasonal fragrances, local smells",
        "gustatory": "flavors, textures, temperature contrasts, local specialties, unique tastes"
    }
    
    # Budget-appropriate activity suggestions
    money_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }
    
    selected_activities = random.sample(money_activities[budget_level], k=2)
    
    # Format locations with context
    locs_text = "\n".join([
        f"{i+1}. {loc['place_name']} ({loc['place_type']}) - {loc.get('reasoning', 'Carefully selected for optimal experience')}"
        for i, loc in enumerate(locations)
    ])
    
    # Time-based narrative elements
    time_context = {
        "morning": "morning light, fresh energy, new beginnings, crisp air",
        "afternoon": "warm afternoon glow, active exploration, shared meals, golden sunlight",
        "evening": "golden hour magic, intimate atmospheres, evening enchantment, soft lighting"
    }
    
    if start_time < 12:
        time_period = "morning"
    elif start_time < 17:
        time_period = "afternoon"
    else:
        time_period = "evening"
    
    # Enhanced storytelling prompt
    user_message = f"""You are a master storyteller who creates unique, immersive travel narratives. 
Transform these {len(locations)} locations into an unforgettable journey that feels personal and one-of-a-kind.

STORY CONTEXT:
- Companion Type: {companion_type}
- Emotional Journey: {emotional_journey[companion_type.lower()]}
- Time Period: {time_context[time_period]}
- Budget Level: {budget_level}

LOCATIONS TO WEAVE INTO STORY:
{locs_text}

STORYTELLING REQUIREMENTS:
1. **OPENING** (Location 1): Set the emotional tone with vivid, unique descriptions
2. **DEVELOPMENT** (Location 2): Build connection with sensory details and personal moments
3. **CLIMAX** (Location 3): Create the most memorable moment with rich imagery
4. **CONTINUATION** (Location 4): Maintain momentum with engaging details
5. **CLOSING** (Location 5): Provide satisfying resolution with future anticipation

UNIQUENESS TECHNIQUES:
- Use specific, vivid language that makes each moment feel unique
- Include unexpected details and personal touches
- Create emotional connections between locations
- Weave in budget-appropriate activities: {selected_activities}
- Use {TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])['style_note']}
- Avoid generic descriptions - make every detail count

SENSORY ENRICHMENT:
Incorporate: {', '.join(sensory_guide.values())}

EMOTIONAL JOURNEY STRUCTURE:
- Opening: {emotional_journey[companion_type.lower()]['opening']}
- Development: {emotional_journey[companion_type.lower()]['development']}
- Climax: {emotional_journey[companion_type.lower()]['climax']}
- Closing: {emotional_journey[companion_type.lower()]['closing']}

Think: How can I make this story feel completely unique and personal? What specific details will make each location memorable? How can I create emotional connections that feel genuine?

Now, craft your unique narrative..."""
    
    return f"""<|im_start|>system
You are a master storyteller and travel writer who creates deeply personal, unique narratives. 
You excel at transforming ordinary locations into extraordinary journeys through vivid sensory language, 
emotional depth, and unexpected details that make every story feel one-of-a-kind.
<|im_end|>
<|im_start|>user
{user_message}
<|im_end|>
<|im_start|>assistant"""
