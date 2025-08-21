"""
CLI Entry Point for WPF Frontend

This script serves as the command-line interface entry point for the WPF frontend.
It reads a JSON payload from the INPUT_JSON environment variable and uses the
existing Preferences workflow to generate an itinerary text.

Key Features:
- Processes location queries and finds coordinates using Kakao Map API
- Generates personalized itineraries based on companion type, budget, and preferences
- Uses real AI models (Phi for random place selection, Qwen for comprehensive storytelling)
- Outputs results in JSON format for easy parsing by the C# frontend
- Supports streaming progress updates for real-time UI feedback

Simplified Algorithm:
- Collects 10-15 places from each place type within walking distance
- Reduces to 20 candidates ensuring variety of place types
- Phi randomly selects 4-5 places from the candidates
- Qwen creates comprehensive itinerary covering all selected places
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
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Go up one level from bin/Debug/net9.0-windows/

# Strategy 1: Try to add project root to Python path if data folder exists there
if project_root.exists() and (project_root / "data").exists():
    sys.path.insert(0, str(project_root))
elif (script_dir / "data").exists():
    # Strategy 2: If data folder is in the same directory as the script
    pass
else:
    # Strategy 3: Try to find the project root by looking for data folder in parent directories
    current = script_dir
    while current.parent != current:  # Stop when we reach the root directory
        current = current.parent
        if (current / "data").exists():
            sys.path.insert(0, str(current))
            break

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
# PROGRESS STREAMING FUNCTIONS
# =============================================================================

def send_progress_update(progress: int, message: str):
    """Send a progress update to the C# frontend."""
    progress_data = {
        "type": "progress",
        "progress": progress,
        "message": message
    }
    print(json.dumps(progress_data, ensure_ascii=False), flush=True)

def send_phi_completion(route_plan_json: str):
    """Send Phi completion signal to show output page immediately."""
    completion_data = {
        "type": "phi_completion",
        "route_plan": route_plan_json
    }
    print(json.dumps(completion_data, ensure_ascii=False), flush=True)

def send_streaming_token(token: str, is_final: bool = False):
    """Send a streaming token to the C# frontend for real-time display."""
    token_data = {
        "type": "streaming_token",
        "token": token,
        "is_final": is_final
    }
    print(json.dumps(token_data, ensure_ascii=False), flush=True)

