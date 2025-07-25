import sys
import json
from data.api_clients.kakao_api import autocomplete_location

def suggest_locations(query):
    try:
        results = autocomplete_location(query)
        suggestions = []

        for place in results.get("documents", []):
            name = place.get("place_name")
            x = place.get("x")
            y = place.get("y")
            if name and x and y:
                suggestions.append({
                    "name": name,
                    "longitude": float(x),
                    "latitude": float(y)
                })

        print(json.dumps(suggestions, ensure_ascii=False))
    except Exception as e:
        print(json.dumps([]))
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps([]))
    else:
        suggest_locations(sys.argv[1])
