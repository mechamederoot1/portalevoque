#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simples para executar a criação das tabelas do banco de dados
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar e executar a função de criação
from criar_tabelas import create_database_migration

if __name__ == "__main__":
    print("=" * 60)
    print("EXECUTANDO CRIAÇÃO DAS TABELAS")
    print("=" * 60)
    
    success = create_database_migration()
    
    if success:
        print("\n🎉 TABELAS CRIADAS COM SUCESSO!")
        print("\nSistema pronto para uso!")
        print("Usuário administrador: admin@evoquefitness.com")
        print("Senha inicial: admin123 (ALTERE IMEDIATAMENTE)")
    else:
        print("\n❌ ERRO NA CRIAÇÃO DAS TABELAS!")
        print("Verifique as configurações do banco de dados.")
