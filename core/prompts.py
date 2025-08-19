"""
AI Prompt Templates and Generation

This module contains optimized prompt templates designed for:
1. Lightweight Phi-3.5 Mini prompt for selecting 4-5 locations
2. Token-efficient Qwen prompt for generating comprehensive, emotional itineraries

The prompts are engineered to:
- Generate optimal 4-5 location routes with minimal complexity
- Create comprehensive narratives covering ALL selected places
- Maintain emotional engagement while being token-efficient
- Ensure consistent quality across different companion types
- Incorporate user preferences effectively
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
Respond with a simple list of selected places, not JSON.
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
1. Review 20 candidates below
2. Select top 4-5 places based on criteria
3. List them in order (1, 2, 3, 4, 5)
4. Include the place name and why you chose it

OUTPUT: Simple numbered list of your selected places:
1. Place Name - Brief reason for selection
2. Place Name - Brief reason for selection
3. Place Name - Brief reason for selection
4. Place Name - Brief reason for selection
5. Place Name - Brief reason for selection

CANDIDATES:
{format_recommendations_for_phi(recommendations_json)}

IMPORTANT: Select actual places from the candidates above. Do NOT use placeholder text.
<|end|>

<|assistant|>
"""

# =============================================================================
# TOKEN-EFFICIENT QWEN PROMPT FOR COMPREHENSIVE STORYTELLING
# =============================================================================

def build_qwen_story_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
) -> str:
    """
    Build a token-efficient prompt for Qwen to generate comprehensive, emotional itineraries.
    
    This prompt is engineered to:
    - Cover ALL selected places comprehensively
    - Create emotional connections between locations
    - Use minimal tokens while maintaining quality
    - Ensure consistent narrative flow
    - Incorporate user preferences effectively
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        
    Returns:
        str: Token-efficient prompt string for comprehensive storytelling
    """
    
    # Get tone and style for companion type
    tone_style = TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])
    
    # Get budget-appropriate activities
    budget_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }
    
    # Select 2-3 budget-appropriate activities
    selected_activities = random.sample(budget_activities[budget_level], k=min(3, len(budget_activities[budget_level])))
    
    # Format locations efficiently
    locs_text = "\n".join([
        f"{i+1}. {loc['place_name']} ({loc.get('place_type', 'Selected location')})"
        for i, loc in enumerate(locations)
    ])
    
    # Time context
    if start_time < 12:
        time_context = "morning light, fresh energy, new beginnings"
    elif start_time < 17:
        time_context = "warm afternoon glow, active exploration, golden sunlight"
    else:
        time_context = "golden hour magic, evening enchantment, soft lighting"
    
    # Core prompt - token-efficient but comprehensive
    prompt = f"""<|im_start|>system
You are a master storyteller creating immersive travel narratives. 
Generate a comprehensive itinerary covering ALL {len(locations)} locations with emotional depth.
<|im_end|>

<|im_start|>user
Create a {tone_style['tone']} itinerary for {companion_type} exploring these locations:

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations in detail
- Use {tone_style['style_note']}
- Include budget activities: {', '.join(selected_activities)}
- Time context: {time_context}
- Budget level: {budget_level}

STRUCTURE:
1. Opening at Location 1: Set emotional tone
2. Development at Location 2: Build connection
3. Climax at Location 3: Peak experience
4. Continuation at Location 4: Maintain momentum
5. Closing at Location 5: Satisfying resolution

Make each location memorable and connect them emotionally. Ensure comprehensive coverage.
<|im_end|>

<|im_start|>assistant"""

    return prompt

