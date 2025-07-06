from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+mysqlconnector://root:@localhost/simnations"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    APP_NAME: str = "SimNations API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Quiz
    MAX_REROLL_ATTEMPTS: int = 3
    QUIZ_QUESTIONS_COUNT: int = 18  # 3 questions per category
    
    class Config:
        env_file = ".env"

settings = Settings()