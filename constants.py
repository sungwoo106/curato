"""
Application Constants and Configuration

Centralized configuration for the Edge Day Planner application.
"""

# =============================================================================
# KAKAO API CATEGORY CODES
# =============================================================================
# Official category codes for precise place type searching
KAKAO_CATEGORY_CODES = {
    # Shopping & Daily Life
    "MT1": "대형마트",           # Supermarket
    "CS2": "편의점",             # Convenience store
    
    # Education & Learning
    "PS3": "어린이집, 유치원",    # Daycare center, kindergarten
    "SC4": "학교",               # School
    "AC5": "학원",               # Hagwon (cram school, private learning institute)
    
    # Transportation & Infrastructure
    "PK6": "주차장",             # Parking lot
    "OL7": "주유소, 충전소",      # Gas station, LPG station
    "SW8": "지하철역",            # Subway station
    
    # Business & Services
    "BK9": "은행",               # Bank
    "AG2": "중개업소",            # Real estate agency
    
    # Culture & Entertainment
    "CT1": "문화시설",            # Cultural facility
    "AT4": "관광명소",            # Attractions
    
    # Government & Public
    "PO3": "공공기관",            # Public institutions
    
    # Accommodation & Food
    "AD5": "숙박",               # Accommodation
    "FD6": "음식점",             # Restaurant
    "CE7": "카페",               # Cafe
    
    # Health & Wellness
    "HP8": "병원",               # Hospital
    "PM9": "약국",               # Pharmacy
}

# Place type to category code mappings for automatic detection
PLACE_TYPE_CATEGORY_MAPPINGS = {
    # Korean mappings
    "카페": "CE7",
    "음식점": "FD6",
    "식당": "FD6",
    "문화시설": "CT1",
    "관광명소": "AT4",
    "공원": "AT4",  # Parks are often tourist attractions
    "대형마트": "MT1",
    "편의점": "CS2",
    "지하철역": "SW8",
    "은행": "BK9",
    "병원": "HP8",
    "약국": "PM9",
    "주차장": "PK6",
    "주유소": "OL7",
    "충전소": "OL7",
    "학교": "SC4",
    "학원": "AC5",
    "어린이집": "PS3",
    "유치원": "PS3",
    "숙박": "AD5",
    "중개업소": "AG2",
    "공공기관": "PO3",
    
    # Specific place type mappings
    "테마카페": "CE7",
    "디저트카페": "CE7",
    "힐링카페": "CE7",
    "키즈카페": "CE7",
    "게임카페": "CT1",  # Cultural facility
    "방탈출카페": "CT1", # Cultural facility
    "보드게임카페": "CT1", # Cultural facility
    "만화카페": "CT1",   # Cultural facility
    "스터디카페": "AC5",  # Academy
    "독립서점": "AC5",    # Academy
    "독서실": "AC5",      # Academy
    "도서관": "CT1",      # Cultural facility
    "박물관": "CT1",
    "과학관": "CT1",
    "수족관": "CT1",
    "동물원": "CT1",
    "놀이공원": "AT4",
    "워터파크": "AT4",    # Tourist attraction
    "식물원": "AT4",
    "천문대": "AT4",
    "동물농장": "AT4",
    "놀이터": "AT4",
    "체험학습장": "AC5",   # Academy
    "가족영화관": "CT1",   # Cultural facility
    "재래시장": "MT1",     # Supermarket
    "아이스크림가게": "FD6", # Restaurant
    "전통문화체험관": "CT1", # Cultural facility
    "자연사박물관": "CT1",   # Cultural facility
    "로맨틱레스토랑": "FD6",
    "와인바": "FD6",
    "칵테일바": "FD6",
    "분위기좋은카페": "CE7",
    "분위기좋은식당": "FD6",
    "분위기좋은술집": "FD6",
    "사진관": "CT1",      # Cultural facility
    "영화관": "CT1",      # Cultural facility
    "공연장": "CT1",      # Cultural facility
    "콘서트홀": "CT1",    # Cultural facility
    "문화센터": "CT1",
    "산책길": "AT4",      # Tourist attraction
    "조용한카페": "CE7",
    "명상숲": "AT4",      # Tourist attraction
    "힐링센터": "CT1",    # Cultural facility
    "요가센터": "CT1",    # Cultural facility
    "필라테스": "CT1",    # Cultural facility
    "탁구장": "CT1",      # Cultural facility
    "테니스장": "CT1",    # Cultural facility
    "골프연습장": "CT1",  # Cultural facility
    "등산로": "AT4",      # Tourist attraction
    "자전거도로": "AT4",  # Tourist attraction
    "조깅코스": "AT4",    # Tourist attraction
    "볼링장": "CT1",      # Cultural facility
    "당구장": "CT1",      # Cultural facility
    "다트바": "FD6",      # Restaurant
    "퀴즈카페": "CT1",    # Cultural facility
    "마술카페": "CT1",    # Cultural facility
    "포토존": "CT1",      # Cultural facility
    "팝업스토어": "MT1",  # Supermarket
    "플리마켓": "MT1",    # Supermarket
    "코인노래방": "CT1",  # Cultural facility
    "펍": "FD6",
    "전시회": "CT1",      # Cultural facility
    "야경좋은곳": "AT4",  # Tourist attraction
    "데이트스팟": "AT4",  # Tourist attraction
    "패밀리레스토랑": "FD6",
    "쇼핑": "MT1",        # Supermarket
    "엔터테인먼트": "CT1", # Cultural facility
    
    # English mappings
    "cafe": "CE7",
    "restaurant": "FD6",
    "cultural": "CT1",
    "culture": "CT1",
    "attraction": "AT4",
    "tourist": "AT4",
    "park": "AT4",
    "supermarket": "MT1",
    "convenience": "CS2",
    "subway": "SW8",
    "station": "SW8",
    "bank": "BK9",
    "hospital": "HP8",
    "pharmacy": "PM9",
    "parking": "PK6",
    "gas": "OL7",
    "charging": "OL7",
    "school": "SC4",
    "academy": "AC5",
    "kindergarten": "PS3",
    "daycare": "PS3",
    "accommodation": "AD5",
    "hotel": "AD5",
    "real estate": "AG2",
    "public": "PO3"
}

