#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados e verificar chamados
"""
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("=== TESTE DE CONEXÃO COM BANCO DE DADOS ===")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_PASSWORD: {'***' + os.getenv('DB_PASSWORD', '')[-3:] if os.getenv('DB_PASSWORD') else 'NÃO DEFINIDA'}")
print()

try:
    # Importar e configurar Flask app
    from app import app
    from database import db, Chamado
    
    with app.app_context():
        print("✅ Contexto da aplicação criado com sucesso")
        
        # Testar conexão com banco
        try:
            result = db.engine.execute("SELECT 1")
            print("✅ Conexão com banco de dados estabelecida")
        except Exception as e:
            print(f"❌ Erro na conexão com banco: {e}")
            sys.exit(1)
        
        # Verificar se a tabela chamado existe
        try:
            total_chamados = Chamado.query.count()
            print(f"✅ Tabela 'chamado' encontrada com {total_chamados} registros")
        except Exception as e:
            print(f"❌ Erro ao acessar tabela chamado: {e}")
            sys.exit(1)
        
        if total_chamados > 0:
            print("\n=== AMOSTRA DOS CHAMADOS ===")
            
            # Contar por status
            status_counts = {}
            chamados_amostra = Chamado.query.limit(5).all()
            
            for chamado in chamados_amostra:
                print(f"ID: {chamado.id} | Código: {getattr(chamado, 'codigo', 'N/A')} | Status: {getattr(chamado, 'status', 'N/A')} | Solicitante: {getattr(chamado, 'solicitante', 'N/A')}")
            
            # Contagem por status
            print("\n=== CONTAGEM POR STATUS ===")
            todos_chamados = Chamado.query.all()
            status_counts = {}
            
            for chamado in todos_chamados:
                status = getattr(chamado, 'status', 'Indefinido')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"{status}: {count}")
        else:
            print("⚠️  Nenhum chamado encontrado no banco de dados")
            
            # Listar todas as tabelas disponíveis
            print("\n=== TABELAS DISPONÍVEIS ===")
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tabelas encontradas: {tables}")

except Exception as e:
    print(f"❌ Erro geral: {e}")
    import traceback
    traceback.print_exc()
