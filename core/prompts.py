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
    
    # Format the candidate places in RANDOM order to ensure Phi doesn't just pick the first few
    import random
    
    # Create a shuffled copy of the recommendations to randomize the order Phi sees
    shuffled_recommendations = recommendations_json.copy()
    random.shuffle(shuffled_recommendations)
    
    places_text = ""
    for i, place in enumerate(shuffled_recommendations, 1):
        place_name = place.get('place_name', 'Unknown')
        place_type = place.get('place_type', 'Unknown')
        places_text += f"{i}. {place_name} ({place_type})\n"
    
    prompt = f"""<|system|>
You are a travel planner. Select exactly 4-5 places from the list below. Do not repeat places.
<|end|>

<|user|>
Select exactly 4-5 places from this list for a {companion_type.lower()} outing:

{places_text}

Rules:
- Pick exactly 4-5 places (no more, no less)
- IMPORTANT: Choose places from DIFFERENT positions in the list (not just the first few)
- Mix selections from early, middle, and late positions for variety
- Do not repeat any place
- Use this format: 1. [Place Name] - [Brief reason]

<|end|>

<|assistant|>
I'll select 4-5 places for your {companion_type.lower()} outing:

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
You are a professional travel writer specializing in personalized itineraries. Create engaging, tailored content that reflects the user's preferences and creates memorable experiences.
<|im_end|>

<|im_start|>user
Create a detailed itinerary for a {companion_type.lower()} outing in Seoul starting at {start_time}:00.

Cover these {len(selected_places)} locations:
{places_text}

Write 3-4 engaging sentences for each place, suitable for {companion_type.lower()} outings with {budget_level} budget.
<|im_end|>

<|im_start|>assistant
I'll create a detailed itinerary for your {companion_type.lower()} outing in Seoul, covering all {len(selected_places)} locations:
"""
    
    return prompt
