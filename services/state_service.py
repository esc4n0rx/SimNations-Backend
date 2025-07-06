from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.state import State
from models.country import Country
from models.user import User
from models.quiz import QuizResult
from schemas.state_schema import StateResponse, StateMatchResponse, StateAssignmentResponse
from services.matching_service import MatchingService
from config.settings import settings

class StateService:
    def __init__(self, db: Session):
        self.db = db
        self.matching_service = MatchingService(db)
    
    def get_available_states_count(self) -> int:
        """Get count of available states"""
        return self.db.query(State).filter(State.is_occupied == False).count()
    
    def get_states_by_country(self, country_name: str) -> List[StateResponse]:
        """Get all states from a specific country"""
        states = self.db.query(State).join(Country).filter(
            Country.name == country_name
        ).all()
        
        return [self._state_to_response(state) for state in states]
    
    def get_user_state(self, user_id: int) -> Optional[StateResponse]:
        """Get the state managed by a user"""
        state = self.db.query(State).filter(State.manager_id == user_id).first()
        
        if state:
            return self._state_to_response(state)
        return None
    
    def get_compatible_states(self, user: User, limit: int = 10) -> List[StateMatchResponse]:
        """Get most compatible states for a user"""
        quiz_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        
        if not quiz_result:
            raise ValueError("User must complete quiz first")
        
        user_traits = {
            'racionalidade': quiz_result.racionalidade,
            'conservadorismo': quiz_result.conservadorismo,
            'audacia': quiz_result.audacia,
            'autoridade': quiz_result.autoridade,
            'coletivismo': quiz_result.coletivismo,
            'influencia': quiz_result.influencia
        }
        
        # Get best matches
        matches = self.matching_service.find_best_matches(user_traits, limit)
        
        # Convert to response objects
        responses = []
        for state_id, score in matches:
            state = self.db.query(State).filter(State.id == state_id).first()
            if state:
                responses.append(StateMatchResponse(
                    state=self._state_to_response(state),
                    compatibility_score=score
                ))
        
        return responses
    
    def assign_random_state(self, user: User) -> StateAssignmentResponse:
        """Assign a random compatible state to user"""
        # Check if user already has a state
        existing_state = self.db.query(State).filter(State.manager_id == user.id).first()
        if existing_state:
            raise ValueError("User already has a state assigned")
        
        # Get user's quiz result
        quiz_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        if not quiz_result:
            raise ValueError("User must complete quiz first")
        
        # Check reroll limit
        if quiz_result.reroll_count >= settings.MAX_REROLL_ATTEMPTS:
            raise ValueError("Maximum reroll attempts exceeded")
        
        # Get a random compatible state
        state = self.matching_service.get_random_compatible_state(quiz_result)
        
        # Assign state to user
        assigned_state = self.matching_service.assign_state_to_user(state, user.id)
        
        return StateAssignmentResponse(
            message="State assigned successfully",
            assigned_state=self._state_to_response(assigned_state),
            rerolls_remaining=settings.MAX_REROLL_ATTEMPTS - quiz_result.reroll_count
        )
    
    def reroll_state(self, user: User) -> StateAssignmentResponse:
        """Reroll user's state assignment"""
        # Get user's quiz result
        quiz_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        if not quiz_result:
            raise ValueError("User must complete quiz first")
        
        # Check reroll limit
        if quiz_result.reroll_count >= settings.MAX_REROLL_ATTEMPTS:
            raise ValueError("Maximum reroll attempts exceeded")
        
        # Release current state
        self.matching_service.release_state_from_user(user.id)
        
        # Get a new random compatible state
        state = self.matching_service.get_random_compatible_state(quiz_result)
        
        # Assign new state
        assigned_state = self.matching_service.assign_state_to_user(state, user.id)
        
        # Increment reroll count
        quiz_result.reroll_count += 1
        self.db.commit()
        
        return StateAssignmentResponse(
            message="State rerolled successfully",
            assigned_state=self._state_to_response(assigned_state),
            rerolls_remaining=settings.MAX_REROLL_ATTEMPTS - quiz_result.reroll_count
        )
    
    def get_state_statistics(self) -> Dict[str, int]:
        """Get general statistics about states"""
        total_states = self.db.query(State).count()
        occupied_states = self.db.query(State).filter(State.is_occupied == True).count()
        available_states = total_states - occupied_states
        
        return {
            "total_states": total_states,
            "occupied_states": occupied_states,
            "available_states": available_states
        }
    
    def _state_to_response(self, state: State) -> StateResponse:
        """Convert State model to StateResponse"""
        manager_name = None
        if state.manager:
            manager_name = state.manager.name
        
        return StateResponse(
            id=state.id,
            name=state.name,
            country_name=state.country.name,
            racionalidade=state.racionalidade,
            conservadorismo=state.conservadorismo,
            audacia=state.audacia,
            autoridade=state.autoridade,
            coletivismo=state.coletivismo,
            influencia=state.influencia,
            is_occupied=state.is_occupied,
            manager_name=manager_name
        )