USER_SELECTABLE_PLACE_TYPES = [
    "Cafe", "Restaurant", "Park", "Cinema", "Mall", "Cultural Spot"
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
    "Solo",
    "Couple",
    "Friends",
    "Family"
]

MAX_DISTANCE_KM = 5  # Default maximum distance for search in kilometers

BUDGET = ["low", "medium", "high"]  # Default budget in KRW

LOCATION : tuple = (37.5563, 126.9237) # Default location for search

STARTING_TIME : int = 12  # Default starting time in hours (12 PM)

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

LOW_BUDGET = [
    "grab a warm cup of street coffee",
    "share a simple snack from a nearby stall",
    "buy a small souvenir from a local stand",
    "pick up a couple of drinks from a convenience store and chat on a bench",
    "try a hotteok or fish cake at a food cart",
    "browse cute trinkets at a Daiso or small shop",
    "toss coins into a wishing fountain",
    "take sticker photos at a self-photo booth",
    "rent a book or comic from a local library café",
    "enjoy an ice cream cone on a quiet walk"
]

MEDIUM_BUDGET = [
    "enjoy a cozy café treat while watching people pass by",
    "try a local specialty dish at a well-known eatery",
    "buy a matching pair of keychains from a souvenir shop",
    "visit a small art exhibit or museum with a modest entrance fee",
    "rent bikes and ride along a scenic path",
    "share a mini dessert platter at a bakery",
    "sit for a caricature drawing or instant portrait",
    "take a short river cruise or paddle boat ride",
    "buy tickets to a themed pop-up or cultural experience",
    "attend a mini workshop (calligraphy, crafts, etc.)"
]

HIGH_BUDGET = [
    "treat yourselves to a luxurious dessert at a famous patisserie",
    "book a private tea or wine tasting experience",
    "shop for handmade accessories at a boutique",
    "go for a scenic cable car or observatory ride",
    "have a multi-course lunch at a beautiful restaurant",
    "enjoy a couple’s spa footbath or massage chair session",
    "take professional photos at a hanbok rental studio",
    "rent a private boat or han river picnic set",
    "purchase matching couple rings or bracelets",
    "sign up for a guided city tour or street food tasting walk"
]
