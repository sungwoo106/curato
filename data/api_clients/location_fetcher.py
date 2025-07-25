import requests
from secure.crypto_utils import get_kakao_map_api_key

# Calls Kakao Map API to search for starting location coordinates

def get_location_coordinates(location_name: str):
    """Return coordinates for the first Kakao Map search result.

    The old implementation prompted the user to select from search results.
    For automated scripts like "main.py" we instead simply return the
    coordinates of the first result. "None" is returned if the query yields
    no results or if the request fails.

    @param location_name: Name of the location to search for.
    @return Tuple (latitude, longitude) or "None" on failure.
    """
    # Fetch the API key
    # Note: The API key is encrypted and needs to be decrypted using the private key.
    api_key = get_kakao_map_api_key()
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": location_name, "size": 1}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])
        if not documents:
            return None
        first = documents[0]
        return float(first["y"]), float(first["x"])
    except Exception:
        # On any failure return None so callers can fall back to defaults
        return None

