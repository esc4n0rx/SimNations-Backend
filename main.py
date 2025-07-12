from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config.database import get_db, engine, test_connection
from config.settings import settings
from utils.data_loader import data_loader
from models import user, country, state, quiz  # Import all models
from controllers import auth_controller, quiz_controller, state_controller, user_controller
import sys

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
    
    # Testar conexão primeiro
    print("🔍 Testando conexão com MySQL...")
    if not test_connection():
        print("❌ Falha na conexão com MySQL. Verifique as configurações.")
        print("💡 Execute: python scripts/test_connection.py para diagnóstico completo")
        sys.exit(1)
    
    print("✅ Conexão com MySQL estabelecida com sucesso!")
    
    db = next(get_db())
    try:
        # Load initial data from JSON
        data_loader.populate_database(db)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("💡 Execute: python scripts/migrate.py para corrigir problemas de schema")
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SimNations API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "database": f"Connected to {settings.DB_HOST}:{settings.DB_PORT}"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if test_connection() else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "version": settings.APP_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    
    # Testar conexão antes de iniciar o servidor
    print("🚀 Iniciando SimNations API...")
    print("🔍 Verificando conexão com banco de dados...")
    
    if not test_connection():
        print("❌ Não foi possível conectar ao banco de dados!")
        print("💡 Verifique o arquivo .env e execute: python scripts/test_connection.py")
        sys.exit(1)
    
    print("✅ Banco de dados conectado com sucesso!")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )