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
    
    # Simplified, direct prompt for better Phi extraction
    prompt = f"""<|system|>
You are a travel planner. Select EXACTLY 4-5 locations from the candidates below.
Respond with ONLY the exact place names, one per line.
Do not add explanations, just list the names.

CRITICAL: Select EXACTLY 4-5 places, no more, no less.
<|end|>

<|user|>
Select 4-5 places for a couple outing near Hongdae Station.
Choose places that are close together (within 800m) and suitable for couples.

Available places:
{formatted_recommendations}

List exactly 4-5 place names:
<|end|>

<|assistant|>
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
    
    # Enhanced prompt with specific guidance and examples
    prompt = f"""<|im_start|>system
You are a master storyteller creating romantic travel itineraries for couples.
Your task: Write a detailed, romantic itinerary covering ALL {len(locations)} locations.
Each location must have its own complete section with rich descriptions.

CRITICAL: You MUST cover every single location listed below.
<|im_end|>

<|im_start|>user
Create a romantic, poetic itinerary for a couple visiting these places near Hongdae Station:

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations with equal attention
- Each location gets its own detailed paragraph (at least 3-4 sentences)
- Use romantic, poetic language with emotional depth
- Include suggested activities: {', '.join(selected_activities)}
- Time context: {time_context}
- Budget level: {budget_level}

MANDATORY STRUCTURE (follow exactly):
{chr(10).join([f"{i+1}. LOCATION {i+1}: {locations[i]['place_name']}" for i in range(len(locations))])}

WRITING GUIDELINES:
- Start each location section with the exact format above
- Write 3-4 detailed sentences per location
- Include sensory details (sights, sounds, smells, feelings)
- Describe romantic moments and shared experiences
- Connect locations emotionally and narratively
- End the entire itinerary with [END]

EXAMPLE FORMAT:
1. LOCATION 1: [Place Name]
   [3-4 detailed sentences about the experience, atmosphere, and romantic moments]

2. LOCATION 2: [Place Name]
   [3-4 detailed sentences about the experience, atmosphere, and romantic moments]

[Continue for all locations...]

