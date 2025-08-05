#!/usr/bin/env python3
"""
Script para testar a configuração do banco de dados
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== TESTE DE CONFIGURAÇÃO ===")
print(f"DB_HOST: {os.environ.get('DB_HOST')}")
print(f"DB_USER: {os.environ.get('DB_USER')}")
print(f"DB_PASSWORD: {'***' if os.environ.get('DB_PASSWORD') else 'None'}")
print(f"DB_NAME: {os.environ.get('DB_NAME')}")
print(f"DB_PORT: {os.environ.get('DB_PORT')}")

try:
    from config import get_config
    config_class = get_config()
    print(f"\nConfiguração selecionada: {config_class.__name__}")
    
    # Instanciar configuração para testar
    if hasattr(config_class, 'SQLALCHEMY_DATABASE_URI'):
        print(f"SQLALCHEMY_DATABASE_URI: {config_class.SQLALCHEMY_DATABASE_URI[:50]}...")
    else:
        print("❌ SQLALCHEMY_DATABASE_URI não encontrada!")
        
except Exception as e:
    print(f"❌ Erro ao carregar configuração: {e}")

print("\n=== TESTE CONCLUÍDO ===")
