
import random
from data.api_clients.location_fetcher import get_location_coordinates
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_TYPES, BUDGET, LOCATION, STARTING_TIME
from preferences import Preferences
import json

# Entry point

# Get user input for location
start_location = input("원하는 장소의 위치를 입력하세요 (기본값: 홍대입구): ")
start_location = get_location_coordinates(start_location) if start_location else LOCATION

# Get user input for companion type
print("동행 유형을 선택하세요:")
for idx, ct in enumerate(COMPANION_TYPES):
    print(f"{idx+1}. {ct}")
companion_selected = input("번호 또는 이름을 입력하세요 (기본값: solo): ")
companion_type = COMPANION_TYPES[0]  # Default
if companion_selected:
    companion_selected = companion_selected.strip()
    if companion_selected.isdigit():
        idx = int(companion_selected) - 1
        if 0 <= idx < len(COMPANION_TYPES):
            companion_type = COMPANION_TYPES[idx]
    elif companion_selected in COMPANION_TYPES:
        companion_type = companion_selected


# Get user input for budget
budget_input = input(f"예산을 입력하세요 (기본값: {BUDGET[0]} level): ")
try:
    budget = budget_input if budget_input else BUDGET[0]
except ValueError:
    print("잘못된 입력입니다. 기본값으로 진행합니다.")
    budget = BUDGET[0]

# Get user input for starting time
starting_time_input = input(f"출발 시간을 입력하세요 (24시간 형식, 예: 13 for 1PM, 기본값: {STARTING_TIME}): ")
try:
    starting_time = int(starting_time_input) if starting_time_input else STARTING_TIME
    if not (0 <= starting_time <= 23):
        print("잘못된 시간입니다. 기본값으로 진행합니다.")
        starting_time = STARTING_TIME
except ValueError:
    print("잘못된 입력입니다. 기본값으로 진행합니다.")
    starting_time = STARTING_TIME

# Get user input for place types
print("원하는 장소 유형을 선택하세요 (여러 개 선택하려면 쉼표로 구분):")
for idx, pt in enumerate(USER_SELECTABLE_PLACE_TYPES):
    print(f"{idx+1}. {pt}")
selected = input("번호 또는 이름을 입력하세요: ") # input example: "1, 3, 카페"


# Parse user input for place types
user_selected_types = []
for item in selected.split(','):
    item = item.strip()
    if item.isdigit():
        idx = int(item) - 1
        if 0 <= idx < len(USER_SELECTABLE_PLACE_TYPES):
            user_selected_types.append(USER_SELECTABLE_PLACE_TYPES[idx])
    elif item in USER_SELECTABLE_PLACE_TYPES:
        user_selected_types.append(item)

# Create Preferences instance and run workflow
planner = Preferences(
    companion_type=companion_type,
    budget=budget,
    starting_time=starting_time,
    start_location=start_location
)
planner.select_place_types(user_selected_types)
planner.collect_best_place()
recommendations_json = planner.format_recommendations()

# Print each place type's recommendation
for pt in planner.selected_types:
    print(f"\n[{pt}] 추천 결과:")
    for place in planner.best_places.get(pt, []):
        print(json.dumps(place, ensure_ascii=False, indent=2))

# Run route planner for 4 locations
route_plan = planner.run_route_planner()
print("\n최적의 1일 경로 추천:")
# Attempt to parse and print the route plan because it should be a JSON response
try:
    parsed_plan = json.loads(route_plan)
    print(json.dumps(parsed_plan, ensure_ascii=False, indent=2))
except Exception:
    print(route_plan)