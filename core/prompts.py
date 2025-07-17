from data.api_clients.kakao_api import search_places

# Contains prompt templates for various tasks in the Edge Day Planner application.



def build_phi_prompt(place_type: str, companion_type: str, budget: int, max_distance_km: float) -> str:
    place_list_json = search_places(place_type, 37.5665, 126.9780)  # Example coordinates (Seoul City Hall)
    return f"""
<|system|>
You are a local recommendation expert AI helping a user choose the best {place_type}.

Consider the following criteria:
- Companion type: {companion_type}
- Budget: {budget} KRW
- Maximum distance: {max_distance_km} km from starting point

Only recommend a place that:
- Matches the place type ({place_type})
- Is within budget and distance
- Feels suitable for the given companion type

<|end|>

<|user|>
Here is the list of candidate places in JSON:

{place_list_json}

Choose the best place and reply in this format only:
"[Place Name]"
<|end|>

<|assistant|>
""".strip()
