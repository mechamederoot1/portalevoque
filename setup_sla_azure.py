#!/usr/bin/env python3
"""
Script para configurar tabelas de SLA no banco MySQL Azure
Verifica e cria tabelas se não existirem, popula dados padrão
"""
import sys
import os
import pymysql
from datetime import datetime, time
import json

# Configurações do banco MySQL Azure
DB_CONFIG = {
    'host': 'evoque-database.mysql.database.azure.com',
    'user': 'infra',
    'password': 'Evoque12@',
    'database': 'infra',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True
}

def conectar_banco():
    """Conecta ao banco MySQL Azure"""
    try:
        print("🔌 Conectando ao banco MySQL Azure...")
        connection = pymysql.connect(**DB_CONFIG)
        print("✅ Conexão estabelecida com sucesso!")
        return connection
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {str(e)}")
        return None

def verificar_tabela_existe(cursor, nome_tabela):
    """Verifica se uma tabela existe"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = '{DB_CONFIG['database']}' 
            AND table_name = '{nome_tabela}'
        """)
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        print(f"❌ Erro ao verificar tabela {nome_tabela}: {str(e)}")
        return False

def criar_tabela_configuracoes_sla(cursor):
    """Cria a tabela configuracoes_sla"""
    sql = """
    CREATE TABLE IF NOT EXISTS configuracoes_sla (
        id INT AUTO_INCREMENT PRIMARY KEY,
        prioridade VARCHAR(50) NOT NULL,
        tempo_primeira_resposta DECIMAL(5,2) DEFAULT 4.0,
        tempo_resolucao DECIMAL(5,2) NOT NULL,
        considera_horario_comercial BOOLEAN DEFAULT TRUE,
        considera_feriados BOOLEAN DEFAULT TRUE,
        escalar_automaticamente BOOLEAN DEFAULT TRUE,
        notificar_em_risco BOOLEAN DEFAULT TRUE,
        percentual_risco DECIMAL(5,2) DEFAULT 80.0,
        ativo BOOLEAN DEFAULT TRUE,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        usuario_atualizacao INT NULL,
        UNIQUE KEY unique_prioridade (prioridade)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    try:
        cursor.execute(sql)
        print("✅ Tabela 'configuracoes_sla' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela configuracoes_sla: {str(e)}")
        return False

def criar_tabela_horario_comercial(cursor):
    """Cria a tabela horario_comercial"""
    sql = """
    CREATE TABLE IF NOT EXISTS horario_comercial (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL DEFAULT 'Padrão',
        descricao VARCHAR(255) NULL,
        hora_inicio TIME NOT NULL DEFAULT '08:00:00',
        hora_fim TIME NOT NULL DEFAULT '18:00:00',
        segunda BOOLEAN DEFAULT TRUE,
        terca BOOLEAN DEFAULT TRUE,
        quarta BOOLEAN DEFAULT TRUE,
        quinta BOOLEAN DEFAULT TRUE,
        sexta BOOLEAN DEFAULT TRUE,
        sabado BOOLEAN DEFAULT FALSE,
        domingo BOOLEAN DEFAULT FALSE,
        considera_almoco BOOLEAN DEFAULT FALSE,
        almoco_inicio TIME NULL DEFAULT '12:00:00',
        almoco_fim TIME NULL DEFAULT '13:00:00',
        emergencia_ativo BOOLEAN DEFAULT FALSE,
        emergencia_inicio TIME NULL DEFAULT '18:00:00',
        emergencia_fim TIME NULL DEFAULT '22:00:00',
        emergencia_dias_semana VARCHAR(20) DEFAULT '0,1,2,3,4',
        timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
        considera_feriados BOOLEAN DEFAULT TRUE,
        ativo BOOLEAN DEFAULT TRUE,
        padrao BOOLEAN DEFAULT FALSE,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        usuario_criacao INT NULL,
        usuario_atualizacao INT NULL,
        UNIQUE KEY unique_padrao (padrao)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    try:
        cursor.execute(sql)
        print("✅ Tabela 'horario_comercial' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela horario_comercial: {str(e)}")
        return False

def inserir_configuracoes_sla_padrao(cursor):
    """Insere configurações SLA padrão"""
    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) FROM configuracoes_sla")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✅ Já existem {count} configurações SLA no banco")
        return True
    
    slas_padrao = [
        ('Crítica', 1.0, 2.0),
        ('Urgente', 1.0, 2.0),
        ('Alta', 2.0, 8.0),
        ('Normal', 4.0, 24.0),
        ('Baixa', 8.0, 72.0)
    ]
    
    try:
        for prioridade, primeira_resposta, resolucao in slas_padrao:
            sql = """
            INSERT INTO configuracoes_sla 
            (prioridade, tempo_primeira_resposta, tempo_resolucao, considera_horario_comercial, considera_feriados, ativo)
            VALUES (%s, %s, %s, TRUE, TRUE, TRUE)
            """
            cursor.execute(sql, (prioridade, primeira_resposta, resolucao))
        
        print(f"✅ {len(slas_padrao)} configurações SLA inseridas")
        return True
    except Exception as e:
        print(f"❌ Erro ao inserir configurações SLA: {str(e)}")
        return False

def inserir_horario_comercial_padrao(cursor):
    """Insere horário comercial padrão"""
    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) FROM horario_comercial")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✅ Já existem {count} configurações de horário comercial no banco")
        return True
    
    try:
        sql = """
        INSERT INTO horario_comercial 
        (nome, descricao, hora_inicio, hora_fim, segunda, terca, quarta, quinta, sexta, 
         sabado, domingo, considera_almoco, emergencia_ativo, ativo, padrao)
        VALUES 
        ('Horário Padrão', 'Horário comercial padrão da empresa (08:00 às 18:00, segunda a sexta)',
         '08:00:00', '18:00:00', TRUE, TRUE, TRUE, TRUE, TRUE, 
         FALSE, FALSE, FALSE, FALSE, TRUE, TRUE)
        """
        cursor.execute(sql)
        print("✅ Horário comercial padrão inserido")
        return True
    except Exception as e:
        print(f"❌ Erro ao inserir horário comercial: {str(e)}")
        return False

def criar_tabela_historico_sla(cursor):
    """Cria tabela para histórico de SLA se não existir"""
    sql = """
    CREATE TABLE IF NOT EXISTS historico_sla (
        id INT AUTO_INCREMENT PRIMARY KEY,
        chamado_id INT NOT NULL,
        data_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
        status_sla VARCHAR(50) NOT NULL,
        tempo_resposta_horas DECIMAL(8,2) NULL,
        tempo_resolucao_horas DECIMAL(8,2) NULL,
        limite_sla_horas DECIMAL(8,2) NOT NULL,
        violou_primeira_resposta BOOLEAN DEFAULT FALSE,
        violou_resolucao BOOLEAN DEFAULT FALSE,
        observacoes TEXT NULL,
        INDEX idx_chamado_id (chamado_id),
        INDEX idx_data_calculo (data_calculo),
        INDEX idx_status_sla (status_sla)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    try:
        cursor.execute(sql)
        print("✅ Tabela 'historico_sla' criada/verificada")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabela historico_sla: {str(e)}")
        return False

def verificar_integridade_dados(cursor):
    """Verifica a integridade dos dados inseridos"""
    print("\n🔍 Verificando integridade dos dados...")
    
    try:
        # Verificar configurações SLA
        cursor.execute("""
            SELECT prioridade, tempo_primeira_resposta, tempo_resolucao, ativo 
            FROM configuracoes_sla 
            ORDER BY 
                CASE prioridade 
                    WHEN 'Crítica' THEN 1
                    WHEN 'Urgente' THEN 2 
                    WHEN 'Alta' THEN 3
                    WHEN 'Normal' THEN 4
                    WHEN 'Baixa' THEN 5
                END
        """)
        slas = cursor.fetchall()
        
        print("📊 Configurações SLA:")
        for sla in slas:
            prioridade, primeira_resposta, resolucao, ativo = sla
            status = "✅ Ativo" if ativo else "❌ Inativo"
            print(f"   {prioridade}: {resolucao}h resolução, {primeira_resposta}h primeira resposta ({status})")
        
        # Verificar horário comercial
        cursor.execute("""
            SELECT nome, hora_inicio, hora_fim, segunda, terca, quarta, quinta, sexta, 
                   sabado, domingo, considera_almoco, ativo, padrao
            FROM horario_comercial 
            WHERE ativo = TRUE
        """)
        horarios = cursor.fetchall()
        
        print("\n📅 Horários Comerciais:")
        for horario in horarios:
            nome, inicio, fim, seg, ter, qua, qui, sex, sab, dom, almoco, ativo, padrao = horario
            
            dias = []
            if seg: dias.append('Seg')
            if ter: dias.append('Ter') 
            if qua: dias.append('Qua')
            if qui: dias.append('Qui')
            if sex: dias.append('Sex')
            if sab: dias.append('Sáb')
            if dom: dias.append('Dom')
            
            tipo = "🌟 PADRÃO" if padrao else "⚙️  Ativo"
            print(f"   {nome}: {inicio} às {fim} ({tipo})")
            print(f"      Dias: {', '.join(dias)}")
            print(f"      Considera almoço: {'Sim' if almoco else 'Não'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação de integridade: {str(e)}")
        return False

def criar_funcoes_auxiliares(cursor):
    """Cria procedures/functions auxiliares se necessário"""
    # Função para obter SLA por prioridade
    sql_function = """
    DELIMITER //
    CREATE FUNCTION IF NOT EXISTS obter_sla_prioridade(p_prioridade VARCHAR(50))
    RETURNS DECIMAL(5,2)
    READS SQL DATA
    DETERMINISTIC
    BEGIN
        DECLARE v_tempo_resolucao DECIMAL(5,2) DEFAULT 24.0;
        
        SELECT tempo_resolucao INTO v_tempo_resolucao
        FROM configuracoes_sla 
        WHERE prioridade = p_prioridade AND ativo = TRUE
        LIMIT 1;
        
        RETURN COALESCE(v_tempo_resolucao, 24.0);
    END //
    DELIMITER ;
    """
    
    try:
        # Note: MySQL functions require specific permissions, so we'll skip this for now
        print("ℹ️  Funções auxiliares podem ser criadas posteriormente conforme necessário")
        return True
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível criar funções auxiliares: {str(e)}")
        return True  # Não é crítico

def main():
    """Função principal do script"""
    print("🏗️  SETUP TABELAS SLA - MYSQL AZURE")
    print("=" * 50)
    print(f"🎯 Conectando em: {DB_CONFIG['host']}")
    print(f"🗄️  Database: {DB_CONFIG['database']}")
    print()
    
    # Conectar ao banco
    connection = conectar_banco()
    if not connection:
        print("❌ Falha na conexão. Encerrando script.")
        return False
    
    try:
        cursor = connection.cursor()
        
        # 1. Verificar e criar tabelas
        print("📋 Fase 1: Verificação e criação de tabelas")
        tabelas_criadas = 0
        
        if criar_tabela_configuracoes_sla(cursor):
            tabelas_criadas += 1
        
        if criar_tabela_horario_comercial(cursor):
            tabelas_criadas += 1
            
        if criar_tabela_historico_sla(cursor):
            tabelas_criadas += 1
        
        print(f"✅ {tabelas_criadas} tabelas verificadas/criadas")
        
        # 2. Inserir dados padrão
        print("\n📝 Fase 2: Inserção de dados padrão")
        
        if inserir_configuracoes_sla_padrao(cursor):
            print("✅ Configurações SLA processadas")
        
        if inserir_horario_comercial_padrao(cursor):
            print("✅ Horário comercial processado")
        
        # 3. Criar funções auxiliares
        print("\n⚙️  Fase 3: Funções auxiliares")
        criar_funcoes_auxiliares(cursor)
        
        # 4. Verificar integridade
        print("\n🔍 Fase 4: Verificação de integridade")
        if verificar_integridade_dados(cursor):
            print("✅ Verificação de integridade concluída")
        
        # Commit final
        connection.commit()
        
        print("\n🎉 SETUP CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        print("✅ Tabelas SLA criadas e configuradas")
        print("✅ Dados padrão inseridos")
        print("✅ Sistema pronto para uso")
        print("\n📚 Próximos passos:")
        print("   1. Execute a aplicação Flask")
        print("   2. Acesse o painel administrativo")
        print("   3. Vá em 'SLA & Métricas' para ver as configurações")
        print("   4. Use o botão 'Migrar SLA' se necessário")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o setup: {str(e)}")
        connection.rollback()
        return False
        
    finally:
        cursor.close()
        connection.close()
        print("\n🔌 Conexão com banco encerrada")

def testar_conexao():
    """Testa apenas a conexão com o banco"""
    print("🧪 TESTE DE CONEXÃO - MYSQL AZURE")
    print("=" * 40)
    
    connection = conectar_banco()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION(), DATABASE(), USER()")
        result = cursor.fetchone()
        
        print(f"✅ MySQL Version: {result[0]}")
        print(f"✅ Database: {result[1]}")
        print(f"✅ User: {result[2]}")
        
        # Listar tabelas existentes
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ Tabelas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Modo teste - apenas verifica conexão
        testar_conexao()
    else:
        # Modo completo - executa setup
        success = main()
        sys.exit(0 if success else 1)
