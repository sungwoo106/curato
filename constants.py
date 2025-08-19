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
    "public": "PO3",
    "government": "PO3",
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
        "박물관", "놀이공원", "동물원", "수족관", "과학관", "패밀리 레스토랑", "재래시장"
        # Museum, Amusement Park, Zoo, Aquarium, Science Center, Family Restaurant, Traditional Market
    ],
    "friends": [
        "게임카페", "방탈출 카페", "코인노래방", "보드게임카페", "펍", "테마카페"
        # Game Cafe, Escape Room Cafe, Coin Karaoke, Board Game Cafe, Pub, Theme Cafe
    ],
    "couple": [
        "데이트 스팟", "야경 좋은 곳", "분위기 좋은 카페", "분위기 좋은 식당", "테마카페", "미술관", "전시회"
        # Date Spot, Scenic Night View, Atmosphere Cafe, Atmosphere Restaurant, Theme Cafe, Art Museum, Exhibition
    ],
    "solo": [
        "산책길", "조용한 카페", "독립서점", "명상센터", "사진 전시회", "한적한 공원", "미술관", "전시회"
        # Walking Path, Quiet Cafe, Independent Bookstore, Meditation Center, Photo Exhibition, Quiet Park, Art Museum, Exhibition
    ]
}

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
