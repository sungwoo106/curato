"""
AI Prompt Templates and Generation

This module contains the prompt templates used to generate AI-powered itineraries.
It provides structured prompts for both the Phi model (route planning) and the
Qwen model (emotional storytelling) to ensure consistent and high-quality output.

The prompts are designed to:
- Generate optimal 4-location routes based on user preferences
- Create emotional, narrative itineraries that match companion types
- Incorporate budget-specific activity suggestions
- Maintain consistent tone and style across different companion types
"""

import json
import random
from constants import TONE_STYLE_MAP, LOW_BUDGET, MEDIUM_BUDGET, HIGH_BUDGET

# =============================================================================
# PHI MODEL PROMPT FOR ROUTE PLANNING
# =============================================================================

def build_phi_four_loc(
    start_location: tuple,
    companion_type: str,
    start_time: int,
    budget_level: str,
    recommendations_json: json,
) -> str:
    """
    Build a prompt for the Phi model to select 4 optimal locations for a one-day route.
    
    This prompt instructs the Phi model to:
    - Choose exactly 4 locations from different place types
    - Ensure locations are near the starting point
    - Match the companion type and budget preferences
    - Avoid repeated brands for variety
    - Return structured JSON with specific fields
    
    Args:
        start_location (tuple): Starting coordinates (latitude, longitude)
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        start_time (int): Starting time in 24-hour format
        budget_level (str): Budget level (low, medium, high)
        recommendations_json (json): Formatted place recommendations from Kakao API
        
    Returns:
        str: Complete prompt string for the Phi model
    """
    return f"""
<|system|>
Choose 4 locations for a one-day route. Each must be from a different place type, near {start_location}, and suit a {companion_type} outing starting at {start_time}h with a {budget_level} budget. Avoid repeated brands and pick quality spots.
Return a JSON list (in order) with these fields: place_name, road_address_name, place_type, distance, place_url, latitude, longitude.
<|end|>

<|user|>
{recommendations_json}

<|end|>

<|assistant|>
""".strip()

# =============================================================================
# QWEN MODEL PROMPT FOR EMOTIONAL STORYTELLING
# =============================================================================

def build_qwen_emotional_prompt(
    four_locations: list,
    companion_type: str,
    budget_level: str,
) -> str:
    """
    Build a prompt for the Qwen model to generate emotional, narrative itineraries.
    
    This prompt instructs the Qwen model to:
    - Create a storytelling experience based on 4 locations
    - Match the emotional tone for the companion type
    - Include budget-appropriate activity suggestions
    - Use rich sensory language and poetic elements
    - Avoid bullet points in favor of narrative flow
    
    Args:
        four_locations (list): List of 4 locations from the route planner
        companion_type (str): Type of outing (Solo, Couple, Friends, Family)
        budget_level (str): Budget level (low, medium, high)
        
    Returns:
        str: Complete prompt string for the Qwen model
    """
    # Get the tone and style guide for the companion type
    # This ensures the generated content matches the expected emotional experience
    style = TONE_STYLE_MAP.get(companion_type.lower(), TONE_STYLE_MAP["solo"])
    
    # Format the locations as a numbered list for the prompt
    locs_text = "\n".join([f"{i+1}. {loc}" for i, loc in enumerate(four_locations)])

    # Select budget-appropriate activity suggestions
    # These provide concrete ideas that fit within the specified budget
    money_activities = {
        "low": LOW_BUDGET,      # Free or very inexpensive activities
        "medium": MEDIUM_BUDGET, # Moderate cost activities
        "high": HIGH_BUDGET,     # Premium and luxury activities
    }

    # Randomly select 2 activities from the appropriate budget level
    # This adds variety while maintaining budget consistency
    selected_activities = random.sample(money_activities[budget_level], k=2)

    # Build the user message with all the context needed for storytelling
    user_message = f"""
You are a storytelling assistant. Describe an emotional itinerary for these places:
{locs_text}

Companion: {companion_type}
Tone: {style['tone']}
Include 1-2 paid activities like: {selected_activities}
Use rich sensory language and finish with a poetic closing. No bullet points.
Style guide: {style['style_note']}
""".strip()

    # Return the complete prompt with proper formatting for the Qwen model
    # The format includes special tokens for the model to understand the conversation structure
    return (
        "<|im_start|>system\nYou are a helpful AI Assistant specializing in creating emotional, engaging stories and itineraries. You excel at crafting narratives that evoke feelings and create memorable experiences.\n<|im_end|>\n<|im_start|>user\n{user_message}\n<|im_end|>\n<|im_start|>assistant"
    )
