#!/usr/bin/env python3
"""
Script de migração para garantir que as tabelas de logs e auditoria existam no banco de dados.
Este script verifica e cria as tabelas necessárias para o sistema de auditoria e logs.
"""

import os
import sys
from datetime import datetime
import pymysql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Configurações do banco de dados do .env
DB_CONFIG = {
    'host': 'evoque-database.mysql.database.azure.com',
    'user': 'infra',
    'password': 'Evoque12@',
    'database': 'infra',
    'port': 3306,
    'charset': 'utf8mb4'
}

def conectar_banco():
    """Conecta ao banco de dados MySQL"""
    try:
        # Remover qualquer '@' extra do host
        host = DB_CONFIG['host'].replace('@', '')
        connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{host}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {str(e)}")
        return None

def verificar_tabela_existe(engine, nome_tabela):
    """Verifica se uma tabela existe no banco"""
    try:
        inspector = inspect(engine)
        tabelas = inspector.get_table_names()
        return nome_tabela in tabelas
    except Exception as e:
        print(f"❌ Erro ao verificar tabela {nome_tabela}: {str(e)}")
        return False

def criar_tabela_logs_acesso(engine):
    """Cria a tabela logs_acesso se não existir"""
    sql = """
    CREATE TABLE IF NOT EXISTS logs_acesso (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NOT NULL,
        data_acesso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        data_logout DATETIME NULL,
        ip_address VARCHAR(45) NULL,
        user_agent TEXT NULL,
        duracao_sessao INT NULL COMMENT 'Duração em minutos',
        ativo BOOLEAN DEFAULT TRUE,
        session_id VARCHAR(255) NULL,
        navegador VARCHAR(100) NULL,
        sistema_operacional VARCHAR(100) NULL,
        dispositivo VARCHAR(50) NULL,
        INDEX idx_usuario_id (usuario_id),
        INDEX idx_data_acesso (data_acesso),
        INDEX idx_ativo (ativo),
        FOREIGN KEY (usuario_id) REFERENCES user(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Tabela logs_acesso criada/verificada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela logs_acesso: {str(e)}")
        return False

def criar_tabela_logs_acoes(engine):
    """Cria a tabela logs_acoes se não existir"""
    sql = """
    CREATE TABLE IF NOT EXISTS logs_acoes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario_id INT NULL,
        acao VARCHAR(255) NOT NULL,
        categoria VARCHAR(100) NULL COMMENT 'login, chamado, usuario, configuracao, etc',
        detalhes TEXT NULL,
        dados_anteriores TEXT NULL COMMENT 'JSON com dados antes da alteração',
        dados_novos TEXT NULL COMMENT 'JSON com dados após alteração',
        data_acao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(45) NULL,
        user_agent TEXT NULL,
        sucesso BOOLEAN DEFAULT TRUE,
        erro_detalhes TEXT NULL,
        recurso_afetado VARCHAR(255) NULL COMMENT 'ID do recurso afetado',
        tipo_recurso VARCHAR(100) NULL COMMENT 'tipo do recurso (chamado, usuario, etc)',
        INDEX idx_usuario_id (usuario_id),
        INDEX idx_data_acao (data_acao),
        INDEX idx_categoria (categoria),
        INDEX idx_sucesso (sucesso),
        INDEX idx_recurso_afetado (recurso_afetado),
        FOREIGN KEY (usuario_id) REFERENCES user(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Tabela logs_acoes criada/verificada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela logs_acoes: {str(e)}")
        return False

def criar_tabela_configuracoes_avancadas(engine):
    """Cria a tabela configuracoes_avancadas se não existir"""
    sql = """
    CREATE TABLE IF NOT EXISTS configuracoes_avancadas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        chave VARCHAR(100) UNIQUE NOT NULL,
        valor TEXT NOT NULL,
        descricao TEXT NULL,
        tipo VARCHAR(20) DEFAULT 'string' COMMENT 'string, number, boolean, json',
        categoria VARCHAR(50) NULL COMMENT 'sistema, backup, alertas, performance',
        requer_reinicio BOOLEAN DEFAULT FALSE,
        data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        usuario_atualizacao INT NULL,
        INDEX idx_chave (chave),
        INDEX idx_categoria (categoria),
        FOREIGN KEY (usuario_atualizacao) REFERENCES user(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Tabela configuracoes_avancadas criada/verificada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela configuracoes_avancadas: {str(e)}")
        return False

def criar_tabela_alertas_sistema(engine):
    """Cria a tabela alertas_sistema se não existir"""
    sql = """
    CREATE TABLE IF NOT EXISTS alertas_sistema (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tipo VARCHAR(50) NOT NULL COMMENT 'sistema, seguranca, performance, backup, etc.',
        titulo VARCHAR(255) NOT NULL,
        descricao TEXT NOT NULL,
        severidade VARCHAR(20) DEFAULT 'media' COMMENT 'baixa, media, alta, critica',
        categoria VARCHAR(100) NULL,
        resolvido BOOLEAN DEFAULT FALSE,
        data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        data_resolucao DATETIME NULL,
        resolvido_por INT NULL,
        observacoes_resolucao TEXT NULL,
        automatico BOOLEAN DEFAULT FALSE COMMENT 'Se foi criado automaticamente',
        dados_contexto TEXT NULL COMMENT 'JSON com dados adicionais',
        contador_ocorrencias INT DEFAULT 1,
        ultima_ocorrencia DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_tipo (tipo),
        INDEX idx_severidade (severidade),
        INDEX idx_resolvido (resolvido),
        INDEX idx_data_criacao (data_criacao),
        FOREIGN KEY (resolvido_por) REFERENCES user(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print("✅ Tabela alertas_sistema criada/verificada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela alertas_sistema: {str(e)}")
        return False

def inserir_configuracoes_padrao(engine):
    """Insere configurações padrão se não existirem"""
    configuracoes_padrao = [
        ('sistema.debug_mode', 'false', 'Ativa o modo de debug para desenvolvimento', 'boolean', 'sistema'),
        ('sistema.max_upload_size', '10', 'Tamanho máximo de upload em MB', 'number', 'sistema'),
        ('sistema.session_timeout', '30', 'Timeout de sessão em minutos', 'number', 'sistema'),
        ('backup.automatico_habilitado', 'true', 'Habilita backup automático', 'boolean', 'backup'),
        ('backup.frequencia_horas', '24', 'Frequência de backup automático em horas', 'number', 'backup'),
        ('backup.manter_arquivos', '30', 'Número de arquivos de backup a manter', 'number', 'backup'),
        ('alertas.email_habilitado', 'true', 'Habilita envio de alertas por email', 'boolean', 'alertas'),
        ('logs.nivel_detalhamento', 'INFO', 'Nível de detalhamento dos logs (DEBUG, INFO, WARNING, ERROR)', 'string', 'logs'),
        ('logs.rotacao_automatica', 'true', 'Habilita rotação automática de logs', 'boolean', 'logs'),
        ('logs.manter_dias', '90', 'Número de dias para manter logs', 'number', 'logs')
    ]
    
    try:
        with engine.connect() as conn:
            for chave, valor, descricao, tipo, categoria in configuracoes_padrao:
                # Verificar se já existe
                result = conn.execute(text(
                    "SELECT COUNT(*) as count FROM configuracoes_avancadas WHERE chave = :chave"
                ), {"chave": chave})
                
                if result.fetchone()[0] == 0:
                    # Inserir configuração
                    conn.execute(text("""
                        INSERT INTO configuracoes_avancadas (chave, valor, descricao, tipo, categoria)
                        VALUES (:chave, :valor, :descricao, :tipo, :categoria)
                    """), {
                        "chave": chave,
                        "valor": valor,
                        "descricao": descricao,
                        "tipo": tipo,
                        "categoria": categoria
                    })
            
            conn.commit()
        print("✅ Configurações padrão inseridas/verificadas com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao inserir configurações padrão: {str(e)}")
        return False

def executar_migracao():
    """Executa a migração completa"""
    print("🚀 Iniciando migração de logs e auditoria...")
    print(f"📅 Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Conectar ao banco
    engine = conectar_banco()
    if not engine:
        print("❌ Falha na conexão com o banco de dados")
        return False
    
    print("✅ Conexão com banco estabelecida")
    
    # Lista de tabelas e funções para criá-las
    migracoes = [
        ("logs_acesso", criar_tabela_logs_acesso),
        ("logs_acoes", criar_tabela_logs_acoes),
        ("configuracoes_avancadas", criar_tabela_configuracoes_avancadas),
        ("alertas_sistema", criar_tabela_alertas_sistema)
    ]
    
    sucesso_total = True
    
    # Executar migrações
    for nome_tabela, funcao_criar in migracoes:
        print(f"\n📋 Verificando/criando tabela: {nome_tabela}")
        
        if verificar_tabela_existe(engine, nome_tabela):
            print(f"✅ Tabela {nome_tabela} já existe")
        else:
            print(f"⚠️  Tabela {nome_tabela} não encontrada, criando...")
            
        if not funcao_criar(engine):
            sucesso_total = False
    
    # Inserir configurações padrão
    print(f"\n📋 Inserindo configurações padrão...")
    if not inserir_configuracoes_padrao(engine):
        sucesso_total = False
    
    # Resultado final
    print("\n" + "=" * 60)
    if sucesso_total:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("🎉 Todas as tabelas de logs e auditoria estão disponíveis")
        print("📊 Sistema de auditoria pronto para uso")
    else:
        print("❌ MIGRAÇÃO FALHOU!")
        print("⚠️  Verifique os erros acima e execute novamente")
    
    return sucesso_total

if __name__ == "__main__":
    try:
        sucesso = executar_migracao()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Migração interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
