import requests
from typing import Dict, List
from secure.crypto_utils import get_kakao_map_api_key

# Calls Kakao Map API

def search_places(query: str, loc: tuple, radius: int = 1000, size: int = 10):
    """
    Searches for places using the Kakao Map API.
    @param query: Search query string.
    @param lat: Latitude of the location to search around.
    @param lng: Longitude of the location to search around.
    @param radius: Search radius in meters (default is 1000).
    @param size: Number of results to return (default is 10).
    @return: JSON response from the Kakao Map API containing search results.
    """

    api_key = get_kakao_map_api_key()

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    params = {
        "query": query,
        "x": str(loc[0]),  # Longitude
        "y": str(loc[1]),  # Latitude
        "radius": radius,
        "size": size,
        "sort": "distance"  # Sort by distance
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


def format_kakao_places_for_prompt(kakao_results: Dict[str, List[Dict]]) -> List[Dict]:
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