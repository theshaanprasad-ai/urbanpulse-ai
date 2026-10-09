"""
Deterministic seed data and geographic fixtures for UrbanPulse AI.
Grounds the application in authentic Chennai municipal geography across all 9 civic categories,
statistical temporal anomaly records (MAD, Poisson), cross-category pattern hypotheses,
and dual operational queues (Emerging Patterns vs Immediate Hazards).
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.schema import (
    City, AdministrativeZone, VulnerableAsset, RainfallObservation,
    RainfallForecast, OfficialWarning, HistoricalWaterloggingRecord,
    CivicComplaint, HotspotCluster, DataSourceStatus, ClimateScenario,
    ComplaintCategoryConfig, TemporalAnomalyRecord, CrossCategoryPatternRecord,
    DecisionAction, ActionAuditLog
)

CHENNAI_ZONES = [
    {"id": "chennai-zone-01", "num": 1, "name": "Thiruvottiyur", "lat": 13.1610, "lon": 80.3010, "elev": 3.2, "imperv": 0.72, "drain": 1.6, "vuln": 0.75, "pop": 320000},
    {"id": "chennai-zone-02", "num": 2, "name": "Manali", "lat": 13.1670, "lon": 80.2600, "elev": 4.1, "imperv": 0.65, "drain": 1.4, "vuln": 0.70, "pop": 210000},
    {"id": "chennai-zone-03", "num": 3, "name": "Madhavaram", "lat": 13.1480, "lon": 80.2310, "elev": 5.5, "imperv": 0.68, "drain": 1.7, "vuln": 0.60, "pop": 280000},
    {"id": "chennai-zone-04", "num": 4, "name": "Tondiarpet", "lat": 13.1280, "lon": 80.2870, "elev": 3.8, "imperv": 0.88, "drain": 2.0, "vuln": 0.80, "pop": 390000},
    {"id": "chennai-zone-05", "num": 5, "name": "Royapuram", "lat": 13.1110, "lon": 80.2940, "elev": 4.0, "imperv": 0.92, "drain": 2.1, "vuln": 0.70, "pop": 420000},
    {"id": "chennai-zone-06", "num": 6, "name": "Thiru Vi Ka Nagar", "lat": 13.1090, "lon": 80.2450, "elev": 5.0, "imperv": 0.85, "drain": 1.8, "vuln": 0.85, "pop": 460000},
    {"id": "chennai-zone-07", "num": 7, "name": "Ambattur", "lat": 13.1140, "lon": 80.1540, "elev": 14.5, "imperv": 0.75, "drain": 1.9, "vuln": 0.55, "pop": 480000},
    {"id": "chennai-zone-08", "num": 8, "name": "Anna Nagar", "lat": 13.0850, "lon": 80.2100, "elev": 12.0, "imperv": 0.80, "drain": 2.3, "vuln": 0.45, "pop": 490000},
    {"id": "chennai-zone-09", "num": 9, "name": "Teynampet (T. Nagar)", "lat": 13.0420, "lon": 80.2450, "elev": 7.5, "imperv": 0.92, "drain": 2.2, "vuln": 0.88, "pop": 520000},
    {"id": "chennai-zone-10", "num": 10, "name": "Kodambakkam", "lat": 13.0520, "lon": 80.2210, "elev": 8.0, "imperv": 0.86, "drain": 2.0, "vuln": 0.82, "pop": 510000},
    {"id": "chennai-zone-11", "num": 11, "name": "Valasaravakkam", "lat": 13.0400, "lon": 80.1740, "elev": 9.5, "imperv": 0.78, "drain": 1.7, "vuln": 0.65, "pop": 340000},
    {"id": "chennai-zone-12", "num": 12, "name": "Alandur", "lat": 13.0030, "lon": 80.2010, "elev": 11.0, "imperv": 0.82, "drain": 1.9, "vuln": 0.60, "pop": 310000},
    {"id": "chennai-zone-13", "num": 13, "name": "Adyar", "lat": 13.0010, "lon": 80.2560, "elev": 4.5, "imperv": 0.79, "drain": 2.4, "vuln": 0.78, "pop": 390000},
    {"id": "chennai-zone-14", "num": 14, "name": "Perungudi (Velachery / Madipakkam)", "lat": 12.9710, "lon": 80.2240, "elev": 3.4, "imperv": 0.84, "drain": 1.5, "vuln": 0.95, "pop": 430000},
    {"id": "chennai-zone-15", "num": 15, "name": "Sholinganallur (OMR IT Corridor)", "lat": 12.8980, "lon": 80.2280, "elev": 3.9, "imperv": 0.76, "drain": 1.3, "vuln": 0.90, "pop": 380000},
]

VULNERABLE_ASSETS = [
    {"id": "asset-sub-01", "zone": "chennai-zone-04", "name": "Vyasarpadi Subway", "type": "SUBWAY", "lat": 13.1160, "lon": 80.2612, "elev": 2.1, "thresh": 35.0, "desc": "Chronic subway underpass connecting North Chennai; water pump failure leads to >1.5m flooding within 40 minutes."},
    {"id": "asset-sub-02", "zone": "chennai-zone-04", "name": "Ganesapuram Subway", "type": "SUBWAY", "lat": 13.1023, "lon": 80.2644, "elev": 2.3, "thresh": 40.0, "desc": "Critical railway subway linking Vyasarpadi and Basin Bridge; frequent vehicular stranding."},
    {"id": "asset-sub-03", "zone": "chennai-zone-09", "name": "Duraisamy Subway, T. Nagar", "type": "SUBWAY", "lat": 13.0410, "lon": 80.2325, "elev": 4.5, "thresh": 45.0, "desc": "Vital transit link between East and West T. Nagar; automated pumps prone to debris choking."},
    {"id": "asset-sub-04", "zone": "chennai-zone-09", "name": "Madley Subway, T. Nagar", "type": "SUBWAY", "lat": 13.0375, "lon": 80.2310, "elev": 4.8, "thresh": 45.0, "desc": "Major traffic artery connecting T. Nagar bus terminus to Saidapet."},
    {"id": "asset-sub-05", "zone": "chennai-zone-12", "name": "Thillai Ganga Nagar Subway", "type": "SUBWAY", "lat": 12.9984, "lon": 80.1970, "elev": 6.2, "thresh": 50.0, "desc": "Nanganallur underpass prone to storm runoff accumulation from GST Road."},
    {"id": "asset-pump-01", "zone": "chennai-zone-14", "name": "Velachery Lake Sluice & Pumping Station", "type": "PUMPING_STATION", "lat": 12.9815, "lon": 80.2180, "elev": 3.0, "thresh": 60.0, "desc": "Drains catchment runoff from southern suburbs into Pallikaranai marshland."},
    {"id": "asset-outfall-01", "zone": "chennai-zone-15", "name": "Okkiyam Maduvu Canal Outfall", "type": "CANAL_OUTFALL", "lat": 12.9230, "lon": 80.2330, "elev": 2.8, "thresh": 55.0, "desc": "Primary southern discharge channel draining Pallikaranai marsh to Buckingham canal."},
    {"id": "asset-hosp-01", "zone": "chennai-zone-06", "name": "Kilpauk Govt Medical College & Hospital", "type": "HOSPITAL", "lat": 13.0780, "lon": 80.2420, "elev": 8.0, "thresh": 75.0, "desc": "Tier-1 trauma and disaster response healthcare hub; ambulance access must remain unhindered."},
    {"id": "asset-hosp-02", "zone": "chennai-zone-10", "name": "Kalaignar Centenary Super Specialty Hospital", "type": "HOSPITAL", "lat": 13.0150, "lon": 80.2200, "elev": 7.5, "thresh": 70.0, "desc": "Major hospital located in Adyar river floodplain vicinity; high patient transit volume."},
]

CATEGORY_CONFIGS = [
    {
        "id": "cat-waste",
        "code": "WASTE_MANAGEMENT",
        "name": "Waste Accumulation & Solid Waste",
        "description": "Uncollected commercial or domestic garbage, overflowing community bins, litter piles on pedestrian pathways.",
        "dept": "Solid Waste Management Dept",
        "sla": 24,
        "baseline": 4.5,
        "weight": 1.0,
        "icon": "Trash2"
    },
    {
        "id": "cat-water",
        "code": "WATER_SUPPLY",
        "name": "Water Supply & Distribution Network",
        "description": "Drinking water pipeline ruptures, zero pressure at household lines, contamination, tanker delivery delays.",
        "dept": "Chennai Metro Water (CMWSSB)",
        "sla": 12,
        "baseline": 3.0,
        "weight": 1.2,
        "icon": "Droplets"
    },
    {
        "id": "cat-roads",
        "code": "ROADS_INFRASTRUCTURE",
        "name": "Roads, Potholes & Transit Surface",
        "description": "Potholes, asphalt road subsidence, crater formation, damaged road medians, broken pedestrian footpaths.",
        "dept": "GCC Bus Route Roads & Bridges Dept",
        "sla": 48,
        "baseline": 3.8,
        "weight": 1.1,
        "icon": "Construction"
    },
    {
        "id": "cat-drainage",
        "code": "DRAINAGE_SANITATION",
        "name": "Drainage, Sewage & Flood Discharges",
        "description": "Stormwater drain silt choking, sewer manhole overflowing, localized waterlogging, stagnant wastewater.",
        "dept": "Storm Water Drainage & Sanitation Dept",
        "sla": 12,
        "baseline": 4.2,
        "weight": 1.3,
        "icon": "Waves"
    },
    {
        "id": "cat-streetlights",
        "code": "STREETLIGHTS_ELECTRICITY",
        "name": "Public Lighting & Street Illumination",
        "description": "Dark road corridors, unlit sodium/LED street poles, faulty automated daylight sensors, flickering fixtures.",
        "dept": "Electrical & Public Lighting Dept",
        "sla": 18,
        "baseline": 2.5,
        "weight": 0.9,
        "icon": "Lightbulb"
    },
    {
        "id": "cat-power",
        "code": "POWER_SUPPLY",
        "name": "Power Supply & Electrical Grid",
        "description": "Distribution transformer sparks, feeder line trips, low voltage fluctuations, dangling overhead cables.",
        "dept": "TANGEDCO Distribution Operations",
        "sla": 6,
        "baseline": 2.0,
        "weight": 1.4,
        "icon": "Zap"
    },
    {
        "id": "cat-assets",
        "code": "PUBLIC_ASSETS",
        "name": "Public Amenities & Civic Infrastructure",
        "description": "Damaged bus passenger shelters, vandalized park benches, dysfunctional public conveniences, perimeter railings.",
        "dept": "Parks, Playgrounds & Public Amenities Dept",
        "sla": 72,
        "baseline": 1.5,
        "weight": 0.8,
        "icon": "Landmark"
    },
    {
        "id": "cat-dumping",
        "code": "ILLEGAL_DUMPING",
        "name": "Illegal Dumping & Debris Obstruction",
        "description": "Unauthorized night dumping of construction debris (C&D waste), hazardous industrial slurry, sidewalk blockades.",
        "dept": "GCC Vigilance & Waste Enforcement Cell",
        "sla": 24,
        "baseline": 1.2,
        "weight": 1.1,
        "icon": "AlertTriangle"
    },
    {
        "id": "cat-other",
        "code": "OTHER",
        "name": "General Grievances & Unclassified Issues",
        "description": "Miscellaneous civic grievances, public nuisance, stray animal pack reports, civic helpline escalations.",
        "dept": "Public Grievance Redressal Cell",
        "sla": 48,
        "baseline": 1.0,
        "weight": 0.7,
        "icon": "HelpCircle"
    }
]

COMPLAINTS_SEED = [
    # Category 1: WASTE_MANAGEMENT (Zone 9 T. Nagar Surge)
    {
        "tracking": "GCC-2026-WM-001",
        "text": "Ranganathan street commercial corridor is overwhelmed with garbage. Two community bins are overflowing onto footpaths.",
        "lang": "English", "cat": "WASTE_MANAGEMENT", "sub": "Commercial Garbage Pile", "sev": 4, "hazard": False,
        "lat": 13.0402, "lon": 80.2335, "landmark": "Ranganathan Street", "zone": "chennai-zone-09"
    },
    {
        "tracking": "GCC-2026-WM-002",
        "text": "T. Nagar Usman Road flyover ke neeche kachre ka dher laga hai. Teen din se safai nahi hui, bohot badboo hai.",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "WASTE_MANAGEMENT", "sub": "Uncollected Refuse", "sev": 4, "hazard": False,
        "lat": 13.0390, "lon": 80.2340, "landmark": "Usman Road Flyover", "zone": "chennai-zone-09"
    },
    {
        "tracking": "GCC-2026-WM-003",
        "text": "தி.நகர் பனகல் பூங்கா அருகில் குப்பைகள் அள்ளப்படாமல் சாலையோரங்களில் குவிந்து கிடக்கிறது.",
        "lang": "Tamil (தமிழ்)", "cat": "WASTE_MANAGEMENT", "sub": "Public Park Waste", "sev": 3, "hazard": False,
        "lat": 13.0415, "lon": 80.2315, "landmark": "Panagal Park, T. Nagar", "zone": "chennai-zone-09"
    },
    {
        "tracking": "GCC-2026-WM-004",
        "text": "Plastic waste and commercial carton packaging dumped near stormwater drain inlets on Pondy Bazaar.",
        "lang": "English", "cat": "WASTE_MANAGEMENT", "sub": "Inlet Blockade", "sev": 4, "hazard": False,
        "lat": 13.0425, "lon": 80.2360, "landmark": "Pondy Bazaar", "zone": "chennai-zone-09"
    },

    # Category 2: WATER_SUPPLY (Zone 10 Kodambakkam & Zone 14 Velachery)
    {
        "tracking": "GCC-2026-WS-001",
        "text": "Underground drinking water main pipeline burst on Arcot Road near power loom junction. High pressure drinking water flooding street.",
        "lang": "English", "cat": "WATER_SUPPLY", "sub": "Distribution Pipeline Burst", "sev": 4, "hazard": False,
        "lat": 13.0515, "lon": 80.2205, "landmark": "Arcot Road Junction", "zone": "chennai-zone-10"
    },
    {
        "tracking": "GCC-2026-WS-002",
        "text": "Velachery 100 Feet Road me pichle do din se peene ka paani nahi aa raha. Metro water pipeline me koi supply nahi hai.",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "WATER_SUPPLY", "sub": "No Water Supply", "sev": 3, "hazard": False,
        "lat": 12.9805, "lon": 80.2195, "landmark": "Velachery 100 Feet Road", "zone": "chennai-zone-14"
    },
    {
        "tracking": "GCC-2026-WS-003",
        "text": "வேளச்சேரி விஜயநகர் பகுதியில் குடிநீர் குழாயில் சாக்கடை நீர் கலந்து துர்நாற்றத்துடன் வருகிறது.",
        "lang": "Tamil (தமிழ்)", "cat": "WATER_SUPPLY", "sub": "Sewage Contamination", "sev": 5, "hazard": True,
        "lat": 12.9790, "lon": 80.2170, "landmark": "Vijayanagar Junction", "zone": "chennai-zone-14"
    },

    # Category 3: ROADS_INFRASTRUCTURE (Zone 8 Anna Nagar & Zone 12 Alandur)
    {
        "tracking": "GCC-2026-RD-001",
        "text": "Huge pothole crater on Anna Nagar 2nd Avenue near roundtana. Multiple two-wheelers skidding daily.",
        "lang": "English", "cat": "ROADS_INFRASTRUCTURE", "sub": "Arterial Road Crater", "sev": 4, "hazard": False,
        "lat": 13.0845, "lon": 80.2110, "landmark": "Anna Nagar Roundtana", "zone": "chennai-zone-08"
    },
    {
        "tracking": "GCC-2026-RD-002",
        "text": "Kathipara junction service road par 3 bade gaddhe ho gaye hain. Gadiyon ka traffic buri tarah ruk gaya hai.",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "ROADS_INFRASTRUCTURE", "sub": "Service Road Degradation", "sev": 4, "hazard": False,
        "lat": 13.0067, "lon": 80.2053, "landmark": "Kathipara Junction", "zone": "chennai-zone-12"
    },
    {
        "tracking": "GCC-2026-RD-003",
        "text": "ஆலந்தூர் ஜி.எஸ்.டி சாலையில் தார் பெயர்ந்து ஆழமான பள்ளங்கள் ஏற்பட்டு விபத்து அபாயம் உள்ளது.",
        "lang": "Tamil (தமிழ்)", "cat": "ROADS_INFRASTRUCTURE", "sub": "Asphalt Subsidence", "sev": 3, "hazard": False,
        "lat": 13.0020, "lon": 80.2005, "landmark": "Alandur GST Road", "zone": "chennai-zone-12"
    },

    # Category 4: DRAINAGE_SANITATION (Zone 14 Perungudi / Velachery & Zone 4 Tondiarpet)
    {
        "tracking": "GCC-2026-DS-001",
        "text": "Stormwater drain along Velachery Main Road is completely choked with silt and plastic debris. Runoff ponding on carriage way.",
        "lang": "English", "cat": "DRAINAGE_SANITATION", "sub": "SWD Silt Choking", "sev": 4, "hazard": False,
        "lat": 12.9818, "lon": 80.2182, "landmark": "Velachery Main Road", "zone": "chennai-zone-14"
    },
    {
        "tracking": "GCC-2026-DS-002",
        "text": "வேளச்சேரி ஏரி நிரம்பி பிரதான சாலையில் கழிவுநீருடன் மழைநீர் பெருக்கெடுத்து ஓடுகிறது.",
        "lang": "Tamil (தமிழ்)", "cat": "DRAINAGE_SANITATION", "sub": "Canal Overflow", "sev": 4, "hazard": False,
        "lat": 12.9825, "lon": 80.2178, "landmark": "Velachery Lake Buffer", "zone": "chennai-zone-14"
    },
    {
        "tracking": "GCC-2026-DS-003",
        "text": "Tondiarpet High Road me sewer line block ho gayi hai. Manhole se ganda badboodar paani nikal kar sadak par beh raha hai.",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "DRAINAGE_SANITATION", "sub": "Sewer Manhole Overflow", "sev": 4, "hazard": False,
        "lat": 13.1275, "lon": 80.2865, "landmark": "Tondiarpet High Road", "zone": "chennai-zone-04"
    },

    # Category 5: STREETLIGHTS_ELECTRICITY (Zone 5 Royapuram Surge)
    {
        "tracking": "GCC-2026-SL-001",
        "text": "Entire stretch of Royapuram coastal road has pitch dark streetlights for 800 meters. Major safety hazard for pedestrians.",
        "lang": "English", "cat": "STREETLIGHTS_ELECTRICITY", "sub": "Feeder Dark Corridor", "sev": 4, "hazard": False,
        "lat": 13.1115, "lon": 80.2935, "landmark": "Royapuram Coastal Road", "zone": "chennai-zone-05"
    },
    {
        "tracking": "GCC-2026-SL-002",
        "text": "Royapuram market gali me 6 street lights band hain. Raat ko bohot andhera rehta hai aur chori ka darr hai.",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "STREETLIGHTS_ELECTRICITY", "sub": "Market Lane Blackout", "sev": 3, "hazard": False,
        "lat": 13.1105, "lon": 80.2950, "landmark": "Royapuram Market", "zone": "chennai-zone-05"
    },
    {
        "tracking": "GCC-2026-SL-003",
        "text": "ராயபுரம் மெயின் ரோட்டில் உள்ள மின்விளக்கு கம்பத்தில் விளக்குகள் ஒளிரவில்லை, தொடர் இருள் சூழ்ந்துள்ளது.",
        "lang": "Tamil (தமிழ்)", "cat": "STREETLIGHTS_ELECTRICITY", "sub": "Pole Lamp Failure", "sev": 3, "hazard": False,
        "lat": 13.1120, "lon": 80.2942, "landmark": "Royapuram Main Road", "zone": "chennai-zone-05"
    },

    # Category 6: POWER_SUPPLY (Zone 7 Ambattur)
    {
        "tracking": "GCC-2026-PS-001",
        "text": "Ambattur industrial estate distribution transformer sparking intermittently during evening peak load.",
        "lang": "English", "cat": "POWER_SUPPLY", "sub": "Transformer Arcing", "sev": 4, "hazard": False,
        "lat": 13.1135, "lon": 80.1535, "landmark": "Ambattur Industrial Estate", "zone": "chennai-zone-07"
    },

    # Category 7: PUBLIC_ASSETS (Zone 8 Anna Nagar)
    {
        "tracking": "GCC-2026-PA-001",
        "text": "Bus passenger shelter roof damaged and collapsed partly near Anna Nagar West depot.",
        "lang": "English", "cat": "PUBLIC_ASSETS", "sub": "Transit Shelter Structural Damage", "sev": 3, "hazard": False,
        "lat": 13.0860, "lon": 80.2085, "landmark": "Anna Nagar West Depot", "zone": "chennai-zone-08"
    },

    # Category 8: ILLEGAL_DUMPING (Zone 15 Sholinganallur)
    {
        "tracking": "GCC-2026-ID-001",
        "text": "Trucks dumping construction debris and concrete rubble directly along the Okkiyam Maduvu canal buffer zone at night.",
        "lang": "English", "cat": "ILLEGAL_DUMPING", "sub": "C&D Waste Dumping", "sev": 4, "hazard": False,
        "lat": 12.9235, "lon": 80.2325, "landmark": "Okkiyam Maduvu Canal Outfall", "zone": "chennai-zone-15"
    },

    # Category 9: OTHER (Zone 6 Thiru Vi Ka Nagar)
    {
        "tracking": "GCC-2026-OT-001",
        "text": "Heavy tree branch broken and hanging precariously over footpath near Perambur railway station.",
        "lang": "English", "cat": "OTHER", "sub": "Arboricultural Hazard", "sev": 3, "hazard": False,
        "lat": 13.1082, "lon": 80.2442, "landmark": "Perambur Railway Station", "zone": "chennai-zone-06"
    },

    # HIGH-SEVERITY IMMEDIATE HAZARDS (Queue B Triage)
    {
        "tracking": "GCC-2026-HZ-001",
        "text": "CRITICAL: Live sparking electrical wire fell near bus stop in Royapuram! Wire sparking on ground next to pedestrians, severe life-threatening electric shock danger!",
        "lang": "English", "cat": "POWER_SUPPLY", "sub": "Live Hanging Wire", "sev": 5, "hazard": True,
        "lat": 13.1118, "lon": 80.2945, "landmark": "Royapuram Bus Stop", "zone": "chennai-zone-05"
    },
    {
        "tracking": "GCC-2026-HZ-002",
        "text": "EMERGENCY: Open 5-foot uncovered manhole near school in Anna Nagar! Lid is completely missing, children walking on waterlogged street, deadly accident hazard!",
        "lang": "English", "cat": "DRAINAGE_SANITATION", "sub": "Uncovered Manhole", "sev": 5, "hazard": True,
        "lat": 13.0855, "lon": 80.2105, "landmark": "Anna Nagar School Zone", "zone": "chennai-zone-08"
    },
    {
        "tracking": "GCC-2026-HZ-003",
        "text": "Vyasarpadi subway ke neeche 4 feet paani bhar gaya hai, ambulance phansi hui hai aur emergency patient andar hai! Pumps nahi chal rahe!",
        "lang": "Hinglish / Hindi (Romanized)", "cat": "DRAINAGE_SANITATION", "sub": "Ambulance Stranded in Subway", "sev": 5, "hazard": True,
        "lat": 13.1160, "lon": 80.2612, "landmark": "Vyasarpadi Subway", "zone": "chennai-zone-04"
    }
]

HISTORICAL_WATERLOGGING = [
    {"loc": "Velachery Main Road & AGS Colony", "zone": "chennai-zone-14", "lat": 12.9820, "lon": 80.2190, "date": "Dec 2023 (Cyclone Michaung)", "rain": 468.0, "depth": 110.0, "disc": "Residential inundation exceeding 1 meter; boats deployed by NDRF."},
    {"loc": "Madipakkam Kuberan Nagar", "zone": "chennai-zone-14", "lat": 12.9640, "lon": 80.1980, "date": "Nov 2021 Monsoon Depression", "rain": 215.0, "depth": 85.0, "disc": "Lake overflow breached earthen bund; 3-day road disconnection."},
    {"loc": "T. Nagar Bazullah Road & GN Chetty Rd", "zone": "chennai-zone-09", "lat": 13.0430, "lon": 80.2390, "date": "Nov 2021 Monsoon Depression", "rain": 180.0, "depth": 65.0, "disc": "Commercial shopping hub completely inundated; Mambalam canal backflow."},
    {"loc": "Vyasarpadi Ganesapuram Subway", "zone": "chennai-zone-04", "lat": 13.1023, "lon": 80.2644, "date": "Annual Recurring Event (2015-2023)", "rain": 85.0, "depth": 150.0, "disc": "Subway submerged to roof level; traffic closed by Greater Chennai Traffic Police."},
    {"loc": "Jafferkhanpet Adyar River Bank", "zone": "chennai-zone-10", "lat": 13.0290, "lon": 80.2045, "date": "Dec 2015 Chennai Mega-Flood", "rain": 345.0, "depth": 180.0, "disc": "Adyar river overtopped retaining wall; severe residential first-floor flooding."},
    {"loc": "Otteri Nullah Channel Corridor", "zone": "chennai-zone-06", "lat": 13.0910, "lon": 80.2520, "date": "Dec 2023 (Cyclone Michaung)", "rain": 390.0, "depth": 90.0, "disc": "Silt sedimentation caused backwater ponding across Perambur and Purasawalkam."},
]


def _seed_reference(db: Session):
    """Geography and configuration rows the app cannot operate without.

    Each block is flushed before dependent tables are populated: the ORM maps
    these links as scalar foreign keys rather than relationships, so a single
    commit of everything at once can order child inserts ahead of their parents.
    """
    if not db.query(City).filter(City.id == "chennai").first():
        db.add(City(
            id="chennai",
            name="Chennai",
            state="Tamil Nadu",
            center_lat=13.0827,
            center_lon=80.2707,
            zoom_level=11,
            boundary_bbox=[12.85, 80.12, 13.25, 80.34],
            drainage_network_type="4 River Basins (Adyar, Cooum, Kosasthalaiyar, Kovalam) & Buckingham Canal",
            population=7100000
        ))
    if not db.query(City).filter(City.id == "bengaluru").first():
        db.add(City(
            id="bengaluru",
            name="Bengaluru",
            state="Karnataka",
            center_lat=12.9716,
            center_lon=77.5946,
            zoom_level=11,
            boundary_bbox=[12.80, 77.45, 13.15, 77.75],
            drainage_network_type="3 Major Valleys (Koramangala-Challaghatta, Hebbal, Vrishabhavathi)",
            population=11500000
        ))
    db.flush()

    known_zones = {z.id for z in db.query(AdministrativeZone.id).all()}
    for z in CHENNAI_ZONES:
        if z["id"] in known_zones:
            continue
        d_lat, d_lon = 0.015, 0.015
        poly = {
            "type": "Polygon",
            "coordinates": [[
                [z["lon"] - d_lon, z["lat"] - d_lat],
                [z["lon"] + d_lon, z["lat"] - d_lat],
                [z["lon"] + d_lon, z["lat"] + d_lat],
                [z["lon"] - d_lon, z["lat"] + d_lat],
                [z["lon"] - d_lon, z["lat"] - d_lat]
            ]]
        }
        db.add(AdministrativeZone(
            id=z["id"],
            city_id="chennai",
            zone_number=z["num"],
            name=z["name"],
            center_lat=z["lat"],
            center_lon=z["lon"],
            boundary_geojson=poly,
            mean_elevation_m=z["elev"],
            impervious_fraction=z["imperv"],
            drainage_density_km_per_sqkm=z["drain"],
            historical_flood_vulnerability=z["vuln"],
            population=z["pop"]
        ))
    db.flush()

    known_categories = {c[0] for c in db.query(ComplaintCategoryConfig.code).all()}
    for c in CATEGORY_CONFIGS:
        if c["code"] in known_categories:
            continue
        db.add(ComplaintCategoryConfig(
            id=c["id"],
            code=c["code"],
            name=c["name"],
            description=c["description"],
            target_department=c["dept"],
            default_sla_hours=c["sla"],
            baseline_rate_per_day=c["baseline"],
            severity_weight=c["weight"],
            icon_name=c["icon"],
            is_active=True
        ))

    if not db.query(VulnerableAsset).filter(VulnerableAsset.city_id == "chennai").first():
        for a in VULNERABLE_ASSETS:
            db.add(VulnerableAsset(
                id=a["id"],
                city_id="chennai",
                zone_id=a["zone"],
                name=a["name"],
                asset_type=a["type"],
                lat=a["lat"],
                lon=a["lon"],
                elevation_m=a["elev"],
                critical_threshold_mm=a["thresh"],
                description=a["desc"]
            ))

    if not db.query(HistoricalWaterloggingRecord).filter(
            HistoricalWaterloggingRecord.city_id == "chennai").first():
        for h in HISTORICAL_WATERLOGGING:
            db.add(HistoricalWaterloggingRecord(
                city_id="chennai",
                zone_id=h["zone"],
                location_name=h["loc"],
                lat=h["lat"],
                lon=h["lon"],
                event_date=h["date"],
                rainfall_amount_mm=h["rain"],
                flood_depth_cm=h["depth"],
                disruption_type=h["disc"],
                source_citation="Greater Chennai Corporation Historical Inundation Atlas (2015-2023)"
            ))

    if not db.query(ClimateScenario).filter(ClimateScenario.city_id == "chennai").first():
        for s in [
            ("chennai-hist", "chennai", "Historical Baseline (1985-2014)", "1985-2014 Reference", 0.0, 1.0, 4, 0.0),
            ("chennai-ssp245-2050", "chennai", "CMIP6 SSP2-4.5 (Moderate Emissions)", "2040-2060 Mid-Century", 7.4, 1.38, 7, 16.5),
            ("chennai-ssp585-2050", "chennai", "CMIP6 SSP5-8.5 (High Emissions)", "2040-2060 Mid-Century", 14.8, 1.85, 11, 28.2),
            ("chennai-ssp585-2080", "chennai", "CMIP6 SSP5-8.5 (Late-Century Extreme)", "2070-2099 Late-Century", 22.1, 2.45, 14, 45.0)
        ]:
            db.add(ClimateScenario(
                id=s[0],
                city_id=s[1],
                scenario_name=s[2],
                time_horizon=s[3],
                projected_annual_rainfall_change_pct=s[4],
                extreme_rainfall_frequency_multiplier=s[5],
                vulnerable_ward_count=s[6],
                projected_runoff_increase_pct=s[7],
                data_source_citation="INDRA-CMIP6 Downscaled Ensemble for Tamil Nadu Urban Basins"
            ))

    if not db.query(DataSourceStatus).first():
        for s_id, s_name, cat, stat, rec_cnt, cov, lic in [
            ("src-gcc-civic", "Greater Chennai Corporation Namma Chennai 1913", "COMPLAINTS", "HEALTHY", 24, "Multilingual grievance stream across 9 categories", "Municipal Public Data Portal"),
            ("src-imd-aws", "IMD Automatic Weather Station Network", "WEATHER", "HEALTHY", 12, "5 City AWS stations synced every 15 mins", "Open Government Data (OGD)"),
            ("src-imd-nwp", "IMD NCMRWF 4km NWP Forecast Grid", "WEATHER", "HEALTHY", 1, "24h/72h ensemble numerical weather predictions", "IMD Open Weather Services"),
            ("src-bhuvan", "ISRO NRSC Bhuvan Flood Inundation Maps", "GEOSPATIAL", "HEALTHY", 6, "Historical flood footprints & low elevation DEM", "ISRO Bhuvan Open Data"),
            ("src-indra", "INDRA-CMIP6 Peninsular India Climate Downscaling", "CLIMATE", "HEALTHY", 4, "High-resolution SSP2-4.5 & SSP5-8.5 projections", "CC-BY 4.0 Academic Research"),
        ]:
            db.add(DataSourceStatus(
                id=s_id,
                source_name=s_name,
                category=cat,
                status=stat,
                last_successful_sync=datetime.utcnow() - timedelta(minutes=5),
                records_count=rec_cnt,
                coverage_details=cov,
                license_type=lic,
                citation="Official Portal Synchronization"
            ))
    db.flush()


def _seed_demo(db: Session):
    """Synthetic complaint/anomaly fixtures used for demonstrations.

    Skipped entirely once real records exist so a live deployment never mixes
    fabricated history into operator queues.
    """
    real_records = db.query(CivicComplaint.id).filter(
        CivicComplaint.provenance != "SYNTHETIC_DEMO").first()
    if real_records:
        return
    if db.query(CivicComplaint.id).filter(
            CivicComplaint.provenance == "SYNTHETIC_DEMO").first():
        return

    now = datetime.utcnow()

    # 6. Rainfall Observations (Contextual signal)
    stations = [
        ("AWS-NUNG", "Nungambakkam Regional Met Centre", 13.0670, 80.2430, "chennai-zone-09", 18.5, 42.0, 78.5),
        ("AWS-MEEN", "Meenambakkam Airport Met Station", 12.9880, 80.1770, "chennai-zone-12", 22.0, 58.0, 94.0),
        ("AWS-SHOL", "Sholinganallur AWS (OMR Corridor)", 12.8980, 80.2280, "chennai-zone-15", 26.5, 64.0, 112.0),
        ("AWS-TARA", "Taramani Science City AWS", 12.9860, 80.2430, "chennai-zone-14", 28.0, 68.5, 118.0),
        ("AWS-ENNR", "Ennore Coastal Port Gauge", 13.2000, 80.3200, "chennai-zone-01", 14.0, 35.0, 62.0),
    ]
    for s_id, s_name, lat, lon, z_id, r1, r3, r24 in stations:
        obs = RainfallObservation(
            city_id="chennai",
            zone_id=z_id,
            station_id=s_id,
            station_name=s_name,
            timestamp=now - timedelta(minutes=15),
            rainfall_1h_mm=r1,
            rainfall_3h_mm=r3,
            rainfall_24h_mm=r24,
            source="IMD Automatic Weather Station Telemetry",
            provenance="SYNTHETIC_DEMO"
        )
        db.add(obs)

    # 7. Rainfall Forecast
    forecast = RainfallForecast(
        city_id="chennai",
        zone_id="chennai-zone-14",
        valid_from=now,
        valid_to=now + timedelta(hours=24),
        forecast_6h_mm=55.0,
        forecast_24h_mm=135.0,
        forecast_72h_mm=210.0,
        model_name="IMD-NCMRWF Unified High-Resolution Model (4km)",
        source="India Meteorological Department Numerical Weather Prediction",
        provenance="SYNTHETIC_DEMO"
    )
    db.add(forecast)

    # 8. Official Warning
    warning = OfficialWarning(
        city_id="chennai",
        warning_level="ORANGE",
        issuing_authority="India Meteorological Department (RMC Chennai)",
        issued_at=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=22),
        headline="Heavy to Very Heavy Rainfall Alert for Chennai Metropolitan Area",
        description="Depression over Southwest Bay of Bengal bringing localized heavy spells over coastal taluks.",
        recommended_actions="Municipal teams to monitor low-lying areas and critical subways.",
        source_url="https://mausam.imd.gov.in/chennai"
    )
    db.add(warning)

    # 9. Civic Complaints across categories
    for idx, c in enumerate(COMPLAINTS_SEED, start=1):
        complaint = CivicComplaint(
            city_id="chennai",
            zone_id=c["zone"],
            tracking_number=c["tracking"],
            raw_text=c["text"],
            parsed_summary=f"[{c['cat']}] {c['sub']} - Reported via {c['lang']}",
            language_detected=c["lang"],
            issue_category=c["cat"],
            subcategory=c.get("sub"),
            severity_score=c["sev"],
            is_severe_hazard=c.get("hazard", False),
            lat=c["lat"],
            lon=c["lon"],
            landmark=c["landmark"],
            reported_at=now - timedelta(minutes=idx * 18),
            status="OPEN",
            source="CITIZEN_APP",
            provenance="SYNTHETIC_DEMO"
        )
        db.add(complaint)

    # 10. Temporal Anomaly Records (MAD + Poisson testing)
    anomalies = [
        {
            "zone": "chennai-zone-09",
            "cat": "WASTE_MANAGEMENT",
            "obs": 28, "base": 4.5, "mad": 4.12, "p": 0.0003, "ratio": 6.22,
            "type": "SUSTAINED_INCREASE", "sig": "SIGNIFICANT_P01",
            "expl": "Significant sustained volume surge in Zone 9 (T. Nagar): 28 reports vs baseline 4.5. MAD Modified Z-score = 4.12, Poisson p=0.0003."
        },
        {
            "zone": "chennai-zone-14",
            "cat": "DRAINAGE_SANITATION",
            "obs": 19, "base": 4.2, "mad": 3.65, "p": 0.0018, "ratio": 4.52,
            "type": "ONE_TIME_SPIKE", "sig": "SIGNIFICANT_P01",
            "expl": "Sharp one-time spike in Zone 14 (Velachery/Perungudi): 19 complaints vs baseline 4.2. MAD Z-score = 3.65, Poisson p=0.0018."
        },
        {
            "zone": "chennai-zone-05",
            "cat": "STREETLIGHTS_ELECTRICITY",
            "obs": 14, "base": 2.5, "mad": 3.42, "p": 0.0035, "ratio": 5.60,
            "type": "NEW_RARE_ISSUE", "sig": "SIGNIFICANT_P01",
            "expl": "New dark corridor cluster in Zone 5 (Royapuram): 14 consecutive outages along 800m coastal stretch. MAD Z-score = 3.42."
        },
        {
            "zone": "chennai-zone-10",
            "cat": "WATER_SUPPLY",
            "obs": 12, "base": 3.0, "mad": 2.85, "p": 0.0120, "ratio": 4.00,
            "type": "SUSTAINED_INCREASE", "sig": "SIGNIFICANT_P05",
            "expl": "Elevated pipeline rupture complaints in Zone 10 (Kodambakkam): 12 reports vs baseline 3.0. Poisson p=0.012."
        },
        {
            "zone": "chennai-zone-08",
            "cat": "ROADS_INFRASTRUCTURE",
            "obs": 10, "base": 3.8, "mad": 2.15, "p": 0.0450, "ratio": 2.63,
            "type": "WEAK_SIGNAL", "sig": "ELEVATED_HEURISTIC",
            "expl": "Emerging pothole reporting in Zone 8 (Anna Nagar): 10 reports vs baseline 3.8. Change-point indicates weak emerging signal."
        }
    ]
    for a in anomalies:
        anom = TemporalAnomalyRecord(
            city_id="chennai",
            zone_id=a["zone"],
            category_code=a["cat"],
            time_window="DAILY",
            observed_count=a["obs"],
            expected_baseline=a["base"],
            mad_z_score=a["mad"],
            poisson_p_value=a["p"],
            magnitude_ratio=a["ratio"],
            anomaly_type=a["type"],
            statistical_significance=a["sig"],
            detection_method="Robust MAD + Poisson Dispersion",
            data_coverage_pct=92.5,
            explanation_text=a["expl"],
            detected_at=now - timedelta(minutes=25)
        )
        db.add(anom)

    # 11. Cross-Category Patterns
    patterns = [
        {
            "zone": "chennai-zone-14",
            "cat_a": "WASTE_MANAGEMENT",
            "cat_b": "DRAINAGE_SANITATION",
            "cnt": 7, "dist": 320.0, "hours": 18, "corr": 0.84,
            "hyp": "Correlated breakdown hypothesis: Commercial waste piles at street intersections co-occur with downstream stormwater drain choking within 320m. Candidate hypothesis for joint municipal desilting and waste clearance."
        },
        {
            "zone": "chennai-zone-10",
            "cat_a": "WATER_SUPPLY",
            "cat_b": "ROADS_INFRASTRUCTURE",
            "cnt": 5, "dist": 150.0, "hours": 24, "corr": 0.79,
            "hyp": "Underground pipeline rupture leaking pressurized water into road subgrade, correlating with accelerated asphalt cratering within 150m. Recommended joint MetroWater and Road Dept repair."
        }
    ]
    for p in patterns:
        pat = CrossCategoryPatternRecord(
            city_id="chennai",
            zone_id=p["zone"],
            category_a=p["cat_a"],
            category_b=p["cat_b"],
            co_occurrence_count=p["cnt"],
            temporal_window_hours=p["hours"],
            geographic_proximity_meters=p["dist"],
            correlation_coefficient=p["corr"],
            hypothesis_text=p["hyp"],
            supporting_complaint_ids=[1, 2, 4, 11, 12],
            detected_at=now - timedelta(minutes=40)
        )
        db.add(pat)

    # 12. Hotspot Cluster
    hotspot = HotspotCluster(
        city_id="chennai",
        zone_id="chennai-zone-09",
        cluster_name="T. Nagar Commercial Hub",
        category_code="WASTE_MANAGEMENT",
        center_lat=13.0410,
        center_lon=80.2335,
        radius_meters=350.0,
        complaint_count=4,
        baseline_normal_count=0.7,
        anomaly_ratio=5.7,
        status="EMERGING",
        detection_timestamp=now - timedelta(minutes=15),
        rainfall_evidence="4 complaints within 350m in past 3 hours; baseline exceeded by 570%"
    )
    db.add(hotspot)

    # 13. Dual Operational Queue Actions
    actions = [
        # Queue A: Emerging Patterns
        {
            "queue": "EMERGING_PATTERN_QUEUE",
            "zone": "chennai-zone-09",
            "cat": "WASTE_MANAGEMENT",
            "dept": "Solid Waste Management Dept",
            "type": "DEPLOY_MECHANIZED_SWEEPERS",
            "score": 88.5, "rank": 1,
            "loc": "T. Nagar Ranganathan St & Pondy Bazaar",
            "desc": "Deploy 4 mechanical sweepers and double tipper rounds across Ranganathan St commercial corridor. Baseline exceeded by 520%.",
            "evidence": "Statistically validated anomaly: MAD Z-score 4.12, Poisson p=0.0003 with 28 complaints in 24 hours.",
            "status": "PENDING_REVIEW"
        },
        {
            "queue": "EMERGING_PATTERN_QUEUE",
            "zone": "chennai-zone-14",
            "cat": "DRAINAGE_SANITATION",
            "dept": "Storm Water Drainage & Sanitation Dept",
            "type": "CROSS_DEPARTMENT_DESILTING",
            "score": 84.0, "rank": 2,
            "loc": "Velachery Main Road Buffer",
            "desc": "Dispatch combined sanitation and SWD team for joint inlet desilting along Velachery Main Road buffer.",
            "evidence": "Cross-category co-occurrence: 7 co-located incidents of uncollected waste and drain choking (r=0.84 within 320m).",
            "status": "PENDING_REVIEW"
        },
        {
            "queue": "EMERGING_PATTERN_QUEUE",
            "zone": "chennai-zone-05",
            "cat": "STREETLIGHTS_ELECTRICITY",
            "dept": "Electrical & Public Lighting Dept",
            "type": "FEEDER_CIRCUIT_INSPECTION",
            "score": 76.5, "rank": 3,
            "loc": "Royapuram Coastal Road",
            "desc": "Mobilize lighting division line repair team to inspect 1.2km stretch of Royapuram feeder circuit.",
            "evidence": "Temporal surge: 14 unlit pole grievances logged along single electrical feeder circuit.",
            "status": "PENDING_REVIEW"
        },
        # Queue B: High-Severity Immediate Hazards
        {
            "queue": "HIGH_SEVERITY_HAZARD_QUEUE",
            "zone": "chennai-zone-05",
            "cat": "POWER_SUPPLY",
            "dept": "TANGEDCO Distribution Operations",
            "type": "EMERGENCY_POWER_ISOLATION",
            "score": 98.0, "rank": 1,
            "loc": "Royapuram Bus Stop",
            "desc": "IMMEDIATE: Disconnect feeder line and deploy emergency line crew for live dangling wire at Royapuram bus stand.",
            "evidence": "Urgent life-safety hazard: Citizen verified live sparking 440V overhead conductor touching pavement near commuters.",
            "status": "PENDING_REVIEW"
        },
        {
            "queue": "HIGH_SEVERITY_HAZARD_QUEUE",
            "zone": "chennai-zone-08",
            "cat": "DRAINAGE_SANITATION",
            "dept": "Storm Water Drainage & Sanitation Dept",
            "type": "EMERGENCY_MANHOLE_BARRICADE",
            "score": 95.0, "rank": 2,
            "loc": "Anna Nagar School Zone",
            "desc": "IMMEDIATE: Place barricade and install heavy-duty ductile iron manhole cover outside Anna Nagar school.",
            "evidence": "Critical pedestrian hazard: 5-foot uncovered manhole on active school pedestrian route.",
            "status": "PENDING_REVIEW"
        },
        {
            "queue": "HIGH_SEVERITY_HAZARD_QUEUE",
            "zone": "chennai-zone-04",
            "cat": "DRAINAGE_SANITATION",
            "dept": "Storm Water Drainage & Sanitation Dept",
            "type": "SUBWAY_DEWATERING_AND_RESCUE",
            "score": 94.0, "rank": 3,
            "loc": "Vyasarpadi Subway",
            "desc": "IMMEDIATE: Deploy high-capacity 50HP mobile diesel pump and rescue tow unit to clear Vyasarpadi subway.",
            "evidence": "Life hazard: Ambulance stranded in 4 feet water with critical patient onboard; stationary pumps non-operational.",
            "status": "PENDING_REVIEW"
        }
    ]
    for act_data in actions:
        action = DecisionAction(
            city_id="chennai",
            zone_id=act_data["zone"],
            queue_type=act_data["queue"],
            category_code=act_data["cat"],
            target_department=act_data["dept"],
            action_type=act_data["type"],
            priority_score=act_data["score"],
            priority_rank=act_data["rank"],
            location_name=act_data["loc"],
            description=act_data["desc"],
            evidence_basis=act_data["evidence"],
            status=act_data["status"],
            updated_at=now
        )
        db.add(action)

    # 14/15. Data source registry and climate scenarios live in reference seeding.
    db.commit()


def _reset_demo(db: Session):
    db.query(ActionAuditLog).delete()
    db.query(DecisionAction).delete()
    db.query(CrossCategoryPatternRecord).delete()
    db.query(TemporalAnomalyRecord).delete()
    db.query(ComplaintCategoryConfig).delete()
    db.query(ClimateScenario).delete()
    db.query(DataSourceStatus).delete()
    db.query(HotspotCluster).delete()
    db.query(CivicComplaint).delete()
    db.query(HistoricalWaterloggingRecord).delete()
    db.query(OfficialWarning).delete()
    db.query(RainfallForecast).delete()
    db.query(RainfallObservation).delete()
    db.query(VulnerableAsset).delete()
    db.query(AdministrativeZone).delete()
    db.query(City).delete()
    db.commit()


def seed_database(db: Session, force_reset: bool = False, include_demo: bool = True):
    """Populates reference geography/configuration, then optional demo fixtures."""
    if force_reset:
        _reset_demo(db)
    _seed_reference(db)
    if include_demo:
        _seed_demo(db)
    db.commit()
