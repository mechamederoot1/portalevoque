#!/usr/bin/env python3
"""
Script para verificar e atualizar estrutura do banco de dados
Verifica se todas as tabelas e colunas necessárias existem e as cria se não existirem
"""

import os
import sys
from sqlalchemy import inspect, text, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.exc import OperationalError, ProgrammingError
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, get_brazil_time

def verificar_e_criar_tabelas():
    """Verifica e cria tabelas que podem estar faltando"""
    
    with app.app_context():
        inspector = inspect(db.engine)
        tabelas_existentes = inspector.get_table_names()
        
        print("🔍 Verificando estrutura do banco de dados...")
        print(f"✅ Tabelas existentes: {len(tabelas_existentes)}")
        
        # Lista de tabelas que devem existir
        tabelas_obrigatorias = [
            'user', 'chamado', 'unidade', 'problema_reportado', 'item_internet',
            'solicitacao_compra', 'historicos_tickets', 'configuracoes',
            'log_acesso', 'log_acoes', 'configuracoes_avancadas', 'alertas_sistema',
            'backup_historico', 'relatorios_gerados', 'manutencao_sistema',
            'agentes_suporte', 'chamados_agentes', 'grupos_usuarios', 'grupos_membros',
            'grupos_unidades', 'grupos_permissoes', 'emails_massa', 'emails_massa_destinatarios',
            'sessoes_ativas', 'notificacoes_agentes', 'historico_atendimentos'
        ]
        
        tabelas_faltando = []
        for tabela in tabelas_obrigatorias:
            if tabela not in tabelas_existentes:
                tabelas_faltando.append(tabela)
        
        if tabelas_faltando:
            print(f"⚠️  Tabelas faltando: {tabelas_faltando}")
            print("🔨 Criando tabelas faltando...")
            
            try:
                db.create_all()
                print("✅ Todas as tabelas foram criadas com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao criar tabelas: {str(e)}")
        else:
            print("✅ Todas as tabelas obrigatórias existem!")
        
        return tabelas_faltando

def verificar_colunas_faltando():
    """Verifica se há colunas importantes faltando em tabelas existentes"""
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("\n🔍 Verificando colunas obrigatórias...")
        
        # Definir colunas obrigatórias por tabela
        colunas_obrigatorias = {
            'chamado': ['usuario_id', 'data_primeira_resposta', 'data_conclusao'],
            'agentes_suporte': ['especialidades', 'nivel_experiencia', 'max_chamados_simultaneos'],
            'chamados_agentes': ['observacoes', 'data_conclusao', 'ativo'],
            'user': ['_setores', 'bloqueado', 'tentativas_login', 'bloqueado_ate']
        }
        
        colunas_adicionadas = []
        
        for tabela, colunas in colunas_obrigatorias.items():
            try:
                colunas_existentes = [col['name'] for col in inspector.get_columns(tabela)]
                
                for coluna in colunas:
                    if coluna not in colunas_existentes:
                        print(f"⚠️  Coluna '{coluna}' faltando na tabela '{tabela}'")
                        
                        # Tentar adicionar a coluna
                        try:
                            if coluna == 'usuario_id':
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} INTEGER')
                                if tabela == 'chamado':
                                    db.engine.execute(f'ALTER TABLE {tabela} ADD FOREIGN KEY ({coluna}) REFERENCES user(id)')
                            elif coluna in ['data_primeira_resposta', 'data_conclusao']:
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} DATETIME')
                            elif coluna in ['observacoes', 'especialidades', '_setores']:
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} TEXT')
                            elif coluna in ['ativo', 'bloqueado']:
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} BOOLEAN DEFAULT FALSE')
                            elif coluna in ['max_chamados_simultaneos', 'tentativas_login']:
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} INTEGER DEFAULT 0')
                            elif coluna == 'nivel_experiencia':
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} VARCHAR(20) DEFAULT "Junior"')
                            elif coluna == 'bloqueado_ate':
                                db.engine.execute(f'ALTER TABLE {tabela} ADD COLUMN {coluna} DATETIME')
                            
                            colunas_adicionadas.append(f"{tabela}.{coluna}")
                            print(f"✅ Coluna '{coluna}' adicionada à tabela '{tabela}'")
                            
                        except Exception as e:
                            print(f"❌ Erro ao adicionar coluna '{coluna}' à tabela '{tabela}': {str(e)}")
                            
            except Exception as e:
                print(f"❌ Erro ao verificar tabela '{tabela}': {str(e)}")
        
        if colunas_adicionadas:
            print(f"\n✅ Colunas adicionadas: {len(colunas_adicionadas)}")
            for coluna in colunas_adicionadas:
                print(f"  - {coluna}")
        else:
            print("\n✅ Todas as colunas obrigatórias existem!")
        
        return colunas_adicionadas

