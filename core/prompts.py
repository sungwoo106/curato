"""
AI Prompt Templates and Generation

This module contains simple, straightforward prompt templates designed for:
1. Simple Phi prompt for randomly selecting 4-5 locations from 20 candidates
2. Simple Qwen prompt for generating itineraries that cover all selected places

The prompts are simplified to:
- Ask Phi to randomly pick 4-5 places from the candidate list
- Ask Qwen to create an itinerary covering ALL selected places
- Keep prompts short and direct
- Remove complex clustering and validation logic
"""

import json
from typing import List, Dict

# =============================================================================
# SIMPLE PHI PROMPT FOR RANDOM LOCATION SELECTION
# =============================================================================

def build_phi_location_prompt(
    start_location: tuple,
    companion_type: str,
    start_time: int,
    budget_level: str,
    recommendations_json: List[Dict],  # This is List[Dict] from parsed Kakao API data
    location_name: str = "Seoul"
) -> str:
    """
    Build a simple prompt for Phi to randomly select 4-5 locations.
    
    Args:
        start_location (tuple): Starting coordinates (latitude, longitude)
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        start_time (int): Starting time in 24-hour format
        budget_level (str): Budget level (low, medium, high)
        recommendations_json (List[Dict]): List of 20 candidate places (parsed from Kakao API)
        location_name (str): Human-readable location name
        
    Returns:
        str: Simple prompt string for Phi
    """
    
    # Format the candidate places simply
    places_text = ""
    for i, place in enumerate(recommendations_json, 1):
        place_name = place.get('place_name', 'Unknown')
        place_type = place.get('place_type', 'Unknown')
        places_text += f"{i}. {place_name} ({place_type})\n"
    
    prompt = f"""<|system|>
You are a travel planning assistant helping to create itineraries for {companion_type.lower()} outings in {location_name}.
<|end|>

<|user|>
I need you to select exactly 4-5 places from the candidate list below for a {companion_type.lower()} outing.

Context:
- Location: {location_name}
- Companion Type: {companion_type}
- Budget: {budget_level}
- Start Time: {start_time}:00

Task:
Randomly select exactly 4-5 places from the candidates below. Ensure variety in place types.

Available Candidates:
{places_text}

Requirements:
- Select EXACTLY 4-5 places (no more, no less)
- Choose randomly from the list above
- Ensure variety across different place types
- Copy the exact place names

Output Format:
1. [Place Name] - [Brief reason for selection]
2. [Place Name] - [Brief reason for selection]
3. [Place Name] - [Brief reason for selection]
4. [Place Name] - [Brief reason for selection]
5. [Place Name] - [Brief reason for selection] (if selecting 5)

Remember: You must select exactly 4-5 places from the candidates above.
<|end|>

<|assistant|>
I'll help you select 4-5 places for your {companion_type.lower()} outing in {location_name}. Let me randomly choose from the candidates while ensuring variety:

"""

    return prompt

# =============================================================================
# SIMPLE QWEN PROMPT FOR ITINERARY GENERATION
# =============================================================================

def build_qwen_itinerary_prompt(
    companion_type: str, 
    budget_level: str, 
    start_time: int, 
    selected_places: List[Dict]
) -> str:
    """
    Build a simple prompt for Qwen to generate an itinerary covering all places.
    
    Args:
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        start_time (int): Starting time in 24-hour format
        selected_places (List[Dict]): List of selected places with metadata
        
    Returns:
        str: Simple prompt for Qwen
    """
    
    # Format places for the prompt
    places_text = ""
    for i, place in enumerate(selected_places, 1):
        place_name = place.get('place_name', 'Unknown')
        place_type = place.get('place_type', 'Unknown')
        places_text += f"{i}. {place_name} - {place_type}\n"
    
    prompt = f"""<|im_start|>system
You are a professional travel writer creating detailed itineraries for {companion_type.lower()} outings in Seoul.
<|im_end|>

<|im_start|>user
Create a comprehensive itinerary for a {companion_type.lower()} outing starting at {start_time}:00.

IMPORTANT: You MUST cover ALL {len(selected_places)} locations below. Do not stop until you have described every single place.

Context:
- Companion Type: {companion_type}
- Budget Level: {budget_level}
- Start Time: {start_time}:00
- Total Locations: {len(selected_places)}

Selected Locations:
{places_text}

Requirements:
- Cover ALL {len(selected_places)} locations completely
- Write 3-4 detailed sentences for each location
- Make it engaging and suitable for {companion_type.lower()} outings
- Consider the budget level: {budget_level}
- Only finish your story after covering ALL locations

Output Format:
1. [Place Name] - [Place Type]
   [3-4 detailed sentences about the experience, atmosphere, and activities]

2. [Place Name] - [Place Type]
   [3-4 detailed sentences about the experience, atmosphere, and activities]

Continue this format for all {len(selected_places)} locations. Do not stop early or truncate your response.
<|im_end|>

<|im_start|>assistant
I'll create a comprehensive itinerary for your {companion_type.lower()} outing in Seoul, covering all {len(selected_places)} locations:

"""
    
    return prompt
