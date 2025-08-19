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
# HELPER FUNCTIONS FOR PHI PROMPT OPTIMIZATION
# =============================================================================

def format_recommendations_for_phi(recommendations_json: json) -> str:
    """
    Format place recommendations in a Phi-optimized structure for better choice selection.
    
    This function transforms the raw recommendations into a clear, structured format
    that helps Phi-3-mini make better decisions by organizing information logically.
    
    Args:
        recommendations_json (json): Raw place recommendations from Kakao API
        
    Returns:
        str: Formatted recommendations string optimized for Phi choice selection
    """
    if not recommendations_json:
        return "No places available for selection."
    
    # Group places by type for better organization
    places_by_type = {}
    for place in recommendations_json:
        place_type = place.get('place_type', 'Unknown')
        if place_type not in places_by_type:
            places_by_type[place_type] = []
        places_by_type[place_type].append(place)
    
    # Format each place type section
    formatted_sections = []
    for place_type, places in places_by_type.items():
        section = f"\n{place_type.upper()} ({len(places)} options):\n"
        
        for i, place in enumerate(places, 1):
            # Extract key information
            name = place.get('place_name', 'Unknown')
            address = place.get('road_address_name', place.get('address_name', 'No address'))
            distance = place.get('distance', 'Unknown')
            category = place.get('category_group_name', place_type)
            
            # Format the place entry - minimal tokens
            place_entry = f"{i}. {name}\n"
            place_entry += f"   Address: {address}\n"
            place_entry += f"   Distance: {distance}m\n"
            place_entry += f"   Category: {category}\n"
            
            # Add additional context if available
            if place.get('phone'):
                place_entry += f"   Phone: {place['phone']}\n"
            if place.get('category_name') and place['category_name'] != category:
                place_entry += f"   Type: {place['category_name']}\n"
            
            section += place_entry + "\n"
        
        formatted_sections.append(section)
    
    # Combine all sections
    formatted_output = "".join(formatted_sections)
    
    # Add summary at the end
    total_places = len(recommendations_json)
    formatted_output += f"\nSUMMARY: {total_places} total places across {len(places_by_type)} categories\n"
    formatted_output += "Choose 4-5 places for best experience.\n"
    
    return formatted_output