def send_completion_update(route_plan_json: str, emotional_itinerary: str):
    """Send the final completion result to the C# frontend."""
    completion_data = {
        "type": "completion",
        "route_plan": route_plan_json,
        "itinerary": emotional_itinerary
    }
    print(json.dumps(completion_data, ensure_ascii=False), flush=True)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _format_sentences(text: str) -> str:
    """
    Format text by placing each sentence on a separate line.
    
    Args:
        text (str): Input text to format
        
    Returns:
        str: Formatted text with each sentence on a separate line
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return "\n".join(s.strip() for s in sentences if s.strip())

# =============================================================================
# MAIN WORKFLOW FUNCTION
# =============================================================================

def main() -> None:
    """
    Main entry point used by the C# UI.
    
    This function:
    1. Parses input JSON from environment variables
    2. Resolves location coordinates using Kakao Map API
    3. Generates personalized itineraries using AI models (Phi + Qwen)
    4. Outputs results in JSON format for the frontend
    5. Provides real-time progress updates during generation
    """
    try:
        # Send initial progress
        send_progress_update(5, "Initializing trip planner...")
        
        # Parse input JSON from the environment. Missing fields fall back to defaults.
        data = json.loads(os.getenv("INPUT_JSON", "{}"))

        # Extract user preferences with sensible defaults
        companion_type = data.get("companion_type", COMPANION_TYPES[0])  # Default: Solo
        budget = data.get("budget", BUDGET[0])                          # Default: low
        starting_time = data.get("starting_time", STARTING_TIME)         # Default: 12 (noon)
        location_query = data.get("location_query")                     # Optional location search
        categories = data.get("categories", [])                         # Optional place type categories

        send_progress_update(15, "Processing user preferences...")

        # =============================================================================
        # LOCATION COORDINATE RESOLUTION
        # =============================================================================
        # Determine the coordinates for the starting location using the Kakao Map API
        start_location = LOCATION  # Default location (Hongdae area)
        if location_query:
            try:
                send_progress_update(25, f"Resolving location: {location_query}...")
                loc = get_location_coordinates(location_query)
                if loc:
                    start_location = loc
                    print(f"Resolved location '{location_query}' to coordinates: {loc}", file=sys.stderr)
                    send_progress_update(35, f"Location resolved: {location_query}")
                else:
                    print(f"Location lookup returned no results for '{location_query}'", file=sys.stderr)
                    send_progress_update(35, "Using default location")
            except Exception as e:
                print(f"Location lookup failed for '{location_query}': {e}", file=sys.stderr)
                send_progress_update(35, "Using default location")
        else:
            send_progress_update(35, "Using default location")

        # =============================================================================
        # AI-POWERED ITINERARY GENERATION
        # =============================================================================
        route_plan_json = None  # Initialize route plan variable

        try:
            # Build the Preferences instance and invoke the main workflow
            send_progress_update(45, "Building personalized planner...")
            
            # Determine the location name to use in prompts
            location_name = location_query if location_query else "Seoul"
            
            planner = Preferences(
                companion_type=companion_type,
                budget=budget,
                starting_time=starting_time,
                start_location=start_location,
                location_name=location_name,
            )
            
            # Select appropriate place types based on companion type and user preferences
            planner.select_place_types(categories)
            send_progress_update(55, "Selecting place types...")

            # Generate the route plan using Phi model
            send_progress_update(65, "Collecting place candidates and generating route plan...")
            route_plan_json = planner.run_route_planner()
            
            if route_plan_json:
                send_progress_update(75, "Route plan generated successfully")
                print(f"✅ Route plan generated: {route_plan_json[:200]}...", file=sys.stderr)
                send_phi_completion(route_plan_json) # Signal Phi completion
            else:
                send_progress_update(75, "Route plan generation failed")
                print("❌ Route plan generation failed", file=sys.stderr)

            # Generate the comprehensive itinerary text using the Qwen model with streaming
            send_progress_update(80, "Generating comprehensive itinerary with Qwen model (streaming)...")
            print("Generating AI-powered itinerary with streaming...", file=sys.stderr)
            
            # Use streaming method for real-time display
            def streaming_callback(token, is_final):
                if not is_final:
                    send_streaming_token(token, False)
                else:
                    send_streaming_token("", True)
            
            itinerary = planner.run_qwen_itinerary_streaming(route_plan_json, streaming_callback)
            
            if itinerary:
                send_progress_update(95, "Itinerary generated successfully")
                print("✅ Itinerary generated successfully", file=sys.stderr)
                # Format the AI-generated text for better readability
                itinerary = _format_sentences(itinerary)
            else:
                itinerary = "Failed to generate itinerary - no route plan available"
                print("❌ Failed to generate itinerary", file=sys.stderr)
                send_progress_update(95, "Itinerary generation failed")

        except Exception as exc:
            # If the AI model workflow fails, provide a helpful error message
            error_msg = f"AI model generation failed: {exc}"
            print(f"❌ {error_msg}", file=sys.stderr)
            itinerary = error_msg
            send_progress_update(95, "AI model generation failed")

        # Send final completion
        send_progress_update(100, "Trip planning completed!")
        print(f"📤 Sending completion - Route plan: {route_plan_json is not None}, Itinerary: {itinerary is not None}", file=sys.stderr)
        if route_plan_json:
            print(f"📤 Route plan data length: {len(route_plan_json)}", file=sys.stderr)
            print(f"📤 Route plan preview: {route_plan_json[:200]}...", file=sys.stderr)
        else:
            print("⚠️ WARNING: Route plan is None - this will cause no map markers!", file=sys.stderr)
        send_completion_update(route_plan_json, itinerary)

    except Exception as e:
        # Handle any unexpected errors
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}", file=sys.stderr)
        send_progress_update(100, "Error occurred during planning")
        send_completion_update(None, error_msg)

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================
if __name__ == "__main__":
    main()
