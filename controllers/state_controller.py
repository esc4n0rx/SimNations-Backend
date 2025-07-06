from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from services.state_service import StateService
from schemas.state_schema import StateResponse, StateMatchResponse, StateAssignmentResponse
from models.user import User
from controllers.auth_controller import get_current_user_dependency

router = APIRouter(prefix="/states", tags=["States"])

@router.get("/statistics")
async def get_state_statistics(db: Session = Depends(get_db)):
    """Get general statistics about states"""
    try:
        state_service = StateService(db)
        stats = state_service.get_state_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )

@router.get("/country/{country_name}", response_model=List[StateResponse])
async def get_states_by_country(
    country_name: str,
    db: Session = Depends(get_db)
):
    """Get all states from a specific country"""
    try:
        state_service = StateService(db)
        states = state_service.get_states_by_country(country_name)
        return states
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get states"
        )

@router.get("/my-state", response_model=Optional[StateResponse])
async def get_my_state(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get the state managed by current user"""
    try:
        state_service = StateService(db)
        state = state_service.get_user_state(current_user.id)
        return state
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user state"
        )

@router.get("/compatible", response_model=List[StateMatchResponse])
async def get_compatible_states(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get most compatible states for current user"""
    try:
        state_service = StateService(db)
        compatible_states = state_service.get_compatible_states(current_user, limit)
        return compatible_states
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get compatible states"
        )

@router.post("/assign", response_model=StateAssignmentResponse)
async def assign_state(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Assign a random compatible state to current user"""
    try:
        state_service = StateService(db)
        assignment = state_service.assign_random_state(current_user)
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign state"
        )

@router.post("/reroll", response_model=StateAssignmentResponse)
async def reroll_state(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Reroll current user's state assignment"""
    try:
        state_service = StateService(db)
        assignment = state_service.reroll_state(current_user)
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reroll state"
        )