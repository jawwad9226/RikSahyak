"""
AI Location Learning System
Automatically learns alternative location names and improves search suggestions
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
import logging
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# File path for AI learning data
LEARNING_DATA_FILE = Path(__file__).parent.parent / "data" / "location_learning.json"


class LocationLearningSystem:
    """
    AI system that learns:
    1. User search patterns
    2. Alternative names for locations
    3. Common typos and corrections
    4. Popular location sequences
    """
    
    def __init__(self):
        self.searches: Dict = {}  # Track user searches
        self.alternatives: Dict = {}  # Learn alternative names
        self.corrections: Dict = {}  # Learn typo corrections
        self.sequences: Dict = {}  # Learn popular routes
        self.load_learning_data()
    
    def load_learning_data(self):
        """Load previously learned data"""
        if LEARNING_DATA_FILE.exists():
            try:
                with open(LEARNING_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.searches = data.get('searches', {})
                    self.alternatives = data.get('alternatives', {})
                    self.corrections = data.get('corrections', {})
                    self.sequences = data.get('sequences', {})
                    logger.info("Loaded previous learning data")
            except Exception as e:
                logger.error(f"Error loading learning data: {e}")
    
    def save_learning_data(self):
        """Save learned data for future use"""
        try:
            LEARNING_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'searches': self.searches,
                'alternatives': self.alternatives,
                'corrections': self.corrections,
                'sequences': self.sequences,
                'last_updated': datetime.now().isoformat(),
            }
            with open(LEARNING_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved learning data")
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def learn_search(self, user_query: str, matched_location_id: str, location_name: str):
        """
        Learn from successful search matches
        
        Example:
        - User searches "railway stn" → matches "malkapur_station"
        - AI learns: "railway stn" is alternative for station
        """
        query_lower = user_query.lower().strip()
        
        # Track search frequency
        if matched_location_id not in self.searches:
            self.searches[matched_location_id] = {}
        
        self.searches[matched_location_id][query_lower] = self.searches[matched_location_id].get(query_lower, 0) + 1
        
        # Learn as alternative name if not exact match
        if query_lower != location_name.lower():
            if matched_location_id not in self.alternatives:
                self.alternatives[matched_location_id] = []
            
            if query_lower not in self.alternatives[matched_location_id]:
                self.alternatives[matched_location_id].append(query_lower)
                logger.info(f"Learned new alternative: '{query_lower}' → '{location_name}'")
        
        self.save_learning_data()
    
    def learn_correction(self, typo: str, correct_location_id: str):
        """
        Learn from typo corrections
        
        Example:
        - User types "hospitl" → corrected to "hospital"
        - AI learns: "hospitl" should map to hospital
        """
        typo_lower = typo.lower().strip()
        
        if typo_lower not in self.corrections:
            self.corrections[typo_lower] = {
                'correct_location_id': correct_location_id,
                'count': 0,
            }
        
        self.corrections[typo_lower]['count'] += 1
        logger.info(f"Learned correction: '{typo}' → location '{correct_location_id}'")
        self.save_learning_data()
    
    def learn_route_sequence(self, from_location: str, to_location: str):
        """
        Learn popular routes (for suggestions)
        
        Example:
        - Many users travel "station" → "bus stand"
        - AI suggests "bus stand" when user books from station
        """
        route_key = f"{from_location}→{to_location}"
        
        if route_key not in self.sequences:
            self.sequences[route_key] = 0
        
        self.sequences[route_key] += 1
        logger.info(f"Learned route: {route_key} (count: {self.sequences[route_key]})")
        self.save_learning_data()
    
    def get_learned_alternatives(self, location_id: str) -> List[str]:
        """Get all learned alternative names for a location"""
        return self.alternatives.get(location_id, [])
    
    def find_correction(self, user_input: str, threshold: float = 0.7) -> Optional[str]:
        """
        Find correction for typos using string similarity
        
        Args:
            user_input: User's search query
            threshold: Similarity threshold (0.7 = 70% match)
        
        Returns:
            Corrected location ID if found
        """
        user_input_lower = user_input.lower().strip()
        
        # Direct match in corrections
        if user_input_lower in self.corrections:
            return self.corrections[user_input_lower]['correct_location_id']
        
        # Fuzzy match for typos
        best_match = None
        best_score = threshold
        
        for typo, data in self.corrections.items():
            similarity = SequenceMatcher(None, user_input_lower, typo).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = data['correct_location_id']
        
        return best_match
    
    def get_route_suggestions(self, from_location: str, limit: int = 3) -> List[tuple]:
        """
        Get suggested destinations from a location based on popularity
        
        Returns: List of (to_location, count) tuples
        """
        suggestions = []
        
        for route_key, count in sorted(self.sequences.items(), key=lambda x: x[1], reverse=True):
            if route_key.startswith(f"{from_location}→"):
                to_location = route_key.split("→")[1]
                suggestions.append((to_location, count))
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    def get_statistics(self) -> Dict:
        """Get statistics about what the AI has learned"""
        total_searches = sum(
            sum(queries.values()) for queries in self.searches.values()
        )
        
        total_alternatives = sum(
            len(alts) for alts in self.alternatives.values()
        )
        
        total_corrections = sum(
            data['count'] for data in self.corrections.values()
        )
        
        return {
            'total_searches': total_searches,
            'total_alternative_names': total_alternatives,
            'total_typo_corrections': total_corrections,
            'popular_routes': len(self.sequences),
            'locations_learned': len(self.alternatives),
        }


# Global instance
location_ai = LocationLearningSystem()


def log_search_interaction(user_query: str, matched_location_id: str, location_name: str):
    """Public function to log search interactions"""
    location_ai.learn_search(user_query, matched_location_id, location_name)


def log_typo_correction(typo: str, correct_location_id: str):
    """Public function to log typo corrections"""
    location_ai.learn_correction(typo, correct_location_id)


def log_route_taken(from_location: str, to_location: str):
    """Public function to log route usage"""
    location_ai.learn_route_sequence(from_location, to_location)


def get_suggested_destinations(from_location: str) -> List[str]:
    """Get suggestions for next destination"""
    suggestions = location_ai.get_route_suggestions(from_location)
    return [location for location, _ in suggestions]


def get_ai_statistics() -> Dict:
    """Get AI learning statistics"""
    return location_ai.get_statistics()
