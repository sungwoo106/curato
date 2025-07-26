import sys
import json
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

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

        # debugging
        with open("popup_python_log.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(suggestions, ensure_ascii=False))

        print(json.dumps(suggestions, ensure_ascii=False))
    except Exception as e:
        print(json.dumps([]))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps([]))
    else:
        suggest_locations(sys.argv[1])
