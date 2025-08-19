"""
Application Constants and Configuration

This module contains all the constant values, configuration options, and data structures
used throughout the Edge Day Planner application. It centralizes configuration to make
the application easy to maintain and modify.

Key Sections:
- Place type definitions for different companion types
- Budget levels and associated activities
- Default locations and timing
- Tone and style mappings for personalized content generation
"""

# =============================================================================
# KAKAO API CATEGORY CODES
# =============================================================================
# Official Kakao Map API category group codes for precise place type searching
# These codes provide more accurate and consistent results than text-based searches
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

# Reverse mapping for category code lookup (category name to code)
CATEGORY_CODE_TO_NAME = {v: k for k, v in KAKAO_CATEGORY_CODES.items()}

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
    
    # Specific place type mappings (using valid category codes)
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
# These are general categories that work well for most outing types
USER_SELECTABLE_PLACE_TYPES = [
    "Cafe", "Restaurant", "Park", "Cinema", "Mall", "Cultural Spot"
]

# =============================================================================
# COMPANION-SPECIFIC PLACE TYPE RECOMMENDATIONS
# =============================================================================
# Curated place type recommendations based on companion type
# Each companion type has specific place types that enhance the experience
# Korean names are used for better local context and API compatibility
COMPANION_PLACE_TYPES = {
    "family": [
        "박물관", "놀이공원", "동물원", "수족관", "과학관", "패밀리 레스토랑", "재래시장",
        "공원", "아이스크림 가게", "도서관", "체험학습장", "키즈카페", "가족영화관", "놀이터",
        "전통문화체험관", "자연사박물관", "천문대", "식물원", "동물농장", "워터파크"
        # Museum, Amusement Park, Zoo, Aquarium, Science Center, Family Restaurant, Traditional Market,
        # Park, Ice Cream Shop, Library, Experience Learning Center, Kids Cafe, Family Cinema, Playground,
        # Traditional Culture Experience Center, Natural History Museum, Observatory, Botanical Garden, Animal Farm, Water Park
    ],
    "friends": [
        "게임카페", "방탈출 카페", "코인노래방", "보드게임카페", "펍", "테마카페",
        "노래방", "PC방", "만화카페", "보드게임방", "VR체험관", "실내운동시설", "볼링장",
        "당구장", "다트바", "퀴즈카페", "마술카페", "포토존", "팝업스토어", "플리마켓"
        # Game Cafe, Escape Room Cafe, Coin Karaoke, Board Game Cafe, Pub, Theme Cafe,
        # Karaoke, PC Room, Comic Cafe, Board Game Room, VR Experience Center, Indoor Sports Facility, Bowling Alley,
        # Billiards Hall, Dart Bar, Quiz Cafe, Magic Cafe, Photo Zone, Pop-up Store, Flea Market
    ],
    "couple": [
        "데이트 스팟", "야경 좋은 곳", "분위기 좋은 카페", "분위기 좋은 식당", "테마카페", "미술관", "전시회",
        "로맨틱 레스토랑", "와인바", "칵테일바", "디저트카페", "스파", "마사지샵", "한복체험관",
        "사진관", "영화관", "공연장", "콘서트홀", "갤러리", "문화센터", "힐링카페", "분위기 좋은 술집"
        # Date Spot, Scenic Night View, Atmosphere Cafe, Atmosphere Restaurant, Theme Cafe, Art Museum, Exhibition,
        # Romantic Restaurant, Wine Bar, Cocktail Bar, Dessert Cafe, Spa, Massage Shop, Hanbok Experience Center,
        # Photo Studio, Cinema, Performance Hall, Concert Hall, Gallery, Culture Center, Healing Cafe, Atmosphere Bar
    ],
    "solo": [
        "산책길", "조용한 카페", "독립서점", "명상센터", "사진 전시회", "한적한 공원", "미술관", "전시회",
        "도서관", "독서실", "스터디카페", "요가센터", "필라테스", "헬스장", "수영장", "탁구장",
        "테니스장", "골프연습장", "등산로", "자전거도로", "조깅코스", "명상숲", "힐링센터", "아로마테라피"
        # Walking Path, Quiet Cafe, Independent Bookstore, Meditation Center, Photo Exhibition, Quiet Park, Art Museum, Exhibition,
        # Library, Study Room, Study Cafe, Yoga Center, Pilates, Gym, Swimming Pool, Table Tennis Court,
        # Tennis Court, Golf Practice Range, Hiking Trail, Bicycle Path, Jogging Course, Meditation Forest, Healing Center, Aromatherapy
    ]
}

# =============================================================================
# VARIETY PLACE TYPES FOR ENHANCED DIVERSITY
# =============================================================================
# Additional place types that provide variety and richness to itineraries
# These are automatically added to create more diverse and interesting experiences
# They complement the companion-specific types without overwhelming user selections
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
# These ensure we always have a basic set of diverse place types
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
# These determine the tone, style, and place recommendations
COMPANION_TYPES = [
    "Solo",      # Individual exploration and reflection
    "Couple",    # Romantic and intimate experiences
    "Friends",   # Social and fun group activities
    "Family"     # Safe and educational family bonding
]

