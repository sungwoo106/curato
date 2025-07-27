import json
import os
import sys
from typing import Any, Dict, List

# Ensure the repository root is on the Python path so imports work when run as a
# script.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
sys.path.insert(0, REPO_ROOT)

from data.api_clients.kakao_api import get_closest_place
from data.api_clients.location_fetcher import get_location_coordinates
from preferences import Preferences
from constants import LOCATION


LOCATION_QUERY = "홍대입구"  # Default location for fetching places
# Fallback coordinates around Hongdae Station entrance 2
LAT = 37.5563
LNG = 126.9237

CATEGORIES = ["Restaurant", "Cafe"]

MOCK_DATA: Dict[str, List[Dict[str, Any]]] = {
    "Restaurant": [
        {
            "place_name": "연남동 맛있는식당",
            "address_name": "서울특별시 마포구 연남동 123-4",
            "road_address_name": "서울특별시 마포구 연남로5길 20",
            "distance": "150",
            "place_url": "https://place.map.kakao.com/987654321",
            "x": str(LNG + 0.002),
            "y": str(LAT + 0.002),
        },
        {
            "place_name": "홍대밥집",
            "address_name": "서울특별시 마포구 서교동 456-7",
            "road_address_name": "서울특별시 마포구 와우산로21길 15",
            "distance": "300",
            "place_url": "https://place.map.kakao.com/987654322",
            "x": str(LNG + 0.003),
            "y": str(LAT + 0.003),
        },
    ],
    "Cafe": [
        {
            "place_name": "홍대 예쁜 카페",
            "address_name": "서울특별시 마포구 서교동 789-1",
            "road_address_name": "서울특별시 마포구 홍익로5길 10",
            "distance": "100",
            "place_url": "https://place.map.kakao.com/987654323",
            "x": str(LNG + 0.001),
            "y": str(LAT + 0.001),
        },
        {
            "place_name": "감성 카페",
            "address_name": "서울특별시 마포구 합정동 12-34",
            "road_address_name": "서울특별시 마포구 독막로7길 30",
            "distance": "250",
            "place_url": "https://place.map.kakao.com/987654324",
            "x": str(LNG + 0.002),
            "y": str(LAT + 0.002),
        },
    ],
}

def fetch_and_save(path: str = "mock_kakao_output.json") -> None:
    """Fetch data from Kakao API and save to a JSON file.

    This follows the same steps as the main application with preset inputs. If
    any API call fails, predefined mock results are used instead.
    """
    # Determine coordinates for the desired location
    try:
        start_location = get_location_coordinates(LOCATION_QUERY)
        if not start_location:
            start_location = LOCATION
    except Exception as exc:  # pragma: no cover - network/credential failure
        print(f"Location fetch failed: {exc}. Using default coordinates.")
        start_location = LOCATION

    prefs = Preferences(companion_type="Couple", start_location=start_location)
    prefs.select_place_types(CATEGORIES)

    results: Dict[str, Any] = {}
    for category in prefs.selected_types:
        try:
            place = get_closest_place(
                category,
                prefs.start_location[0],
                prefs.start_location[1],
                int(prefs.max_distance_km * 1000),
                10,
            )
            results[category] = [place] if place else []
        except Exception as exc:  # pragma: no cover - network/credential failure
            print(f"API call for {category} failed: {exc}. Using mock data.")
            results[category] = MOCK_DATA.get(category, [])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved response to {path}")


if __name__ == "__main__":
    fetch_and_save()