def build_comprehensive_qwen_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
) -> str:
    """
    Build a comprehensive prompt for Qwen that ensures ALL places are covered.
    
    This is an alternative prompt that provides more explicit guidance for comprehensive coverage.
    Use this when the token-efficient version doesn't provide enough coverage.
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        
    Returns:
        str: Comprehensive prompt string for complete coverage
    """
    
    # Get tone and style for companion type
    tone_style = TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])
    
    # Get budget-appropriate activities
    budget_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }
    
    # Select 2-3 budget-appropriate activities
    selected_activities = random.sample(budget_activities[budget_level], k=min(3, len(budget_activities[budget_level])))
    
    # Format locations with more context
    locs_text = "\n".join([
        f"{i+1}. {loc['place_name']} ({loc.get('place_type', 'Selected location')}) - {loc.get('selection_reason', 'Carefully chosen for optimal experience')}"
        for i, loc in enumerate(locations)
    ])
    
    # Time context
    if start_time < 12:
        time_context = "morning light, fresh energy, new beginnings"
    elif start_time < 17:
        time_context = "warm afternoon glow, active exploration, golden sunlight"
    else:
        time_context = "golden hour magic, evening enchantment, soft lighting"
    
    # Enhanced comprehensive prompt
    prompt = f"""<|im_start|>system
You are a master storyteller creating comprehensive travel itineraries.
Your task is to cover ALL {len(locations)} locations in detail, ensuring no place is missed.
<|im_end|>

<|im_start|>user
Create a {tone_style['tone']} itinerary for {companion_type} exploring these locations:

{locs_text}

CRITICAL REQUIREMENTS:
- MUST cover ALL {len(locations)} locations with equal attention
- Each location gets its own detailed paragraph
- Use {tone_style['style_note']}
- Include budget activities: {', '.join(selected_activities)}
- Time context: {time_context}
- Budget level: {budget_level}

MANDATORY STRUCTURE (follow exactly):
1. LOCATION 1: {locations[0]['place_name']} - Opening experience, emotional tone
2. LOCATION 2: {locations[1]['place_name']} - Development, building connection
3. LOCATION 3: {locations[2]['place_name']} - Climax, peak experience
4. LOCATION 4: {locations[3]['place_name']} - Continuation, maintaining momentum
5. LOCATION 5: {locations[4]['place_name']} - Closing, satisfying resolution

IMPORTANT: Each location must be clearly labeled and described in detail.
Do not skip any location. Make emotional connections between them.
<|im_end|>

<|im_start|>assistant"""

    return prompt

def build_ultra_comprehensive_qwen_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
) -> str:
    """
    Build an ultra-comprehensive prompt for Qwen that guarantees ALL places are covered.
    
    This is the most explicit prompt that uses numbered sections and strict formatting
    to ensure maximum coverage. Use this as a final fallback when other prompts fail.
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        
    Returns:
        str: Ultra-comprehensive prompt string for guaranteed coverage
    """
    
    # Get tone and style for companion type
    tone_style = TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])
    
    # Get budget-appropriate activities
    budget_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }
    
    # Select 2-3 budget-appropriate activities
    selected_activities = random.sample(budget_activities[budget_level], k=min(3, len(budget_activities[budget_level])))
    
    # Time context
    if start_time < 12:
        time_context = "morning light, fresh energy, new beginnings"
    elif start_time < 17:
        time_context = "warm afternoon glow, active exploration, golden sunlight"
    else:
        time_context = "golden hour magic, evening enchantment, soft lighting"
    
    # Build dynamic location sections based on actual count
    location_sections = []
    for i, location in enumerate(locations, 1):
        if i == 1:
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, including emotional tone and {tone_style['style_note']}]"
        elif i == 2:
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, building connection from previous location]"
        elif i == 3:
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, creating peak experience]"
        elif i == 4:
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, maintaining momentum]"
        elif i == 5:
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, providing satisfying resolution]"
        else:
            # Handle any additional locations dynamically
            section = f"# LOCATION {i}: {location['place_name']}\n[Write 3-4 sentences about this location, continuing the journey]"
        
        location_sections.append(section)
    
    # Join all location sections
    locations_text = "\n\n".join(location_sections)
    
    # Ultra-comprehensive prompt with dynamic formatting
    prompt = f"""<|im_start|>system
You are a travel writer creating detailed itineraries. You MUST cover ALL {len(locations)} locations.
Use the EXACT format specified below. Do not skip any location.
<|im_end|>

<|im_start|>user
Write a {tone_style['tone']} itinerary for {companion_type} with budget {budget_level}.
Time: {time_context}

FORMAT: Use exactly this structure with these exact headings:

{locations_text}

Include these budget activities: {', '.join(selected_activities)}
<|im_end|>

<|im_start|>assistant"""

    return prompt