Now write your romantic itinerary covering all {len(locations)} locations:
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
    
    # Enhanced fallback prompt with specific guidance
    prompt = f"""<|im_start|>system
You are a storyteller creating romantic itineraries for couples.
Write a detailed itinerary covering ALL {len(locations)} locations.
Each location must have its own complete section.
<|im_end|>

<|im_start|>user
Create a romantic itinerary for a couple visiting these places:

{locs_text}

REQUIREMENTS:
- Cover ALL {len(locations)} locations with detailed descriptions
- Each location gets its own paragraph (at least 2-3 sentences)
- Use romantic, emotional language
- Include activities: {', '.join(selected_activities)}
- Connect locations with a flowing narrative

STRUCTURE:
{chr(10).join([f"{i+1}. LOCATION {i+1}: {locations[i]['place_name']}" for i in range(len(locations))])}

Write a detailed paragraph for each location. End with [END].
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

def extract_and_validate_place_names(phi_output: str, candidate_places: list) -> list:
    """
    Extract and validate place names from Phi model output.
    
    Args:
        phi_output (str): Raw output from Phi model
        candidate_places (list): List of candidate places to match against
        
    Returns:
        list: List of validated place names
    """
    if not phi_output or not candidate_places:
        return []
    
    # Clean the output
    cleaned_output = phi_output.strip()
    
    # Extract potential place names
    potential_names = []
    lines = cleaned_output.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('<') and not line.startswith('['):
            # Remove common prefixes and suffixes
            clean_line = line.replace('1.', '').replace('2.', '').replace('3.', '').replace('4.', '').replace('5.', '')
            clean_line = clean_line.replace('-', '').replace(':', '').strip()
            if clean_line:
                potential_names.append(clean_line)
    
    # Match against candidate places
    validated_names = []
    candidate_names = [place.get('place_name', '') for place in candidate_places]
    
    for potential_name in potential_names:
        # Exact match
        if potential_name in candidate_names:
            validated_names.append(potential_name)
            continue
        
        # Partial match (for cases where Phi might truncate names)
        for candidate_name in candidate_names:
            if candidate_name in potential_name or potential_name in candidate_name:
                if candidate_name not in validated_names:
                    validated_names.append(candidate_name)
                break
    
    return validated_names

def validate_prompt_effectiveness(prompt_text: str, model_output: str, expected_locations: list) -> dict:
    """
    Validate the effectiveness of a prompt by analyzing the model output.
    
    Args:
        prompt_text (str): The prompt that was used
        model_output (str): The output from the model
        expected_locations (list): List of locations that should be covered
        
    Returns:
        dict: Validation results with effectiveness metrics
    """
    validation = {
        "prompt_length": len(prompt_text),
        "output_length": len(model_output),
        "output_quality": "unknown",
        "location_coverage": 0,
        "structure_compliance": False,
        "completion_signal": False,
        "suggestions": []
    }
    
    # Check output length
    if len(model_output) < 100:
        validation["output_quality"] = "poor"
        validation["suggestions"].append("Output too short - prompt may need more specific guidance")
    elif len(model_output) < 500:
        validation["output_quality"] = "moderate"
        validation["suggestions"].append("Output could be longer - consider adding length requirements")
    else:
        validation["output_quality"] = "good"
    
    # Check location coverage
    covered_count = 0
    for location in expected_locations:
        place_name = location.get('place_name', '')
        if place_name and place_name in model_output:
            covered_count += 1
    
    validation["location_coverage"] = (covered_count / len(expected_locations)) * 100 if expected_locations else 0
    
    if validation["location_coverage"] < 100:
        validation["suggestions"].append(
            f"Missing {len(expected_locations) - covered_count} locations - "
            "prompt needs stronger coverage requirements"
        )
    
    # Check structure compliance
    if "LOCATION 1:" in model_output and "LOCATION 2:" in model_output:
        validation["structure_compliance"] = True
    else:
        validation["suggestions"].append("Structure not followed - add clearer formatting requirements")
    
    # Check completion signal
    if "[END]" in model_output:
        validation["completion_signal"] = True
    else:
        validation["suggestions"].append("Missing completion signal - add [END] requirement")
    
    return validation

def generate_debug_prompt(original_prompt: str, validation_results: dict) -> str:
    """
    Generate a debug version of a prompt based on validation results.
    
    Args:
        original_prompt (str): The original prompt that had issues
        validation_results (dict): Results from prompt validation
        
    Returns:
        str: Enhanced prompt with debugging improvements
    """
    debug_prompt = original_prompt
    
    # Add length requirements if output was too short
    if validation_results["output_quality"] == "poor":
        debug_prompt += "\n\nLENGTH REQUIREMENT: Write at least 500 characters total."
    
    # Add stronger coverage requirements if locations were missed
    if validation_results["location_coverage"] < 100:
        debug_prompt += "\n\nCOVERAGE REQUIREMENT: You MUST mention every single location listed above."
    
    # Add structure requirements if not followed
    if not validation_results["structure_compliance"]:
        debug_prompt += "\n\nSTRUCTURE REQUIREMENT: Use exactly the format 'LOCATION X: [Place Name]' for each location."
    
    # Add completion signal if missing
    if not validation_results["completion_signal"]:
        debug_prompt += "\n\nCOMPLETION REQUIREMENT: End your response with [END]."
    
    return debug_prompt

def create_fallback_route_plan(candidate_places: list, companion_type: str, max_places: int = 4) -> list:
    """
    Create a fallback route plan when Phi model fails to select places.
    
    Args:
        candidate_places (list): List of candidate places
        companion_type (str): Type of outing
        max_places (int): Maximum number of places to select
        
    Returns:
        list: Fallback route plan with selected places
    """
    if not candidate_places:
        return []
    
    # Sort by distance and select closest places
    sorted_places = sorted(candidate_places, key=lambda x: float(x.get('distance', 999999)))
    
    # Select up to max_places
    selected_places = sorted_places[:max_places]
    
    # Ensure we have at least 4 places
    if len(selected_places) < 4 and len(candidate_places) >= 4:
        # Add more places if available
        remaining = [p for p in candidate_places if p not in selected_places]
        selected_places.extend(remaining[:4 - len(selected_places)])
    
    return selected_places

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
