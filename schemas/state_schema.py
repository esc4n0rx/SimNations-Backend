from pydantic import BaseModel
from typing import Optional

class StateResponse(BaseModel):
    id: int
    name: str
    country_name: str
    racionalidade: float
    conservadorismo: float
    audacia: float
    autoridade: float
    coletivismo: float
    influencia: float
    is_occupied: bool
    manager_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class StateMatchResponse(BaseModel):
    state: StateResponse
    compatibility_score: float
    
class StateAssignmentResponse(BaseModel):
    message: str
    assigned_state: StateResponse
    rerolls_remaining: int