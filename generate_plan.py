"""
CLI Entry Point for WPF Frontend

This script serves as the command-line interface entry point for the WPF frontend.
It reads a JSON payload from the INPUT_JSON environment variable and uses the
existing Preferences workflow to generate an itinerary text. The logic mirrors
the interactive steps found in main.py but in a non-interactive form suitable
for launching from C#.

Key Features:
- Processes location queries and finds coordinates using Kakao Map API
- Generates personalized itineraries based on companion type, budget, and preferences
- Falls back to mock data for testing when real API calls fail
- Outputs results in JSON format for easy parsing by the C# frontend
"""

import json
import re
import sys, os
import io
from pathlib import Path

# =============================================================================
# PATH SETUP AND PYTHON PATH CONFIGURATION
# =============================================================================
# Add the project root to Python path so imports work when running from compiled output
# This is necessary because the script may be executed from different locations
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Go up one level from bin/Debug/net9.0-windows/

# Debug logging to help troubleshoot path issues
print(f"Script directory: {script_dir}", file=sys.stderr)
print(f"Project root: {project_root}", file=sys.stderr)
print(f"Project root exists: {project_root.exists()}", file=sys.stderr)
print(f"Data folder in project root: {(project_root / 'data').exists()}", file=sys.stderr)

# Strategy 1: Try to add project root to Python path if data folder exists there
if project_root.exists() and (project_root / "data").exists():
    sys.path.insert(0, str(project_root))
    print(f"Added {project_root} to Python path", file=sys.stderr)
elif (script_dir / "data").exists():
    # Strategy 2: If data folder is in the same directory as the script
    print("Data folder found in script directory", file=sys.stderr)
    pass
else:
    # Strategy 3: Try to find the project root by looking for data folder in parent directories
    current = script_dir
    while current.parent != current:  # Stop when we reach the root directory
        current = current.parent
        if (current / "data").exists():
            sys.path.insert(0, str(current))
            print(f"Found data folder in {current}, added to Python path", file=sys.stderr)
            break
    else:
        print("Could not find data folder in any parent directory", file=sys.stderr)

print(f"Python path: {sys.path[:3]}", file=sys.stderr)

# =============================================================================
# ENCODING SETUP
# =============================================================================
# Ensure proper UTF-8 encoding for Korean text output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =============================================================================
# IMPORTS (after path setup)
# =============================================================================
from constants import LOCATION, COMPANION_TYPES, BUDGET, STARTING_TIME
from data.api_clients.location_fetcher import get_location_coordinates
from preferences import Preferences

# =============================================================================
# MOCK DATA CONFIGURATION
# =============================================================================
# Mock directory for testing purposes - use pathlib for cross-platform compatibility
# Try to find mock directory in project root first, then fall back to script directory
_MOCK_DIR = None

# Look for the first path in sys.path that contains a 'data' folder (project root)
for path_str in sys.path:
    path = Path(path_str)
    if (path / "data").exists():
        project_mock_dir = path / "mock"
        if project_mock_dir.exists():
            _MOCK_DIR = project_mock_dir
            print(f"Using project root mock directory: {_MOCK_DIR}", file=sys.stderr)
            break
        else:
            print(f"Found project root {path} but no mock directory", file=sys.stderr)

# Fall back to script directory if no project mock directory found
if _MOCK_DIR is None:
    _MOCK_DIR = Path(__file__).parent / "mock"
    print(f"Using script directory mock: {_MOCK_DIR}", file=sys.stderr)

# Debug: Print resolved mock directory path for troubleshooting
print(f"Resolved mock directory: {_MOCK_DIR}", file=sys.stderr)
print(f"Mock directory exists: {_MOCK_DIR.exists()}", file=sys.stderr)
if _MOCK_DIR.exists():
    print(f"Mock directory contents: {list(_MOCK_DIR.glob('*.txt'))}", file=sys.stderr)

# =============================================================================
# MOCK DATA MAPPING
# =============================================================================
# Map of location slug to mock story filename
# Each location has a corresponding text file with sample itinerary content
MOCK_STORIES = {
    "hongdae": "mock_llama_hd_output.txt",    # Hongdae area mock data
    "seongsu": "mock_llama_ss_output.txt",    # Seongsu area mock data
    "gangnam": "mock_llama_gn_output.txt",    # Gangnam area mock data
    "itaewon": "mock_llama_it_output.txt",    # Itaewon area mock data
    "bukchon": "mock_llama_bc_output.txt",    # Bukchon area mock data
}

