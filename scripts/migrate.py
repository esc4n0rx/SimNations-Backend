#!/usr/bin/env python3
"""
Script de migrations para SimNations
Executa automaticamente todos os SQLs necessários
Uso: python scripts/migrate.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mysql.connector
from mysql.connector import Error
from config.settings import settings
from datetime import datetime
import hashlib

class Colors:
    """Cores para output colorido"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class MigrationRunner:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.migrations_executed = []
    
    def connect(self):
        """Conecta ao MySQL"""
        try:
            connection_params = settings.get_db_connection_params()
            self.connection = mysql.connector.connect(**connection_params)
            self.cursor = self.connection.cursor()
            print(f"{Colors.OKGREEN}✅ Conectado ao MySQL{Colors.ENDC}")
            return True
        except Error as e:
            print(f"{Colors.FAIL}❌ Erro ao conectar: {e}{Colors.ENDC}")
            return False
    
    def disconnect(self):
        """Desconecta do MySQL"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print(f"{Colors.OKCYAN}ℹ️  Conexão fechada{Colors.ENDC}")
    
    def create_migrations_table(self):
        """Cria tabela de controle de migrations"""
        migration_table_sql = """
        CREATE TABLE IF NOT EXISTS migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            migration_hash VARCHAR(64) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_migration_name (migration_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.cursor.execute(migration_table_sql)
            self.connection.commit()
            print(f"{Colors.OKGREEN}✅ Tabela de migrations criada/verificada{Colors.ENDC}")
            return True
        except Error as e:
            print(f"{Colors.FAIL}❌ Erro ao criar tabela de migrations: {e}{Colors.ENDC}")
            return False
    
    def get_executed_migrations(self):
        """Obtém lista de migrations já executadas"""
        try:
            self.cursor.execute("SELECT migration_name, migration_hash FROM migrations")
            return {name: hash_val for name, hash_val in self.cursor.fetchall()}
        except Error as e:
            print(f"{Colors.WARNING}⚠️  Erro ao obter migrations executadas: {e}{Colors.ENDC}")
            return {}
    
    def calculate_migration_hash(self, sql_content):
        """Calcula hash MD5 do conteúdo SQL"""
        return hashlib.md5(sql_content.encode('utf-8')).hexdigest()
    
    def record_migration(self, migration_name, migration_hash):
        """Registra migration como executada"""
        try:
            insert_sql = "INSERT INTO migrations (migration_name, migration_hash) VALUES (%s, %s)"
            self.cursor.execute(insert_sql, (migration_name, migration_hash))
            self.connection.commit()
            return True
        except Error as e:
            print(f"{Colors.FAIL}❌ Erro ao registrar migration: {e}{Colors.ENDC}")
            return False
    
    def execute_sql_file(self, file_path, migration_name):
        """Executa arquivo SQL"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Calcular hash
            migration_hash = self.calculate_migration_hash(sql_content)
            
            # Verificar se já foi executada
            executed_migrations = self.get_executed_migrations()
            
            if migration_name in executed_migrations:
                if executed_migrations[migration_name] == migration_hash:
                    print(f"{Colors.OKCYAN}ℹ️  Migration '{migration_name}' já executada (sem alterações){Colors.ENDC}")
                    return True
                else:
                    print(f"{Colors.WARNING}⚠️  Migration '{migration_name}' foi modificada. Executando novamente...{Colors.ENDC}")
            
            # Dividir em comandos individuais
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            print(f"{Colors.OKBLUE}🔄 Executando migration: {migration_name}{Colors.ENDC}")
            
            for i, command in enumerate(commands, 1):
                if command.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'DROP')):
                    try:
                        self.cursor.execute(command)
                        print(f"   {Colors.OKGREEN}✅ Comando {i}/{len(commands)} executado{Colors.ENDC}")
                    except Error as e:
                        print(f"   {Colors.FAIL}❌ Erro no comando {i}: {e}{Colors.ENDC}")
                        # Para alguns erros, continuamos (ex: tabela já existe)
                        if "already exists" in str(e).lower():
                            print(f"   {Colors.WARNING}⚠️  Comando ignorado (recurso já existe){Colors.ENDC}")
                            continue
                        else:
                            raise
            
            self.connection.commit()
            
            # Registrar migration
            if migration_name in executed_migrations:
                # Atualizar hash
                update_sql = "UPDATE migrations SET migration_hash = %s, executed_at = CURRENT_TIMESTAMP WHERE migration_name = %s"
                self.cursor.execute(update_sql, (migration_hash, migration_name))
            else:
                # Inserir nova
                self.record_migration(migration_name, migration_hash)
            
            self.connection.commit()
            self.migrations_executed.append(migration_name)
            print(f"{Colors.OKGREEN}✅ Migration '{migration_name}' executada com sucesso{Colors.ENDC}")
            return True
            
        except FileNotFoundError:
            print(f"{Colors.FAIL}❌ Arquivo não encontrado: {file_path}{Colors.ENDC}")
            return False
        except Error as e:
            print(f"{Colors.FAIL}❌ Erro ao executar migration '{migration_name}': {e}{Colors.ENDC}")
            self.connection.rollback()
            return False
        except Exception as e:
            print(f"{Colors.FAIL}❌ Erro inesperado: {e}{Colors.ENDC}")
            self.connection.rollback()
            return False
    
    def execute_direct_sql(self, sql_content, migration_name):
        """Executa SQL direto (string)"""
        try:
            # Calcular hash
            migration_hash = self.calculate_migration_hash(sql_content)
            
            # Verificar se já foi executada
            executed_migrations = self.get_executed_migrations()
            
            if migration_name in executed_migrations:
                if executed_migrations[migration_name] == migration_hash:
                    print(f"{Colors.OKCYAN}ℹ️  Migration '{migration_name}' já executada (sem alterações){Colors.ENDC}")
                    return True
                else:
                    print(f"{Colors.WARNING}⚠️  Migration '{migration_name}' foi modificada. Executando novamente...{Colors.ENDC}")
            
            # Dividir em comandos
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            print(f"{Colors.OKBLUE}🔄 Executando migration: {migration_name}{Colors.ENDC}")
            
            for i, command in enumerate(commands, 1):
                if command.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'DROP')):
                    try:
                        self.cursor.execute(command)
                        print(f"   {Colors.OKGREEN}✅ Comando {i}/{len(commands)} executado{Colors.ENDC}")
                    except Error as e:
                        if "already exists" in str(e).lower():
                            print(f"   {Colors.WARNING}⚠️  Comando ignorado (recurso já existe){Colors.ENDC}")
                            continue
                        else:
                            raise
            
            self.connection.commit()
            
            # Registrar migration
            if migration_name in executed_migrations:
                update_sql = "UPDATE migrations SET migration_hash = %s, executed_at = CURRENT_TIMESTAMP WHERE migration_name = %s"
                self.cursor.execute(update_sql, (migration_hash, migration_name))
            else:
                self.record_migration(migration_name, migration_hash)
            
            self.connection.commit()
            self.migrations_executed.append(migration_name)
            print(f"{Colors.OKGREEN}✅ Migration '{migration_name}' executada com sucesso{Colors.ENDC}")
            return True
            
        except Error as e:
            print(f"{Colors.FAIL}❌ Erro ao executar migration '{migration_name}': {e}{Colors.ENDC}")
            self.connection.rollback()
            return False
        except Exception as e:
            print(f"{Colors.FAIL}❌ Erro inesperado: {e}{Colors.ENDC}")
            self.connection.rollback()
            return False

def print_header():
    """Imprime cabeçalho"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("🚀 MIGRATIONS SIMNATIONS - EXECUÇÃO AUTOMÁTICA")
    print(f"{'='*80}{Colors.ENDC}")

def get_migrations():
    """Define todas as migrations a serem executadas"""
    
    # Migration 1: Estrutura básica das tabelas
    create_tables_sql = """
    -- Criar banco se não existir
    CREATE DATABASE IF NOT EXISTS simnations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    USE simnations;

    -- Tabela de usuários
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        birth_date DATE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- Tabela de países
    CREATE TABLE IF NOT EXISTS countries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        code VARCHAR(3) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_name (name),
        INDEX idx_code (code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- Tabela de estados
    CREATE TABLE IF NOT EXISTS states (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        country_id INT NOT NULL,
        manager_id INT NULL,
        racionalidade DECIMAL(3,1) NOT NULL,
        conservadorismo DECIMAL(3,1) NOT NULL,
        audacia DECIMAL(3,1) NOT NULL,
        autoridade DECIMAL(3,1) NOT NULL,
        coletivismo DECIMAL(3,1) NOT NULL,
        influencia DECIMAL(3,1) NOT NULL,
        is_occupied BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE,
        FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_country (country_id),
        INDEX idx_manager (manager_id),
        INDEX idx_occupied (is_occupied),
        INDEX idx_state_traits (racionalidade, conservadorismo, audacia, autoridade, coletivismo, influencia),
        INDEX idx_state_available (is_occupied, country_id),
        UNIQUE KEY unique_manager (manager_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- Tabela de resultados do quiz
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        racionalidade DECIMAL(3,1) NOT NULL,
        conservadorismo DECIMAL(3,1) NOT NULL,
        audacia DECIMAL(3,1) NOT NULL,
        autoridade DECIMAL(3,1) NOT NULL,
        coletivismo DECIMAL(3,1) NOT NULL,
        influencia DECIMAL(3,1) NOT NULL,
        answers JSON NOT NULL,
        reroll_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_user (user_id),
        INDEX idx_reroll (reroll_count),
        INDEX idx_quiz_traits (racionalidade, conservadorismo, audacia, autoridade, coletivismo, influencia),
        UNIQUE KEY unique_user_quiz (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # Migration 2: Dados iniciais de países
    insert_countries_sql = """
    INSERT INTO countries (name, code) VALUES 
    ('Brazil', 'BRA'),
    ('United States', 'USA'),
    ('France', 'FRA'),
    ('Germany', 'DEU'),
    ('Japan', 'JPN'),
    ('United Kingdom', 'GBR'),
    ('Canada', 'CAN'),
    ('Australia', 'AUS'),
    ('Italy', 'ITA'),
    ('Spain', 'ESP')
    ON DUPLICATE KEY UPDATE name = VALUES(name);
    """
    
    # Migration 3: Otimizações de performance
    performance_optimizations_sql = """
    -- Configurações de otimização para tabelas
    ALTER TABLE users ROW_FORMAT=DYNAMIC;
    ALTER TABLE countries ROW_FORMAT=DYNAMIC;
    ALTER TABLE states ROW_FORMAT=DYNAMIC;
    ALTER TABLE quiz_results ROW_FORMAT=DYNAMIC;
    
    -- Índices adicionais para performance
    CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
    CREATE INDEX IF NOT EXISTS idx_states_updated_at ON states(updated_at);
    CREATE INDEX IF NOT EXISTS idx_quiz_created_at ON quiz_results(created_at);
    """
    
    # Migration 4: Configurações de charset e collation
    charset_fix_sql = """
    -- Garantir charset correto em todas as tabelas
    ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE countries CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE states CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ALTER TABLE quiz_results CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    
    return [
        ("001_create_tables", create_tables_sql),
        ("002_insert_countries", insert_countries_sql),
        ("003_performance_optimizations", performance_optimizations_sql),
        ("004_charset_fix", charset_fix_sql),
    ]

def main():
    """Função principal"""
    print_header()
    
    print(f"{Colors.WARNING}Este script executará todas as migrations necessárias do SimNations.{Colors.ENDC}")
    print(f"{Colors.WARNING}Migrations já executadas serão ignoradas automaticamente.{Colors.ENDC}")
    
    # Inicializar runner
    runner = MigrationRunner()
    
    try:
        # Conectar
        if not runner.connect():
            return False
        
        # Criar tabela de controle
        if not runner.create_migrations_table():
            return False
        
        # Obter migrations
        migrations = get_migrations()
        
        print(f"\n{Colors.OKBLUE}📋 {len(migrations)} migrations encontradas{Colors.ENDC}")
        
        success_count = 0
        
        # Executar cada migration
        for migration_name, migration_sql in migrations:
            print(f"\n{Colors.OKCYAN}{'─'*60}{Colors.ENDC}")
            
            if runner.execute_direct_sql(migration_sql, migration_name):
                success_count += 1
            else:
                print(f"{Colors.FAIL}❌ Falha na migration: {migration_name}{Colors.ENDC}")
        
        # Relatório final
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
        print("📊 RELATÓRIO DE MIGRATIONS")
        print(f"{'='*80}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Resumo:{Colors.ENDC}")
        print(f"   Total de migrations: {len(migrations)}")
        print(f"   {Colors.OKGREEN}✅ Executadas com sucesso: {success_count}{Colors.ENDC}")
        print(f"   {Colors.FAIL}❌ Falharam: {len(migrations) - success_count}{Colors.ENDC}")
        
        if runner.migrations_executed:
            print(f"\n{Colors.BOLD}Migrations executadas nesta sessão:{Colors.ENDC}")
            for migration in runner.migrations_executed:
                print(f"   {Colors.OKGREEN}✅ {migration}{Colors.ENDC}")
        
        success_rate = (success_count / len(migrations)) * 100
        
        if success_rate == 100:
            print(f"\n{Colors.OKGREEN}🎉 Todas as migrations foram executadas com sucesso!{Colors.ENDC}")
            print(f"{Colors.OKGREEN}Banco de dados está pronto para uso.{Colors.ENDC}")
        elif success_rate >= 80:
            print(f"\n{Colors.WARNING}⚠️  A maioria das migrations foi executada. Verifique os erros acima.{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}💥 Muitas migrations falharam. Verifique a configuração.{Colors.ENDC}")
        
        return success_rate == 100
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Execução interrompida pelo usuário.{Colors.ENDC}")
        return False
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Erro inesperado: {e}{Colors.ENDC}")
        return False
    finally:
        runner.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)