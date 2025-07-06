import math
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from models.state import State
from models.quiz import QuizResult
from utils.data_loader import data_loader

class MatchingService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_compatibility_score(self, user_traits: Dict[str, float], state_traits: Tuple) -> float:
        """Calculate compatibility score between user and state using optimized algorithm"""
        # State traits tuple: (id, name, country, racionalidade, conservadorismo, audacia, autoridade, coletivismo, influencia)
        state_values = {
            'racionalidade': state_traits[3],
            'conservadorismo': state_traits[4],
            'audacia': state_traits[5],
            'autoridade': state_traits[6],
            'coletivismo': state_traits[7],
            'influencia': state_traits[8]
        }
        
        # Calculate Euclidean distance
        distance_squared = 0
        for trait in ['racionalidade', 'conservadorismo', 'audacia', 'autoridade', 'coletivismo', 'influencia']:
            diff = user_traits[trait] - state_values[trait]
            distance_squared += diff * diff
        
        distance = math.sqrt(distance_squared)
        
        # Convert distance to compatibility score (0-100)
        max_distance = math.sqrt(6 * 10 * 10)  # Maximum possible distance
        compatibility = max(0, 100 - (distance / max_distance * 100))
        
        return round(compatibility, 2)
    
    def find_best_matches(self, user_traits: Dict[str, float], limit: int = 10) -> List[Tuple[int, float]]:
        """Find best matching states for user traits using optimized algorithm"""
        # Get cached state data for fast processing
        available_states = data_loader.get_optimized_state_data(self.db)
        
        # Calculate compatibility scores
        matches = []
        for state_data in available_states:
            score = self.calculate_compatibility_score(user_traits, state_data)
            matches.append((state_data[0], score))  # (state_id, score)
        
        # Sort by compatibility score (descending) and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def get_random_compatible_state(self, quiz_result: QuizResult) -> State:
        """Get a random state from top compatible matches"""
        user_traits = {
            'racionalidade': quiz_result.racionalidade,
            'conservadorismo': quiz_result.conservadorismo,
            'audacia': quiz_result.audacia,
            'autoridade': quiz_result.autoridade,
            'coletivismo': quiz_result.coletivismo,
            'influencia': quiz_result.influencia
        }
        
        # Get top 20 matches for better randomization
        best_matches = self.find_best_matches(user_traits, limit=20)
        
        if not best_matches:
            raise ValueError("No available states found")
        
        # Select randomly from top matches with weighted probability
        import random
        weights = [match[1] for match in best_matches]  # Use compatibility scores as weights
        selected_match = random.choices(best_matches, weights=weights)[0]
        
        # Get the actual state object
        state = self.db.query(State).filter(
            State.id == selected_match[0],
            State.is_occupied == False
        ).first()
        
        if not state:
            raise ValueError("Selected state is no longer available")
        
        return state
    
    def assign_state_to_user(self, state: State, user_id: int) -> State:
        """Assign a state to a user"""
        if state.is_occupied:
            raise ValueError("State is already occupied")
        
        state.is_occupied = True
        state.manager_id = user_id
        
        self.db.commit()
        self.db.refresh(state)
        
        # Invalidate cache since state availability changed
        data_loader.invalidate_cache()
        
        return state
    
    def release_state_from_user(self, user_id: int) -> bool:
        """Release a state from a user (for rerolls)"""
        state = self.db.query(State).filter(State.manager_id == user_id).first()
        
        if state:
            state.is_occupied = False
            state.manager_id = None
            self.db.commit()
            
            # Invalidate cache
            data_loader.invalidate_cache()
            return True
        
        return False
