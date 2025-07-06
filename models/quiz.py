from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Calculated personality traits
    racionalidade = Column(Float, nullable=False)
    conservadorismo = Column(Float, nullable=False)
    audacia = Column(Float, nullable=False)
    autoridade = Column(Float, nullable=False)
    coletivismo = Column(Float, nullable=False)
    influencia = Column(Float, nullable=False)
    
    # Quiz answers stored as JSON
    answers = Column(JSON, nullable=False)
    
    # Reroll tracking
    reroll_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quiz_results")