def verificar_indices():
    """Verifica e cria índices importantes para performance"""
    
    with app.app_context():
        print("\n🔍 Verificando índices para performance...")
        
        indices_importantes = [
            "CREATE INDEX IF NOT EXISTS idx_chamado_status ON chamado(status)",
            "CREATE INDEX IF NOT EXISTS idx_chamado_data_abertura ON chamado(data_abertura)",
            "CREATE INDEX IF NOT EXISTS idx_chamado_usuario_id ON chamado(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_chamados_agentes_ativo ON chamados_agentes(ativo)",
            "CREATE INDEX IF NOT EXISTS idx_chamados_agentes_chamado_id ON chamados_agentes(chamado_id)",
            "CREATE INDEX IF NOT EXISTS idx_chamados_agentes_agente_id ON chamados_agentes(agente_id)",
            "CREATE INDEX IF NOT EXISTS idx_notificacoes_agente_id ON notificacoes_agentes(agente_id)",
            "CREATE INDEX IF NOT EXISTS idx_notificacoes_lida ON notificacoes_agentes(lida)",
            "CREATE INDEX IF NOT EXISTS idx_historico_atendimentos_chamado_id ON historico_atendimentos(chamado_id)",
            "CREATE INDEX IF NOT EXISTS idx_historico_atendimentos_agente_id ON historico_atendimentos(agente_id)"
        ]
        
        indices_criados = []
        
        for sql_index in indices_importantes:
            try:
                db.engine.execute(text(sql_index))
                nome_index = sql_index.split("idx_")[1].split(" ")[0] if "idx_" in sql_index else "unknown"
                indices_criados.append(nome_index)
            except Exception as e:
                # Ignorar erros de índices que já existem
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Erro ao criar índice: {str(e)}")
        
        print(f"✅ Índices verificados/criados: {len(indices_criados)}")
        
        return indices_criados

def migrar_dados_existentes():
    """Migra dados existentes para nova estrutura se necessário"""
    
    with app.app_context():
        print("\n🔄 Verificando migração de dados...")
        
        try:
            # Importar modelos
            from database import Chamado, User, ChamadoAgente, AgenteSuporte
            
            # 1. Vincular chamados sem usuario_id baseado no email
            chamados_sem_usuario = Chamado.query.filter_by(usuario_id=None).all()
            if chamados_sem_usuario:
                print(f"🔄 Vinculando {len(chamados_sem_usuario)} chamados aos usuários...")
                
                for chamado in chamados_sem_usuario:
                    usuario = User.query.filter_by(email=chamado.email).first()
                    if usuario:
                        chamado.usuario_id = usuario.id
                
                db.session.commit()
                print("✅ Chamados vinculados aos usuários!")
            
            # 2. Criar histórico para atribuições existentes
            from database import HistoricoAtendimento
            
            atribuicoes_sem_historico = []
            chamados_agentes = ChamadoAgente.query.all()
            
            for ca in chamados_agentes:
                historico_existe = HistoricoAtendimento.query.filter_by(
                    chamado_id=ca.chamado_id,
                    agente_id=ca.agente_id,
                    data_atribuicao=ca.data_atribuicao
                ).first()
                
                if not historico_existe:
                    atribuicoes_sem_historico.append(ca)
            
            if atribuicoes_sem_historico:
                print(f"🔄 Criando histórico para {len(atribuicoes_sem_historico)} atribuições...")
                
                for ca in atribuicoes_sem_historico:
                    historico = HistoricoAtendimento(
                        chamado_id=ca.chamado_id,
                        agente_id=ca.agente_id,
                        data_atribuicao=ca.data_atribuicao,
                        status_inicial='Aguardando',
                        observacoes_iniciais=ca.observacoes
                    )
                    
                    # Se tem data de conclusão, adicionar
                    if ca.data_conclusao and ca.chamado:
                        historico.data_conclusao = ca.data_conclusao
                        historico.status_final = ca.chamado.status
                        historico.calcular_tempo_resolucao()
                    
                    db.session.add(historico)
                
                db.session.commit()
                print("✅ Histórico criado para atribuições existentes!")
            
            print("✅ Migração de dados concluída!")
            
        except Exception as e:
            print(f"❌ Erro na migração de dados: {str(e)}")
            db.session.rollback()

def main():
    """Executa todas as verificações e atualizações do banco"""
    
    print("🚀 Iniciando verificação completa do banco de dados...")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # 1. Verificar e criar tabelas
        tabelas_criadas = verificar_e_criar_tabelas()
        
        # 2. Verificar e adicionar colunas
        colunas_criadas = verificar_colunas_faltando()
        
        # 3. Verificar e criar índices
        indices_criados = verificar_indices()
        
        # 4. Migrar dados existentes
        migrar_dados_existentes()
        
        print("\n" + "=" * 60)
        print("✅ VERIFICAÇÃO COMPLETA!")
        print(f"📊 Resumo:")
        print(f"  - Tabelas criadas: {len(tabelas_criadas) if tabelas_criadas else 0}")
        print(f"  - Colunas adicionadas: {len(colunas_criadas) if colunas_criadas else 0}")
        print(f"  - Índices criados: {len(indices_criados) if indices_criados else 0}")
        print("🎉 Banco de dados atualizado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        print("💡 Verifique as configurações do banco de dados e tente novamente.")
        return False
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
