"""
Rules-based civic complaint normalization for UrbanPulse AI.

Works fully offline (no LLM): sanitizes untrusted text, detects script/language,
maps text to a canonical municipal category with a subcategory, estimates an
operational severity heuristic, and grounds locations only against a verified
landmark gazetteer or caller-supplied coordinates. It never invents coordinates.
"""

import math
import re
from typing import Dict, Any, Tuple, Optional, List, Iterable


CANONICAL_CATEGORIES: List[str] = [
    "WASTE_MANAGEMENT",
    "WATER_SUPPLY",
    "ROADS_INFRASTRUCTURE",
    "DRAINAGE_SANITATION",
    "STREETLIGHTS_ELECTRICITY",
    "POWER_SUPPLY",
    "PUBLIC_ASSETS",
    "ILLEGAL_DUMPING",
    "OTHER",
]

CATEGORY_LABELS: Dict[str, str] = {
    "WASTE_MANAGEMENT": "Waste Management",
    "WATER_SUPPLY": "Water Supply",
    "ROADS_INFRASTRUCTURE": "Roads & Infrastructure",
    "DRAINAGE_SANITATION": "Drainage & Sanitation",
    "STREETLIGHTS_ELECTRICITY": "Streetlights",
    "POWER_SUPPLY": "Power Supply",
    "PUBLIC_ASSETS": "Public Assets",
    "ILLEGAL_DUMPING": "Illegal Dumping",
    "OTHER": "Other",
}

# Older category codes from earlier versions of this project -> (canonical, subcategory)
LEGACY_CATEGORY_MAP: Dict[str, Tuple[str, str]] = {
    "ROAD_FLOODING": ("DRAINAGE_SANITATION", "Road / subway flooding"),
    "WATERLOGGING": ("DRAINAGE_SANITATION", "Waterlogging"),
    "BLOCKED_DRAIN": ("DRAINAGE_SANITATION", "Blocked drain"),
    "SEWER_OVERFLOW": ("DRAINAGE_SANITATION", "Sewer overflow"),
    "ROAD_DAMAGE": ("ROADS_INFRASTRUCTURE", "Pothole / road damage"),
}

# Free-text category names commonly seen in municipal exports -> canonical code.
_CATEGORY_KEYWORDS: List[Tuple[str, str]] = [
    ("DUMP", "ILLEGAL_DUMPING"),
    ("DEBRIS", "ILLEGAL_DUMPING"),
    ("GARBAGE", "WASTE_MANAGEMENT"),
    ("WASTE", "WASTE_MANAGEMENT"),
    ("SOLID", "WASTE_MANAGEMENT"),
    ("SANITATION", "DRAINAGE_SANITATION"),
    ("DRAIN", "DRAINAGE_SANITATION"),
    ("SEWER", "DRAINAGE_SANITATION"),
    ("SEWAGE", "DRAINAGE_SANITATION"),
    ("FLOOD", "DRAINAGE_SANITATION"),
    ("STREETLIGHT", "STREETLIGHTS_ELECTRICITY"),
    ("STREET_LIGHT", "STREETLIGHTS_ELECTRICITY"),
    ("LIGHT", "STREETLIGHTS_ELECTRICITY"),
    ("POWER", "POWER_SUPPLY"),
    ("ELECTRIC", "POWER_SUPPLY"),
    ("WATER", "WATER_SUPPLY"),
    ("POTHOLE", "ROADS_INFRASTRUCTURE"),
    ("ROAD", "ROADS_INFRASTRUCTURE"),
    ("FOOTPATH", "ROADS_INFRASTRUCTURE"),
    ("PARK", "PUBLIC_ASSETS"),
    ("TOILET", "PUBLIC_ASSETS"),
    ("ASSET", "PUBLIC_ASSETS"),
    ("BUS", "PUBLIC_ASSETS"),
]


