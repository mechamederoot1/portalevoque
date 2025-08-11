#!/bin/bash

# SCRIPT DE EXECUÇÃO - SINCRONIZAÇÃO SLA
# =====================================
# 
# Script bash para facilitar a execução da sincronização SLA
# Pode ser executado com diferentes opções

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para exibir header
show_header() {
    echo -e "${BLUE}"
    echo "======================================"
    echo "🇧🇷 SINCRONIZAÇÃO SLA - EVOQUE FITNESS"
    echo "   Timezone: São Paulo/Brasil"
    echo "======================================"
    echo -e "${NC}"
}

# Função para verificação rápida
quick_check() {
    echo -e "${YELLOW}Executando verificação rápida...${NC}"
    python3 verify_sla_sync.py
    return $?
}

# Função para sincronização completa
full_sync() {
    echo -e "${YELLOW}Executando sincronização completa...${NC}"
    python3 sync_sla_database.py
    return $?
}

# Função para backup antes da sincronização
backup_database() {
    echo -e "${YELLOW}Criando backup do banco de dados...${NC}"
    timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Aqui você pode adicionar comando de backup específico do seu banco
    # Exemplo para MySQL:
    # mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > "backup_sla_${timestamp}.sql"
    
    echo -e "${GREEN}Backup criado (se configurado)${NC}"
}

# Função principal
main() {
    show_header
    
    case "$1" in
        "check" | "verificar")
            quick_check
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Sistema SLA está sincronizado!${NC}"
            else
                echo -e "${RED}❌ Sistema SLA necessita sincronização!${NC}"
                echo -e "${YELLOW}Execute: $0 sync${NC}"
            fi
            ;;
        
        "sync" | "sincronizar")
            echo -e "${YELLOW}Iniciando processo de sincronização...${NC}"
            
            # Verificação inicial
            echo "1. Verificação inicial..."
            quick_check
            initial_status=$?
            
            # Backup (opcional)
            if [ "$2" = "--backup" ]; then
                echo "2. Criando backup..."
                backup_database
            fi
            
            # Sincronização
            echo "3. Executando sincronização..."
            full_sync
            sync_status=$?
            
            # Verificação final
            echo "4. Verificação final..."
            quick_check
            final_status=$?
            
            if [ $sync_status -eq 0 ] && [ $final_status -eq 0 ]; then
                echo -e "${GREEN}"
                echo "🎉 SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!"
                echo "✅ Sistema SLA 100% sincronizado com São Paulo/Brasil"
                echo -e "${NC}"
            else
                echo -e "${RED}"
                echo "❌ ERRO NA SINCRONIZAÇÃO!"
                echo "Verifique os logs acima para mais detalhes"
                echo -e "${NC}"
            fi
            ;;
        
        "status")
            echo -e "${BLUE}Status atual do sistema SLA:${NC}"
            quick_check
            ;;
        
        "help" | "--help" | "-h" | "")
            echo "USO: $0 [COMANDO] [OPÇÕES]"
            echo ""
            echo "COMANDOS:"
            echo "  check, verificar    - Verificação rápida do sistema"
            echo "  sync, sincronizar   - Sincronização completa"
            echo "  status             - Status atual do sistema"
            echo "  help               - Exibe esta ajuda"
            echo ""
            echo "OPÇÕES (para sync):"
            echo "  --backup           - Cria backup antes da sincronização"
            echo ""
            echo "EXEMPLOS:"
            echo "  $0 check           # Verificação rápida"
            echo "  $0 sync            # Sincronização sem backup"
            echo "  $0 sync --backup   # Sincronização com backup"
            echo ""
            echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
            echo "Este script deve ser executado no diretório raiz do projeto"
            echo "onde estão os arquivos sync_sla_database.py e verify_sla_sync.py"
            ;;
        
        *)
            echo -e "${RED}Comando inválido: $1${NC}"
            echo "Use '$0 help' para ver os comandos disponíveis"
            exit 1
            ;;
    esac
}

# Verificar se estamos no diretório correto
if [ ! -f "sync_sla_database.py" ] || [ ! -f "verify_sla_sync.py" ]; then
    echo -e "${RED}❌ ERRO: Scripts não encontrados!${NC}"
    echo "Certifique-se de executar este script no diretório raiz do projeto"
    echo "onde estão os arquivos sync_sla_database.py e verify_sla_sync.py"
    exit 1
fi

# Executar função principal
main "$@"
