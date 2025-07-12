from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "simnations"
    DB_SSL_DISABLED: bool = True
    
    # Connection Settings
    DB_CONNECT_TIMEOUT: int = 30
    DB_READ_TIMEOUT: int = 30
    DB_WRITE_TIMEOUT: int = 30
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Application Settings
    SECRET_KEY: str = "your-super-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    APP_NAME: str = "SimNations API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    MAX_REROLL_ATTEMPTS: int = 3
    QUIZ_QUESTIONS_COUNT: int = 18
    
    @property
    def DATABASE_URL(self) -> str:
        """Constrói a URL de conexão com o MySQL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    def get_db_connection_params(self) -> dict:
        """Retorna parâmetros de conexão para mysql-connector-python"""
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "database": self.DB_NAME,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "use_unicode": True,
            "autocommit": False,
            "connection_timeout": self.DB_CONNECT_TIMEOUT,
            "read_timeout": self.DB_READ_TIMEOUT,
            "write_timeout": self.DB_WRITE_TIMEOUT,
            "sql_mode": "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
        }
    
    def validate_database_config(self) -> tuple[bool, str]:
        """Valida a configuração do banco de dados"""
        if not self.DB_HOST:
            return False, "DB_HOST não pode estar vazio"
        
        if not self.DB_USER:
            return False, "DB_USER não pode estar vazio"
        
        if not self.DB_PASSWORD:
            return False, "DB_PASSWORD não pode estar vazio"
        
        if not self.DB_NAME:
            return False, "DB_NAME não pode estar vazio"
        
        if self.DB_PORT <= 0 or self.DB_PORT > 65535:
            return False, f"DB_PORT deve estar entre 1 e 65535, valor atual: {self.DB_PORT}"
        
        return True, "Configuração válida"
    
    def get_pymysql_connection_args(self) -> dict:
        """Retorna argumentos específicos para PyMySQL"""
        return {
            "connect_timeout": self.DB_CONNECT_TIMEOUT,
            "read_timeout": self.DB_READ_TIMEOUT,
            "write_timeout": self.DB_WRITE_TIMEOUT,
            "charset": "utf8mb4",
            "use_unicode": True,
            "autocommit": False,
            "ssl_disabled": self.DB_SSL_DISABLED
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Instância global das configurações
settings = Settings()

# Validação automática na inicialização
if __name__ != "__main__":
    is_valid, message = settings.validate_database_config()
    if not is_valid:
        print(f"❌ Erro na configuração do banco: {message}")