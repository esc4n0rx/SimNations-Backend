#!/usr/bin/env python3
"""
Script para testar conexão com MySQL remoto
Uso: python scripts/test_connection.py
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import mysql.connector
from mysql.connector import Error
from config.settings import settings
import time
from datetime import datetime

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

def print_header():
    """Imprime cabeçalho do teste"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("🔍 TESTE DE CONEXÃO MYSQL - SIMNATIONS")
    print(f"{'='*80}{Colors.ENDC}")

def print_step(step: str, description: str):
    """Imprime passo do teste"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}[PASSO {step}]{Colors.ENDC} {description}")
    print(f"{Colors.OKCYAN}{'─'*60}{Colors.ENDC}")

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message: str):
    """Imprime informação"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def test_basic_connection():
    """Testa conexão básica com MySQL"""
    print_step("1", "Testando conexão básica com MySQL")
    
    try:
        connection_params = settings.get_db_connection_params()
        print_info(f"Host: {connection_params['host']}")
        print_info(f"Porta: {connection_params['port']}")
        print_info(f"Usuário: {connection_params['user']}")
        print_info(f"Banco: {connection_params['database']}")
        
        connection = mysql.connector.connect(**connection_params)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print_success(f"Conectado ao MySQL Server versão {db_info}")
            
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            database_name = cursor.fetchone()
            print_success(f"Conectado ao banco: {database_name[0]}")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print_error(f"Erro ao conectar ao MySQL: {e}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

def test_charset_and_timezone():
    """Testa configurações de charset e timezone"""
    print_step("2", "Verificando configurações de charset e timezone")
    
    try:
        connection_params = settings.get_db_connection_params()
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Testar charset
        cursor.execute("SHOW VARIABLES LIKE 'character_set_database'")
        charset_result = cursor.fetchone()
        print_info(f"Charset do banco: {charset_result[1]}")
        
        # Testar collation
        cursor.execute("SHOW VARIABLES LIKE 'collation_database'")
        collation_result = cursor.fetchone()
        print_info(f"Collation do banco: {collation_result[1]}")
        
        # Testar timezone
        cursor.execute("SELECT @@time_zone")
        timezone_result = cursor.fetchone()
        print_info(f"Timezone: {timezone_result[0]}")
        
        # Testar encoding
        cursor.execute("SELECT @@character_set_client, @@character_set_connection, @@character_set_results")
        encoding_result = cursor.fetchone()
        print_info(f"Client charset: {encoding_result[0]}")
        print_info(f"Connection charset: {encoding_result[1]}")
        print_info(f"Results charset: {encoding_result[2]}")
        
        cursor.close()
        connection.close()
        print_success("Configurações de charset e timezone verificadas")
        return True
        
    except Error as e:
        print_error(f"Erro ao verificar configurações: {e}")
        return False

def test_database_operations():
    """Testa operações básicas no banco"""
    print_step("3", "Testando operações básicas no banco")
    
    try:
        connection_params = settings.get_db_connection_params()
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Criar tabela de teste
        test_table_query = """
        CREATE TEMPORARY TABLE test_connection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(test_table_query)
        print_success("Tabela temporária criada")
        
        # Inserir dados de teste
        insert_query = "INSERT INTO test_connection (message) VALUES (%s)"
        test_message = "Teste de conexão SimNations - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(insert_query, (test_message,))
        connection.commit()
        print_success("Dados inseridos com sucesso")
        
        # Ler dados
        cursor.execute("SELECT * FROM test_connection")
        results = cursor.fetchall()
        
        for row in results:
            print_info(f"ID: {row[0]}, Mensagem: {row[1]}, Data: {row[2]}")
        
        print_success(f"Lidos {len(results)} registros")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print_error(f"Erro nas operações do banco: {e}")
        return False

def test_sqlalchemy_connection():
    """Testa conexão via SQLAlchemy"""
    print_step("4", "Testando conexão via SQLAlchemy")
    
    try:
        from config.database import engine, test_connection
        
        # Teste básico do engine
        if test_connection():
            print_success("SQLAlchemy Engine conectado com sucesso")
        else:
            print_error("Falha na conexão do SQLAlchemy Engine")
            return False
        
        # Teste de query
        with engine.connect() as connection:
            result = connection.execute("SELECT VERSION() as version")
            version = result.fetchone()
            print_info(f"MySQL Version via SQLAlchemy: {version[0]}")
        
        print_success("SQLAlchemy funcionando corretamente")
        return True
        
    except Exception as e:
        print_error(f"Erro no SQLAlchemy: {e}")
        return False

def test_connection_pool():
    """Testa pool de conexões"""
    print_step("5", "Testando pool de conexões")
    
    try:
        from config.database import engine
        
        connections = []
        max_connections = 5
        
        print_info(f"Criando {max_connections} conexões...")
        
        for i in range(max_connections):
            conn = engine.connect()
            connections.append(conn)
            result = conn.execute("SELECT CONNECTION_ID()")
            conn_id = result.fetchone()[0]
            print_info(f"Conexão {i+1}: ID {conn_id}")
        
        print_success(f"Pool suporta {max_connections} conexões simultâneas")
        
        # Fechar conexões
        for conn in connections:
            conn.close()
        
        print_success("Pool de conexões testado com sucesso")
        return True
        
    except Exception as e:
        print_error(f"Erro no pool de conexões: {e}")
        return False

def test_performance():
    """Testa performance da conexão"""
    print_step("6", "Testando performance da conexão")
    
    try:
        connection_params = settings.get_db_connection_params()
        
        # Teste de latência
        start_time = time.time()
        connection = mysql.connector.connect(**connection_params)
        connection_time = time.time() - start_time
        
        print_info(f"Tempo de conexão: {connection_time:.3f}s")
        
        if connection_time < 1.0:
            print_success("Conexão rápida (< 1s)")
        elif connection_time < 3.0:
            print_info("Conexão moderada (1-3s)")
        else:
            print_error("Conexão lenta (> 3s)")
        
        # Teste de query
        cursor = connection.cursor()
        start_time = time.time()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        query_time = time.time() - start_time
        
        print_info(f"Tempo de query simples: {query_time:.3f}s")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print_error(f"Erro no teste de performance: {e}")
        return False

def main():
    """Função principal"""
    print_header()
    
    print(f"{Colors.WARNING}Este script testa a conectividade com o MySQL remoto configurado.{Colors.ENDC}")
    print(f"{Colors.WARNING}Certifique-se de que o arquivo .env está configurado corretamente.{Colors.ENDC}")
    
    tests = [
        ("Conexão Básica", test_basic_connection),
        ("Charset e Timezone", test_charset_and_timezone),
        ("Operações Básicas", test_database_operations),
        ("SQLAlchemy", test_sqlalchemy_connection),
        ("Pool de Conexões", test_connection_pool),
        ("Performance", test_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}⚠️  Teste interrompido pelo usuário.{Colors.ENDC}")
            break
        except Exception as e:
            print_error(f"Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print("📊 RELATÓRIO FINAL")
    print(f"{'='*80}{Colors.ENDC}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Resumo:{Colors.ENDC}")
    print(f"   Total de testes: {total}")
    print(f"   {Colors.OKGREEN}✅ Passou: {passed}{Colors.ENDC}")
    print(f"   {Colors.FAIL}❌ Falhou: {total - passed}{Colors.ENDC}")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    color = Colors.OKGREEN if success_rate >= 80 else Colors.WARNING if success_rate >= 60 else Colors.FAIL
    print(f"   {color}📈 Taxa de sucesso: {success_rate:.1f}%{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Detalhes:{Colors.ENDC}")
    for test_name, success in results:
        status = f"{Colors.OKGREEN}✅ PASSOU{Colors.ENDC}" if success else f"{Colors.FAIL}❌ FALHOU{Colors.ENDC}"
        print(f"   {test_name:<25} {status}")
    
    if success_rate == 100:
        print(f"\n{Colors.OKGREEN}🎉 Todos os testes passaram! MySQL está pronto para uso.{Colors.ENDC}")
    elif success_rate >= 80:
        print(f"\n{Colors.WARNING}⚠️  A maioria dos testes passou. Verifique os que falharam.{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}💥 Muitos testes falharam. Verifique a configuração do banco.{Colors.ENDC}")

if __name__ == "__main__":
    main()