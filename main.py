from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config.database import get_db, engine
from config.settings import settings
from utils.data_loader import data_loader
from models import user, country, state, quiz  # Import all models
from controllers import auth_controller, quiz_controller, state_controller, user_controller

# Create tables
from config.database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for SimNations - A country simulation game",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(quiz_controller.router)
app.include_router(state_controller.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database with countries and states data"""
    db = next(get_db())
    try:
        # Load initial data from JSON
        data_loader.populate_database(db)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SimNations API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )