#!/usr/bin/env python3
"""
Script completo de verificação e migração do banco de dados.
Verifica consistência dos modelos e aplica migrações necessárias.
"""

import os
import sys
from datetime import datetime
import pymysql
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.exc import SQLAlchemyError
import json

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

def listar_tabelas_existentes(engine):
    """Lista todas as tabelas existentes no banco"""
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    except Exception as e:
        print(f"❌ Erro ao listar tabelas: {str(e)}")
        return []

def verificar_colunas_tabela(engine, nome_tabela):
    """Verifica colunas de uma tabela específica"""
    try:
        inspector = inspect(engine)
        colunas = inspector.get_columns(nome_tabela)
        return {col['name']: col for col in colunas}
    except Exception as e:
        print(f"❌ Erro ao verificar colunas da tabela {nome_tabela}: {str(e)}")
        return {}

def verificar_chaves_estrangeiras(engine, nome_tabela):
    """Verifica chaves estrangeiras de uma tabela"""
    try:
        inspector = inspect(engine)
        return inspector.get_foreign_keys(nome_tabela)
    except Exception as e:
        print(f"❌ Erro ao verificar chaves estrangeiras da tabela {nome_tabela}: {str(e)}")
        return []

def verificar_indices(engine, nome_tabela):
    """Verifica índices de uma tabela"""
    try:
        inspector = inspect(engine)
        return inspector.get_indexes(nome_tabela)
    except Exception as e:
        print(f"❌ Erro ao verificar índices da tabela {nome_tabela}: {str(e)}")
        return []

# Definição das tabelas esperadas e suas estruturas
TABELAS_ESPERADAS = {
    'user': {
        'colunas_obrigatorias': ['id', 'nome', 'sobrenome', 'usuario', 'email', 'senha_hash', 'nivel_acesso'],
        'indices_esperados': ['usuario', 'email'],
        'descricao': 'Tabela de usuários do sistema'
    },
    'chamado': {
        'colunas_obrigatorias': ['id', 'codigo', 'protocolo', 'solicitante', 'email', 'problema', 'status'],
        'indices_esperados': ['codigo', 'protocolo'],
        'descricao': 'Tabela de chamados/tickets'
    },
    'unidade': {
        'colunas_obrigatorias': ['id', 'nome'],
        'indices_esperados': ['nome'],
        'descricao': 'Tabela de unidades/filiais'
    },
    'agentes_suporte': {
        'colunas_obrigatorias': ['id', 'usuario_id', 'ativo', 'nivel_experiencia'],
        'indices_esperados': ['usuario_id'],
        'descricao': 'Tabela de agentes de suporte'
    },
    'chamado_agente': {
        'colunas_obrigatorias': ['id', 'chamado_id', 'agente_id', 'ativo'],
        'indices_esperados': ['chamado_id', 'agente_id'],
        'descricao': 'Tabela de atribuição de chamados a agentes'
    },
    'logs_acesso': {
        'colunas_obrigatorias': ['id', 'usuario_id', 'data_acesso'],
        'indices_esperados': ['usuario_id', 'data_acesso'],
        'descricao': 'Tabela de logs de acesso'
    },
    'logs_acoes': {
        'colunas_obrigatorias': ['id', 'acao', 'data_acao'],
        'indices_esperados': ['data_acao', 'categoria'],
        'descricao': 'Tabela de logs de ações'
    },
    'configuracoes': {
        'colunas_obrigatorias': ['id', 'chave', 'valor'],
        'indices_esperados': ['chave'],
        'descricao': 'Tabela de configurações básicas'
    },
    'configuracoes_avancadas': {
        'colunas_obrigatorias': ['id', 'chave', 'valor'],
        'indices_esperados': ['chave'],
        'descricao': 'Tabela de configurações avançadas'
    },
    'alertas_sistema': {
        'colunas_obrigatorias': ['id', 'tipo', 'titulo', 'descricao'],
        'indices_esperados': ['tipo', 'resolvido'],
        'descricao': 'Tabela de alertas do sistema'
    },
    'grupos_usuarios': {
        'colunas_obrigatorias': ['id', 'nome', 'ativo'],
        'indices_esperados': ['nome'],
        'descricao': 'Tabela de grupos de usuários'
    },
    'grupo_membros': {
        'colunas_obrigatorias': ['id', 'grupo_id', 'usuario_id'],
        'indices_esperados': ['grupo_id', 'usuario_id'],
        'descricao': 'Tabela de membros dos grupos'
    }
}

def executar_verificacao_completa():
    """Executa verificação completa do banco de dados"""
    print("🔍 Iniciando verificação completa do banco de dados...")
    print(f"📅 Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 80)
    
    engine = conectar_banco()
    if not engine:
        return False
    
    print("✅ Conexão com banco estabelecida")
    
    # Listar tabelas existentes
    tabelas_existentes = listar_tabelas_existentes(engine)
    print(f"\n📋 Tabelas encontradas no banco: {len(tabelas_existentes)}")
    for tabela in sorted(tabelas_existentes):
        print(f"  - {tabela}")
    
    # Verificar cada tabela esperada
    print(f"\n🔍 Verificando {len(TABELAS_ESPERADAS)} tabelas esperadas...")
    resultados = {}
    
    for nome_tabela, spec in TABELAS_ESPERADAS.items():
        print(f"\n📊 Verificando tabela: {nome_tabela}")
        print(f"   Descrição: {spec['descricao']}")
        
        resultado = {
            'existe': nome_tabela in tabelas_existentes,
            'colunas_ok': False,
            'indices_ok': False,
            'problemas': []
        }
        
        if not resultado['existe']:
            resultado['problemas'].append(f"Tabela {nome_tabela} não existe")
            print(f"   ❌ Tabela não encontrada")
        else:
            print(f"   ✅ Tabela existe")
            
            # Verificar colunas
            colunas_existentes = verificar_colunas_tabela(engine, nome_tabela)
            colunas_faltando = []
            
            for coluna_obrigatoria in spec['colunas_obrigatorias']:
                if coluna_obrigatoria not in colunas_existentes:
                    colunas_faltando.append(coluna_obrigatoria)
            
            if colunas_faltando:
                resultado['problemas'].append(f"Colunas faltando: {', '.join(colunas_faltando)}")
                print(f"   ❌ Colunas faltando: {', '.join(colunas_faltando)}")
            else:
                resultado['colunas_ok'] = True
                print(f"   ✅ Todas as colunas obrigatórias presentes")
            
            # Verificar índices
            indices_existentes = verificar_indices(engine, nome_tabela)
            indices_existentes_nomes = [idx['name'] for idx in indices_existentes]
            
            indices_faltando = []
            for indice in spec['indices_esperados']:
                if not any(indice in idx_nome for idx_nome in indices_existentes_nomes):
                    indices_faltando.append(indice)
            
            if indices_faltando:
                resultado['problemas'].append(f"Índices faltando: {', '.join(indices_faltando)}")
                print(f"   ⚠️  Índices faltando: {', '.join(indices_faltando)}")
            else:
                resultado['indices_ok'] = True
                print(f"   ✅ Índices adequados")
            
            # Verificar chaves estrangeiras se aplicável
            chaves_estrangeiras = verificar_chaves_estrangeiras(engine, nome_tabela)
            print(f"   📎 Chaves estrangeiras: {len(chaves_estrangeiras)}")
        
        resultados[nome_tabela] = resultado
    
    # Resumo da verificação
    print("\n" + "=" * 80)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("=" * 80)
    
    tabelas_ok = 0
    tabelas_com_problemas = 0
    problemas_totais = []
    
    for nome_tabela, resultado in resultados.items():
        if resultado['existe'] and resultado['colunas_ok']:
            tabelas_ok += 1
            status = "✅ OK"
        else:
            tabelas_com_problemas += 1
            status = "❌ PROBLEMAS"
            problemas_totais.extend(resultado['problemas'])
        
        print(f"{nome_tabela:25} - {status}")
        for problema in resultado['problemas']:
            print(f"    └─ {problema}")
    
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"   Tabelas OK: {tabelas_ok}")
    print(f"   Tabelas com problemas: {tabelas_com_problemas}")
    print(f"   Total de problemas: {len(problemas_totais)}")
    
    # Verificações adicionais
    print(f"\n🔍 VERIFICAÇÕES ADICIONAIS:")
    
    # Verificar foreign keys importantes
    verificar_foreign_keys_importantes(engine)
    
    # Verificar dados essenciais
    verificar_dados_essenciais(engine)
    
    if tabelas_com_problemas == 0:
        print("\n🎉 VERIFICAÇÃO CONCLUÍDA - BANCO ESTÁ CONSISTENTE!")
        return True
    else:
        print(f"\n⚠️  VERIFICAÇÃO CONCLUÍDA - {tabelas_com_problemas} PROBLEMAS ENCONTRADOS")
        return False

def verificar_foreign_keys_importantes(engine):
    """Verifica se as foreign keys importantes estão criadas"""
    foreign_keys_importantes = [
        ('chamado', 'usuario_id', 'user', 'id'),
        ('agentes_suporte', 'usuario_id', 'user', 'id'),
        ('chamado_agente', 'chamado_id', 'chamado', 'id'),
        ('chamado_agente', 'agente_id', 'agentes_suporte', 'id'),
        ('logs_acesso', 'usuario_id', 'user', 'id'),
        ('grupo_membros', 'grupo_id', 'grupos_usuarios', 'id'),
        ('grupo_membros', 'usuario_id', 'user', 'id')
    ]
    
    for tabela, coluna, tabela_ref, coluna_ref in foreign_keys_importantes:
        try:
            fks = verificar_chaves_estrangeiras(engine, tabela)
            fk_existe = any(
                fk['constrained_columns'] == [coluna] and 
                fk['referred_table'] == tabela_ref 
                for fk in fks
            )
            
            if fk_existe:
                print(f"   ✅ FK {tabela}.{coluna} -> {tabela_ref}.{coluna_ref}")
            else:
                print(f"   ❌ FK {tabela}.{coluna} -> {tabela_ref}.{coluna_ref} - FALTANDO")
        except:
            print(f"   ⚠️  Não foi possível verificar FK {tabela}.{coluna}")

def verificar_dados_essenciais(engine):
    """Verifica se dados essenciais existem"""
    try:
        with engine.connect() as conn:
            # Verificar se há usuários
            result = conn.execute(text("SELECT COUNT(*) as count FROM user WHERE nivel_acesso = 'Administrador'"))
            admin_count = result.fetchone()[0]
            
            if admin_count > 0:
                print(f"   ✅ Administradores cadastrados: {admin_count}")
            else:
                print(f"   ⚠️  Nenhum administrador encontrado")
            
            # Verificar configurações básicas
            result = conn.execute(text("SELECT COUNT(*) as count FROM configuracoes"))
            config_count = result.fetchone()[0]
            
            if config_count > 0:
                print(f"   ✅ Configurações encontradas: {config_count}")
            else:
                print(f"   ⚠️  Nenhuma configuração encontrada")
                
    except Exception as e:
        print(f"   ❌ Erro ao verificar dados essenciais: {str(e)}")

def aplicar_migracoes_necessarias():
    """Aplica migrações necessárias baseadas na verificação"""
    print("\n🔧 APLICANDO MIGRAÇÕES NECESSÁRIAS...")
    
    engine = conectar_banco()
    if not engine:
        return False
    
    migracoes_aplicadas = 0
    
    try:
        with engine.connect() as conn:
            # Migração 1: Verificar e criar tabela agentes_suporte
            if 'agentes_suporte' not in listar_tabelas_existentes(engine):
                print("   🔧 Criando tabela agentes_suporte...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS agentes_suporte (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        usuario_id INT NOT NULL UNIQUE,
                        ativo BOOLEAN DEFAULT TRUE,
                        especialidades TEXT NULL,
                        nivel_experiencia VARCHAR(20) DEFAULT 'junior',
                        max_chamados_simultaneos INT DEFAULT 10,
                        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_usuario_id (usuario_id),
                        INDEX idx_ativo (ativo),
                        FOREIGN KEY (usuario_id) REFERENCES user(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """))
                migracoes_aplicadas += 1
                print("   ✅ Tabela agentes_suporte criada")
            
            # Migração 2: Verificar e criar tabela chamado_agente
            if 'chamado_agente' not in listar_tabelas_existentes(engine):
                print("   🔧 Criando tabela chamado_agente...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chamado_agente (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        chamado_id INT NOT NULL,
                        agente_id INT NOT NULL,
                        data_atribuicao DATETIME DEFAULT CURRENT_TIMESTAMP,
                        data_conclusao DATETIME NULL,
                        ativo BOOLEAN DEFAULT TRUE,
                        observacoes TEXT NULL,
                        atribuido_por INT NULL,
                        INDEX idx_chamado_id (chamado_id),
                        INDEX idx_agente_id (agente_id),
                        INDEX idx_ativo (ativo),
                        FOREIGN KEY (chamado_id) REFERENCES chamado(id) ON DELETE CASCADE,
                        FOREIGN KEY (agente_id) REFERENCES agentes_suporte(id) ON DELETE CASCADE,
                        FOREIGN KEY (atribuido_por) REFERENCES user(id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """))
                migracoes_aplicadas += 1
                print("   ✅ Tabela chamado_agente criada")
            
            conn.commit()
        
        print(f"\n✅ {migracoes_aplicadas} migrações aplicadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao aplicar migrações: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        print("🚀 INICIANDO VERIFICAÇÃO E MIGRAÇÃO DO BANCO DE DADOS")
        print("=" * 80)
        
        # Fase 1: Verificação
        verificacao_ok = executar_verificacao_completa()
        
        # Fase 2: Migração (se necessário)
        if not verificacao_ok:
            print("\n" + "=" * 80)
            resposta = input("Deseja aplicar migrações para corrigir os problemas? (s/N): ")
            if resposta.lower() in ['s', 'sim', 'y', 'yes']:
                migracoes_ok = aplicar_migracoes_necessarias()
                if migracoes_ok:
                    print("\n🔄 Executando nova verificação...")
                    verificacao_ok = executar_verificacao_completa()
        
        # Resultado final
        print("\n" + "=" * 80)
        if verificacao_ok:
            print("🎉 BANCO DE DADOS ESTÁ CONSISTENTE E PRONTO PARA USO!")
            sys.exit(0)
        else:
            print("⚠️  ALGUNS PROBLEMAS AINDA PRECISAM SER RESOLVIDOS MANUALMENTE")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Verificação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)
