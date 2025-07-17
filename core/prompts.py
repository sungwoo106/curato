import json
from constants import TONE_STYLE_MAP

# Contains prompt templates for various tasks in the Edge Day Planner application.



def build_phi_prompt(start_location: tuple, place_type: str, companion_type: str, start_time: int, max_distance_km: float, place_list_json: json) -> str:
    place_list = json.dumps(place_list_json, ensure_ascii=False, indent=2)
    return f"""
<|system|>
You are a local recommendation expert AI helping a user choose the best {place_type}.

Consider the following criteria:
- Starting location: {start_location} in latitude, longitude format
- Companion type: {companion_type}
- Starting time: Plan starts at {start_time} in Military Time format
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
  "documents": [
    {{
      "address_name": "...",
      "category_group_code": "...",
      "category_group_name": "...",
      "category_name": "...",
      "distance": "...",
      "id": "...",
      "phone": "...",
      "place_name": "...",
      "place_url": "...",
      "road_address_name": "...",
      "x": "...",
      "y": "..."
      // ...other fields from the input JSON
    }}
    // Only include the best place(s) you recommend
  ],
  "meta": {{
    // You may copy the meta field from the input, or set is_end: true, and pageable_count: 1, total_count: 1
    "is_end": true,
    "pageable_count": 1,
    "total_count": 1
  }}
}}
<|end|>

<|assistant|>
""".strip()


def build_phi_four_loc(start_location: tuple, companion_type: str, start_time: int, budget: int, recommendations_json: json)-> str:
    return f"""
<|system|>
You are an expert travel assistant AI. Your task is to select the best 4 locations from a list of recommended places grouped by place type. These locations come from the Kakao Map API and are intended to form a 1-day route optimized for user preferences.

Each place entry has these fields:
- place_name: name of the place
- address_name: full land address
- road_address_name: road address
- category_group_name: broad category (e.g., 카페)
- category_name: detailed category path
- distance: distance from the user's start location in meters (string)
- phone: optional contact info
- place_url: Kakao Maps URL
- x: longitude (string)
- y: latitude (string)

Instructions:
1. Select exactly 4 places from the list, each from a different category (place_type).
2. Choose places that are reasonably close to the starting location (low distance), diverse in experience, and well-distributed across place types.
3. Prioritize quality over brand repetition (e.g., avoid picking 3 Starbucks).
4. The 4 places should be optimal for the user's route and preferences.
5. Return only a JSON list of the 4 selected places in order of the route, each including:
   - place_name
   - road_address_name
   - place_type (manually inferred from category_group_name or category_name)
   - distance (as integer)
   - place_url
   - latitude (float from 'y')
   - longitude (float from 'x')

<|end|>

<|user|>
User Plan Settings:
- Start location: "{start_location}"
- Start time: "{start_time}"
- Total budget: {budget} (won)
- Companion type: "{companion_type}"

Data:
{recommendations_json}

Respond ONLY with a JSON array of 4 selected places. No explanations.
<|end|>

<|assistant|>
""".strip()

def build_llama_emotional_prompt(four_locations: list, companion_type: str) -> str:
    style = TONE_STYLE_MAP.get(companion_type, TONE_STYLE_MAP["혼자"])
    locs_text = "\n".join([f"{i+1}. {loc}" for i, loc in enumerate(four_locations)])

    user_message = f"""
You are a storytelling assistant that creates emotionally resonant day plans.

Write a heartfelt, immersive itinerary for the following 4 places:
{locs_text}

The user is spending the day with: {companion_type}
Tone: {style['tone']}

Instructions:
- Begin with a warm greeting or a sense of anticipation.
- For each location, describe the experience as if the user is already there.
- Use rich sensory language and emotional cues.
- End the day with a thoughtful or satisfying closing moment.

Style Guide:
{style['style_note']}

Output Format:
Write one continuous, beautiful paragraph per location (4 total), followed by a poetic closing.

Avoid using numbered steps or bullet points.
""".strip()

    return (
        "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
        + user_message
        + "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    )
