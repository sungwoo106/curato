from core.prompts import build_phi_prompt
from models.phi_runner import run_phi_runner
from data.api_clients.location_fetcher import get_location_coordinates
from constants import USER_SELECTABLE_PLACE_TYPES, COMPANION_TYPES, COMPANION_PLACE_TYPES, MIN_RATING, BUDGET, LOCATION, STARTING_TIME
from preferences import Preferences

# Entry point

# Get user input for location
location = input("원하는 장소의 위치를 입력하세요 (기본값: 홍대입구): ")
location = get_location_coordinates(location) if location else LOCATION

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
budget_input = input(f"예산을 입력하세요 (기본값: {BUDGET}원): ")
try:
    budget = int(budget_input) if budget_input else BUDGET
except ValueError:
    print("잘못된 입력입니다. 기본값으로 진행합니다.")
    budget = BUDGET

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
selected = input("번호 또는 이름을 입력하세요: ")

# Parse user input
selected_types = []
for item in selected.split(','):
    item = item.strip()
    if item.isdigit():
        idx = int(item) - 1
        if 0 <= idx < len(USER_SELECTABLE_PLACE_TYPES):
            selected_types.append(USER_SELECTABLE_PLACE_TYPES[idx])
    elif item in USER_SELECTABLE_PLACE_TYPES:
        selected_types.append(item)

# Add companion-specific place types
companion_places = COMPANION_PLACE_TYPES.get(companion_type, [])
for pt in companion_places:
    if pt not in selected_types:
        selected_types.append(pt)

if not selected_types:
    print("선택된 장소 유형이 없습니다. 기본값(카페)으로 진행합니다.")
    selected_types = [USER_SELECTABLE_PLACE_TYPES[0]]

# Run for each selected place type
for pt in selected_types:
    planner = Preferences(place_type=pt, companion_type=companion_type, budget=budget, starting_time=starting_time, location=location)
    phi_output = planner.run()
    print(f"\n[{pt}] 추천 결과:")
    print(phi_output)