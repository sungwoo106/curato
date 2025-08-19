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

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two coordinates using the Haversine formula.
    
    Args:
        lat1, lon1: First coordinate pair
        lat2, lon2: Second coordinate pair
        
    Returns:
        float: Distance in meters
    """
    import math
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in meters
    r = 6371000
    return r * c

def validate_geographic_proximity(locations: list, max_distance: float = 800.0) -> dict:
    """
    Validate that selected locations are within acceptable walking distance.
    
    Args:
        locations (list): List of location dictionaries with lat/lng coordinates
        max_distance (float): Maximum acceptable distance in meters
        
    Returns:
        dict: Validation results with distances and recommendations
    """
    if len(locations) < 2:
        return {"valid": True, "max_distance": 0, "average_distance": 0, "recommendations": []}
    
    distances = []
    recommendations = []
    
    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            loc1 = locations[i]
            loc2 = locations[j]
            
            if 'latitude' in loc1 and 'longitude' in loc1 and 'latitude' in loc2 and 'longitude' in loc2:
                distance = calculate_distance(
                    loc1['latitude'], loc1['longitude'],
                    loc2['latitude'], loc2['longitude']
                )
                distances.append(distance)
                
                if distance > max_distance:
                    recommendations.append(
                        f"Consider replacing {loc1['place_name']} or {loc2['place_name']} "
                        f"with a closer alternative (distance: {distance:.1f}m)"
                    )
    
    if distances:
        max_dist = max(distances)
        avg_dist = sum(distances) / len(distances)
        valid = max_dist <= max_distance
    else:
        max_dist = avg_dist = 0
        valid = True
    
    return {
        "valid": valid,
        "max_distance": max_dist,
        "average_distance": avg_dist,
        "recommendations": recommendations
    }

def get_geographic_clustering_info(recommendations_json: json) -> str:
    """
    Analyze and provide geographic clustering information for Phi prompt optimization.
    
    Args:
        recommendations_json (json): Raw place recommendations from Kakao API
        
    Returns:
        str: Geographic clustering analysis and recommendations
    """
    if not recommendations_json:
        return "No geographic data available."
    
    # Extract coordinates and calculate basic clustering info
    coordinates = []
    for place in recommendations_json:
        if 'latitude' in place and 'longitude' in place:
            coordinates.append({
                'name': place.get('place_name', 'Unknown'),
                'lat': place['latitude'],
                'lng': place['longitude']
            })
    
    if len(coordinates) < 2:
        return f"Single location available: {coordinates[0]['name'] if coordinates else 'None'}"
    
    # Calculate center point
    center_lat = sum(coord['lat'] for coord in coordinates) / len(coordinates)
    center_lng = sum(coord['lng'] for coord in coordinates) / len(coordinates)
    
    # Find distances from center
    distances_from_center = []
    for coord in coordinates:
        distance = calculate_distance(center_lat, center_lng, coord['lat'], coord['lng'])
        distances_from_center.append((coord['name'], distance))
    
    # Sort by distance from center
    distances_from_center.sort(key=lambda x: x[1])
    
    # Group into proximity zones
    close_places = [name for name, dist in distances_from_center if dist <= 400]
    medium_places = [name for name, dist in distances_from_center if 400 < dist <= 800]
    far_places = [name for name, dist in distances_from_center if dist > 800]
    
    # Generate clustering recommendations
    clustering_info = f"""GEOGRAPHIC CLUSTERING ANALYSIS:
Center point: {len(coordinates)} places clustered around ({center_lat:.6f}, {center_lng:.6f})

PROXIMITY ZONES:
• Close (≤400m): {len(close_places)} places - {', '.join(close_places[:3])}{'...' if len(close_places) > 3 else ''}
• Medium (400-800m): {len(medium_places)} places - {', '.join(medium_places[:3])}{'...' if len(medium_places) > 3 else ''}
• Far (>800m): {len(far_places)} places - {', '.join(far_places[:3])}{'...' if len(far_places) > 3 else ''}

RECOMMENDATION: Prioritize places in the Close and Medium zones for walkable itineraries.
Avoid selecting multiple places from the Far zone unless necessary."""
    
    return clustering_info

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
            "priority": ["all-ages appeal", "educational value", "safe environment", "group activities"],
            "avoid": ["adult-only", "dangerous", "expensive", "quiet/reflective"]
        }
    }
    
    # Get companion-specific criteria
    criteria = companion_criteria.get(companion_type.lower(), companion_criteria["solo"])
    
    # Get companion-specific prompt enhancement
    companion_enhancement = get_companion_specific_prompt_enhancement(
        companion_type, start_time, budget_level
    )
    
    # Format recommendations for Phi
    formatted_recommendations = format_recommendations_for_phi(recommendations_json)
    
    # Get geographic clustering information
    clustering_info = get_geographic_clustering_info(recommendations_json)
    
    # Enhanced prompt with stronger geographic constraints
    prompt = f"""<|system|>
