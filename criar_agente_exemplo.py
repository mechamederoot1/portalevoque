#!/usr/bin/env python3
"""
Script para criar um usuário agente de exemplo
"""
from app import app
from database import db, User, AgenteSuporte
from werkzeug.security import generate_password_hash

def criar_agente_exemplo():
    with app.app_context():
        try:
            # Verificar se já existe
            agente_existente = User.query.filter_by(usuario='agente.suporte').first()
            if agente_existente:
                print("✅ Usuário agente.suporte já existe")
                
                # Verificar se tem registro de agente
                agente_reg = AgenteSuporte.query.filter_by(usuario_id=agente_existente.id).first()
                if not agente_reg:
                    agente_reg = AgenteSuporte(
                        usuario_id=agente_existente.id,
                        ativo=True,
                        nivel_experiencia='senior',
                        max_chamados_simultaneos=10
                    )
                    agente_reg.especialidades_list = ['Sistema EVO', 'Notebook/Desktop', 'Internet']
                    db.session.add(agente_reg)
                    db.session.commit()
                    print("✅ Registro de agente criado")
                else:
                    print("✅ Registro de agente já existe")
                return

            # Criar usuário agente
            novo_agente = User(
                nome='Agente',
                sobrenome='Suporte',
                usuario='agente.suporte',
                email='agente@evoquefitness.com',
                nivel_acesso='Agente de Suporte',
                setor='TI',
                senha_hash=generate_password_hash('agente123'),
                alterar_senha_primeiro_acesso=False
            )
            novo_agente.setores = ['TI']
            
            db.session.add(novo_agente)
            db.session.flush()  # Para obter o ID
            
            # Criar registro de agente
            agente_suporte = AgenteSuporte(
                usuario_id=novo_agente.id,
                ativo=True,
                nivel_experiencia='senior',
                max_chamados_simultaneos=10
            )
            agente_suporte.especialidades_list = ['Sistema EVO', 'Notebook/Desktop', 'Internet']
            
            db.session.add(agente_suporte)
            db.session.commit()
            
            print("✅ Usuário agente criado com sucesso!")
            print("🔑 Credenciais:")
            print("   Usuário: agente.suporte")
            print("   Senha: agente123")
            print("   Acesso: /ti/painel-agente")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    criar_agente_exemplo()
