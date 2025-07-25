import json
import re
import sys, os
# Get the root directory of the entire project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)


"""CLI entry for the WPF frontend.

This script reads a JSON payload from the ``INPUT_JSON`` environment variable
and uses the existing ``Preferences`` workflow to generate an itinerary text.
The logic mirrors the interactive steps found in ``main.py`` but in a non-
interactive form suitable for launching from C#.
"""

from constants import LOCATION, COMPANION_TYPES, BUDGET, STARTING_TIME
from data.api_clients.location_fetcher import get_location_coordinates
from preferences import Preferences

_MOCK_DIR = os.path.join(os.path.dirname(__file__), "mock")

# Map of location slug to mock story filename
MOCK_STORIES = {
    "hongdae": "mock_llama_hd_output.txt",
    "seongsu": "mock_llama_ss_output.txt",
    "gangnam": "mock_llama_gn_output.txt",
    "itaewon": "mock_llama_it_output.txt",
    "bukchon": "mock_llama_bc_output.txt",
}

# Keywords to identify each location.  Both English and Korean names are
# supported so that queries in either language will match.
MOCK_KEYWORDS = {
    "hongdae": ["hongdae", "홍대"],
    "seongsu": ["seongsu", "성수"],
    "gangnam": ["gangnam", "강남"],
    "itaewon": ["itaewon", "이태원"],
    "bukchon": ["bukchon", "북촌"],
}


def _format_sentences(text: str) -> str:
    """Return the text with one sentence per line."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return "\n".join(s.strip() for s in sentences if s.strip())


def _load_mock_story(query: str | None) -> str | None:
    """Return the formatted mock story if the query matches a known location."""
    if not query:
        return None

    lower = query.lower()
    for key, keywords in MOCK_KEYWORDS.items():
        if any(k.lower() in lower for k in keywords):
            path = os.path.join(_MOCK_DIR, MOCK_STORIES[key])
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                return _format_sentences(text)
            except Exception as exc:  # pragma: no cover - unlikely path
                return f"Failed to load mock story: {exc}"
    return None

# The previous implementation only produced a placeholder summary.  Here we
# replicate the workflow of "main.py" to call into the real backend logic.

def main() -> None:
    try:
        """Entry point used by the C# UI."""

        # Log the start of the script and the input JSON for debugging purposes.
        try:
            with open("debug_log.txt", "a", encoding="utf-8") as log:
                log.write("STARTING SCRIPT\\n")
                log.write(f"INPUT_JSON = {os.getenv('INPUT_JSON')}\\n")
        except Exception as e:
            print(json.dumps({"itinerary": f"Logging error: {e}"}))

        # Parse input JSON from the environment.  Missing fields fall back to the
        # same defaults used throughout the Python CLI.
        data = json.loads(os.getenv("INPUT_JSON", "{}"))

        companion_type = data.get("companion_type", COMPANION_TYPES[0])
        budget = data.get("budget", BUDGET[0])
        starting_time = data.get("starting_time", STARTING_TIME)
        location_query = data.get("location_query")
        categories = data.get("categories", [])

        # Check if the query matches one of our mock stories
        mock = _load_mock_story(location_query)
        if mock is not None:
            print(json.dumps({"itinerary": mock}, ensure_ascii=False))
            return

        # Determine the coordinates for the starting location using the Kakao Map
        # API. If the lookup fails or no query is provided, fall back to the default
        # location from "constants.py".
        start_location = LOCATION
        if location_query:
            try:
                loc = get_location_coordinates(location_query)
                if loc:
                    start_location = loc
            except Exception:
                pass

        # Build the Preferences instance and invoke the main workflow.
        planner = Preferences(
            companion_type=companion_type,
            budget=budget,
            starting_time=starting_time,
            start_location=start_location,
        )
        planner.select_place_types(categories)

        # Generate the emotional itinerary text using the Llama model.  In case the
        # backend fails (e.g. missing models), return a helpful message.
        try:
            itinerary = planner.run_llama_story()
        except Exception as exc:  # Broad catch so the frontend always gets a reply
            itinerary = f"Backend failure: {exc}"

        print(json.dumps({"itinerary": itinerary}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"itinerary": f"Script failed: {e}"}))


if __name__ == "__main__":
    main()
