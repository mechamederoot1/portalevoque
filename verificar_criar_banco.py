#!/usr/bin/env python3
"""
Script para verificar e criar todas as tabelas e colunas do banco de dados
baseado no modelo database.py

Este script:
1. Verifica se todas as tabelas existem
2. Verifica se todas as colunas de cada tabela existem
3. Cria tabelas e colunas faltantes automaticamente
4. Cria índices e chaves estrangeiras
5. Inicializa dados padrão se necessário
"""

import os
import sys
import json
from datetime import datetime
import pytz

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verificar_criar_estrutura_banco():
    """Função principal para verificar e criar estrutura do banco"""
    print("=" * 80)
    print("🔧 VERIFICAÇÃO E CRIAÇÃO DA ESTRUTURA DO BANCO DE DADOS")
    print("=" * 80)
    
    try:
        # Importar depois de configurar o path
        from app import app
        from database import db, get_brazil_time
        from sqlalchemy import inspect, text, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, Float, Numeric
        from sqlalchemy.exc import SQLAlchemyError
        
        with app.app_context():
            print("✅ Contexto da aplicação inicializado")
            
            # Conectar ao banco
            try:
                db.engine.connect()
                print("✅ Conexão com banco de dados estabelecida")
            except Exception as e:
                print(f"❌ Erro ao conectar com o banco: {str(e)}")
                return False
            
            # Verificar estrutura das tabelas
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            print(f"\n📊 Tabelas existentes no banco: {len(existing_tables)}")
            for table in existing_tables:
                print(f"   • {table}")
            
            # Definir estrutura esperada baseada no database.py
            estrutura_esperada = {
                'user': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome': {'tipo': 'VARCHAR(150)', 'nullable': False},
                        'sobrenome': {'tipo': 'VARCHAR(150)', 'nullable': False},
                        'usuario': {'tipo': 'VARCHAR(80)', 'nullable': False, 'unique': True},
                        'email': {'tipo': 'VARCHAR(120)', 'nullable': False, 'unique': True},
                        'senha_hash': {'tipo': 'VARCHAR(128)', 'nullable': False},
                        'alterar_senha_primeiro_acesso': {'tipo': 'BOOLEAN', 'default': False},
                        'nivel_acesso': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'setor': {'tipo': 'VARCHAR(255)', 'nullable': True},
                        '_setores': {'tipo': 'TEXT', 'nullable': True},
                        'bloqueado': {'tipo': 'BOOLEAN', 'default': False},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'ultimo_acesso': {'tipo': 'DATETIME', 'nullable': True},
                        'tentativas_login': {'tipo': 'INTEGER', 'default': 0},
                        'bloqueado_ate': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'chamado': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'codigo': {'tipo': 'VARCHAR(20)', 'nullable': False, 'unique': True},
                        'protocolo': {'tipo': 'VARCHAR(20)', 'nullable': False, 'unique': True},
                        'solicitante': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'cargo': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'email': {'tipo': 'VARCHAR(120)', 'nullable': False},
                        'telefone': {'tipo': 'VARCHAR(20)', 'nullable': False},
                        'unidade': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'problema': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'internet_item': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'descricao': {'tipo': 'TEXT', 'nullable': True},
                        'data_visita': {'tipo': 'DATE', 'nullable': True},
                        'data_abertura': {'tipo': 'DATETIME', 'nullable': True},
                        'data_primeira_resposta': {'tipo': 'DATETIME', 'nullable': True},
                        'data_conclusao': {'tipo': 'DATETIME', 'nullable': True},
                        'status': {'tipo': 'VARCHAR(20)', 'default': 'Aberto'},
                        'prioridade': {'tipo': 'VARCHAR(20)', 'default': 'Normal'},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'}
                    }
                },
                'unidade': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome': {'tipo': 'VARCHAR(150)', 'nullable': False, 'unique': True},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'problema_reportado': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome': {'tipo': 'VARCHAR(100)', 'nullable': False, 'unique': True},
                        'prioridade_padrao': {'tipo': 'VARCHAR(20)', 'default': 'Normal'},
                        'requer_item_internet': {'tipo': 'BOOLEAN', 'default': False},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True}
                    }
                },
                'item_internet': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome': {'tipo': 'VARCHAR(50)', 'nullable': False, 'unique': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True}
                    }
                },
                'solicitacao_compra': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'protocolo': {'tipo': 'VARCHAR(20)', 'nullable': False, 'unique': True},
                        'solicitante_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'produto': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'quantidade': {'tipo': 'INTEGER', 'nullable': False},
                        'categoria': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'prioridade': {'tipo': 'VARCHAR(20)', 'default': 'Normal'},
                        'valor_estimado': {'tipo': 'DECIMAL(10,2)', 'nullable': True},
                        'data_entrega_desejada': {'tipo': 'DATE', 'nullable': True},
                        'justificativa': {'tipo': 'TEXT', 'nullable': False},
                        'observacoes': {'tipo': 'TEXT', 'nullable': True},
                        'urgente': {'tipo': 'BOOLEAN', 'default': False},
                        'status': {'tipo': 'VARCHAR(30)', 'default': 'Pendente'},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_atualizacao': {'tipo': 'DATETIME', 'nullable': True},
                        'aprovado_por': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'},
                        'data_aprovacao': {'tipo': 'DATETIME', 'nullable': True},
                        'motivo_rejeicao': {'tipo': 'TEXT', 'nullable': True}
                    }
                },
                'historicos_tickets': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'chamado_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'chamado.id'},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'assunto': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'mensagem': {'tipo': 'TEXT', 'nullable': False},
                        'destinatarios': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'data_envio': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'configuracoes': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'chave': {'tipo': 'VARCHAR(100)', 'nullable': False, 'unique': True},
                        'valor': {'tipo': 'TEXT', 'nullable': False},
                        'data_atualizacao': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'logs_acesso': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'data_acesso': {'tipo': 'DATETIME', 'nullable': True},
                        'data_logout': {'tipo': 'DATETIME', 'nullable': True},
                        'ip_address': {'tipo': 'VARCHAR(45)', 'nullable': True},
                        'user_agent': {'tipo': 'TEXT', 'nullable': True},
                        'duracao_sessao': {'tipo': 'INTEGER', 'nullable': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'session_id': {'tipo': 'VARCHAR(255)', 'nullable': True},
                        'navegador': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'sistema_operacional': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'dispositivo': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'pais': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'cidade': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'provedor_internet': {'tipo': 'VARCHAR(200)', 'nullable': True},
                        'mac_address': {'tipo': 'VARCHAR(17)', 'nullable': True},
                        'resolucao_tela': {'tipo': 'VARCHAR(20)', 'nullable': True},
                        'timezone': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'latitude': {'tipo': 'DECIMAL(10,8)', 'nullable': True},
                        'longitude': {'tipo': 'DECIMAL(11,8)', 'nullable': True}
                    }
                },
                'logs_acoes': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'},
                        'acao': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'categoria': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'detalhes': {'tipo': 'TEXT', 'nullable': True},
                        'dados_anteriores': {'tipo': 'TEXT', 'nullable': True},
                        'dados_novos': {'tipo': 'TEXT', 'nullable': True},
                        'data_acao': {'tipo': 'DATETIME', 'nullable': True},
                        'ip_address': {'tipo': 'VARCHAR(45)', 'nullable': True},
                        'user_agent': {'tipo': 'TEXT', 'nullable': True},
                        'sucesso': {'tipo': 'BOOLEAN', 'default': True},
                        'erro_detalhes': {'tipo': 'TEXT', 'nullable': True},
                        'recurso_afetado': {'tipo': 'VARCHAR(255)', 'nullable': True},
                        'tipo_recurso': {'tipo': 'VARCHAR(100)', 'nullable': True}
                    }
                },
                'configuracoes_avancadas': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'chave': {'tipo': 'VARCHAR(100)', 'nullable': False, 'unique': True},
                        'valor': {'tipo': 'TEXT', 'nullable': False},
                        'descricao': {'tipo': 'TEXT', 'nullable': True},
                        'tipo': {'tipo': 'VARCHAR(20)', 'default': 'string'},
                        'categoria': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'requer_reinicio': {'tipo': 'BOOLEAN', 'default': False},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_atualizacao': {'tipo': 'DATETIME', 'nullable': True},
                        'usuario_atualizacao': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'}
                    }
                },
                'alertas_sistema': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'tipo': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'titulo': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'descricao': {'tipo': 'TEXT', 'nullable': False},
                        'severidade': {'tipo': 'VARCHAR(20)', 'default': 'media'},
                        'categoria': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'resolvido': {'tipo': 'BOOLEAN', 'default': False},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_resolucao': {'tipo': 'DATETIME', 'nullable': True},
                        'resolvido_por': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'},
                        'observacoes_resolucao': {'tipo': 'TEXT', 'nullable': True},
                        'automatico': {'tipo': 'BOOLEAN', 'default': False},
                        'dados_contexto': {'tipo': 'TEXT', 'nullable': True},
                        'contador_ocorrencias': {'tipo': 'INTEGER', 'default': 1},
                        'ultima_ocorrencia': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'backup_historico': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome_arquivo': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'caminho_arquivo': {'tipo': 'VARCHAR(500)', 'nullable': True},
                        'tamanho_mb': {'tipo': 'FLOAT', 'nullable': True},
                        'tipo': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'status': {'tipo': 'VARCHAR(20)', 'default': 'em_progresso'},
                        'data_backup': {'tipo': 'DATETIME', 'nullable': True},
                        'data_inicio': {'tipo': 'DATETIME', 'nullable': True},
                        'data_fim': {'tipo': 'DATETIME', 'nullable': True},
                        'observacoes': {'tipo': 'TEXT', 'nullable': True},
                        'erro_detalhes': {'tipo': 'TEXT', 'nullable': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'automatico': {'tipo': 'BOOLEAN', 'default': False},
                        'hash_arquivo': {'tipo': 'VARCHAR(64)', 'nullable': True},
                        'compressao': {'tipo': 'VARCHAR(20)', 'nullable': True},
                        'tabelas_incluidas': {'tipo': 'TEXT', 'nullable': True},
                        'registros_total': {'tipo': 'INTEGER', 'nullable': True},
                        'tempo_execucao': {'tipo': 'INTEGER', 'nullable': True}
                    }
                },
                'relatorios_gerados': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome_relatorio': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'tipo_relatorio': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'formato': {'tipo': 'VARCHAR(20)', 'nullable': False},
                        'parametros': {'tipo': 'TEXT', 'nullable': True},
                        'nome_arquivo': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'caminho_arquivo': {'tipo': 'VARCHAR(500)', 'nullable': True},
                        'tamanho_kb': {'tipo': 'FLOAT', 'nullable': True},
                        'status': {'tipo': 'VARCHAR(20)', 'default': 'gerando'},
                        'data_geracao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_conclusao': {'tipo': 'DATETIME', 'nullable': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'erro_detalhes': {'tipo': 'TEXT', 'nullable': True},
                        'registros_processados': {'tipo': 'INTEGER', 'nullable': True},
                        'tempo_execucao': {'tipo': 'INTEGER', 'nullable': True}
                    }
                },
                'manutencao_sistema': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'tipo_manutencao': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'descricao': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'status': {'tipo': 'VARCHAR(20)', 'default': 'iniciada'},
                        'data_inicio': {'tipo': 'DATETIME', 'nullable': True},
                        'data_fim': {'tipo': 'DATETIME', 'nullable': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'automatica': {'tipo': 'BOOLEAN', 'default': False},
                        'resultados': {'tipo': 'TEXT', 'nullable': True},
                        'erro_detalhes': {'tipo': 'TEXT', 'nullable': True},
                        'recursos_afetados': {'tipo': 'TEXT', 'nullable': True},
                        'tempo_execucao': {'tipo': 'INTEGER', 'nullable': True}
                    }
                },
                'agentes_suporte': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'unique': True, 'foreign_key': 'user.id'},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'especialidades': {'tipo': 'TEXT', 'nullable': True},
                        'nivel_experiencia': {'tipo': 'VARCHAR(20)', 'default': 'junior'},
                        'max_chamados_simultaneos': {'tipo': 'INTEGER', 'default': 10},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_atualizacao': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'chamado_agente': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'chamado_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'chamado.id'},
                        'agente_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'agentes_suporte.id'},
                        'data_atribuicao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_conclusao': {'tipo': 'DATETIME', 'nullable': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'observacoes': {'tipo': 'TEXT', 'nullable': True},
                        'atribuido_por': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'}
                    }
                },
                'grupos_usuarios': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'nome': {'tipo': 'VARCHAR(150)', 'nullable': False, 'unique': True},
                        'descricao': {'tipo': 'TEXT', 'nullable': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_atualizacao': {'tipo': 'DATETIME', 'nullable': True},
                        'criado_por': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'}
                    }
                },
                'grupo_membros': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'grupo_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'grupos_usuarios.id'},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'data_adicao': {'tipo': 'DATETIME', 'nullable': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'adicionado_por': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'}
                    }
                },
                'grupo_unidades': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'grupo_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'grupos_usuarios.id'},
                        'unidade_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'unidade.id'},
                        'data_adicao': {'tipo': 'DATETIME', 'nullable': True}
                    }
                },
                'grupo_permissoes': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'grupo_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'grupos_usuarios.id'},
                        'permissao': {'tipo': 'VARCHAR(100)', 'nullable': False},
                        'concedida': {'tipo': 'BOOLEAN', 'default': True},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'concedida_por': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'}
                    }
                },
                'emails_massa': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'grupo_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'grupos_usuarios.id'},
                        'assunto': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'conteudo': {'tipo': 'TEXT', 'nullable': False},
                        'tipo': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'destinatarios_count': {'tipo': 'INTEGER', 'default': 0},
                        'enviados_count': {'tipo': 'INTEGER', 'default': 0},
                        'falhas_count': {'tipo': 'INTEGER', 'default': 0},
                        'status': {'tipo': 'VARCHAR(20)', 'default': 'preparando'},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_envio': {'tipo': 'DATETIME', 'nullable': True},
                        'data_conclusao': {'tipo': 'DATETIME', 'nullable': True},
                        'criado_por': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'erro_detalhes': {'tipo': 'TEXT', 'nullable': True}
                    }
                },
                'email_massa_destinatarios': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'email_massa_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'emails_massa.id'},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'user.id'},
                        'email_destinatario': {'tipo': 'VARCHAR(120)', 'nullable': False},
                        'nome_destinatario': {'tipo': 'VARCHAR(150)', 'nullable': True},
                        'status_envio': {'tipo': 'VARCHAR(20)', 'default': 'pendente'},
                        'data_envio': {'tipo': 'DATETIME', 'nullable': True},
                        'erro_envio': {'tipo': 'TEXT', 'nullable': True}
                    }
                },
                'sessoes_ativas': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'usuario_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'user.id'},
                        'session_id': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'ip_address': {'tipo': 'VARCHAR(45)', 'nullable': True},
                        'user_agent': {'tipo': 'TEXT', 'nullable': True},
                        'data_inicio': {'tipo': 'DATETIME', 'nullable': True},
                        'ultima_atividade': {'tipo': 'DATETIME', 'nullable': True},
                        'ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'pais': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'cidade': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'navegador': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'sistema_operacional': {'tipo': 'VARCHAR(100)', 'nullable': True},
                        'dispositivo': {'tipo': 'VARCHAR(50)', 'nullable': True}
                    }
                },
                'notificacoes_agentes': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'agente_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'agentes_suporte.id'},
                        'titulo': {'tipo': 'VARCHAR(255)', 'nullable': False},
                        'mensagem': {'tipo': 'TEXT', 'nullable': False},
                        'tipo': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'chamado_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'chamado.id'},
                        'lida': {'tipo': 'BOOLEAN', 'default': False},
                        'data_criacao': {'tipo': 'DATETIME', 'nullable': True},
                        'data_leitura': {'tipo': 'DATETIME', 'nullable': True},
                        'metadados': {'tipo': 'TEXT', 'nullable': True},
                        'exibir_popup': {'tipo': 'BOOLEAN', 'default': True},
                        'som_ativo': {'tipo': 'BOOLEAN', 'default': True},
                        'prioridade': {'tipo': 'VARCHAR(20)', 'default': 'normal'}
                    }
                },
                'historico_atendimentos': {
                    'colunas': {
                        'id': {'tipo': 'INTEGER', 'primary_key': True},
                        'chamado_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'chamado.id'},
                        'agente_id': {'tipo': 'INTEGER', 'nullable': False, 'foreign_key': 'agentes_suporte.id'},
                        'data_atribuicao': {'tipo': 'DATETIME', 'nullable': False},
                        'data_primeira_resposta': {'tipo': 'DATETIME', 'nullable': True},
                        'data_conclusao': {'tipo': 'DATETIME', 'nullable': True},
                        'status_inicial': {'tipo': 'VARCHAR(50)', 'nullable': False},
                        'status_final': {'tipo': 'VARCHAR(50)', 'nullable': True},
                        'tempo_primeira_resposta_min': {'tipo': 'INTEGER', 'nullable': True},
                        'tempo_total_resolucao_min': {'tipo': 'INTEGER', 'nullable': True},
                        'observacoes_iniciais': {'tipo': 'TEXT', 'nullable': True},
                        'observacoes_finais': {'tipo': 'TEXT', 'nullable': True},
                        'solucao_aplicada': {'tipo': 'TEXT', 'nullable': True},
                        'transferido_de_agente_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'agentes_suporte.id'},
                        'transferido_para_agente_id': {'tipo': 'INTEGER', 'nullable': True, 'foreign_key': 'agentes_suporte.id'},
                        'motivo_transferencia': {'tipo': 'TEXT', 'nullable': True},
                        'avaliacao_cliente': {'tipo': 'INTEGER', 'nullable': True},
                        'comentario_avaliacao': {'tipo': 'TEXT', 'nullable': True}
                    }
                }
            }
            
            print(f"\n📋 Estrutura esperada define {len(estrutura_esperada)} tabelas")
            
            # Verificar e criar tabelas faltantes
            tabelas_criadas = 0
            colunas_adicionadas = 0
            
            for nome_tabela, definicao in estrutura_esperada.items():
                print(f"\n🔍 Verificando tabela: {nome_tabela}")
                
                if nome_tabela not in existing_tables:
                    print(f"   ❌ Tabela '{nome_tabela}' não existe - criando...")
                    
                    # Criar SQL para criação da tabela
                    sql_create = f"CREATE TABLE {nome_tabela} ("
                    colunas_sql = []
                    foreign_keys = []
                    
                    for nome_coluna, config in definicao['colunas'].items():
                        coluna_sql = f"{nome_coluna} {config['tipo']}"
                        
                        # Primary key
                        if config.get('primary_key'):
                            coluna_sql += " PRIMARY KEY AUTO_INCREMENT"
                        
                        # Nullable
                        if config.get('nullable') == False:
                            coluna_sql += " NOT NULL"
                        
                        # Default
                        if 'default' in config:
                            default_val = config['default']
                            if isinstance(default_val, str):
                                coluna_sql += f" DEFAULT '{default_val}'"
                            elif isinstance(default_val, bool):
                                coluna_sql += f" DEFAULT {1 if default_val else 0}"
                            else:
                                coluna_sql += f" DEFAULT {default_val}"
                        
                        # Unique
                        if config.get('unique'):
                            coluna_sql += " UNIQUE"
                        
                        colunas_sql.append(coluna_sql)
                        
                        # Foreign key
                        if 'foreign_key' in config:
                            foreign_keys.append(f"FOREIGN KEY ({nome_coluna}) REFERENCES {config['foreign_key']}")
                    
                    sql_create += ", ".join(colunas_sql)
                    if foreign_keys:
                        sql_create += ", " + ", ".join(foreign_keys)
                    sql_create += ")"
                    
                    try:
                        db.engine.execute(text(sql_create))
                        print(f"   ✅ Tabela '{nome_tabela}' criada com sucesso")
                        tabelas_criadas += 1
                    except Exception as e:
                        print(f"   ❌ Erro ao criar tabela '{nome_tabela}': {str(e)}")
                
                else:
                    print(f"   ✅ Tabela '{nome_tabela}' existe")
                    
                    # Verificar colunas da tabela
                    colunas_existentes = [col['name'] for col in inspector.get_columns(nome_tabela)]
                    
                    for nome_coluna, config in definicao['colunas'].items():
                        if nome_coluna not in colunas_existentes:
                            print(f"   📝 Adicionando coluna '{nome_coluna}' à tabela '{nome_tabela}'")
                            
                            # Criar SQL para adicionar coluna
                            sql_add = f"ALTER TABLE {nome_tabela} ADD COLUMN {nome_coluna} {config['tipo']}"
                            
                            # Nullable
                            if config.get('nullable') == False:
                                sql_add += " NOT NULL"
                            
                            # Default
                            if 'default' in config:
                                default_val = config['default']
                                if isinstance(default_val, str):
                                    sql_add += f" DEFAULT '{default_val}'"
                                elif isinstance(default_val, bool):
                                    sql_add += f" DEFAULT {1 if default_val else 0}"
                                else:
                                    sql_add += f" DEFAULT {default_val}"
                            
                            try:
                                db.engine.execute(text(sql_add))
                                print(f"     ✅ Coluna '{nome_coluna}' adicionada")
                                colunas_adicionadas += 1
                                
                                # Adicionar foreign key se necessário
                                if 'foreign_key' in config:
                                    try:
                                        fk_sql = f"ALTER TABLE {nome_tabela} ADD CONSTRAINT fk_{nome_tabela}_{nome_coluna} FOREIGN KEY ({nome_coluna}) REFERENCES {config['foreign_key']}"
                                        db.engine.execute(text(fk_sql))
                                        print(f"     ✅ Foreign key para '{nome_coluna}' adicionada")
                                    except Exception as e:
                                        print(f"     ⚠️  Erro ao adicionar foreign key: {str(e)}")
                                
                            except Exception as e:
                                print(f"     ❌ Erro ao adicionar coluna '{nome_coluna}': {str(e)}")
            
            # Executar db.create_all() para garantir que todas as estruturas SQLAlchemy estejam sincronizadas
            print(f"\n🔄 Executando db.create_all() para sincronizar estruturas...")
            try:
                db.create_all()
                print("✅ db.create_all() executado com sucesso")
            except Exception as e:
                print(f"❌ Erro no db.create_all(): {str(e)}")
            
            # Resumo final
            print(f"\n" + "=" * 80)
            print("📊 RESUMO DA VERIFICAÇÃO")
            print("=" * 80)
            print(f"✅ Tabelas criadas: {tabelas_criadas}")
            print(f"📝 Colunas adicionadas: {colunas_adicionadas}")
            
            # Verificar novamente as tabelas existentes
            existing_tables_final = inspector.get_table_names()
            print(f"📋 Total de tabelas no banco: {len(existing_tables_final)}")
            
            # Listar todas as tabelas finais
            print(f"\n📋 Tabelas no banco após verificação:")
            for table in sorted(existing_tables_final):
                colunas = inspector.get_columns(table)
                print(f"   • {table} ({len(colunas)} colunas)")
            
            print(f"\n✅ Verificação da estrutura do banco concluída!")
            return True
            
    except ImportError as e:
        print(f"❌ Erro de importação: {str(e)}")
        print("   Certifique-se de que está executando no diretório correto")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return False

