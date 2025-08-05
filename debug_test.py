#!/usr/bin/env python3
"""
Debug script to test user authentication and API
"""
import sys
import os

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, User
from flask import url_for
import requests

def test_login_and_api():
    """Testa login e chamada da API"""
    with app.app_context():
        try:
            # Verificar se admin existe
            admin_user = User.query.filter_by(usuario='admin').first()
            if not admin_user:
                print("❌ Usuário admin não encontrado")
                return False
                
            print(f"✅ Usuário admin encontrado:")
            print(f"   ID: {admin_user.id}")
            print(f"   Nome: {admin_user.nome} {admin_user.sobrenome}")
            print(f"   Email: {admin_user.email}")
            print(f"   Nível: {admin_user.nivel_acesso}")
            print(f"   Setores: {admin_user.setores}")
            print(f"   Bloqueado: {admin_user.bloqueado}")
            print(f"   tem_permissao('Administrador'): {admin_user.tem_permissao('Administrador')}")
            print(f"   tem_acesso_setor('ti'): {admin_user.tem_acesso_setor('ti')}")
            
            # Testar password
            password_valid = admin_user.check_password('admin123')
            print(f"   Senha válida: {password_valid}")
            
            # Listar todos os usuários
            all_users = User.query.all()
            print(f"\n📊 Total de usuários no banco: {len(all_users)}")
            for user in all_users:
                print(f"   - {user.usuario} ({user.email}) - {user.nivel_acesso}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_login_and_api()
