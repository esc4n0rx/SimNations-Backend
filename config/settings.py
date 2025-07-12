from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .settings import settings
import logging

# Configurar logging do SQLAlchemy
if settings.DEBUG:
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Configurações do engine com pool de conexões otimizado
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hora
    pool_timeout=30,
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": False,
        "ssl_disabled": settings.DB_SSL_DISABLED
    }
)

# Evento para configurar charset da sessão
@event.listens_for(engine, "connect")
def set_mysql_charset(dbapi_connection, connection_record):
    """Configura charset e timezone para cada conexão"""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute("SET time_zone = '+00:00'")  # UTC
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1 as test").fetchone()
            return result[0] == 1
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False