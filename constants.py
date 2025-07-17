USER_SELECTABLE_PLACE_TYPES = [
    "카페", "식당", "공원", "영화관", "쇼핑몰", "문화공간"
]

COMPANION_PLACE_TYPES = {
    "family": [
        "박물관", "놀이공원", "동물원", "수족관", "과학관", "패밀리 레스토랑", "재래시장"
    ],
    "friends": [
        "게임카페", "방탈출 카페", "코인노래방", "보드게임카페", "펍", "테마카페"
    ],
    "couple": [
        "데이트 스팟", "야경 좋은 곳", "분위기 좋은 카페", "분위기 좋은 식당", "테마카페", "미술관", "전시회"
    ],
    "solo": [
        "산책길", "조용한 카페", "독립서점", "명상센터", "사진 전시회", "한적한 공원", "미술관", "전시회"
    ]
}

COMPANION_TYPES = [
    "solo",
    "couple",
    "friends",
    "family"
]

MAX_DISTANCE_KM = 5  # Default maximum distance for search in kilometers

BUDGET : int = 50000  # Default budget in KRW

LOCATION : tuple = (37.5563, 126.9237) # Default location for search

STARTING_TIME : int = 12  # Default starting time in hours (12 PM)