# =============================================================================
# USER SELECTABLE PLACE TYPES
# =============================================================================
# Basic place types that users can manually select from the UI
USER_SELECTABLE_PLACE_TYPES = [
    "Cafe", "Restaurant", "Park", "Cinema", "Mall", "Cultural Spot"
]

# =============================================================================
# COMPANION-SPECIFIC PLACE TYPE RECOMMENDATIONS
# =============================================================================
# Curated place type recommendations based on companion type
COMPANION_PLACE_TYPES = {
    "family": [
        "박물관", "놀이공원", "동물원", "수족관", "과학관", "패밀리 레스토랑", "재래시장",
        "공원", "아이스크림 가게", "도서관", "체험학습장", "키즈카페", "가족영화관", "놀이터",
        "전통문화체험관", "자연사박물관", "천문대", "식물원", "동물농장", "워터파크"
    ],
    "friends": [
        "게임카페", "방탈출 카페", "코인노래방", "보드게임카페", "펍", "테마카페",
        "노래방", "PC방", "만화카페", "보드게임방", "VR체험관", "실내운동시설", "볼링장",
        "당구장", "다트바", "퀴즈카페", "마술카페", "포토존", "팝업스토어", "플리마켓"
    ],
    "couple": [
        "데이트 스팟", "야경 좋은 곳", "분위기 좋은 카페", "분위기 좋은 식당", "테마카페", "미술관", "전시회",
        "로맨틱 레스토랑", "와인바", "칵테일바", "디저트카페", "스파", "마사지샵", "한복체험관",
        "사진관", "영화관", "공연장", "콘서트홀", "갤러리", "문화센터", "힐링카페", "분위기 좋은 술집"
    ],
    "solo": [
        "산책길", "조용한 카페", "독립서점", "명상센터", "사진 전시회", "한적한 공원", "미술관", "전시회",
        "도서관", "독서실", "스터디카페", "요가센터", "필라테스", "헬스장", "수영장", "탁구장",
        "테니스장", "골프연습장", "등산로", "자전거도로", "조깅코스", "명상숲", "힐링센터", "아로마테라피"
    ]
}

# =============================================================================
# VARIETY PLACE TYPES FOR ENHANCED DIVERSITY
# =============================================================================
# Additional place types that provide variety and richness to itineraries
VARIETY_PLACE_TYPES = [
    "테마카페",      # Theme cafes - unique experiences
    "문화시설",      # Cultural facilities - museums, galleries, theaters
    "관광명소",      # Tourist attractions - landmarks, viewpoints
    "공원",         # Parks - outdoor spaces, nature
    "쇼핑",         # Shopping - retail, markets, boutiques
    "엔터테인먼트"   # Entertainment - fun activities, games
]

# =============================================================================
# DEFAULT PLACE TYPES FOR MINIMUM VARIETY
# =============================================================================
# Default place types used as fallbacks when minimum variety is needed
DEFAULT_PLACE_TYPES = [
    "Cafe",           # Basic cafe option
    "Restaurant",     # Basic restaurant option  
    "문화시설",        # Cultural facilities
    "관광명소"         # Tourist attractions
]

# =============================================================================
# COMPANION TYPE OPTIONS
# =============================================================================
# Available companion types for user selection
COMPANION_TYPES = [
    "Solo",      # Individual exploration and reflection
    "Couple",    # Romantic and intimate experiences
    "Friends",   # Social and fun group activities
    "Family"     # Safe and educational family bonding
]

# =============================================================================
# BUDGET CONFIGURATION
# =============================================================================
# Available budget levels for user selection
BUDGET = ["low", "medium", "high"]  # Budget levels in ascending order

# =============================================================================
# DEFAULT LOCATION AND TIMING
# =============================================================================
# Default location coordinates for search (Hongdae area, Seoul)
LOCATION : tuple = (37.5563, 126.9237)

# Default starting time in 24-hour format (12 = 12:00 PM / noon)
STARTING_TIME : int = 12




