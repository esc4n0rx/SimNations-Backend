from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, date
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    birth_date: date
    password: str
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v >= date.today():
            raise ValueError('Birth date must be in the past')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    birth_date: date
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None