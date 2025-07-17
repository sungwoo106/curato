from data.api_clients.kakao_api import search_places
import json

# Contains prompt templates for various tasks in the Edge Day Planner application.



def build_phi_prompt(location: tuple, place_type: str, companion_type: str, budget: int, starting_time: int, max_distance_km: float, place_list_json: json) -> str:
    place_list = json.dumps(place_list_json, ensure_ascii=False, indent=2)
    return f"""
<|system|>
You are a local recommendation expert AI helping a user choose the best {place_type}.

Consider the following criteria:
- Starting location: {location} in latitude, longitude format
- Companion type: {companion_type}
- Budget: {budget} KRW
- Starting time: Plan starts at {starting_time} in Military Time format
- Maximum distance: {max_distance_km} km from starting point

Only recommend a place that:
- Matches the place type ({place_type})
- Is within budget and distance
- Feels suitable for the given companion type

<|end|>

<|user|>
Here is the list of candidate places in JSON:

{place_list}

Choose the best place and reply in this format only:
{{
  "place": {{
    "place_name": "...",
    "address_name": "...",
    "road_address_name": "...",
    "x": "...",  // longitude
    "y": "...",  // latitude
    "category_name": "...",
    "phone": "..."
    // ...other fields from the input JSON
  }}
}}
<|end|>

<|assistant|>
""".strip()
