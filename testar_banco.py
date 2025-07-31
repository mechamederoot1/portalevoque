#!/usr/bin/env python3
"""
Script para testar a conexão com o banco de dados
"""

import os
from flask import Flask
from config import Config

def testar_conexao():
    try:
        # Criar app Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Importar database
        from database import db
        db.init_app(app)
        
        with app.app_context():
            # Testar conexão
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
            print("✅ Conexão com banco de dados estabelecida!")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas!")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testando conexão com banco de dados...")
    if testar_conexao():
        print("🎉 Teste concluído com sucesso!")
    else:
        print("💥 Teste falhou!")
