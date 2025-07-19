import requests
from typing import Dict, List, Optional
from secure.crypto_utils import get_kakao_map_api_key

# Calls Kakao Map API

def search_places(query: str, lat: float, lng: float, radius: int = 1000, size: int = 10):
    """
    Searches for places using the Kakao Map API.
    @param query: Search keyword (e.g., "카페").
    @param lat: Latitude of the center point.
    @param lng: Longitude of the center point.
    @param radius: Search radius in meters (default is 1000).
    @param size: Number of results to return (default is 10).
    @return: JSON response from the Kakao Map API containing place information.
    """

    api_key = get_kakao_map_api_key()

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    params = {
        "query": query,
        "x": str(lng),  # Longitude
        "y": str(lat),  # Latitude
        "radius": radius,
        "size": size,
        "sort": "distance"  # Sort by distance
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def get_closest_place(query: str, lat: float, lng: float, radius: int = 1000, size: int = 10) -> Optional[Dict]:
    """
    Return the closest place result for the given query.
    @param query: Search keyword (e.g., "카페").
    @param lat: Latitude of the center point.
    @param lng: Longitude of the center point.
    @param radius: Search radius in meters (default is 1000).
    @param size: Number of results to return (default is 10).
    @return: The closest place as a dictionary, or None if no results found.
    """
    data = search_places(query, lat, lng, radius, size)
    documents = data.get("documents", [])
    if not documents:
        return None
    return min(documents, key=lambda d: int(d.get("distance", "999999")))


def format_kakao_places_for_prompt(kakao_results: Dict[str, List[Dict]]) -> List[Dict]:
    '''
    Formats the Kakao Map API results into a list of dictionaries suitable for the prompt.
    @param kakao_results: Dictionary where keys are place types and values are lists of places
    @return: List of formatted places with necessary fields.
    '''
    formatted = []

    for place_type, places in kakao_results.items():
        for place in places:
            try:
                formatted.append({
                    "place_name": place.get("place_name", ""),
                    "road_address_name": place.get("road_address_name") or place.get("address_name", ""),
                    "place_type": place_type,
                    "distance": int(place.get("distance", "99999")),
                    "place_url": place.get("place_url", ""),
                    "latitude": float(place.get("y", "0")),
                    "longitude": float(place.get("x", "0")),
                })
            except Exception as e:
                continue

    return formatted