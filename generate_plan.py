import json
import re
import sys, os
import io
from pathlib import Path

# Add the project root to Python path so imports work when running from compiled output
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Go up one level from bin/Debug/net9.0-windows/

print(f"Script directory: {script_dir}", file=sys.stderr)
print(f"Project root: {project_root}", file=sys.stderr)
print(f"Project root exists: {project_root.exists()}", file=sys.stderr)
print(f"Data folder in project root: {(project_root / 'data').exists()}", file=sys.stderr)

if project_root.exists() and (project_root / "data").exists():
    sys.path.insert(0, str(project_root))
    print(f"Added {project_root} to Python path", file=sys.stderr)
elif (script_dir / "data").exists():
    # If data folder is in the same directory as the script
    print("Data folder found in script directory", file=sys.stderr)
    pass
else:
    # Try to find the project root by looking for data folder
    current = script_dir
    while current.parent != current:
        current = current.parent
        if (current / "data").exists():
            sys.path.insert(0, str(current))
            print(f"Found data folder in {current}, added to Python path", file=sys.stderr)
            break
    else:
        print("Could not find data folder in any parent directory", file=sys.stderr)

print(f"Python path: {sys.path[:3]}", file=sys.stderr)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""CLI entry for the WPF frontend.

This script reads a JSON payload from the ``INPUT_JSON`` environment variable
and uses the existing ``Preferences`` workflow to generate an itinerary text.
The logic mirrors the interactive steps found in ``main.py`` but in a non-
interactive form suitable for launching from C#.
"""

from constants import LOCATION, COMPANION_TYPES, BUDGET, STARTING_TIME
from data.api_clients.location_fetcher import get_location_coordinates
from preferences import Preferences

# Mock directory for testing purposes - use pathlib for cross-platform compatibility
_MOCK_DIR = Path(__file__).parent / "mock"

# Debug: Print resolved mock directory path for troubleshooting
print(f"Resolved mock directory: {_MOCK_DIR}", file=sys.stderr)
print(f"Mock directory exists: {_MOCK_DIR.exists()}", file=sys.stderr)
if _MOCK_DIR.exists():
    print(f"Mock directory contents: {list(_MOCK_DIR.glob('*.txt'))}", file=sys.stderr)

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
    """Return a formatted mock story for the location or a default one."""

    # Check if mock directory exists
    if not _MOCK_DIR.exists():
        error_msg = f"Mock directory does not exist: {_MOCK_DIR}"
        print(error_msg, file=sys.stderr)
        return f"Failed to load mock story: {error_msg}"

    # Fallback to the Hongdae mock story if no match is found.
    path = _MOCK_DIR / MOCK_STORIES["hongdae"]

    if query:
        lower = query.lower()
        for key, keywords in MOCK_KEYWORDS.items():
            if any(k.lower() in lower for k in keywords):
                path = _MOCK_DIR / MOCK_STORIES[key]
                break

    # Check if the specific file exists
    if not path.exists():
        error_msg = f"Mock story file does not exist: {path}"
        print(error_msg, file=sys.stderr)
        return f"Failed to load mock story: {error_msg}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return _format_sentences(text)
    except Exception as exc:  # pragma: no cover - unlikely path
        error_msg = f"Failed to load mock story: {exc}"
        print(error_msg, file=sys.stderr)
        return error_msg

# The previous implementation only produced a placeholder summary.  Here we
# replicate the workflow of "main.py" to call into the real backend logic.

def main() -> None:
    """Entry point used by the C# UI."""

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


if __name__ == "__main__":
    main()
