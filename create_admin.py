#!/usr/bin/env python3
"""
Script para criar usuário admin padrão
"""
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Cria usuário admin padrão"""
    with app.app_context():
        try:
            # Verificar se usuário admin já existe
            existing_admin = User.query.filter_by(usuario='admin').first()
            if existing_admin:
                print(f"✅ Usuário admin já existe: {existing_admin.email}")
                print(f"   Atualizando senha para 'admin123'...")
                existing_admin.set_password('admin123')
                existing_admin.nivel_acesso = 'Administrador'
                existing_admin.setores = ['TI']
                existing_admin.bloqueado = False
                db.session.commit()
                print("✅ Senha do admin atualizada com sucesso!")
                return existing_admin
            
            # Criar novo usuário admin
            admin_user = User(
                nome='Administrador',
                sobrenome='Sistema',
                usuario='admin',
                email='admin@evoquefitness.com',
                nivel_acesso='Administrador',
                setor='TI',
                bloqueado=False
            )
            admin_user.set_password('admin123')
            admin_user.setores = ['TI']
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Usuário admin criado com sucesso!")
            print(f"   Usuário: admin")
            print(f"   Senha: admin123")
            print(f"   Email: admin@evoquefitness.com")
            print(f"   Nível: Administrador")
            
            return admin_user
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário admin: {str(e)}")
            db.session.rollback()
            return None

if __name__ == '__main__':
    create_admin_user()