def build_adaptive_qwen_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
    target_tokens: int = 800,
) -> str:
    """
    Build an adaptive prompt for Qwen that automatically adjusts based on target token count.
    
    This function creates prompts that are optimized for specific token targets while
    maintaining comprehensive coverage of all locations.
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        target_tokens (int): Target token count for the generated response
        
    Returns:
        str: Adaptive prompt string optimized for target token count
    """
    
    # Get tone and style for companion type
    tone_style = TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])
    
    # Get budget-appropriate activities
    budget_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }
    
    # Select activities based on target token count
    if target_tokens <= 600:
        activity_count = 1
    elif target_tokens <= 800:
        activity_count = 2
    else:
        activity_count = 3
    
    selected_activities = random.sample(budget_activities[budget_level], k=min(activity_count, len(budget_activities[budget_level])))
    
    # Time context
    if start_time < 12:
        time_context = "morning light, fresh energy, new beginnings"
    elif start_time < 17:
        time_context = "warm afternoon glow, active exploration, golden sunlight"
    else:
        time_context = "golden hour magic, evening enchantment, soft lighting"
    
    # Calculate sentences per location based on target tokens
    # Assume ~20-25 tokens per sentence
    total_sentences = max(3, target_tokens // 25)
    sentences_per_location = max(2, total_sentences // len(locations))
    
    # Format locations efficiently
    locs_text = "\n".join([
        f"{i+1}. {loc['place_name']} ({loc.get('place_type', 'Selected location')})"
        for i, loc in enumerate(locations)
    ])
    
    # Adaptive prompt based on target tokens
    if target_tokens <= 600:
        # Compact prompt
        prompt = f"""<|im_start|>system
You are a travel writer. Cover ALL {len(locations)} locations in {target_tokens} tokens.
<|im_end|>

<|im_start|>user
Write a {tone_style['tone']} itinerary for {companion_type} ({budget_level} budget, {time_context}):

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations
- Use {tone_style['style_note']}
- Include: {', '.join(selected_activities)}
- Target: {target_tokens} tokens total
- {sentences_per_location} sentences per location

Format: Number each location clearly.
<|im_end|>

<|im_start|>assistant"""
    
    elif target_tokens <= 800:
        # Standard prompt
        prompt = f"""<|im_start|>system
You are a travel writer creating comprehensive itineraries.
Cover ALL {len(locations)} locations with emotional depth.
<|im_end|>

<|im_start|>user
Create a {tone_style['tone']} itinerary for {companion_type} exploring:

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations in detail
- Use {tone_style['style_note']}
- Include budget activities: {', '.join(selected_activities)}
- Time context: {time_context}
- Budget: {budget_level}
- Target: {target_tokens} tokens

STRUCTURE: Number each location and describe it with {sentences_per_location} sentences.
<|im_end|>

<|im_start|>assistant"""
    
    else:
        # Detailed prompt
        prompt = f"""<|im_start|>system
You are a master storyteller creating immersive travel narratives.
Generate a comprehensive itinerary covering ALL {len(locations)} locations with rich detail.
<|im_end|>

<|im_start|>user
Create a {tone_style['tone']} itinerary for {companion_type} exploring:

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations comprehensively
- Use {tone_style['style_note']}
- Include budget activities: {', '.join(selected_activities)}
- Time context: {time_context}
- Budget level: {budget_level}
- Target: {target_tokens} tokens

STRUCTURE:
1. Location 1: Opening experience and emotional tone
2. Location 2: Development and connection building
3. Location 3: Peak experience and climax
4. Location 4: Continuation and momentum
5. Location 5: Resolution and future anticipation

Each location: {sentences_per_location} detailed sentences with emotional depth.
<|im_end|>

<|im_start|>assistant"""
    
    return prompt