You are a travel planner. Select EXACTLY 4-5 locations from the provided candidates.
Respond with a simple list of selected places, not JSON.
IMPORTANT: You must select REAL places from the candidates list below. 
Do not use placeholder text or generic terms.
CRITICAL: Generate EXACTLY 4-5 places, no more, no less.

GEOGRAPHIC CONSTRAINT: The candidates below are PRE-CLUSTERED for geographic proximity.
You MUST prioritize places that are within 800 meters of each other for a walkable experience.
Maximum walking distance between any two places should be 800m or less.

COMPANION TYPE: {companion_type}
PRIORITY CRITERIA: {', '.join(criteria['priority'])}
AVOID: {', '.join(criteria['avoid'])}

{companion_enhancement}

{clustering_info}

CANDIDATE PLACES:
{formatted_recommendations}

SELECTION PROCESS:
1. First, identify places that match your companion type priorities
2. Then, ensure geographic proximity (max 800m between places)
3. Finally, select EXACTLY 4-5 places that create a logical walking route
4. List only the exact place names from the candidates above

RESPONSE FORMAT:
[Copy exact name from candidates]
[Copy exact name from candidates]
[Copy exact name from candidates]
[Copy exact name from candidates]
[Copy exact name from candidates] (if selecting 5)

Remember: Geographic proximity is CRITICAL for walkable itineraries!
<|end|>

<|user|>
TASK: Select EXACTLY 4-5 locations from the candidates above for a {companion_type.lower()} outing.
Focus on geographic proximity (max 800m between places) and {companion_type.lower()}-appropriate experiences.
<|end|>

<|assistant|>
I'll select 4-5 places that are geographically close and suitable for {companion_type.lower()} outings:

"""

    return prompt

# =============================================================================
# TOKEN-EFFICIENT QWEN PROMPT FOR COMPREHENSIVE STORYTELLING
# =============================================================================

def build_qwen_itinerary_prompt(
    locations: list,
    companion_type: str,
    budget_level: str,
    start_time: int = 12,
) -> str:
    """
    Build a unified, well-engineered prompt for Qwen that ensures comprehensive coverage.
    
    This is the primary prompt that consolidates all Qwen functionality into a single,
    optimized prompt for maximum place coverage and emotional engagement.
    
    Args:
        locations (list): List of 4-5 locations from the location selector
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time for temporal context
        
    Returns:
        str: Unified prompt string for comprehensive itinerary generation
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
    
    # Format locations with detailed context
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
    
    # Enhanced structure with stronger place coverage requirements
    prompt = f"""<|im_start|>system
You are a master storyteller creating comprehensive travel itineraries.
Your task is to cover ALL {len(locations)} locations in detail, ensuring no place is missed.
Use {tone_style['tone']} language and {tone_style['style_note']} for maximum engagement.

CRITICAL: You MUST cover every single location listed below. Missing any location is NOT acceptable.
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
{chr(10).join([f"{i+1}. LOCATION {i+1}: {locations[i]['place_name']} - {_get_location_description(i, len(locations))}" for i in range(len(locations))])}

PLACE COVERAGE CHECKLIST:
{chr(10).join([f"□ {locations[i]['place_name']}" for i in range(len(locations))])}

IMPORTANT: 
- Each location must be clearly labeled and described in detail
- Do not skip any location - this is mandatory
- Make emotional connections between them
- Create a cohesive narrative that flows from one location to the next
- End with [END] to signal completion

VERIFICATION: Before finishing, ensure you have covered all {len(locations)} locations.
<|im_end|>

<|im_start|>assistant"""

    return prompt

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
    
    # Enhanced core prompt with stronger coverage requirements
    prompt = f"""<|im_start|>system
You are a master storyteller creating immersive travel narratives. 
Generate a comprehensive itinerary covering ALL {len(locations)} locations with emotional depth.

CRITICAL: You MUST cover every single location listed below. Missing any location is NOT acceptable.
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

MANDATORY STRUCTURE (follow exactly):
{chr(10).join([f"{i+1}. LOCATION {i+1}: {locations[i]['place_name']} - {_get_location_description(i, len(locations))}" for i in range(len(locations))])}

PLACE COVERAGE CHECKLIST:
{chr(10).join([f"□ {locations[i]['place_name']}" for i in range(len(locations))])}

Make each location memorable and connect them emotionally. Ensure comprehensive coverage.
End with [END] to signal completion.

VERIFICATION: Before finishing, ensure you have covered all {len(locations)} locations.
<|im_end|>

<|im_start|>assistant"""

    return prompt

