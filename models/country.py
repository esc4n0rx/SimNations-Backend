from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    code = Column(String(3), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship with states
    states = relationship("State", back_populates="country")
