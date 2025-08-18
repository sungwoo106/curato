"""
Interactive Command Line Interface

This module provides an interactive command-line interface for the Curato
application. It allows users to input their preferences through a series of prompts
and then generates personalized itineraries based on those preferences.

The workflow mirrors the non-interactive version in generate_plan.py but provides
a user-friendly interactive experience for direct command-line usage.

Key Features:
- Interactive user input for all preferences
- Location search and coordinate resolution
- Place type selection with validation
- Real-time itinerary generation and display
"""

import random
from data.api_clients.location_fetcher import get_location_coordinates
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, STARTING_TIME
from preferences import Preferences
import json

# =============================================================================
# MAIN ENTRY POINT AND USER INTERACTION FLOW
# =============================================================================

# =============================================================================
# LOCATION INPUT AND VALIDATION
# =============================================================================
# Get user input for starting location
# Users can enter any location name (e.g., "홍대입구", "Gangnam Station")
# The system will search for coordinates using the Kakao Map API
start_location = input("원하는 장소의 위치를 입력하세요 (기본값: 홍대입구): ")
start_location = get_location_coordinates(start_location) if start_location else LOCATION

# =============================================================================
# COMPANION TYPE SELECTION
# =============================================================================
# Display available companion types and get user selection
# This affects the tone, style, and place type recommendations
print("동행 유형을 선택하세요:")
for idx, ct in enumerate(COMPANION_TYPES):
    print(f"{idx+1}. {ct}")

# Accept both numeric and text input for flexibility
companion_selected = input("번호 또는 이름을 입력하세요 (기본값: solo): ")
companion_type = COMPANION_TYPES[0]  # Default to Solo

if companion_selected:
    companion_selected = companion_selected.strip()
    
    # Handle numeric input (1, 2, 3, 4)
    if companion_selected.isdigit():
        idx = int(companion_selected) - 1
        if 0 <= idx < len(COMPANION_TYPES):
            companion_type = COMPANION_TYPES[idx]
    
    # Handle text input (Solo, Couple, Friends, Family)
    elif companion_selected in COMPANION_TYPES:
        companion_type = companion_selected

# =============================================================================
# BUDGET LEVEL SELECTION
# =============================================================================
# Get user's budget preference for the outing
# This affects the types of activities and places recommended
budget_input = input(f"예산을 입력하세요 (기본값: {BUDGET[0]} level): ")

try:
    budget = budget_input if budget_input else BUDGET[0]
except ValueError:
    print("잘못된 입력입니다. 기본값으로 진행합니다.")
    budget = BUDGET[0]

# =============================================================================
# STARTING TIME INPUT
# =============================================================================
# Get the preferred starting time for the day's activities
# This affects the flow and timing of the recommended itinerary
starting_time_input = input(f"출발 시간을 입력하세요 (24시간 형식, 예: 13 for 1PM, 기본값: {STARTING_TIME}): ")

try:
    starting_time = int(starting_time_input) if starting_time_input else STARTING_TIME
    
    # Validate time is within 24-hour range
    if not (0 <= starting_time <= 23):
        print("잘못된 시간입니다. 기본값으로 진행합니다.")
        starting_time = STARTING_TIME
        
except ValueError:
    print("잘못된 입력입니다. 기본값으로 진행합니다.")
    starting_time = STARTING_TIME

# =============================================================================
# PLACE TYPE SELECTION
# =============================================================================
# Display available place types and get user preferences
# Users can select multiple types to customize their experience
print("원하는 장소 유형을 선택하세요 (여러 개 선택하려면 쉼표로 구분):")
for idx, pt in enumerate(USER_SELECTABLE_PLACE_TYPES):
    print(f"{idx+1}. {pt}")

# Accept comma-separated input for multiple selections
# Example input: "1, 3, 카페" or "Cafe, Restaurant"
selected = input("번호 또는 이름을 입력하세요: ")

# =============================================================================
# PLACE TYPE PARSING AND VALIDATION
# =============================================================================
# Parse the user input and convert to actual place type names
user_selected_types = []

for item in selected.split(','):
    item = item.strip()
    
    # Handle numeric input (1, 2, 3, etc.)
    if item.isdigit():
        idx = int(item) - 1
        if 0 <= idx < len(USER_SELECTABLE_PLACE_TYPES):
            user_selected_types.append(USER_SELECTABLE_PLACE_TYPES[idx])
    
    # Handle text input (Cafe, Restaurant, etc.)
    elif item in USER_SELECTABLE_PLACE_TYPES:
        user_selected_types.append(item)

# =============================================================================
# ITINERARY GENERATION WORKFLOW
# =============================================================================
# Create Preferences instance with all user inputs and run the main workflow
# This orchestrates the entire process from preferences to final itinerary
planner = Preferences(
    companion_type=companion_type,      # Selected companion type
    budget=budget,                      # Selected budget level
    starting_time=starting_time,        # Selected starting time
    start_location=start_location       # Resolved location coordinates
)

# Select appropriate place types based on companion type and user preferences
planner.select_place_types(user_selected_types)

# Collect place recommendations from external APIs
planner.collect_best_place()

# Format recommendations for display and AI processing
recommendations_json = planner.format_recommendations()

# =============================================================================
# RESULTS DISPLAY
# =============================================================================
# Display the collected place recommendations for each selected place type
# This shows users what places were found before generating the final itinerary
for pt in planner.selected_types:
    print(f"\n[{pt}] 추천 결과:")
    for place in planner.best_places.get(pt, []):
        print(json.dumps(place, ensure_ascii=False, indent=2))

# =============================================================================
# ROUTE PLANNING AND FINAL ITINERARY
# =============================================================================
# Generate the optimal route plan using AI models
# This creates a coherent sequence of 4 locations for the day
route_plan = planner.run_route_planner()
print("\n최적의 1일 경로 추천:")

# Attempt to parse and display the route plan
# The route plan should be a JSON response from the AI model
try:
    parsed_plan = json.loads(route_plan)
    print(json.dumps(parsed_plan, ensure_ascii=False, indent=2))
except Exception:
    # If parsing fails, display the raw response
    print(route_plan)
    