def inicializar_dados_essenciais():
    """Inicializa dados essenciais se não existirem"""
    print("\n" + "=" * 80)
    print("🌱 INICIALIZANDO DADOS ESSENCIAIS")
    print("=" * 80)
    
    try:
        from app import app
        from database import (db, Unidade, ProblemaReportado, ItemInternet, 
                             Configuracao, ConfiguracaoAvancada, User,
                             seed_unidades, get_brazil_time)
        import json
        
        with app.app_context():
            dados_criados = 0
            
            # Verificar e criar unidades
            if Unidade.query.count() == 0:
                print("🔄 Criando unidades padrão...")
                seed_unidades()
                dados_criados += Unidade.query.count()
                print(f"✅ {Unidade.query.count()} unidades criadas")
            else:
                print(f"✅ Unidades já existem ({Unidade.query.count()} registros)")
            
            # Verificar e criar problemas reportados
            problemas_padrao = [
                "Sistema EVO", "Catraca", "Internet", "Som", "TVs", 
                "Notebook/Desktop", "Ar condicionado", "Iluminação",
                "Equipamentos de academia", "Câmeras", "Telefone"
            ]
            
            problemas_existentes = ProblemaReportado.query.count()
            if problemas_existentes == 0:
                print("🔄 Criando problemas reportados padrão...")
                for problema in problemas_padrao:
                    novo_problema = ProblemaReportado(
                        nome=problema,
                        prioridade_padrao='Normal',
                        requer_item_internet=(problema == 'Internet'),
                        ativo=True
                    )
                    db.session.add(novo_problema)
                
                db.session.commit()
                dados_criados += len(problemas_padrao)
                print(f"✅ {len(problemas_padrao)} problemas reportados criados")
            else:
                print(f"✅ Problemas reportados já existem ({problemas_existentes} registros)")
            
            # Verificar e criar itens de internet
            itens_internet_padrao = [
                "Roteador Wi-Fi", "Switch", "Cabo de rede", "Repetidor Wi-Fi",
                "Modem", "Access Point", "Powerline", "Cabo USB", "Adaptador"
            ]
            
            itens_existentes = ItemInternet.query.count()
            if itens_existentes == 0:
                print("🔄 Criando itens de internet padrão...")
                for item in itens_internet_padrao:
                    novo_item = ItemInternet(nome=item, ativo=True)
                    db.session.add(novo_item)
                
                db.session.commit()
                dados_criados += len(itens_internet_padrao)
                print(f"✅ {len(itens_internet_padrao)} itens de internet criados")
            else:
                print(f"✅ Itens de internet já existem ({itens_existentes} registros)")
            
            # Verificar e criar configurações básicas
            config_basicas = {
                'sla': {
                    'primeira_resposta': 4,
                    'resolucao_critico': 2,
                    'resolucao_alto': 8,
                    'resolucao_normal': 24,
                    'resolucao_baixo': 72
                },
                'notificacoes': {
                    'email_novo_chamado': True,
                    'email_status_mudou': True,
                    'notificar_sla_risco': True,
                    'intervalo_verificacao': 15
                },
                'sistema': {
                    'timeout_sessao': 30,
                    'maximo_tentativas_login': 5,
                    'backup_automatico': True,
                    'log_nivel': 'INFO'
                }
            }
            
            configs_criadas = 0
            for chave, valor in config_basicas.items():
                if not Configuracao.query.filter_by(chave=chave).first():
                    config = Configuracao(
                        chave=chave,
                        valor=json.dumps(valor),
                        data_atualizacao=get_brazil_time().replace(tzinfo=None)
                    )
                    db.session.add(config)
                    configs_criadas += 1
            
            if configs_criadas > 0:
                db.session.commit()
                print(f"✅ {configs_criadas} configurações básicas criadas")
            else:
                print("✅ Configurações básicas já existem")
            
            # Verificar usuários essenciais
            admin_user = User.query.filter_by(usuario='admin').first()
            if not admin_user:
                print("🔄 Criando usuário administrador padrão...")
                admin_user = User(
                    nome='Administrador',
                    sobrenome='Sistema',
                    usuario='admin',
                    email='admin@evoquefitness.com',
                    nivel_acesso='Administrador',
                    setor='TI',
                    bloqueado=False,
                    data_criacao=get_brazil_time().replace(tzinfo=None)
                )
                admin_user.set_password('admin123')
                admin_user.setores = ['TI']
                db.session.add(admin_user)
                db.session.commit()
                dados_criados += 1
                print("✅ Usuário admin criado (admin/admin123)")
            else:
                print("✅ Usuário admin já existe")
            
            print(f"\n📊 Total de registros de dados criados: {dados_criados}")
            print("✅ Inicialização de dados essenciais concluída!")
            
    except Exception as e:
        print(f"❌ Erro ao inicializar dados essenciais: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando verificação e criação da estrutura do banco de dados...")
    print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar e criar estrutura
    sucesso = verificar_criar_estrutura_banco()
    
    if sucesso:
        # Inicializar dados essenciais
        inicializar_dados_essenciais()
        
        print(f"\n🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print("✅ Estrutura do banco de dados verificada e atualizada")
        print("✅ Dados essenciais inicializados")
        print("✅ Sistema pronto para uso")
        print("=" * 80)
    else:
        print(f"\n❌ PROCESSO CONCLUÍDO COM ERROS")
        print("=" * 80)
        print("❌ Verifique os erros acima e tente novamente")
        print("=" * 80)
