import requests
from secure.crypto_utils import get_kakao_map_api_key

# Calls Kakao Map API to search for starting location coordinates

def get_location_coordinates(location_name: str):
    """
    Given a location name (e.g., '홍대입구', '명동'), return its latitude and longitude using Kakao Map API.
    @param location_name: Name of the location to search for.
    @return: Tuple of (latitude, longitude) if found, otherwise None.
    """
    api_key = get_kakao_map_api_key()

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": location_name, "size": 1}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status() # Raise an error for bad responses
    data = response.json()
    documents = data.get("documents", [])
    if documents:
        first = documents[0]
        lat = float(first["y"])
        lng = float(first["x"])
        return lat, lng
    return None # If no results found, return None

