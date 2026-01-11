"""
Malkapur Locations Database with Landmarks and Alternative Names
This database grows with AI learning - new alternatives are added automatically
"""

from typing import List, Dict, Tuple
from pydantic import BaseModel

class LocationInfo(BaseModel):
    """Location with coordinates, landmarks, and alternative names"""
    id: str
    primary_name: str
    coordinates: Tuple[float, float]  # (latitude, longitude)
    street_name: str
    landmark: str
    category: str  # 'station', 'market', 'hospital', 'bus_stand', 'landmark'
    description: str
    nearby_streets: List[str]
    alternative_names: List[str]  # AI learns these
    search_count: int = 0  # Track popularity
    ai_learned: bool = False


# Base Malkapur Locations Database
MALKAPUR_LOCATIONS: Dict[str, LocationInfo] = {
    "malkapur_station": LocationInfo(
        id="malkapur_station",
        primary_name="Malkapur Railway Station",
        coordinates=(20.8845, 76.2010),
        street_name="Station Road",
        landmark="Central Railway Station",
        category="station",
        description="Main railway station in Malkapur",
        nearby_streets=["Station Road", "Railway Square", "Platform Road"],
        alternative_names=[
            "malkapur station",
            "railway station",
            "station",
            "ry stn",
            "central station",
            "malkapur railway",
            "train station",
            "railway",
            "railve stn",
            "mk station",
        ],
    ),
    "civil_lines": LocationInfo(
        id="civil_lines",
        primary_name="Civil Lines",
        coordinates=(20.8900, 76.2100),
        street_name="Civil Road",
        landmark="Civil Administrative Area",
        category="landmark",
        description="Administrative and residential area",
        nearby_streets=["Civil Road", "Government Road", "Admin Circle"],
        alternative_names=[
            "civil lines",
            "civil",
            "civil area",
            "government area",
            "admin area",
            "civil district",
        ],
    ),
    "bus_stand": LocationInfo(
        id="bus_stand",
        primary_name="Malkapur Bus Stand",
        coordinates=(20.8820, 76.2080),
        street_name="Bus Stand Road",
        landmark="Central Bus Depot",
        category="bus_stand",
        description="Main public transportation hub",
        nearby_streets=["Bus Stand Road", "Transport Road", "Depot Road"],
        alternative_names=[
            "bus stand",
            "bus station",
            "central bus stand",
            "malkapur bus",
            "bus depot",
            "transport hub",
            "bus terminal",
        ],
    ),
    "malkapur_hospital": LocationInfo(
        id="malkapur_hospital",
        primary_name="Malkapur City Hospital",
        coordinates=(20.8950, 76.2150),
        street_name="Hospital Road",
        landmark="Primary Health Center",
        category="hospital",
        description="Main hospital in Malkapur",
        nearby_streets=["Hospital Road", "Medical Lane", "Health Street"],
        alternative_names=[
            "hospital",
            "malkapur hospital",
            "city hospital",
            "health center",
            "medical center",
            "clinic",
            "dispensary",
            "civil hospital",
            "government hospital",
            "sarkari hospital",
        ],
    ),
    "malkapur_market": LocationInfo(
        id="malkapur_market",
        primary_name="Malkapur Market",
        coordinates=(20.8870, 76.2000),
        street_name="Market Street",
        landmark="Central Market Square",
        category="market",
        description="Main shopping and trading area",
        nearby_streets=["Market Street", "Shop Lane", "Commercial Road"],
        alternative_names=[
            "market",
            "malkapur market",
            "central market",
            "shopping area",
            "bazaar",
            "market square",
            "commercial area",
        ],
    ),
    "old_bus_stand": LocationInfo(
        id="old_bus_stand",
        primary_name="Old Bus Stand",
        coordinates=(20.8835, 76.2055),
        street_name="Old Bus Stand Road",
        landmark="Old Transport Depot",
        category="bus_stand",
        description="Former bus stand area",
        nearby_streets=["Old Stand Road", "Transport Circle"],
        alternative_names=["old bus stand", "old stand", "purana bus stand"],
    ),
    "new_bus_stand": LocationInfo(
        id="new_bus_stand",
        primary_name="New Bus Stand",
        coordinates=(20.8815, 76.2095),
        street_name="New Stand Road",
        landmark="Modern Bus Terminal",
        category="bus_stand",
        description="New bus terminal",
        nearby_streets=["New Terminal Road", "Highway Circle"],
        alternative_names=["new bus stand", "new stand", "naya bus stand"],
    ),
    "college_road": LocationInfo(
        id="college_road",
        primary_name="College Road",
        coordinates=(20.8920, 76.2070),
        street_name="College Road",
        landmark="Educational Area",
        category="landmark",
        description="College and education area",
        nearby_streets=["College Road", "Education Lane", "Student Road"],
        alternative_names=["college road", "college", "college area", "education area"],
    ),
    "old_market": LocationInfo(
        id="old_market",
        primary_name="Old Market",
        coordinates=(20.8855, 76.1985),
        street_name="Old Market Road",
        landmark="Traditional Market",
        category="market",
        description="Old traditional market",
        nearby_streets=["Old Market Road", "Bazaar Lane"],
        alternative_names=["old market", "purana market", "old bazaar"],
    ),
    "sadar_bazaar": LocationInfo(
        id="sadar_bazaar",
        primary_name="Sadar Bazaar",
        coordinates=(20.8880, 76.2015),
        street_name="Sadar Road",
        landmark="Sadar Shopping Area",
        category="market",
        description="Sadar market area",
        nearby_streets=["Sadar Road", "Main Market"],
        alternative_names=["sadar bazaar", "sadar market", "sadar"],
    ),
    "police_station": LocationInfo(
        id="police_station",
        primary_name="Malkapur Police Station",
        coordinates=(20.8890, 76.2040),
        street_name="Police Line",
        landmark="City Police Station",
        category="landmark",
        description="Main police station",
        nearby_streets=["Police Line", "Thana Road"],
        alternative_names=["police station", "thana", "police chowki"],
    ),
    "post_office": LocationInfo(
        id="post_office",
        primary_name="Post Office",
        coordinates=(20.8865, 76.2025),
        street_name="Post Office Road",
        landmark="Main Post Office",
        category="landmark",
        description="Central post office",
        nearby_streets=["Post Office Road", "Dak Ghar Road"],
        alternative_names=["post office", "dak ghar", "postal"],
    ),
    "tahsil_office": LocationInfo(
        id="tahsil_office",
        primary_name="Tahsil Office",
        coordinates=(20.8895, 76.2085),
        street_name="Tahsil Road",
        landmark="Revenue Office",
        category="landmark",
        description="Tahsil administrative office",
        nearby_streets=["Tahsil Road", "Revenue Circle"],
        alternative_names=["tahsil", "tahsil office", "revenue office"],
    ),
    "temple_road": LocationInfo(
        id="temple_road",
        primary_name="Temple Road",
        coordinates=(20.8910, 76.2030),
        street_name="Temple Road",
        landmark="Religious Area",
        category="landmark",
        description="Temple area",
        nearby_streets=["Temple Road", "Mandir Road"],
        alternative_names=["temple road", "mandir road", "temple area"],
    ),
}


