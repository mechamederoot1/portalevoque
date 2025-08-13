#!/bin/bash

# Script para executar setup das tabelas SLA no MySQL Azure
# Evoque Fitness - Sistema de Chamados

echo "🏗️  SETUP SLA - EVOQUE FITNESS"
echo "=============================="
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.7+ para continuar."
    exit 1
fi

echo "✅ Python3 encontrado"

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instale pip para continuar."
    exit 1
fi

echo "✅ pip3 encontrado"

# Instalar dependências se necessário
echo "📦 Verificando dependências..."
pip3 install -r requirements_sla_setup.txt --quiet

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas/verificadas"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Função para mostrar menu
show_menu() {
    echo ""
    echo "🎯 ESCOLHA UMA OPÇÃO:"
    echo "==================="
    echo "1) Testar conexão com banco"
    echo "2) Executar setup completo (criar tabelas + dados)"
    echo "3) Validar configurações existentes"
    echo "4) Sair"
    echo ""
}

# Função para testar conexão
test_connection() {
    echo ""
    echo "🧪 Testando conexão com MySQL Azure..."
    python3 setup_sla_azure.py test
    
    if [ $? -eq 0 ]; then
        echo "✅ Teste de conexão bem-sucedido!"
    else
        echo "❌ Falha no teste de conexão"
        echo "⚠️  Verifique as credenciais no arquivo .env"
    fi
}

# Função para executar setup
run_setup() {
    echo ""
    echo "🏗️  Executando setup completo..."
    python3 setup_sla_azure.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Setup concluído com sucesso!"
        echo "✅ Tabelas SLA criadas"
        echo "✅ Dados padrão inseridos"
        echo ""
        echo "📚 Próximos passos:"
        echo "   1. Execute a aplicação Flask"
        echo "   2. Acesse /ti/painel"
        echo "   3. Vá em 'SLA & Métricas'"
        echo "   4. Verifique as configurações"
    else
        echo "❌ Falha no setup"
    fi
}

# Função para validar
run_validation() {
    echo ""
    echo "🔍 Validando configurações..."
    python3 validate_sla_setup.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Validação concluída"
    else
        echo "❌ Problemas encontrados na validação"
    fi
}

# Loop principal
while true; do
    show_menu
    read -p "Digite sua opção (1-4): " choice
    
    case $choice in
        1)
            test_connection
            ;;
        2)
            run_setup
            ;;
        3)
            run_validation
            ;;
        4)
            echo "👋 Saindo..."
            exit 0
            ;;
        *)
            echo "❌ Opção inválida. Tente novamente."
            ;;
    esac
    
    echo ""
    read -p "Pressione Enter para continuar..."
done
