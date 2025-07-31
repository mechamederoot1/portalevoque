#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para setup rápido do banco de dados via Flask
"""

from flask import Flask, jsonify
from config import Config
from database import *
from datetime import datetime, timedelta
import random

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def inserir_dados_completos():
    """Insere todos os dados necessários para demonstração"""
    try:
        print("🔄 Inserindo dados para demonstração...")
        
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
        
        # 2. Criar usuário de teste
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
        logs_existentes = LogAcesso.query.count()
        
        if logs_existentes < 10:
            # Criar logs de acesso para demonstração
            ips_exemplo = ['192.168.1.100', '192.168.1.101', '192.168.1.102', '10.0.0.50', '172.16.0.10']
            navegadores = ['Chrome', 'Firefox', 'Safari', 'Edge']
            sistemas = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
            dispositivos = ['Desktop', 'Mobile', 'Tablet']
            cidades = ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Brasília']
            paises = ['Brasil'] * 5
            
            usuarios = [admin, usuario_teste, agente_teste]
            
            for i in range(15):
                data_acesso = get_brazil_time().replace(tzinfo=None) - timedelta(hours=random.randint(1, 168))  # Última semana
                duracao = random.randint(15, 240)  # 15 min a 4 horas
                usuario_escolhido = random.choice(usuarios)
                
                log = LogAcesso(
                    usuario_id=usuario_escolhido.id,
                    data_acesso=data_acesso,
                    data_logout=data_acesso + timedelta(minutes=duracao) if random.choice([True, False, False]) else None,
                    ip_address=random.choice(ips_exemplo),
                    user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {random.choice(navegadores)}/91.0.4472.124 Safari/537.36",
                    duracao_sessao=duracao if random.choice([True, False]) else None,
                    ativo=random.choice([True, False]),
                    session_id=f"sess_{random.randint(100000, 999999)}",
                    navegador=random.choice(navegadores),
                    sistema_operacional=random.choice(sistemas),
                    dispositivo=random.choice(dispositivos),
                    pais=random.choice(paises),
                    cidade=random.choice(cidades),
                    provedor_internet=random.choice(['Vivo', 'Claro', 'TIM', 'NET', 'Oi']),
                    resolucao_tela=random.choice(['1920x1080', '1366x768', '1440x900', '2560x1440']),
                    timezone='America/Sao_Paulo'
                )
                db.session.add(log)
            
            print("✅ Logs de acesso de exemplo criados")
        
        # 9. Inserir logs de ações de exemplo
        logs_acoes_existentes = LogAcao.query.count()
        
        if logs_acoes_existentes < 5:
            acoes_exemplo = [
                ('Login realizado', 'autenticacao', 'Usuário fez login no sistema'),
                ('Chamado criado', 'chamado', 'Novo chamado de suporte criado'),
                ('Configuração alterada', 'configuracao', 'Configuração do sistema modificada'),
                ('Usuário bloqueado', 'usuario', 'Usuário foi bloqueado pelo administrador'),
                ('Backup criado', 'sistema', 'Backup automático do banco de dados'),
                ('Agente atribuído', 'chamado', 'Agente foi atribuído a um chamado'),
                ('Email enviado', 'notificacao', 'Email de notificação enviado'),
                ('Relatório gerado', 'relatorio', 'Relatório de SLA gerado'),
            ]
            
            for i in range(12):
                acao, categoria, detalhes = random.choice(acoes_exemplo)
                data_acao = get_brazil_time().replace(tzinfo=None) - timedelta(hours=random.randint(1, 72))
                
                log_acao = LogAcao(
                    usuario_id=random.choice(usuarios).id,
                    acao=acao,
                    categoria=categoria,
                    detalhes=detalhes,
                    data_acao=data_acao,
                    ip_address=random.choice(ips_exemplo),
                    sucesso=random.choice([True, True, True, False]),  # 75% de sucesso
                    recurso_afetado=str(random.randint(1, 100)),
                    tipo_recurso=categoria
                )
                db.session.add(log_acao)
            
            print("✅ Logs de ações de exemplo criados")
        
        # 10. Criar sessões ativas de exemplo
        sessoes_existentes = SessaoAtiva.query.count()
        
        if sessoes_existentes < 3:
            for usuario in usuarios:
                if random.choice([True, False]):  # 50% chance de ter sessão ativa
                    data_inicio = get_brazil_time().replace(tzinfo=None) - timedelta(minutes=random.randint(5, 120))
                    
                    sessao = SessaoAtiva(
                        usuario_id=usuario.id,
                        session_id=f"sess_ativa_{random.randint(100000, 999999)}",
                        ip_address=random.choice(ips_exemplo),
                        user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        data_inicio=data_inicio,
                        ultima_atividade=data_inicio + timedelta(minutes=random.randint(1, 30)),
                        ativo=True,
                        pais='Brasil',
                        cidade=random.choice(cidades),
                        navegador=random.choice(navegadores),
                        sistema_operacional=random.choice(sistemas),
                        dispositivo=random.choice(dispositivos)
                    )
                    db.session.add(sessao)
            
            print("✅ Sessões ativas de exemplo criadas")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("🎉 DADOS DE DEMONSTRAÇÃO INSERIDOS COM SUCESSO!")
        print("=" * 60)
        print(f"Data/Hora: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S')}")
        print("\n📊 Resumo dos dados inseridos:")
        print(f"- Usuários: {User.query.count()}")
        print(f"- Chamados: {Chamado.query.count()}")
        print(f"- Agentes: {AgenteSuporte.query.count()}")
        print(f"- Logs de Acesso: {LogAcesso.query.count()}")
        print(f"- Logs de Ações: {LogAcao.query.count()}")
        print(f"- Sessões Ativas: {SessaoAtiva.query.count()}")
        print(f"- Unidades: {Unidade.query.count()}")
        print(f"- Problemas: {ProblemaReportado.query.count()}")
        
        print("\n🔑 Credenciais de acesso:")
        print("Administrador: admin / admin123")
        print("Usuário Teste: joao.silva / teste123")
        print("Agente: maria.santos / agente123")
        print("\n✅ Agora você pode acessar a seção 'Auditoria & Logs' e ver os dados!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        inserir_dados_completos()
