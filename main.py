from core.prompts import build_phi_prompt
from models.phi_runner import run_phi_runner
from constants import PLACE_TYPES, COMPANION_TYPES, MIN_RATING, BUDGET, LOCATION
from preferences import Preferences

# Entry point

# Get user input for location
location = input("원하는 장소의 위치를 입력하세요 (기본값: 홍대입구): ")
LOCATION = location if location else LOCATION

print("원하는 장소 유형을 선택하세요 (여러 개 선택하려면 쉼표로 구분):")
for idx, pt in enumerate(PLACE_TYPES):
    print(f"{idx+1}. {pt}")
selected = input("번호 또는 이름을 입력하세요: ")

# Parse user input
selected_types = []
for item in selected.split(','):
    item = item.strip()
    if item.isdigit():
        idx = int(item) - 1
        if 0 <= idx < len(PLACE_TYPES):
            selected_types.append(PLACE_TYPES[idx])
    elif item in PLACE_TYPES:
        selected_types.append(item)

if not selected_types:
    print("선택된 장소 유형이 없습니다. 기본값(restaurant)으로 진행합니다.")
    selected_types = [PLACE_TYPES[0]]

# Run for each selected place type
for pt in selected_types:
    planner = Preferences(place_type=pt, location=location)
    phi_output = planner.run()
    print(f"\n[{pt}] 추천 결과:")
    print(phi_output)