# Verified Chennai landmark gazetteer: key -> (lat, lon, zone_id, canonical name)
LANDMARK_COORDINATES: Dict[str, Tuple[float, float, str, str]] = {
    "vyasarpadi subway": (13.1160, 80.2612, "chennai-zone-04", "Vyasarpadi Subway"),
    "ganesapuram subway": (13.1023, 80.2644, "chennai-zone-04", "Ganesapuram Subway"),
    "villivakkam subway": (13.1095, 80.2078, "chennai-zone-08", "Villivakkam Subway"),
    "duraisamy subway": (13.0410, 80.2325, "chennai-zone-09", "Duraisamy Subway, T. Nagar"),
    "madley subway": (13.0375, 80.2310, "chennai-zone-09", "Madley Subway, T. Nagar"),
    "velachery main road": (12.9815, 80.2180, "chennai-zone-14", "Velachery Main Road"),
    "velachery bus stand": (12.9805, 80.2195, "chennai-zone-14", "Velachery Bus Stand"),
    "madipakkam lake": (12.9647, 80.1989, "chennai-zone-14", "Madipakkam Lake Junction"),
    "thillai ganga nagar subway": (12.9984, 80.1970, "chennai-zone-12", "Thillai Ganga Nagar Subway"),
    "saidapet adyar bridge": (13.0210, 80.2230, "chennai-zone-10", "Saidapet Adyar Bridge"),
    "jafferkhanpet": (13.0290, 80.2045, "chennai-zone-10", "Jafferkhanpet / Mambalam Canal"),
    "korattur lake": (13.1110, 80.1770, "chennai-zone-07", "Korattur Lake"),
    "otteri nullah": (13.0910, 80.2520, "chennai-zone-06", "Otteri Nullah, Thiru Vi Ka Nagar"),
    "perambur railway station": (13.1080, 80.2440, "chennai-zone-06", "Perambur Railway Station"),
    "ranganathan street": (13.0402, 80.2335, "chennai-zone-09", "Ranganathan Street, T. Nagar"),
    "sholinganallur junction": (12.9010, 80.2279, "chennai-zone-15", "Sholinganallur Junction, OMR"),
    "okkiyam maduvu": (12.9230, 80.2330, "chennai-zone-15", "Okkiyam Maduvu Canal Outfall"),
    "thiruvottiyur high road": (13.1610, 80.3010, "chennai-zone-01", "Thiruvottiyur High Road"),
    "kathipara junction": (13.0067, 80.2053, "chennai-zone-12", "Kathipara Junction"),
    # Native-script aliases
    "வேளச்சேரி": (12.9815, 80.2180, "chennai-zone-14", "Velachery Main Road"),
    "रंगनाथन स्ट्रीट": (13.0402, 80.2335, "chennai-zone-09", "Ranganathan Street, T. Nagar"),
}

# Maximum distance from a zone centroid at which a coordinate is attributed to that zone.
MAX_ZONE_ASSIGNMENT_KM = 8.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
    )
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def nearest_zone(lat: float, lon: float, zones: Iterable[Dict[str, Any]]) -> Optional[str]:
    """Nearest zone centroid within MAX_ZONE_ASSIGNMENT_KM. Approximate: zone polygons are not available."""
    best_id, best_d = None, float("inf")
    for z in zones:
        d = haversine_m(lat, lon, z["center_lat"], z["center_lon"])
        if d < best_d:
            best_id, best_d = z["id"], d
    if best_id is None or best_d > MAX_ZONE_ASSIGNMENT_KM * 1000:
        return None
    return best_id


