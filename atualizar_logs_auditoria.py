#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar estrutura de logs de auditoria com informações detalhadas
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from database import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def atualizar_estrutura_logs():
    """Atualiza estrutura de logs para incluir mais informações"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Atualizando estrutura de logs de auditoria...")
            
            from sqlalchemy import text, inspect
            
            # Verificar se colunas existem na tabela logs_acesso
            inspector = inspect(db.engine)
            colunas_logs_acesso = [col['name'] for col in inspector.get_columns('logs_acesso')]
            
            # Adicionar colunas faltantes
            colunas_necessarias = {
                'pais': 'VARCHAR(100)',
                'cidade': 'VARCHAR(100)', 
                'provedor_internet': 'VARCHAR(200)',
                'mac_address': 'VARCHAR(17)',
                'resolucao_tela': 'VARCHAR(20)',
                'timezone': 'VARCHAR(50)',
                'latitude': 'DECIMAL(10, 8)',
                'longitude': 'DECIMAL(11, 8)'
            }
            
            with db.engine.connect() as connection:
                for coluna, tipo in colunas_necessarias.items():
                    if coluna not in colunas_logs_acesso:
                        try:
                            sql = f"ALTER TABLE logs_acesso ADD COLUMN {coluna} {tipo}"
                            connection.execute(text(sql))
                            print(f"   ✅ Coluna {coluna} adicionada")
                        except Exception as e:
                            print(f"   ⚠ Erro ao adicionar coluna {coluna}: {str(e)}")
                
                connection.commit()
            
            # Verificar se tabela de sessões ativas existe
            tabelas_existentes = inspector.get_table_names()
            
            if 'sessoes_ativas' not in tabelas_existentes:
                sql_sessoes = """
                CREATE TABLE sessoes_ativas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    data_inicio DATETIME NOT NULL,
                    ultima_atividade DATETIME NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    pais VARCHAR(100),
                    cidade VARCHAR(100),
                    navegador VARCHAR(100),
                    sistema_operacional VARCHAR(100),
                    dispositivo VARCHAR(50),
                    INDEX idx_usuario_id (usuario_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_ativo (ativo),
                    FOREIGN KEY (usuario_id) REFERENCES user(id) ON DELETE CASCADE
                )
                """
                
                with db.engine.connect() as connection:
                    connection.execute(text(sql_sessoes))
                    connection.commit()
                    print("   ✅ Tabela sessoes_ativas criada")
            
            print("✅ Estrutura de logs atualizada com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar estrutura: {str(e)}")
            return False

if __name__ == "__main__":
    atualizar_estrutura_logs()
