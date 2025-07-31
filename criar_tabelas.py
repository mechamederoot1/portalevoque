#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar/migrar todas as tabelas do banco de dados
Executa automaticamente todas as migrações necessárias
"""

import os
import sys
import json
from datetime import datetime
import pytz

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar diretamente as configurações e criar a aplicação
from flask import Flask
from config import Config
from database import db, init_app, seed_unidades, get_brazil_time
from database import (
    User, Chamado, Unidade, ProblemaReportado, ItemInternet, 
    HistoricoTicket, Configuracao, LogAcesso, LogAcao, 
    ConfiguracaoAvancada, AlertaSistema, BackupHistorico, 
    RelatorioGerado, ManutencaoSistema, AgenteSuporte, 
    ChamadoAgente, GrupoUsuarios, GrupoMembro, GrupoUnidade, 
    GrupoPermissao, EmailMassa, EmailMassaDestinatario
)

def create_database_migration():
    """Cria e migra todas as tabelas do banco de dados"""
    print("=" * 60)
    print("INICIANDO MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 60)

    # Criar aplicação Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar o banco de dados
    from database import db
    db.init_app(app)
    
    with app.app_context():
        try:
            print("\n1. Conectando ao banco de dados...")
            
            # Verificar conexão
            try:
                db.engine.execute('SELECT 1')
                print("   ✓ Conexão com banco de dados estabelecida")
            except Exception as e:
                print(f"   ✗ Erro na conexão: {str(e)}")
                return False
            
            print("\n2. Criando/atualizando estrutura das tabelas...")
            
            # Criar todas as tabelas
            db.create_all()
            print("   ✓ Estrutura das tabelas criada/atualizada")
            
            print("\n3. Executando migrações específicas...")
            
            # Migração: Verificar e adicionar colunas faltantes
            execute_custom_migrations()
            
            print("\n4. Inicializando dados padrão...")
            
            # Seed das unidades e dados básicos
            seed_unidades()
            print("   ✓ Unidades e dados básicos inseridos")
            
            # Criar usuário administrador padrão se não existir
            create_default_admin()
            
            # Inicializar configurações padrão
            initialize_default_configurations()
            
            print("\n5. Validando estrutura final...")
            
            # Validar todas as tabelas
            validate_table_structure()
            
            print("\n" + "=" * 60)
            print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            print(f"Data/Hora: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S')}")
            print("\nTabelas criadas/atualizadas:")
            print("- user (usuários)")
            print("- chamado (chamados/tickets)")
            print("- unidade (unidades)")
            print("- problema_reportado (tipos de problemas)")
            print("- item_internet (itens de internet)")
            print("- historicos_tickets (histórico de tickets)")
            print("- configuracoes (configurações básicas)")
            print("- logs_acesso (logs de acesso)")
            print("- logs_acoes (logs de ações)")
            print("- configuracoes_avancadas (configurações avançadas)")
            print("- alertas_sistema (alertas do sistema)")
            print("- backup_historico (histórico de backups)")
            print("- relatorios_gerados (relatórios gerados)")
            print("- manutencao_sistema (manutenção do sistema)")
            print("- agentes_suporte (agentes de suporte)")
            print("- chamado_agente (atribuições de chamados)")
            print("- grupos_usuarios (grupos de usuários)")
            print("- grupo_membros (membros dos grupos)")
            print("- grupo_unidades (unidades dos grupos)")
            print("- grupo_permissoes (permissões dos grupos)")
            print("- emails_massa (emails em massa)")
            print("- email_massa_destinatarios (destinatários de emails)")
            print("\n✓ Sistema pronto para uso!")
            
            return True
            
        except Exception as e:
            print(f"\n✗ ERRO DURANTE A MIGRAÇÃO: {str(e)}")
            db.session.rollback()
            return False

def execute_custom_migrations():
    """Executa migrações customizadas para colunas específicas"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Migração 1: Adicionar usuario_id à tabela chamado se não existir
        try:
            columns = [col['name'] for col in inspector.get_columns('chamado')]
            if 'usuario_id' not in columns:
                db.engine.execute(text('ALTER TABLE chamado ADD COLUMN usuario_id INTEGER'))
                try:
                    db.engine.execute(text('ALTER TABLE chamado ADD FOREIGN KEY (usuario_id) REFERENCES user(id)'))
                except:
                    pass  # Foreign key pode já existir
                print("   ✓ Coluna usuario_id adicionada à tabela chamado")
        except Exception as e:
            print(f"   ⚠ Aviso na migração chamado.usuario_id: {str(e)}")
        
        # Migração 2: Verificar coluna _setores na tabela user
        try:
            columns = [col['name'] for col in inspector.get_columns('user')]
            if '_setores' not in columns:
                db.engine.execute(text('ALTER TABLE user ADD COLUMN _setores TEXT'))
                print("   ✓ Coluna _setores adicionada à tabela user")
        except Exception as e:
            print(f"   ⚠ Aviso na migração user._setores: {str(e)}")
        
        # Migração 3: Verificar todas as tabelas existem
        existing_tables = inspector.get_table_names()
        required_tables = [
            'user', 'chamado', 'unidade', 'problema_reportado', 'item_internet',
            'historicos_tickets', 'configuracoes', 'logs_acesso', 'logs_acoes',
            'configuracoes_avancadas', 'alertas_sistema', 'backup_historico',
            'relatorios_gerados', 'manutencao_sistema', 'agentes_suporte',
            'chamado_agente', 'grupos_usuarios', 'grupo_membros', 'grupo_unidades',
            'grupo_permissoes', 'emails_massa', 'email_massa_destinatarios'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        if missing_tables:
            print(f"   ⚠ Tabelas faltantes serão criadas: {', '.join(missing_tables)}")
        else:
            print("   ✓ Todas as tabelas necessárias estão presentes")
        
        # Commit das migrações
        db.session.commit()
        
    except Exception as e:
        print(f"   ✗ Erro nas migrações customizadas: {str(e)}")
        db.session.rollback()

def create_default_admin():
    """Cria usuário administrador padrão se não existir"""
    try:
        admin_user = User.query.filter_by(usuario='admin').first()
        if not admin_user:
            admin = User(
                nome='Administrador',
                sobrenome='Sistema',
                usuario='admin',
                email='admin@evoquefitness.com',
                nivel_acesso='Administrador',
                setor='TI'
            )
            admin.set_password('admin123')  # Senha padrão - DEVE SER ALTERADA
            admin.setores = ['TI']
            
            db.session.add(admin)
            db.session.commit()
            
            print("   ✓ Usuário administrador padrão criado")
            print("   📧 Email: admin@evoquefitness.com")
            print("   🔑 Senha: admin123 (ALTERE IMEDIATAMENTE)")
        else:
            print("   ✓ Usuário administrador já existe")
            
    except Exception as e:
        print(f"   ✗ Erro ao criar usuário administrador: {str(e)}")
        db.session.rollback()

def initialize_default_configurations():
    """Inicializa configurações padrão do sistema"""
    try:
        # Configurações básicas
        configuracoes_basicas = {
            'sistema_inicializado': {
                'valor': 'true',
                'descricao': 'Indica se o sistema foi inicializado corretamente'
            },
            'versao_database': {
                'valor': '1.0.0',
                'descricao': 'Versão atual do banco de dados'
            },
            'data_criacao': {
                'valor': get_brazil_time().isoformat(),
                'descricao': 'Data de criação do banco de dados'
            }
        }
        
        for chave, config in configuracoes_basicas.items():
            existing = Configuracao.query.filter_by(chave=chave).first()
            if not existing:
                nova_config = Configuracao(
                    chave=chave,
                    valor=config['valor']
                )
                db.session.add(nova_config)
        
        # Configurações avançadas específicas da migração
        config_migracao = ConfiguracaoAvancada.query.filter_by(chave='sistema.database_migrated').first()
        if not config_migracao:
            config_migracao = ConfiguracaoAvancada(
                chave='sistema.database_migrated',
                valor='true',
                descricao='Indica se a migração do banco de dados foi executada',
                tipo='boolean',
                categoria='sistema'
            )
            db.session.add(config_migracao)
        
        db.session.commit()
        print("   ✓ Configurações padrão inicializadas")
        
    except Exception as e:
        print(f"   ✗ Erro ao inicializar configurações: {str(e)}")
        db.session.rollback()

def validate_table_structure():
    """Valida se todas as tabelas e colunas necessárias existem"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        # Validar tabelas principais
        tables_to_check = {
            'user': ['id', 'nome', 'sobrenome', 'usuario', 'email', 'senha_hash', 'nivel_acesso'],
            'chamado': ['id', 'codigo', 'protocolo', 'solicitante', 'email', 'status', 'prioridade'],
            'agentes_suporte': ['id', 'usuario_id', 'ativo', 'nivel_experiencia'],
            'grupos_usuarios': ['id', 'nome', 'descricao', 'ativo'],
            'logs_acesso': ['id', 'usuario_id', 'data_acesso', 'ip_address'],
            'configuracoes': ['id', 'chave', 'valor'],
        }
        
        validation_errors = []
        
        for table_name, required_columns in tables_to_check.items():
            if table_name in inspector.get_table_names():
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                missing_columns = [col for col in required_columns if col not in existing_columns]
                if missing_columns:
                    validation_errors.append(f"Tabela {table_name}: colunas faltantes {missing_columns}")
            else:
                validation_errors.append(f"Tabela {table_name} não encontrada")
        
        if validation_errors:
            print("   ⚠ Avisos de validação:")
            for error in validation_errors:
                print(f"     - {error}")
        else:
            print("   ✓ Estrutura do banco validada com sucesso")
        
        # Contar registros em tabelas principais
        try:
            user_count = User.query.count()
            chamado_count = Chamado.query.count()
            unidade_count = Unidade.query.count()
            
            print(f"   📊 Estatísticas:")
            print(f"     - Usuários: {user_count}")
            print(f"     - Chamados: {chamado_count}")
            print(f"     - Unidades: {unidade_count}")
            
        except Exception as e:
            print(f"   ⚠ Não foi possível obter estatísticas: {str(e)}")
            
    except Exception as e:
        print(f"   ✗ Erro na validação: {str(e)}")

def main():
    """Função principal do script"""
    print("Script de Migração do Banco de Dados - ERP Evoque Fitness")
    print("Versão: 1.0.0")
    print("Data: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    # Verificar se o arquivo .env existe
    if not os.path.exists('.env'):
        print("\n⚠ AVISO: Arquivo .env não encontrado!")
        print("Certifique-se de que as variáveis de ambiente estão configuradas.")
        response = input("Deseja continuar mesmo assim? (s/N): ")
        if response.lower() != 's':
            print("Migração cancelada pelo usuário.")
            return
    
    # Executar migração
    success = create_database_migration()
    
    if success:
        print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\nPróximos passos:")
        print("1. Faça login com o usuário admin (senha: admin123)")
        print("2. ALTERE IMEDIATAMENTE a senha do administrador")
        print("3. Configure as variáveis de ambiente de produção")
        print("4. Execute testes para validar o funcionamento")
        return 0
    else:
        print("\n❌ MIGRAÇÃO FALHOU!")
        print("Verifique os logs de erro acima e tente novamente.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
