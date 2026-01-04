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
