#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar todas as atualizações necessárias do sistema
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("EXECUTANDO TODAS AS ATUALIZAÇÕES DO SISTEMA")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    success_count = 0
    total_steps = 3
    
    # 1. Atualizar estrutura de logs de auditoria
    print("📋 Passo 1/3: Atualizando estrutura de logs de auditoria...")
    try:
        from atualizar_logs_auditoria import atualizar_estrutura_logs
        if atualizar_estrutura_logs():
            print("✅ Estrutura de logs atualizada com sucesso!")
            success_count += 1
        else:
            print("❌ Falha ao atualizar estrutura de logs")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print()
    
    # 2. Inserir dados iniciais
    print("📋 Passo 2/3: Inserindo dados iniciais...")
    try:
        from inserir_dados_iniciais import inserir_dados_iniciais
        if inserir_dados_iniciais():
            print("✅ Dados iniciais inseridos com sucesso!")
            success_count += 1
        else:
            print("❌ Falha ao inserir dados iniciais")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print()
    
    # 3. Criar tabelas se necessário
    print("📋 Passo 3/3: Verificando e criando tabelas...")
    try:
        from criar_tabelas import create_database_migration
        if create_database_migration():
            print("✅ Tabelas verificadas/criadas com sucesso!")
            success_count += 1
        else:
            print("❌ Falha ao verificar/criar tabelas")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    print()
    print("=" * 60)
    
    if success_count == total_steps:
        print("🎉 TODAS AS ATUALIZAÇÕES CONCLUÍDAS COM SUCESSO!")
        print("=" * 60)
        print("\n✅ Sistema totalmente configurado e pronto para uso!")
        print("\n🔑 Credenciais de acesso:")
        print("Administrador: admin / admin123")
        print("Usuário Teste: joao.silva / teste123") 
        print("Agente: maria.santos / agente123")
        print("\n📊 Funcionalidades ativadas:")
        print("- ✅ Auditoria e logs com informações detalhadas")
        print("- ✅ Gerenciamento de grupos de usuários")
        print("- ✅ Email automático para atribuição de agentes")
        print("- ✅ Seção de agentes de suporte")
        print("- ✅ Chamado de teste inserido")
        print("- ✅ Logs de acesso de exemplo")
        return 0
    else:
        print(f"⚠️  ATUALIZAÇÕES PARCIALMENTE CONCLUÍDAS: {success_count}/{total_steps}")
        print("=" * 60)
        print("\nAlgumas atualizações falharam. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
