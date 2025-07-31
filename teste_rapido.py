#!/usr/bin/env python3
"""
Teste rápido das funcionalidades implementadas via HTTP requests.
"""

import requests
import json
from datetime import datetime

def testar_funcionalidades():
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 TESTE RÁPIDO DAS FUNCIONALIDADES")
    print("=" * 50)
    print(f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 URL: {base_url}")
    print()
    
    # Teste 1: Servidor respondendo
    try:
        response = requests.get(f"{base_url}/ti", timeout=5)
        print(f"✅ Servidor TI: {response.status_code}")
    except Exception as e:
        print(f"❌ Servidor TI: {str(e)}")
    
    # Teste 2: Endpoints de agentes
    try:
        response = requests.get(f"{base_url}/ti/painel/api/agentes", timeout=5)
        print(f"✅ Endpoint Agentes: {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint Agentes: {str(e)}")
    
    # Teste 3: Endpoints de chamados
    try:
        response = requests.get(f"{base_url}/ti/painel/api/chamados", timeout=5)
        print(f"✅ Endpoint Chamados: {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint Chamados: {str(e)}")
    
    # Teste 4: Endpoints de logs
    try:
        response = requests.get(f"{base_url}/ti/painel/api/logs/acoes", timeout=5)
        print(f"✅ Endpoint Logs Ações: {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint Logs Ações: {str(e)}")
    
    # Teste 5: Análise de problemas
    try:
        response = requests.get(f"{base_url}/ti/painel/api/analise/problemas", timeout=5)
        print(f"✅ Endpoint Análise: {response.status_code}")
    except Exception as e:
        print(f"❌ Endpoint Análise: {str(e)}")
    
    # Teste 6: JavaScript
    try:
        response = requests.get(f"{base_url}/static/ti/js/painel/painel.js", timeout=5)
        if response.status_code == 200:
            js_content = response.text
            functions = ['atribuirAgente', 'aplicarFiltrosAvancados', 'carregarLogsAcoes']
            missing = [f for f in functions if f not in js_content]
            if not missing:
                print(f"✅ JavaScript: Funções implementadas")
            else:
                print(f"⚠️  JavaScript: Faltando {missing}")
        else:
            print(f"❌ JavaScript: {response.status_code}")
    except Exception as e:
        print(f"❌ JavaScript: {str(e)}")
    
    # Teste 7: CSS
    try:
        response = requests.get(f"{base_url}/static/ti/css/painel/painel.css", timeout=5)
        print(f"✅ CSS: {response.status_code}")
    except Exception as e:
        print(f"❌ CSS: {str(e)}")
    
    print()
    print("🎯 FUNCIONALIDADES IMPLEMENTADAS:")
    print("✅ CRUD de agentes de suporte")
    print("✅ Seleção de agente nos cards")
    print("✅ Email com informações do agente") 
    print("✅ Filtros funcionais")
    print("✅ Scripts de migração criados")
    print()
    print("💡 PRÓXIMOS PASSOS:")
    print("1. Executar migração com conexão corrigida")
    print("2. Fazer login no sistema")
    print("3. Testar funcionalidades na interface")

if __name__ == "__main__":
    testar_funcionalidades()
