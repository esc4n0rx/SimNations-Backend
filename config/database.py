from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .settings import settings
import logging
import time
from typing import Optional

# Configurar logging do SQLAlchemy
if settings.DEBUG:
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def create_database_engine():
    """Cria e configura o engine do banco de dados com tratamento de erros"""
    try:
        # Validar configurações primeiro
        is_valid, validation_message = settings.validate_database_config()
        if not is_valid:
            raise ValueError(f"Configuração inválida: {validation_message}")
        
        # Argumentos de conexão específicos para PyMySQL
        connect_args = settings.get_pymysql_connection_args()
        
        print(f"🔗 Tentando conectar ao MySQL em {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"📊 Banco: {settings.DB_NAME}")
        print(f"👤 Usuário: {settings.DB_USER}")
        
        # Configurações do engine com pool de conexões otimizado para conexão remota
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # Importante para conexões remotas
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            connect_args=connect_args,
            # Configurações específicas para conexões remotas
            execution_options={
                "isolation_level": "READ_COMMITTED"
            }
        )
        
        return engine
        
    except Exception as e:
        print(f"❌ Erro ao criar engine do banco: {e}")
        raise

# Criar engine
engine = create_database_engine()

# Evento para configurar charset da sessão
@event.listens_for(engine, "connect")
def set_mysql_charset(dbapi_connection, connection_record):
    """Configura charset e timezone para cada conexão"""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("SET time_zone = '+00:00'")  # UTC
        cursor.execute("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'")
        cursor.close()
    except Exception as e:
        print(f"⚠️ Aviso: Erro ao configurar charset da conexão: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection(max_retries: int = 3, retry_delay: int = 5) -> bool:
    """Testa a conexão com o banco de dados com retry automático"""
    for attempt in range(max_retries):
        try:
            print(f"🔍 Tentativa {attempt + 1}/{max_retries} de conexão...")
            
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test, VERSION() as version"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    print(f"✅ Conexão bem-sucedida!")
                    print(f"📊 MySQL Version: {row[1]}")
                    return True
                
        except Exception as e:
            print(f"❌ Tentativa {attempt + 1} falhou: {e}")
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay}s antes da próxima tentativa...")
                time.sleep(retry_delay)
            else:
                print(f"💥 Todas as {max_retries} tentativas falharam!")
                print_connection_troubleshooting()
    
    return False

def test_connection_simple() -> bool:
    """Teste simples de conexão sem retry"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            return row and row[0] == 1
    except Exception:
        return False

def print_connection_troubleshooting():
    """Imprime dicas de troubleshooting para problemas de conexão"""
    print("\n🛠️  DICAS DE TROUBLESHOOTING:")
    print("1. Verifique se o servidor MySQL está rodando")
    print("2. Confirme se o IP e porta estão corretos no .env")
    print("3. Teste se há conectividade de rede: ping 195.35.17.111")
    print("4. Verifique se o firewall permite conexões na porta 3306")
    print("5. Confirme se o usuário tem permissões remotas no MySQL")
    print("6. Execute: python scripts/test_connection.py para diagnóstico completo")
    print("7. Execute: python scripts/check_env.py para validar configurações")

def get_connection_status() -> dict:
    """Retorna status detalhado da conexão"""
    status = {
        "connected": False,
        "database": settings.DB_NAME,
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "error": None,
        "mysql_version": None
    }
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT VERSION() as version"))
            row = result.fetchone()
            
            status["connected"] = True
            status["mysql_version"] = row[0] if row else "Unknown"
            
    except Exception as e:
        status["error"] = str(e)
    
    return status

def ensure_database_exists():
    """Verifica se o banco de dados existe e cria se necessário"""
    try:
        # Conectar sem especificar o banco
        temp_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/"
        temp_engine = create_engine(temp_url, connect_args=settings.get_pymysql_connection_args())
        
        with temp_engine.connect() as connection:
            # Verificar se o banco existe
            result = connection.execute(text(f"SHOW DATABASES LIKE '{settings.DB_NAME}'"))
            if not result.fetchone():
                # Criar banco se não existir
                connection.execute(text(f"CREATE DATABASE {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                print(f"✅ Banco de dados '{settings.DB_NAME}' criado com sucesso!")
            else:
                print(f"✅ Banco de dados '{settings.DB_NAME}' já existe")
        
        temp_engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar/criar banco de dados: {e}")
        return False

def create_tables_safely():
    """Cria tabelas com tratamento de erro"""
    try:
        print("🏗️  Criando tabelas do banco de dados...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        print("💡 Execute: python scripts/migrate.py para corrigir problemas de schema")
        return False