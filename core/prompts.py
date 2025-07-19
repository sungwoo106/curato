import json
import random
from constants import TONE_STYLE_MAP, LOW_BUDGET, MEDIUM_BUDGET, HIGH_BUDGET

# Contains prompt templates for various tasks in the Edge Day Planner application.

def build_phi_four_loc(
    start_location: tuple,
    companion_type: str,
    start_time: int,
    budget_level: str,
    recommendations_json: json,
) -> str:
    """    Builds a prompt for the Phi model to select 4 locations based on user preferences.    """
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

def build_llama_emotional_prompt(
    four_locations: list,
    companion_type: str,
    budget_level: str,
) -> str:
    style = TONE_STYLE_MAP.get(companion_type, TONE_STYLE_MAP["solo"])
    locs_text = "\n".join([f"{i+1}. {loc}" for i, loc in enumerate(four_locations)])

    money_activities = {
        "low": LOW_BUDGET,
        "medium": MEDIUM_BUDGET,
        "high": HIGH_BUDGET,
    }

    selected_activities = random.sample(money_activities[budget_level], k=2)

    user_message = f"""
You are a storytelling assistant. Describe an emotional itinerary for these places:
{locs_text}

Companion: {companion_type}
Tone: {style['tone']}
Include 1-2 paid activities like: {selected_activities}
Use rich sensory language and finish with a poetic closing. No bullet points.
Style guide: {style['style_note']}
""".strip()

    return (
        "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
        + user_message
        + "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )
