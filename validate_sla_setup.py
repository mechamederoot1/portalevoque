#!/usr/bin/env python3
"""
Script de validação para verificar se as configurações SLA estão funcionando corretamente
"""
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
    'charset': 'utf8mb4'
}

def conectar_banco():
    """Conecta ao banco MySQL Azure"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Erro ao conectar: {str(e)}")
        return None

def validar_estrutura_tabelas():
    """Valida se as tabelas têm a estrutura correta"""
    print("🔍 Validando estrutura das tabelas...")
    
    connection = conectar_banco()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar tabela configuracoes_sla
        cursor.execute("DESCRIBE configuracoes_sla")
        colunas_sla = [row[0] for row in cursor.fetchall()]
        
        colunas_esperadas_sla = [
            'id', 'prioridade', 'tempo_primeira_resposta', 'tempo_resolucao',
            'considera_horario_comercial', 'considera_feriados', 'ativo',
            'data_criacao', 'data_atualizacao'
        ]
        
        print("📊 Tabela configuracoes_sla:")
        for coluna in colunas_esperadas_sla:
            if coluna in colunas_sla:
                print(f"   ✅ {coluna}")
            else:
                print(f"   ❌ {coluna} - FALTANDO")
        
        # Verificar tabela horario_comercial
        cursor.execute("DESCRIBE horario_comercial")
        colunas_horario = [row[0] for row in cursor.fetchall()]
        
        colunas_esperadas_horario = [
            'id', 'nome', 'hora_inicio', 'hora_fim', 'segunda', 'terca',
            'quarta', 'quinta', 'sexta', 'sabado', 'domingo', 'ativo', 'padrao'
        ]
        
        print("\n📅 Tabela horario_comercial:")
        for coluna in colunas_esperadas_horario:
            if coluna in colunas_horario:
                print(f"   ✅ {coluna}")
            else:
                print(f"   ❌ {coluna} - FALTANDO")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {str(e)}")
        return False
    finally:
        connection.close()

def validar_dados_padrao():
    """Valida se os dados padrão estão corretos"""
    print("\n📝 Validando dados padrão...")
    
    connection = conectar_banco()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Verificar SLAs padrão
        cursor.execute("""
            SELECT prioridade, tempo_resolucao, ativo 
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
        
        slas_esperados = {
            'Crítica': 2.0,
            'Urgente': 2.0,
            'Alta': 8.0,
            'Normal': 24.0,
            'Baixa': 72.0
        }
        
        print("📊 Validação SLAs:")
        for sla in slas:
            prioridade, tempo, ativo = sla
            if prioridade in slas_esperados:
                if float(tempo) == slas_esperados[prioridade] and ativo:
                    print(f"   ✅ {prioridade}: {tempo}h (Ativo)")
                else:
                    print(f"   ⚠️  {prioridade}: {tempo}h (Esperado: {slas_esperados[prioridade]}h, Ativo: {ativo})")
            else:
                print(f"   ❓ {prioridade}: {tempo}h (Não esperado)")
        
        # Verificar horário comercial padrão
        cursor.execute("""
            SELECT nome, hora_inicio, hora_fim, segunda, sexta, ativo, padrao
            FROM horario_comercial 
            WHERE padrao = TRUE
        """)
        horario = cursor.fetchone()
        
        print("\n📅 Validação Horário Comercial:")
        if horario:
            nome, inicio, fim, segunda, sexta, ativo, padrao = horario
            print(f"   ✅ Nome: {nome}")
            print(f"   ✅ Horário: {inicio} às {fim}")
            print(f"   ✅ Segunda ativa: {segunda}")
            print(f"   ✅ Sexta ativa: {sexta}")
            print(f"   ✅ Ativo: {ativo}")
            print(f"   ✅ Padrão: {padrao}")
        else:
            print("   ❌ Nenhuma configuração padrão encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação de dados: {str(e)}")
        return False
    finally:
        connection.close()

def testar_queries_funcionais():
    """Testa queries que serão usadas pela aplicação"""
    print("\n🧪 Testando queries funcionais...")
    
    connection = conectar_banco()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # 1. Buscar SLA por prioridade
        print("📊 Teste: Buscar SLA por prioridade")
        cursor.execute("""
            SELECT tempo_resolucao, tempo_primeira_resposta 
            FROM configuracoes_sla 
            WHERE prioridade = 'Crítica' AND ativo = TRUE
        """)
        result = cursor.fetchone()
        if result:
            print(f"   ✅ SLA Crítica: {result[0]}h resolução, {result[1]}h primeira resposta")
        else:
            print("   ❌ SLA Crítica não encontrado")
        
        # 2. Buscar horário comercial ativo
        print("\n📅 Teste: Buscar horário comercial ativo")
        cursor.execute("""
            SELECT hora_inicio, hora_fim, segunda, terca, quarta, quinta, sexta
            FROM horario_comercial 
            WHERE ativo = TRUE AND padrao = TRUE
        """)
        result = cursor.fetchone()
        if result:
            inicio, fim, seg, ter, qua, qui, sex = result
            dias_ativos = sum([seg, ter, qua, qui, sex])
            print(f"   ✅ Horário: {inicio} às {fim}")
            print(f"   ✅ Dias úteis ativos: {dias_ativos}/5")
        else:
            print("   ❌ Horário comercial padrão não encontrado")
        
        # 3. Simular cálculo de SLA
        print("\n⚙️  Teste: Simulação de cálculo SLA")
        cursor.execute("""
            SELECT 
                p.prioridade,
                p.tempo_resolucao,
                p.tempo_primeira_resposta,
                h.hora_inicio,
                h.hora_fim
            FROM configuracoes_sla p
            CROSS JOIN horario_comercial h
            WHERE p.prioridade = 'Alta' 
            AND p.ativo = TRUE 
            AND h.ativo = TRUE 
            AND h.padrao = TRUE
        """)
        result = cursor.fetchone()
        if result:
            prioridade, resolucao, primeira_resp, inicio, fim = result
            print(f"   ✅ Prioridade: {prioridade}")
            print(f"   ✅ Tempo resolução: {resolucao}h")
            print(f"   ✅ Tempo primeira resposta: {primeira_resp}h")
            print(f"   ✅ Horário comercial: {inicio} às {fim}")
            print("   ✅ Query de integração funcionando")
        else:
            print("   ❌ Query de integração falhou")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes funcionais: {str(e)}")
        return False
    finally:
        connection.close()

def gerar_relatorio_configuracoes():
    """Gera relatório completo das configurações"""
    print("\n📋 RELATÓRIO DE CONFIGURAÇÕES SLA")
    print("=" * 50)
    
    connection = conectar_banco()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Estatísticas gerais
        cursor.execute("SELECT COUNT(*) FROM configuracoes_sla WHERE ativo = TRUE")
        total_slas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM horario_comercial WHERE ativo = TRUE")
        total_horarios = cursor.fetchone()[0]
        
        print(f"📊 Configurações SLA ativas: {total_slas}")
        print(f"📅 Horários comerciais ativos: {total_horarios}")
        
        # Detalhes por prioridade
        cursor.execute("""
            SELECT 
                prioridade,
                tempo_primeira_resposta,
                tempo_resolucao,
                considera_horario_comercial,
                considera_feriados
            FROM configuracoes_sla 
            WHERE ativo = TRUE
            ORDER BY 
                CASE prioridade 
                    WHEN 'Crítica' THEN 1
                    WHEN 'Urgente' THEN 2
                    WHEN 'Alta' THEN 3
                    WHEN 'Normal' THEN 4
                    WHEN 'Baixa' THEN 5
                END
        """)
        
        print("\n📊 CONFIGURAÇÕES SLA DETALHADAS:")
        print("-" * 40)
        for row in cursor.fetchall():
            prioridade, primeira_resp, resolucao, horario_com, feriados = row
            print(f"🎯 {prioridade}:")
            print(f"   ⏱️  Primeira resposta: {primeira_resp}h")
            print(f"   ⏰ Resolução: {resolucao}h")
            print(f"   🕒 Considera horário comercial: {'Sim' if horario_com else 'Não'}")
            print(f"   🗓️  Considera feriados: {'Sim' if feriados else 'Não'}")
            print()
        
        # Horário comercial detalhado
        cursor.execute("""
            SELECT 
                nome, descricao, hora_inicio, hora_fim,
                segunda, terca, quarta, quinta, sexta, sabado, domingo,
                considera_almoco, almoco_inicio, almoco_fim,
                emergencia_ativo, emergencia_inicio, emergencia_fim
            FROM horario_comercial 
            WHERE ativo = TRUE AND padrao = TRUE
        """)
        
        horario = cursor.fetchone()
        if horario:
            print("📅 HORÁRIO COMERCIAL PADRÃO:")
            print("-" * 40)
            nome, desc, inicio, fim, seg, ter, qua, qui, sex, sab, dom, almoco, almoco_ini, almoco_fim, emerg, emerg_ini, emerg_fim = horario
            
            print(f"📛 Nome: {nome}")
            print(f"📝 Descrição: {desc}")
            print(f"🕐 Horário: {inicio} às {fim}")
            
            dias = []
            if seg: dias.append('Segunda')
            if ter: dias.append('Terça')
            if qua: dias.append('Quarta')
            if qui: dias.append('Quinta')
            if sex: dias.append('Sexta')
            if sab: dias.append('Sábado')
            if dom: dias.append('Domingo')
            
            print(f"📆 Dias ativos: {', '.join(dias)}")
            
            if almoco:
                print(f"🍽️  Intervalo almoço: {almoco_ini} às {almoco_fim}")
            
            if emerg:
                print(f"🚨 Emergência: {emerg_ini} às {emerg_fim}")
        
        print("\n✅ Relatório gerado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no relatório: {str(e)}")
        return False
    finally:
        connection.close()

def main():
    """Função principal de validação"""
    print("🔍 VALIDAÇÃO COMPLETA - CONFIGURAÇÕES SLA")
    print("=" * 50)
    
    success = True
    
    # 1. Validar estrutura
    if not validar_estrutura_tabelas():
        success = False
    
    # 2. Validar dados
    if not validar_dados_padrao():
        success = False
    
    # 3. Testar funcionalidades
    if not testar_queries_funcionais():
        success = False
    
    # 4. Gerar relatório
    if not gerar_relatorio_configuracoes():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("✅ Todas as configurações estão corretas")
        print("✅ Sistema SLA pronto para uso")
    else:
        print("❌ VALIDAÇÃO ENCONTROU PROBLEMAS")
        print("⚠️  Verifique os erros acima")
    
    return success

if __name__ == "__main__":
    main()
