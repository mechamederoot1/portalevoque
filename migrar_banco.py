#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para criar todas as tabelas do banco de dados
"""

import os
import sys
from flask import Flask
from config import Config

def main():
    print("🚀 Iniciando migração do banco de dados...")
    
    try:
        # Criar aplicação Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Importar e inicializar o banco
        from database import db, seed_unidades, User
        db.init_app(app)
        
        with app.app_context():
            print("📊 Criando todas as tabelas...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/atualizadas com sucesso!")
            
            # Executar seed de unidades
            print("🏢 Inserindo unidades padrão...")
            seed_unidades()
            print("✅ Unidades inseridas!")
            
            # Verificar se existe usuário admin
            admin_user = User.query.filter_by(usuario='admin').first()
            if not admin_user:
                print("👤 Criando usuário administrador padrão...")
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
                print("✅ Usuário admin criado!")
                print("📧 Email: admin@evoquefitness.com")
                print("🔑 Senha: admin123")
            else:
                print("✅ Usuário admin já existe!")
            
            print("\n" + "="*50)
            print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*50)
            print("✅ Banco de dados pronto para uso!")
            print("🌐 Você pode iniciar o servidor com: python app.py")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Script executado com sucesso!")
    else:
        print("\n❌ Script falhou!")
        sys.exit(1)
