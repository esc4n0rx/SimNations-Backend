from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from config.database import get_db
from services.user_service import UserService
from schemas.user_schema import UserResponse
from models.user import User
from controllers.auth_controller import get_current_user_dependency
from pydantic import BaseModel, EmailStr, validator
from datetime import date

router = APIRouter(prefix="/users", tags=["Users"])

class UserUpdateRequest(BaseModel):
    name: str
    birth_date: date
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v >= date.today():
            raise ValueError('Birth date must be in the past')
        return v

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class EmailCheckRequest(BaseModel):
    email: EmailStr

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user's basic profile"""
    try:
        return current_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.get("/profile/complete")
async def get_complete_profile(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get complete user profile with quiz results and state information"""
    try:
        user_service = UserService(db)
        complete_profile = user_service.get_user_profile_complete(current_user)
        return complete_profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get complete profile"
        )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        user_service = UserService(db)
        
        update_dict = {
            "name": update_data.name,
            "birth_date": update_data.birth_date
        }
        
        updated_user = user_service.update_user_profile(current_user, update_dict)
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        user_service = UserService(db)
        user_service.change_user_password(
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/check-email")
async def check_email_availability(
    email_data: EmailCheckRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Check if email is available"""
    try:
        user_service = UserService(db)
        is_available = user_service.check_email_availability(
            email_data.email,
            current_user.id
        )
        
        return {
            "email": email_data.email,
            "available": is_available
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check email availability"
        )

@router.get("/statistics")
async def get_user_statistics(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get user statistics and achievements"""
    try:
        user_service = UserService(db)
        stats = user_service.get_user_statistics(current_user)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )

@router.post("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Deactivate user account"""
    try:
        user_service = UserService(db)
        user_service.deactivate_user(current_user)
        
        return {"message": "Account deactivated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )

@router.post("/reactivate")
async def reactivate_account(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Reactivate user account"""
    try:
        user_service = UserService(db)
        user_service.reactivate_user(current_user)
        
        return {"message": "Account reactivated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate account"
        )

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Permanently delete user account"""
    try:
        user_service = UserService(db)
        user_service.delete_user_account(current_user)
        
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )

# Admin endpoints (optional - for future admin panel)
@router.get("/admin/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """Get all users (admin only)"""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.get("/admin/users/{user_id}")
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """Get user by ID (admin only)"""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user_service.get_user_profile_complete(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )