from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.user import User
from schemas.user_schema import UserCreate, UserLogin, Token
from utils.security import verify_password, get_password_hash, create_access_token
from config.settings import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            name=user_data.name,
            email=user_data.email,
            birth_date=user_data.birth_date,
            password_hash=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, login_data: UserLogin) -> User:
        """Authenticate user credentials"""
        user = self.db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        return user
    
    def create_access_token_for_user(self, user: User) -> Token:
        """Create access token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()