import sys
import json
from data.api_clients.kakao_api import search_places


def main():
    if len(sys.argv) < 4:
        print("[]")
        return
    query = sys.argv[1]
    lat = float(sys.argv[2])
    lng = float(sys.argv[3])
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    try:
        data = search_places(query, lat, lng, size=size)
        docs = data.get("documents", [])
        out = [
            {
                "name": d.get("place_name", ""),
                "lat": float(d.get("y", 0)),
                "lng": float(d.get("x", 0)),
            }
            for d in docs
        ]
        print(json.dumps(out, ensure_ascii=False))
    except Exception:
        print("[]")


if __name__ == "__main__":
    main()