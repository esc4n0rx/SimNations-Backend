from pydantic import BaseModel, validator
from typing import List, Dict
from enum import Enum

class QuizCategory(str, Enum):
    RACIONALIDADE = "racionalidade"
    CONSERVADORISMO = "conservadorismo"
    AUDACIA = "audacia"
    AUTORIDADE = "autoridade"
    COLETIVISMO = "coletivismo"
    INFLUENCIA = "influencia"

class QuizAnswer(BaseModel):
    question_id: int
    category: QuizCategory
    answer_value: int  # 1-5 scale
    
    @validator('answer_value')
    def validate_answer(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Answer value must be between 1 and 5')
        return v

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]
    
    @validator('answers')
    def validate_answers(cls, v):
        if len(v) != 18:  # 3 questions per category
            raise ValueError('Must answer all 18 questions')
        
        # Check if all categories are represented
        categories = [answer.category for answer in v]
        for category in QuizCategory:
            if categories.count(category) != 3:
                raise ValueError(f'Must have exactly 3 answers for {category}')
        
        return v

class QuizQuestion(BaseModel):
    id: int
    category: QuizCategory
    question: str
    options: List[str]

class QuizResultResponse(BaseModel):
    racionalidade: float
    conservadorismo: float
    audacia: float
    autoridade: float
    coletivismo: float
    influencia: float
    reroll_count: int
    
    class Config:
        from_attributes = True