def get_location_by_id(location_id: str) -> LocationInfo:
    """Get location by ID"""
    return MALKAPUR_LOCATIONS.get(location_id)


def get_location_by_name(name: str) -> LocationInfo:
    """
    Get location by searching through primary names and alternatives
    Used by AI learning system
    """
    search_name = name.lower().strip()
    
    for location in MALKAPUR_LOCATIONS.values():
        # Check primary name
        if location.primary_name.lower() == search_name:
            return location
        
        # Check alternatives
        for alt_name in location.alternative_names:
            if alt_name.lower() == search_name:
                return location
    
    return None


def add_alternative_name(location_id: str, alt_name: str, ai_learned: bool = True):
    """
    Add alternative name to location (learned by AI)
    
    Args:
        location_id: ID of the location
        alt_name: New alternative name
        ai_learned: Mark if this was learned by AI
    """
    if location_id in MALKAPUR_LOCATIONS:
        location = MALKAPUR_LOCATIONS[location_id]
        
        # Avoid duplicates
        if alt_name.lower() not in [a.lower() for a in location.alternative_names]:
            location.alternative_names.append(alt_name.lower())
            location.ai_learned = True
            location.search_count += 1


def get_all_locations() -> Dict[str, LocationInfo]:
    """Get all locations"""
    return MALKAPUR_LOCATIONS


def increment_search_count(location_id: str):
    """Track popular searches for AI learning"""
    if location_id in MALKAPUR_LOCATIONS:
        MALKAPUR_LOCATIONS[location_id].search_count += 1


def get_popular_locations(limit: int = 5) -> List[LocationInfo]:
    """Get most searched locations (for smart suggestions)"""
    locations = list(MALKAPUR_LOCATIONS.values())
    sorted_locations = sorted(locations, key=lambda x: x.search_count, reverse=True)
    return sorted_locations[:limit]


def export_locations_json():
    """Export locations for frontend use"""
    return {
        location_id: {
            "id": location.id,
            "primary_name": location.primary_name,
            "coordinates": list(location.coordinates),
            "street_name": location.street_name,
            "landmark": location.landmark,
            "category": location.category,
            "description": location.description,
            "nearby_streets": location.nearby_streets,
            "alternative_names": location.alternative_names,
        }
        for location_id, location in MALKAPUR_LOCATIONS.items()
    }