def _get_location_description(position: int, total_locations: int) -> str:
    """
    Generate appropriate description for a location based on its position in the itinerary.
    
    Args:
        position (int): 0-based position of the location
        total_locations (int): Total number of locations in the itinerary
        
    Returns:
        str: Description appropriate for the location's position
    """
    if total_locations == 4:
        descriptions = [
            "Opening experience, emotional tone",
            "Development, building connection", 
            "Climax, peak experience",
            "Closing, satisfying resolution"
        ]
    elif total_locations == 5:
        descriptions = [
            "Opening experience, emotional tone",
            "Development, building connection",
            "Climax, peak experience", 
            "Continuation, maintaining momentum",
            "Closing, satisfying resolution"
        ]
    else:
        # Fallback for unexpected counts
        descriptions = ["Carefully selected location"] * total_locations
    
    return descriptions[position] if position < len(descriptions) else "Carefully selected location"

def analyze_itinerary_quality(itinerary_text: str, locations: list) -> dict:
    """
    Analyze the quality of a generated itinerary and provide improvement suggestions.
    
    Args:
        itinerary_text (str): The generated itinerary text
        locations (list): List of locations that should be covered
        
    Returns:
        dict: Analysis results with quality metrics and suggestions
    """
    analysis = {
        "total_locations": len(locations),
        "covered_locations": 0,
        "missing_locations": [],
        "coverage_percentage": 0.0,
        "structure_quality": "unknown",
        "emotional_depth": "unknown",
        "suggestions": []
    }
    
    # Check location coverage
    covered = []
    missing = []
    
    for location in locations:
        place_name = location.get('place_name', '')
        if place_name and place_name in itinerary_text:
            covered.append(place_name)
        else:
            missing.append(place_name)
    
    analysis["covered_locations"] = len(covered)
    analysis["missing_locations"] = missing
    analysis["coverage_percentage"] = (len(covered) / len(locations)) * 100 if locations else 0
    
    # Analyze structure quality
    if "LOCATION 1:" in itinerary_text and "LOCATION 2:" in itinerary_text:
        analysis["structure_quality"] = "good"
    elif any(f"LOCATION {i}:" in itinerary_text for i in range(1, len(locations) + 1)):
        analysis["structure_quality"] = "moderate"
    else:
        analysis["structure_quality"] = "poor"
    
    # Analyze emotional depth
    emotional_keywords = ["feeling", "emotion", "beautiful", "romantic", "tender", "warm", "magical", "special"]
    emotional_count = sum(1 for keyword in emotional_keywords if keyword.lower() in itinerary_text.lower())
    
    if emotional_count >= 5:
        analysis["emotional_depth"] = "excellent"
    elif emotional_count >= 3:
        analysis["emotional_depth"] = "good"
    elif emotional_count >= 1:
        analysis["emotional_depth"] = "moderate"
    else:
        analysis["emotional_depth"] = "poor"
    
    # Generate improvement suggestions
    if analysis["coverage_percentage"] < 100:
        analysis["suggestions"].append(
            f"Missing {len(missing)} locations: {', '.join(missing)}. "
            "Ensure all selected locations are covered in detail."
        )
    
    if analysis["structure_quality"] == "poor":
        analysis["suggestions"].append(
            "Improve structure by clearly labeling each location with 'LOCATION X:' format."
        )
    
    if analysis["emotional_depth"] == "poor":
        analysis["suggestions"].append(
            "Enhance emotional engagement by including more descriptive language and feelings."
        )
    
    if len(itinerary_text) < 1000:
        analysis["suggestions"].append(
            "Consider expanding the itinerary with more detailed descriptions and activities."
        )
    
    return analysis

def generate_improvement_prompt(analysis: dict, locations: list) -> str:
    """
    Generate a targeted improvement prompt based on itinerary analysis.
    
    Args:
        analysis (dict): Quality analysis results
        locations (list): List of locations to cover
        
    Returns:
        str: Targeted improvement prompt
    """
    if analysis["coverage_percentage"] == 100 and analysis["structure_quality"] == "good":
        return "Itinerary quality is good. No specific improvements needed."
    
    improvement_prompt = f"""<|im_start|>system
You are improving an existing travel itinerary. Address the following issues:

QUALITY ANALYSIS:
- Location Coverage: {analysis['coverage_percentage']:.1f}% ({analysis['covered_locations']}/{analysis['total_locations']})
- Structure Quality: {analysis['structure_quality']}
- Emotional Depth: {analysis['emotional_depth']}

ISSUES TO FIX:
{chr(10).join([f"• {suggestion}" for suggestion in analysis['suggestions']])}

TARGET LOCATIONS:
{chr(10).join([f"{i+1}. {loc.get('place_name', 'Unknown')}" for i, loc in enumerate(locations)])}

IMPROVEMENT REQUIREMENTS:
- Cover ALL {len(locations)} locations with equal attention
- Use clear 'LOCATION X:' structure
- Maintain emotional engagement and narrative flow
- End with [END] to signal completion
<|im_end|>

<|im_start|>user
Please improve this itinerary to address the quality issues identified above.
<|im_end|>

<|im_start|>assistant"""

    return improvement_prompt
