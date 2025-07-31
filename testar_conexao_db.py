#!/usr/bin/env python3
"""
Script simples para testar a conexão com o banco de dados.
"""

import os
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine, text

# Carregar variáveis de ambiente
load_dotenv()

def testar_conexao():
    """Testa a conexão com o banco de dados"""
    print("🔗 Testando conexão com banco de dados...")
    
    # Configurações do banco
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER') 
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    
    print(f"📊 Configurações:")
    print(f"   Host: {DB_HOST}")
    print(f"   User: {DB_USER}")
    print(f"   Database: {DB_NAME}")
    print(f"   Port: {DB_PORT}")
    print()
    
    try:
        # Conectar usando SQLAlchemy
        connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        print(f"🔗 String de conexão: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
        
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
        print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
        print(f"✅ Teste de query executado: resultado = {row[0]}")
        
        # Listar algumas tabelas
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tabelas = [row[0] for row in result.fetchall()]
            
        print(f"📋 Tabelas encontradas ({len(tabelas)}): {', '.join(tabelas[:10])}")
        if len(tabelas) > 10:
            print(f"    ... e mais {len(tabelas) - 10} tabelas")
            
        return True
        
    except Exception as e:
        print(f"❌ ERRO NA CONEXÃO: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = testar_conexao()
    if sucesso:
        print("\n🎉 Banco de dados acessível - pode executar a migração!")
    else:
        print("\n⚠️  Verifique as configurações do banco antes de executar a migração")