def get_companion_specific_prompt_enhancement(companion_type: str, start_time: int, budget_level: str) -> str:
    """
    Get companion-specific prompt enhancements for Phi to improve selection quality.
    
    This function provides tailored guidance based on companion type, timing, and budget
    to help Phi-3-mini make more contextually appropriate choices.
    
    Args:
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        start_time (int): Starting time in 24-hour format
        budget_level (str): Budget level (low, medium, high)
        
    Returns:
        str: Companion-specific prompt enhancement
    """
    
    # Concise companion-specific guidance
    companion_enhancements = {
        "solo": {
            "morning": "Focus on quiet spots: reflection cafes, morning markets, parks, early cultural venues.",
            "afternoon": "Choose personal exploration: museums, unique shops, quiet dining, scenic spots.",
            "evening": "Select intimate venues: reading cafes, cultural performances, rooftop views, quiet bars."
        },
        "couple": {
            "morning": "Prioritize romantic experiences: atmospheric cafes, scenic paths, morning culture, intimate brunch.",
            "afternoon": "Choose romantic activities: cultural experiences, scenic dining, unique shopping, outdoor activities.",
            "evening": "Focus on romantic atmosphere: intimate restaurants, evening entertainment, romantic views, cozy venues."
        },
        "friends": {
            "morning": "Select group activities: social cafes, group markets, outdoor activities, group cultural venues.",
            "afternoon": "Choose fun activities: interactive experiences, social dining, entertainment, outdoor group activities.",
            "evening": "Focus on social activities: group dining, entertainment venues, nightlife, social gathering places."
        },
        "family": {
            "morning": "Prioritize family activities: all-ages cafes, parks, educational activities, family cultural venues.",
            "afternoon": "Choose family activities: interactive museums, family restaurants, outdoor activities, educational experiences.",
            "evening": "Select family activities: family dining, all-ages entertainment, safe activities, family bonding."
        }
    }
    
    # Determine time period
    if start_time < 12:
        time_period = "morning"
    elif start_time < 17:
        time_period = "afternoon"
    else:
        time_period = "evening"
    
    # Get the specific enhancement
    enhancement = companion_enhancements.get(companion_type.lower(), companion_enhancements["solo"])
    time_specific_guidance = enhancement.get(time_period, enhancement["afternoon"])
    
    # Concise budget considerations
    budget_considerations = {
        "low": "Keep costs minimal while maintaining quality.",
        "medium": "Balance cost and experience quality.",
        "high": "Focus on premium experiences and quality."
    }
    
    return f"""
{companion_type.upper()} GUIDANCE:
{time_specific_guidance}

BUDGET: {budget_considerations[budget_level]}

Use this guidance to score and rank your 20 candidate places.
"""

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
    Build an optimized prompt for Phi-3.5 Mini to select 4-5 optimal locations from 20 candidates.
    
    This prompt is specifically designed for Phi-3-mini's choice selection capabilities:
    - Clear selection criteria and ranking system
    - Structured decision-making process
    - Companion type and context awareness
    - Geographic flow optimization
    - Budget and timing considerations
    
    Args:
        start_location (tuple): Starting coordinates (latitude, longitude)
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        start_time (int): Starting time in 24-hour format
        budget_level (str): Budget level (low, medium, high)
        recommendations_json (json): 20 candidate places from enhanced algorithm
        
    Returns:
        str: Optimized prompt string for Phi-3.5 Mini choice selection
    """
    
    # Enhanced companion-specific selection criteria
    companion_criteria = {
        "solo": {
            "priority": ["quiet atmosphere", "personal reflection", "cultural depth", "unique experiences"],
            "avoid": ["overly crowded", "group-focused", "romantic couples"]
        },
        "couple": {
            "priority": ["romantic atmosphere", "intimate settings", "shared experiences", "memorable moments"],
            "avoid": ["family-oriented", "solo activities", "business-focused"]
        },
        "friends": {
            "priority": ["social atmosphere", "fun activities", "group experiences", "entertainment value"],
            "avoid": ["quiet/isolated", "romantic", "educational only"]
        },
        "family": {
            "priority": ["child-friendly", "educational value", "safe environment", "entertainment for all ages"],
            "avoid": ["adult-only", "dangerous", "expensive", "quiet/reflective"]
        }
    }
    
    # Time-based selection guidance
    time_guidance = {
        "morning": {
            "ideal": ["breakfast spots", "morning activities", "fresh starts", "daytime exploration"],
            "avoid": ["evening venues", "nightlife", "late dining"]
        },
        "afternoon": {
            "ideal": ["lunch spots", "daytime activities", "outdoor exploration", "cultural visits"],
            "avoid": ["breakfast-only", "late night venues"]
        },
        "evening": {
            "ideal": ["dinner spots", "evening atmosphere", "nightlife", "romantic settings"],
            "avoid": ["breakfast spots", "daytime activities", "early closing"]
        }
    }
    
    # Budget considerations
    budget_guidance = {
        "low": "Focus on free or low-cost activities, public spaces, and budget-friendly dining",
        "medium": "Mix of free and paid activities, moderate dining options, and varied experiences",
        "high": "Premium experiences, fine dining, exclusive venues, and luxury activities"
    }
    
    # Determine time period
    if start_time < 12:
        time_period = "morning"
    elif start_time < 17:
        time_period = "afternoon"
    else:
        time_period = "evening"
    
    # Get companion-specific criteria
    criteria = companion_criteria.get(companion_type.lower(), companion_criteria["solo"])
    time_criteria = time_guidance.get(time_period, time_guidance["afternoon"])
    
    return f"""<|system|>
You are a travel planner. Select 4-5 locations from 20 candidates.
Respond ONLY with valid JSON.
CRITICAL: Generate REAL place data, not placeholder text.
<|end|>

<|user|>
TASK: Select 4-5 locations from 20 candidates.
Location: {start_location}
Companion: {companion_type}
Time: {start_time}:00 ({time_period})
Budget: {budget_level}

CRITERIA:
1. Companion fit: {', '.join(criteria['priority'])}
2. Time appropriate: {', '.join(time_criteria['ideal'])}
3. Budget: {budget_guidance[budget_level]}
4. Geographic flow: logical, walkable route
5. Variety: different place types

{get_companion_specific_prompt_enhancement(companion_type, start_time, budget_level)}

PROCESS:
1. Review 20 candidates
2. Score on companion fit, time, budget
3. Consider geographic proximity
4. Select top 4-5 places
5. Order for optimal route

OUTPUT: JSON array with place_name, road_address_name, place_type, distance, place_url, latitude, longitude, selection_reason

REQUIREMENTS:
- Each place MUST have unique latitude and longitude coordinates
- Coordinates must be different for each location
- Generate REAL data from the candidates, not placeholder text
- Use actual place names, addresses, and coordinates

CANDIDATES:
{format_recommendations_for_phi(recommendations_json)}

IMPORTANT: Generate REAL JSON with actual place data from the candidates above.
Do NOT use placeholder text like "string" or "float".
<|end|>

<|assistant|>
"""

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
