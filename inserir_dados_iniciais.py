#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inserir dados iniciais necessários para o funcionamento do sistema
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from database import db, get_brazil_time, User, Chamado, Unidade, ProblemaReportado, ItemInternet, AgenteSuporte

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def inserir_dados_iniciais():
    """Insere dados iniciais necessários para o funcionamento"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Inserindo dados iniciais...")
            
            # 1. Verificar/criar usuário administrador
            admin = User.query.filter_by(usuario='admin').first()
            if not admin:
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
                print("✅ Usuário administrador criado")
            else:
                print("✅ Usuário administrador já existe")
            
            # 2. Criar usuário de teste para chamado
            usuario_teste = User.query.filter_by(email='teste@evoquefitness.com').first()
            if not usuario_teste:
                usuario_teste = User(
                    nome='João',
                    sobrenome='Silva',
                    usuario='joao.silva',
                    email='teste@evoquefitness.com',
                    nivel_acesso='Gestor',
                    setor='Comercial'
                )
                usuario_teste.set_password('teste123')
                usuario_teste.setores = ['Comercial']
                db.session.add(usuario_teste)
                print("✅ Usuário de teste criado")
            
            # 3. Criar agente de suporte
            agente_teste = User.query.filter_by(email='agente@evoquefitness.com').first()
            if not agente_teste:
                agente_teste = User(
                    nome='Maria',
                    sobrenome='Santos',
                    usuario='maria.santos',
                    email='agente@evoquefitness.com',
                    nivel_acesso='Agente de Suporte',
                    setor='TI'
                )
                agente_teste.set_password('agente123')
                agente_teste.setores = ['TI']
                db.session.add(agente_teste)
                print("✅ Usuário agente criado")
            
            db.session.commit()
            
            # 4. Criar registro de agente de suporte
            agente_suporte = AgenteSuporte.query.filter_by(usuario_id=agente_teste.id).first()
            if not agente_suporte:
                agente_suporte = AgenteSuporte(
                    usuario_id=agente_teste.id,
                    ativo=True,
                    nivel_experiencia='senior',
                    max_chamados_simultaneos=15
                )
                agente_suporte.especialidades_list = ['Sistema EVO', 'Notebook/Desktop', 'Internet']
                db.session.add(agente_suporte)
                print("✅ Agente de suporte registrado")
            
            # 5. Verificar unidades
            unidade_teste = Unidade.query.filter_by(nome='GUILHERMINA - 1').first()
            if not unidade_teste:
                unidade_teste = Unidade(nome='GUILHERMINA - 1')
                db.session.add(unidade_teste)
                print("✅ Unidade de teste criada")
            
            # 6. Verificar problema reportado
            problema_teste = ProblemaReportado.query.filter_by(nome='Sistema EVO').first()
            if not problema_teste:
                problema_teste = ProblemaReportado(
                    nome='Sistema EVO',
                    prioridade_padrao='Normal',
                    requer_item_internet=False
                )
                db.session.add(problema_teste)
                print("✅ Problema reportado criado")
            
            db.session.commit()
            
            # 7. Criar chamado de teste
            chamado_teste = Chamado.query.filter_by(codigo='TI-2025-001').first()
            if not chamado_teste:
                data_abertura = get_brazil_time().replace(tzinfo=None) - timedelta(hours=2)
                
                chamado_teste = Chamado(
                    codigo='TI-2025-001',
                    protocolo='PROT-001-2025',
                    solicitante='João Silva',
                    cargo='Gerente Comercial',
                    email='teste@evoquefitness.com',
                    telefone='(11) 99999-9999',
                    unidade='GUILHERMINA - 1',
                    problema='Sistema EVO',
                    descricao='Sistema EVO apresentando lentidão durante o cadastro de novos alunos. Erro intermitente ao salvar dados.',
                    data_abertura=data_abertura,
                    status='Aberto',
                    prioridade='Alta',
                    usuario_id=usuario_teste.id
                )
                db.session.add(chamado_teste)
                print("✅ Chamado de teste criado")
            
            db.session.commit()
            
            # 8. Inserir logs de acesso de exemplo
            from database import LogAcesso
            logs_existentes = LogAcesso.query.count()
            
            if logs_existentes < 5:
                # Criar alguns logs de acesso para demonstração
                ips_exemplo = ['192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.50', '172.16.0.10']
                navegadores = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
                ]
                
                usuarios = [admin, usuario_teste, agente_teste]
                
                for i in range(10):
                    data_acesso = get_brazil_time().replace(tzinfo=None) - timedelta(hours=random.randint(1, 72))
                    duracao = random.randint(15, 240)  # 15 min a 4 horas
                    
                    log = LogAcesso(
                        usuario_id=random.choice(usuarios).id,
                        data_acesso=data_acesso,
                        data_logout=data_acesso + timedelta(minutes=duracao) if random.choice([True, False]) else None,
                        ip_address=random.choice(ips_exemplo),
                        user_agent=random.choice(navegadores),
                        duracao_sessao=duracao if random.choice([True, False]) else None,
                        ativo=random.choice([True, False]),
                        session_id=f"sess_{random.randint(100000, 999999)}",
                        navegador=random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                        sistema_operacional=random.choice(['Windows', 'macOS', 'Linux']),
                        dispositivo=random.choice(['Desktop', 'Mobile', 'Tablet'])
                    )
                    db.session.add(log)
                
                print("✅ Logs de acesso de exemplo criados")
            
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("🎉 DADOS INICIAIS INSERIDOS COM SUCESSO!")
            print("=" * 60)
            print(f"Data/Hora: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S')}")
            print("\n📊 Resumo dos dados inseridos:")
            print(f"- Usuários: {User.query.count()}")
            print(f"- Chamados: {Chamado.query.count()}")
            print(f"- Agentes: {AgenteSuporte.query.count()}")
            print(f"- Logs de Acesso: {LogAcesso.query.count()}")
            print(f"- Unidades: {Unidade.query.count()}")
            print(f"- Problemas: {ProblemaReportado.query.count()}")
            
            print("\n🔑 Credenciais de acesso:")
            print("Administrador: admin / admin123")
            print("Usuário Teste: joao.silva / teste123")
            print("Agente: maria.santos / agente123")
            print("\n✅ Sistema pronto para uso!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Script de Inserção de Dados Iniciais - ERP Evoque Fitness")
    print("Versão: 1.0.0")
    print("Data: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("\n🚀 Iniciando inserção de dados...")
    
    success = inserir_dados_iniciais()
    
    if success:
        print("\n🎉 INSERÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("\n❌ INSERÇÃO FALHOU!")
        print("Verifique os logs de erro acima.")
