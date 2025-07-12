from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from config.database import (
    get_db, engine, test_connection, 
    ensure_database_exists, create_tables_safely,
    get_connection_status, print_connection_troubleshooting
)
from config.settings import settings
from utils.data_loader import data_loader
from models import user, country, state, quiz  # Import all models
from controllers import auth_controller, quiz_controller, state_controller, user_controller
import sys
import time

# Não criar tabelas imediatamente - será feito no startup com tratamento de erro
print("🚀 Inicializando SimNations API...")

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
    
    print("🔧 Executando startup da aplicação...")
    
    # Validar configurações
    is_valid, validation_message = settings.validate_database_config()
    if not is_valid:
        print(f"❌ Configuração inválida: {validation_message}")
        print("💡 Verifique o arquivo .env")
        sys.exit(1)
    
    # Testar conexão com retry
    print("🔍 Testando conexão com MySQL...")
    if not test_connection(max_retries=3, retry_delay=2):
        print("❌ Falha na conexão com MySQL após várias tentativas.")
        print("💡 Execute: python scripts/test_connection.py para diagnóstico completo")
        print("💡 Execute: python scripts/check_env.py para verificar configurações")
        sys.exit(1)
    
    print("✅ Conexão com MySQL estabelecida com sucesso!")
    
    # Verificar/criar banco de dados
    print("🔍 Verificando banco de dados...")
    if not ensure_database_exists():
        print("❌ Erro ao verificar/criar banco de dados")
        sys.exit(1)
    
    # Criar tabelas
    if not create_tables_safely():
        print("❌ Erro ao criar tabelas")
        print("💡 Execute: python scripts/migrate.py para executar migrations")
        sys.exit(1)
    
    # Carregar dados iniciais
    db = next(get_db())
    try:
        print("📊 Carregando dados iniciais...")
        data_loader.populate_database(db)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao carregar dados iniciais: {e}")
        print("💡 Dados podem já existir ou há problema no arquivo JSON")
    finally:
        db.close()
    
    print("🎉 Startup concluído com sucesso!")

@app.get("/")
async def root():
    """Root endpoint"""
    connection_status = get_connection_status()
    
    return {
        "message": "Welcome to SimNations API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "database": {
            "host": f"{settings.DB_HOST}:{settings.DB_PORT}",
            "connected": connection_status["connected"],
            "mysql_version": connection_status.get("mysql_version")
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    connection_status = get_connection_status()
    
    return {
        "status": "healthy" if connection_status["connected"] else "unhealthy",
        "database": connection_status,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }

@app.get("/debug/connection")
async def debug_connection():
    """Debug endpoint para verificar conexão"""
    return get_connection_status()

if __name__ == "__main__":
    import uvicorn
    
    # Testar conexão antes de iniciar o servidor
    print("🚀 Iniciando SimNations API...")
    print("🔍 Verificando conexão com banco de dados...")
    
    # Validar configurações primeiro
    is_valid, validation_message = settings.validate_database_config()
    if not is_valid:
        print(f"❌ Configuração inválida: {validation_message}")
        print("💡 Execute: python scripts/check_env.py para verificar configurações")
        sys.exit(1)
    
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