# =============================================================================
# SEARCH AND DISTANCE CONSTRAINTS
# =============================================================================
# Default maximum distance for search in kilometers
# This ensures recommended places are within reasonable travel distance
MAX_DISTANCE_KM = 5

# =============================================================================
# BUDGET CONFIGURATION
# =============================================================================
# Available budget levels for user selection
# Each level corresponds to different activity suggestions and spending expectations
BUDGET = ["low", "medium", "high"]  # Budget levels in ascending order

# =============================================================================
# DEFAULT LOCATION AND TIMING
# =============================================================================
# Default location coordinates for search (Hongdae area, Seoul)
# Format: (latitude, longitude) - used when no specific location is provided
LOCATION : tuple = (37.5563, 126.9237)

# Default starting time in 24-hour format (12 = 12:00 PM / noon)
# This affects the flow and timing of the recommended itinerary
STARTING_TIME : int = 12

# =============================================================================
# TONE AND STYLE MAPPING
# =============================================================================
# Defines the emotional tone and writing style for each companion type
# This ensures the generated itineraries match the expected experience
TONE_STYLE_MAP = {
    "solo": {
        "tone": "introspective and calm",
        "style_note": "Use peaceful and reflective language. Highlight moments of stillness or self-connection."
    },
    "family": {
        "tone": "warm and secure",
        "style_note": "Use comforting and affectionate language. Emphasize bonding, laughter, and safety."
    },
    "couple": {
        "tone": "poetic and romantic",
        "style_note": "Use tender and lyrical language. Focus on shared moments, feelings, and beauty."
    },
    "friends": {
        "tone": "casual and playful",
        "style_note": "Use energetic, humorous language. Emphasize fun, spontaneity, and good vibes."
    }
}

# =============================================================================
# BUDGET-SPECIFIC ACTIVITY SUGGESTIONS
# =============================================================================
# Curated activity suggestions for each budget level
# These provide concrete ideas that fit within the specified budget constraints

# Low budget activities (typically under 10,000 KRW)
# Focus on free or very inexpensive experiences
LOW_BUDGET = [
    "grab a warm cup of street coffee",                    # Street coffee (~3,000 KRW)
    "share a simple snack from a nearby stall",            # Street food (~2,000-5,000 KRW)
    "buy a small souvenir from a local stand",             # Small trinkets (~5,000 KRW)
    "pick up a couple of drinks from a convenience store and chat on a bench",  # Convenience store (~3,000 KRW)
    "try a hotteok or fish cake at a food cart",          # Street snacks (~1,000-3,000 KRW)
    "browse cute trinkets at a Daiso or small shop",       # Daiso shopping (~1,000-5,000 KRW)
    "toss coins into a wishing fountain",                  # Free activity
    "take sticker photos at a self-photo booth",           # Photo booth (~3,000-5,000 KRW)
    "rent a book or comic from a local library café",      # Library activities (free)
    "enjoy an ice cream cone on a quiet walk"              # Ice cream (~2,000-4,000 KRW)
]

# Medium budget activities (typically 10,000-30,000 KRW)
# Balance between cost and experience quality
MEDIUM_BUDGET = [
    "enjoy a cozy café treat while watching people pass by",    # Cafe (~8,000-15,000 KRW)
    "try a local specialty dish at a well-known eatery",        # Restaurant (~15,000-25,000 KRW)
    "buy a matching pair of keychains from a souvenir shop",    # Souvenirs (~10,000-20,000 KRW)
    "visit a small art exhibit or museum with a modest entrance fee",  # Museums (~5,000-15,000 KRW)
    "rent bikes and ride along a scenic path",                  # Bike rental (~10,000-20,000 KRW)
    "share a mini dessert platter at a bakery",                 # Bakery (~8,000-15,000 KRW)
    "sit for a caricature drawing or instant portrait",         # Art services (~15,000-25,000 KRW)
    "take a short river cruise or paddle boat ride",            # Boat activities (~20,000-30,000 KRW)
    "buy tickets to a themed pop-up or cultural experience",    # Cultural events (~10,000-25,000 KRW)
    "attend a mini workshop (calligraphy, crafts, etc.)"        # Workshops (~15,000-25,000 KRW)
]

# High budget activities (typically 30,000+ KRW)
# Premium experiences and luxury options
HIGH_BUDGET = [
    "treat yourselves to a luxurious dessert at a famous patisserie",  # High-end desserts (~20,000-40,000 KRW)
    "book a private tea or wine tasting experience",                   # Private tastings (~50,000-100,000 KRW)
    "shop for handmade accessories at a boutique",                     # Boutique shopping (~30,000-100,000 KRW)
    "go for a scenic cable car or observatory ride",                   # Tourist attractions (~30,000-50,000 KRW)
    "have a multi-course lunch at a beautiful restaurant",             # Fine dining (~50,000-100,000 KRW)
    "enjoy a couple's spa footbath or massage chair session",         # Spa services (~30,000-80,000 KRW)
    "take professional photos at a hanbok rental studio",              # Photo sessions (~50,000-100,000 KRW)
    "rent a private boat or han river picnic set",                     # Private experiences (~100,000+ KRW)
    "purchase matching couple rings or bracelets",                     # Jewelry (~100,000+ KRW)
    "sign up for a guided city tour or street food tasting walk"      # Guided tours (~50,000-150,000 KRW)
]
