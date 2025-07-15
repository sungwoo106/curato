from .kakao_api import search_places

# Example coordinates (Seoul City Hall)
lat = 37.5665
lng = 126.9780
query = "카페"  # Example search for 'cafe'

try:
    result = search_places(query, lat, lng)
    print(result)
except Exception as e:
    print("API call failed:", e)