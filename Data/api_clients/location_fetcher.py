import requests
from secure.crypto_utils import get_kakao_map_api_key

# Calls Kakao Map API to search for starting location coordinates

def get_location_coordinates(location_name: str):
    """
    Given a location name (e.g., '홍대입구', '명동'), search Kakao Map API and let the user select from up to 8 results.
    @param location_name: Name of the location to search for.
    @return: Tuple of (latitude, longitude) if a location is selected, otherwise None.
    """
    # Fetch the API key
    # Note: The API key is encrypted and needs to be decrypted using the private key.
    api_key = get_kakao_map_api_key()
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": location_name, "size": 8}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    # Check if there are any results
    documents = data.get("documents", [])
    if not documents:
        print("검색 결과가 없습니다.")
        return None

    # Display the results and let the user choose one
    print("검색 결과를 선택하세요:")
    for idx, doc in enumerate(documents):
        name = doc.get("place_name", "")
        address = doc.get("address_name", "")
        print(f"{idx+1}. {name} ({address})")


    selected = input("번호를 입력하세요 (1~{}): ".format(len(documents)))
    try:
        sel_idx = int(selected) - 1
        if 0 <= sel_idx < len(documents):
            chosen = documents[sel_idx]
            lat = float(chosen["y"])
            lng = float(chosen["x"])
            return lat, lng
        else:
            print("잘못된 번호입니다.")
            return None
    except ValueError:
        print("잘못된 입력입니다.")
        return None

