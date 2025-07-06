from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from services.quiz_service import QuizService
from schemas.quiz_schema import QuizQuestion, QuizSubmission, QuizResultResponse
from models.user import User
from controllers.auth_controller import get_current_user_dependency

router = APIRouter(prefix="/quiz", tags=["Quiz"])

@router.get("/questions", response_model=List[QuizQuestion])
async def get_quiz_questions():
    """Get all quiz questions"""
    try:
        quiz_service = QuizService(None)  # No DB needed for static questions
        questions = quiz_service.get_quiz_questions()
        return questions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quiz questions"
        )

@router.post("/submit")
async def submit_quiz(
    quiz_submission: QuizSubmission,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get personality results with auto-assigned state"""
    try:
        quiz_service = QuizService(db)
        quiz_result = quiz_service.save_quiz_result(current_user, quiz_submission, auto_assign_state=True)
        
        # Check if state was assigned
        from models.state import State
        assigned_state = db.query(State).filter(State.manager_id == current_user.id).first()
        
        response = {
            "quiz_result": {
                "racionalidade": quiz_result.racionalidade,
                "conservadorismo": quiz_result.conservadorismo,
                "audacia": quiz_result.audacia,
                "autoridade": quiz_result.autoridade,
                "coletivismo": quiz_result.coletivismo,
                "influencia": quiz_result.influencia,
                "reroll_count": quiz_result.reroll_count
            },
            "state_assigned": assigned_state is not None
        }
        
        if assigned_state:
            response["assigned_state"] = {
                "id": assigned_state.id,
                "name": assigned_state.name,
                "country_name": assigned_state.country.name,
                "is_occupied": assigned_state.is_occupied
            }
            response["message"] = f"Quiz completed! You've been assigned to manage {assigned_state.name}, {assigned_state.country.name}"
        else:
            response["message"] = "Quiz completed! You can now request a state assignment."
        
        return response
    except Exception as e:
        print(f"Error in submit_quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit quiz"
        )

@router.post("/submit-without-assignment", response_model=QuizResultResponse)
async def submit_quiz_without_assignment(
    quiz_submission: QuizSubmission,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Submit quiz answers without auto-assigning state"""
    try:
        quiz_service = QuizService(db)
        quiz_result = quiz_service.save_quiz_result(current_user, quiz_submission, auto_assign_state=False)
        
        return QuizResultResponse(
            racionalidade=quiz_result.racionalidade,
            conservadorismo=quiz_result.conservadorismo,
            audacia=quiz_result.audacia,
            autoridade=quiz_result.autoridade,
            coletivismo=quiz_result.coletivismo,
            influencia=quiz_result.influencia,
            reroll_count=quiz_result.reroll_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit quiz"
        )

@router.get("/result", response_model=QuizResultResponse)
async def get_quiz_result(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get current user's quiz results"""
    try:
        quiz_service = QuizService(db)
        quiz_result = quiz_service.get_user_quiz_result(current_user)
        
        if not quiz_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not completed yet"
            )
        
        return QuizResultResponse(
            racionalidade=quiz_result.racionalidade,
            conservadorismo=quiz_result.conservadorismo,
            audacia=quiz_result.audacia,
            autoridade=quiz_result.autoridade,
            coletivismo=quiz_result.coletivismo,
            influencia=quiz_result.influencia,
            reroll_count=quiz_result.reroll_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quiz result"
        )