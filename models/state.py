from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class State(Base):
    __tablename__ = "states"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Personality traits
    racionalidade = Column(Float, nullable=False)
    conservadorismo = Column(Float, nullable=False)
    audacia = Column(Float, nullable=False)
    autoridade = Column(Float, nullable=False)
    coletivismo = Column(Float, nullable=False)
    influencia = Column(Float, nullable=False)
    
    # State management
    is_occupied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", back_populates="states")
    manager = relationship("User", back_populates="managed_state")
    
    # Composite indexes for optimized matching
    __table_args__ = (
        Index('idx_state_traits', 'racionalidade', 'conservadorismo', 'audacia', 'autoridade', 'coletivismo', 'influencia'),
        Index('idx_state_available', 'is_occupied', 'country_id'),
    )