class CivicIntelligenceEngine:
    """Multilingual rules-based parser and classifier for municipal complaints."""

    VOCABULARY: Dict[str, List[str]] = {
        "WASTE_MANAGEMENT": [
            "waste", "garbage", "trash", "uncollected garbage", "overflowing dustbin", "refuse", "bin overflow",
            "kachra", "kooda", "kachre ka dher", "safai nahi hui", "dustbin overflow", "gandagi",
            "kuppai", "kuppaikkoodu", "குப்பை", "குப்பைத்தொட்டி", "கழிவு", "कचरा", "कूड़ा",
        ],
        "WATER_SUPPLY": [
            "water supply", "drinking water", "pipe leak", "water pipe burst", "low pressure", "no water",
            "dirty water", "contaminated water", "borewell", "tanker", "water line", "pipeline burst",
            "peene ka paani", "paani ki line", "paani nahi aa raha", "paani ka pressure kam",
            "kudineer", "thanni vara villai", "kuzhai udaindhadhu", "குடிநீர்", "தண்ணீர் வரவில்லை", "குழாய் கசிவு",
            "पानी नहीं", "पीने का पानी",
        ],
        "ROADS_INFRASTRUCTURE": [
            "pothole", "crater", "road damage", "road broken", "asphalt", "caved in road", "sinkhole", "footpath broken",
            "gaddha", "sadak toot gayi", "sadak kharab", "sadak dhas gayi", "potholes",
            "pallam", "saalai setham", "saalai pallam", "பள்ளம்", "சாலை சேதம்", "गड्ढा", "सड़क टूटी",
        ],
        "DRAINAGE_SANITATION": [
            "drain", "blocked drain", "choked drain", "drainage", "stormwater drain", "culvert blocked",
            "gutter", "silt", "desilting", "sewage", "sewer overflow", "manhole overflow", "manhole overflowing",
            "waterlogging", "inundation", "standing water", "knee deep water", "waist deep", "submerged",
            "flooding", "subway flooded", "subway", "underpass",
            "naala", "nala jaam", "nala band", "sewer ubaal", "jalbharav", "paani bhar gaya", "pani bhara",
            "vadikaal", "vadikaal adaipu", "kaalvaai adaipu", "saakkadai", "neer thekkam", "vella neer",
            "வடிகால் அடைப்பு", "சாக்கடை", "நீர் தேக்கம்", "வெள்ள நீர்", "வெள்ளம்", "नाला", "जलभराव", "गंदा पानी",
        ],
        "STREETLIGHTS_ELECTRICITY": [
            "streetlight", "street light", "lamp post", "dark road", "street lights off", "pole light not working",
            "flickering light", "batti gul", "street light band", "bulb fused", "andhera hai",
            "theru vilakku", "vilakku eriyavillai", "தெரு விளக்கு", "மின்விளக்கு", "स्ट्रीट लाइट",
        ],
        "POWER_SUPPLY": [
            "power cut", "electricity", "transformer", "power outage", "low voltage", "voltage fluctuation",
            "live wire", "hanging wire", "wire loose", "sparking", "bijli gul", "light cut", "current nahi hai",
            "minsaram", "current cut", "current illai", "min kambi", "மின்சாரம்", "மின் கம்பி", "बिजली",
        ],
        "PUBLIC_ASSETS": [
            "bus stand", "bus shelter", "broken railing", "park bench", "public toilet",
            "traffic signal broken", "park maintenance", "community hall", "playground",
            "bus stop toot gaya", "park kharab", "railing toot gayi",
            "perundhu nilayam", "poonga", "நிழற்குடை", "பூங்கா", "पार्क",
        ],
        "ILLEGAL_DUMPING": [
            "illegal dumping", "construction debris", "debris dumped", "rubble", "hazardous waste dump", "dumping",
            "malba", "sadak par malba", "illegal kachra", "kattida kazhivu", "கட்டிட கழிவு", "मलबा",
        ],
        "OTHER": [
            "stray animals", "stray dog", "noise pollution", "encroachment", "tree fallen", "branch fallen",
            "ped gir gaya", "shor", "maram vilundhadhu", "மரம் விழுந்தது",
        ],
    }

    SUBCATEGORY_RULES: List[Tuple[str, str, List[str]]] = [
        ("DRAINAGE_SANITATION", "Road / subway flooding", ["subway", "underpass", "suranga"]),
        ("DRAINAGE_SANITATION", "Sewer overflow", ["sewage", "sewer", "manhole", "saakkadai", "சாக்கடை", "ganda paani", "गंदा पानी"]),
        ("DRAINAGE_SANITATION", "Blocked drain", ["blocked drain", "choked drain", "silt", "nala jaam", "adaipu", "नाला जाम", "culvert"]),
        ("DRAINAGE_SANITATION", "Waterlogging", ["standing water", "waterlogging", "inundation", "jalbharav", "thekkam", "bhar gaya", "தேக்கம்", "जलभराव"]),
        ("ROADS_INFRASTRUCTURE", "Pothole / road damage", ["pothole", "crater", "gaddha", "pallam", "பள்ளம்", "गड्ढा"]),
        ("ROADS_INFRASTRUCTURE", "Road collapse / sinkhole", ["sinkhole", "caved", "dhas gayi"]),
        ("WATER_SUPPLY", "Pipeline leak / burst", ["leak", "burst", "kasivu", "கசிவு", "udaindhadhu"]),
        ("WATER_SUPPLY", "No supply / low pressure", ["no water", "low pressure", "nahi aa raha", "vara villai", "வரவில்லை", "पानी नहीं"]),
        ("WATER_SUPPLY", "Contaminated water", ["dirty water", "contaminated", "smell"]),
        ("WASTE_MANAGEMENT", "Missed collection", ["uncollected", "not collected", "safai nahi", "missed"]),
        ("WASTE_MANAGEMENT", "Overflowing bin", ["overflow", "dustbin", "bin"]),
        ("POWER_SUPPLY", "Exposed / live wire", ["live wire", "hanging wire", "sparking", "min kambi"]),
        ("POWER_SUPPLY", "Outage", ["power cut", "outage", "bijli gul", "current cut", "current illai"]),
    ]

    SEVERE_HAZARD_TERMS: List[str] = [
        "open manhole", "manhole khula", "khula manhole", "manhole open", "manhole lid missing",
        "live wire", "hanging wire", "wire sparking", "electric shock", "bijli ka taar",
        "ambulance stuck", "hospital access blocked", "life threatening",
        "vehicle trapped", "people trapped", "sinkhole", "road caved in", "child fell",
        "உயிருக்கு ஆபத்து", "ஆபத்தான மின்கம்பி", "திறந்த மேன்ஹோல்",
    ]

    HIGH_SEVERITY_TERMS: List[str] = [
        "submerged", "underpass closed", "subway closed", "knee deep", "waist deep", "ambulance",
        "doob gaya", "gaadi phansi", "phansi", "feet deep", "3 feet", "2 feet", "trapped",
        "major leak", "entire area dark", "total blackout", "வெள்ளம் சூழ்ந்தது", "சிக்கியுள்ளன",
    ]

    MODERATE_TERMS: List[str] = [
        "heavy", "overflowing", "blocked", "standing water", "jam", "bad", "pothole", "dark", "no water",
        "days", "again", "smell",
    ]

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Strips control characters and markup from untrusted text; caps length."""
        if not text:
            return ""
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        cleaned = re.sub(r"<[^>]*>", "", cleaned)
        cleaned = re.sub(r"(.)\1{10,}", r"\1\1\1", cleaned)
        return cleaned.strip()[:1000]

    @classmethod
    def detect_language(cls, text: str) -> str:
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "Tamil (தமிழ்)"
        if re.search(r"[\u0900-\u097F]", text):
            return "Hindi (हिन्दी)"
        lower = text.lower()
        hinglish = ["paani", "pani", "bhara", "gaya", "naala", "sadak", "kachra", "badboo", "neeche", "hai", "bijli", "gaddha", "nahi"]
        if any(re.search(rf"\b{w}\b", lower) for w in hinglish):
            return "Hinglish / Hindi (Romanized)"
        tamil_roman = ["thanni", "vella", "vadikaal", "adaipu", "thekkam", "saalai", "kuppai", "kudineer", "vilakku"]
        if any(w in lower for w in tamil_roman):
            return "Tamil (Romanized)"
        return "English"

    @classmethod
    def normalize_category(cls, raw: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Maps a user-supplied category label to (canonical_code, subcategory). Returns (None, None) if unknown."""
        if not raw or not str(raw).strip():
            return None, None
        code = re.sub(r"[^A-Z0-9]+", "_", str(raw).strip().upper()).strip("_")
        if code in CANONICAL_CATEGORIES:
            return code, None
        if code in LEGACY_CATEGORY_MAP:
            return LEGACY_CATEGORY_MAP[code]
        for kw, canonical in _CATEGORY_KEYWORDS:
            if kw in code:
                return canonical, str(raw).strip()[:100]
        return None, None

    @classmethod
    def _subcategory(cls, category: str, lower: str) -> Optional[str]:
        for cat, sub, terms in cls.SUBCATEGORY_RULES:
            if cat == category and any(t in lower for t in terms):
                return sub
        return None

    @classmethod
    def classify_complaint(cls, raw_text: str) -> Dict[str, Any]:
        """Keyword-scored category, subcategory, operational severity heuristic and hazard flag."""
        sanitized = cls.sanitize_input(raw_text)
        lower = sanitized.lower()
        detected_lang = cls.detect_language(sanitized)

        category_scores: Dict[str, int] = {}
        matched_keywords: List[str] = []
        for category, vocab in cls.VOCABULARY.items():
            score = 0
            for term in vocab:
                if term in lower:
                    score += 3 if len(term.split()) > 1 else 1
                    matched_keywords.append(term)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            classification_method = "KEYWORD_RULES"
        else:
            best_category = "OTHER"
            classification_method = "NO_KEYWORD_MATCH"

        is_severe_hazard = any(term in lower for term in cls.SEVERE_HAZARD_TERMS)

        severity = 3
        if is_severe_hazard or any(t in lower for t in cls.HIGH_SEVERITY_TERMS):
            severity = 5
        elif any(t in lower for t in cls.MODERATE_TERMS):
            severity = 4
        elif any(t in lower for t in ("little", "minor", "puddle", "small")):
            severity = 2

        subcategory = cls._subcategory(best_category, lower)
        label = CATEGORY_LABELS.get(best_category, best_category)
        summary = f"{label}{' — ' + subcategory if subcategory else ''} ({detected_lang}); operational severity {severity}/5"
        if is_severe_hazard:
            summary += "; possible immediate safety hazard"

        return {
            "sanitized_text": sanitized,
            "detected_language": detected_lang,
            "issue_category": best_category,
            "subcategory": subcategory,
            "severity_score": severity,
            "is_severe_hazard": is_severe_hazard,
            "matched_keywords": sorted(set(matched_keywords)),
            "classification_method": classification_method,
            "parsed_summary": summary,
        }

    @classmethod
    def match_landmark(cls, *texts: Optional[str]) -> Optional[Tuple[float, float, str, str]]:
        for text in texts:
            if not text:
                continue
            lower = text.lower()
            for key, value in LANDMARK_COORDINATES.items():
                if key in lower:
                    return value
        return None

    @classmethod
    def resolve_location(
        cls,
        text: str,
        landmark: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        zone_id: Optional[str] = None,
        zones: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Resolves location without inventing it. Priority: supplied coordinates, then gazetteer landmark
        match (landmark field, then text), then a supplied zone without coordinates. Unresolved fields are None.
        """
        zones = zones or []
        zone_ids = {z["id"] for z in zones}
        if lat is not None and lon is not None:
            resolved_zone = zone_id if zone_id in zone_ids else nearest_zone(lat, lon, zones)
            return {
                "lat": lat, "lon": lon, "zone_id": resolved_zone, "landmark": landmark,
                "method": "PROVIDED_COORDINATES" + ("" if zone_id in zone_ids else "+NEAREST_ZONE_CENTROID"),
            }
        match = cls.match_landmark(landmark, text)
        if match:
            m_lat, m_lon, m_zone, m_name = match
            return {"lat": m_lat, "lon": m_lon, "zone_id": m_zone, "landmark": m_name, "method": "GAZETTEER_LANDMARK"}
        if zone_id in zone_ids:
            return {"lat": None, "lon": None, "zone_id": zone_id, "landmark": landmark, "method": "ZONE_ONLY"}
        return {"lat": None, "lon": None, "zone_id": None, "landmark": landmark, "method": "UNRESOLVED"}

    @classmethod
    def resolve_landmark_and_coordinates(cls, text: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """Gazetteer-only lookup. Returns Nones when nothing matches."""
        match = cls.match_landmark(text)
        if not match:
            return None, None, None, None
        return match
