#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Flask para criar banco de dados
"""
import os
from flask import Flask
from config import Config
from database import db, init_app, seed_unidades, get_brazil_time

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar banco
    db.init_app(app)
    
    return app

def create_tables():
    """Cria todas as tabelas do banco de dados"""
    app = create_app()
    
    with app.app_context():
        print("Conectando ao banco de dados...")
        
        try:
            # Testar conexão
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text('SELECT 1'))
                print("✅ Conexão com banco estabelecida!")
            
            # Criar todas as tabelas
            print("Criando estrutura das tabelas...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Seed dos dados básicos
            print("Inserindo dados iniciais...")
            seed_unidades()
            print("✅ Dados iniciais inseridos!")
            
            # Criar usuário admin
            from database import User
            admin_exists = User.query.filter_by(usuario='admin').first()
            if not admin_exists:
                admin = User(
                    nome='Administrador',
                    sobrenome='Sistema',
                    usuario='admin',
                    email='admin@evoquefitness.com',
                    nivel_acesso='Administrador',
                    setor='TI'
                )
                admin.set_password('admin123')
                admin.setores = ['TI']
                
                db.session.add(admin)
                db.session.commit()
                
                print("✅ Usuário administrador criado!")
                print("   📧 Email: admin@evoquefitness.com")
                print("   🔑 Senha: admin123 (ALTERE IMEDIATAMENTE)")
            else:
                print("✅ Usuário administrador já existe!")
            
            print("\n" + "=" * 60)
            print("🎉 BANCO DE DADOS CRIADO COM SUCESSO!")
            print("=" * 60)
            print(f"Data/Hora: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S')}")
            print("\nTabelas principais criadas:")
            print("- user (usuários)")
            print("- chamado (chamados/tickets)")
            print("- unidade (unidades)")
            print("- problema_reportado (tipos de problemas)")
            print("- item_internet (itens de internet)")
            print("- Mais 17 tabelas auxiliares para funcionalidades avançadas")
            print("\n✅ Sistema pronto para uso!")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            return False

if __name__ == "__main__":
    create_tables()