# Keywords to identify each location. Both English and Korean names are
# supported so that queries in either language will match.
MOCK_KEYWORDS = {
    "hongdae": ["hongdae", "홍대"],           # Hongdae keywords
    "seongsu": ["seongsu", "성수"],           # Seongsu keywords
    "gangnam": ["gangnam", "강남"],           # Gangnam keywords
    "itaewon": ["itaewon", "이태원"],         # Itaewon keywords
    "bukchon": ["bukchon", "북촌"],           # Bukchon keywords
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _format_sentences(text: str) -> str:
    """
    Format text by placing each sentence on a separate line.
    
    This function splits text on sentence-ending punctuation marks (.!?) and
    formats each sentence on its own line for better readability.
    
    Args:
        text (str): Input text to format
        
    Returns:
        str: Formatted text with one sentence per line
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return "\n".join(s.strip() for s in sentences if s.strip())


def _load_mock_story(query: str | None) -> str | None:
    """
    Load and return a formatted mock story for the specified location.
    
    This function searches for mock data files based on location keywords
    and returns the content formatted for display. If no match is found,
    it falls back to the Hongdae mock story as a default.
    
    Args:
        query (str | None): Location query string to search for
        
    Returns:
        str | None: Formatted mock story text or error message
    """
    # Check if mock directory exists
    if not _MOCK_DIR.exists():
        error_msg = f"Mock directory does not exist: {_MOCK_DIR}"
        print(error_msg, file=sys.stderr)
        return f"Failed to load mock story: {error_msg}"

    # Fallback to the Hongdae mock story if no match is found
    path = _MOCK_DIR / MOCK_STORIES["hongdae"]

    # Try to match the query against location keywords
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
        # Read and format the mock story file
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return _format_sentences(text)
    except Exception as exc:  # pragma: no cover - unlikely path
        error_msg = f"Failed to load mock story: {exc}"
        print(error_msg, file=sys.stderr)
        return error_msg

# =============================================================================
# MAIN WORKFLOW FUNCTION
# =============================================================================
# The previous implementation only produced a placeholder summary. Here we
# replicate the workflow of "main.py" to call into the real backend logic.

def main() -> None:
    """
    Main entry point used by the C# UI.
    
    This function:
    1. Parses input JSON from environment variables
    2. Checks for mock data matches first
    3. Falls back to real API calls for location coordinates
    4. Generates personalized itineraries using the Preferences workflow
    5. Outputs results in JSON format for the frontend
    """
    # Parse input JSON from the environment. Missing fields fall back to the
    # same defaults used throughout the Python CLI.
    data = json.loads(os.getenv("INPUT_JSON", "{}"))

    # Extract user preferences with sensible defaults
    companion_type = data.get("companion_type", COMPANION_TYPES[0])  # Default: Solo
    budget = data.get("budget", BUDGET[0])                          # Default: low
    starting_time = data.get("starting_time", STARTING_TIME)         # Default: 12 (noon)
    location_query = data.get("location_query")                     # Optional location search
    categories = data.get("categories", [])                         # Optional place type categories

    # =============================================================================
    # MOCK DATA CHECK
    # =============================================================================
    # Check if the query matches one of our mock stories
    # This provides immediate responses for testing without API calls
    mock = _load_mock_story(location_query)
    if mock is not None:
        print(json.dumps({"itinerary": mock}, ensure_ascii=False))
        return

    # =============================================================================
    # LOCATION COORDINATE RESOLUTION
    # =============================================================================
    # Determine the coordinates for the starting location using the Kakao Map
    # API. If the lookup fails or no query is provided, fall back to the default
    # location from "constants.py".
    start_location = LOCATION  # Default location (Hongdae area)
    if location_query:
        try:
            loc = get_location_coordinates(location_query)
            if loc:
                start_location = loc
        except Exception:
            # If location lookup fails, continue with default location
            pass

    # =============================================================================
    # ITINERARY GENERATION
    # =============================================================================
    # Build the Preferences instance and invoke the main workflow.
    # This creates a personalized planner based on user preferences
    planner = Preferences(
        companion_type=companion_type,
        budget=budget,
        starting_time=starting_time,
        start_location=start_location,
    )
    
    # Select appropriate place types based on companion type and user preferences
    planner.select_place_types(categories)

    # Generate the emotional itinerary text using the Llama model. In case the
    # backend fails (e.g. missing models), return a helpful message.
    try:
        itinerary = planner.run_llama_story()
    except Exception as exc:  # Broad catch so the frontend always gets a reply
        itinerary = f"Backend failure: {exc}"

    # Output the result in JSON format for easy parsing by the C# frontend
    print(json.dumps({"itinerary": itinerary}, ensure_ascii=False))


# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
if __name__ == "__main__":
    main()
