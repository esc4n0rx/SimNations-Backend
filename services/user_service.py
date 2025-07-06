from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from models.user import User
from models.state import State
from models.quiz import QuizResult
from schemas.user_schema import UserResponse
from utils.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user_profile(self, user: User, update_data: Dict[str, Any]) -> User:
        """Update user profile information"""
        # Only allow updating specific fields
        allowed_fields = ['name', 'birth_date']
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_user_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user password"""
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def deactivate_user(self, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Release any managed state
        managed_state = self.db.query(State).filter(State.manager_id == user.id).first()
        if managed_state:
            managed_state.is_occupied = False
            managed_state.manager_id = None
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def reactivate_user(self, user: User) -> User:
        """Reactivate user account"""
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_profile_complete(self, user: User) -> Dict[str, Any]:
        """Get complete user profile with additional information"""
        # Get user's quiz result
        quiz_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        
        # Get user's managed state
        managed_state = self.db.query(State).filter(State.manager_id == user.id).first()
        
        profile = {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "birth_date": user.birth_date,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            },
            "quiz_completed": quiz_result is not None,
            "quiz_result": None,
            "managed_state": None,
            "has_state": managed_state is not None
        }
        
        if quiz_result:
            profile["quiz_result"] = {
                "racionalidade": quiz_result.racionalidade,
                "conservadorismo": quiz_result.conservadorismo,
                "audacia": quiz_result.audacia,
                "autoridade": quiz_result.autoridade,
                "coletivismo": quiz_result.coletivismo,
                "influencia": quiz_result.influencia,
                "reroll_count": quiz_result.reroll_count,
                "created_at": quiz_result.created_at
            }
        
        if managed_state:
            profile["managed_state"] = {
                "id": managed_state.id,
                "name": managed_state.name,
                "country_name": managed_state.country.name,
                "assigned_at": managed_state.updated_at
            }
        
        return profile
    
    def delete_user_account(self, user: User) -> bool:
        """Permanently delete user account and all associated data"""
        try:
            # Release any managed state
            managed_state = self.db.query(State).filter(State.manager_id == user.id).first()
            if managed_state:
                managed_state.is_occupied = False
                managed_state.manager_id = None
            
            # Delete quiz results (will cascade)
            quiz_results = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).all()
            for quiz_result in quiz_results:
                self.db.delete(quiz_result)
            
            # Delete user
            self.db.delete(user)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def check_email_availability(self, email: str, current_user_id: Optional[int] = None) -> bool:
        """Check if email is available for use"""
        query = self.db.query(User).filter(User.email == email)
        
        # Exclude current user if updating
        if current_user_id:
            query = query.filter(User.id != current_user_id)
        
        existing_user = query.first()
        return existing_user is None
    
    def get_user_statistics(self, user: User) -> Dict[str, Any]:
        """Get user statistics and achievements"""
        quiz_result = self.db.query(QuizResult).filter(QuizResult.user_id == user.id).first()
        managed_state = self.db.query(State).filter(State.manager_id == user.id).first()
        
        # Calculate days since registration
        days_active = (datetime.utcnow() - user.created_at).days
        
        stats = {
            "days_active": days_active,
            "quiz_completed": quiz_result is not None,
            "has_state": managed_state is not None,
            "rerolls_used": quiz_result.reroll_count if quiz_result else 0,
            "rerolls_remaining": 3 - (quiz_result.reroll_count if quiz_result else 0),
            "account_status": "active" if user.is_active else "inactive"
        }
        
        if managed_state:
            # Calculate days managing state
            days_managing = (datetime.utcnow() - managed_state.updated_at).days
            stats["days_managing_state"] = days_managing
            stats["state_info"] = {
                "name": managed_state.name,
                "country": managed_state.country.name
            }
        
        return stats