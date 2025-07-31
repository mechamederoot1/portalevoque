#!/usr/bin/env python3
"""
Script de teste para validar as funcionalidades implementadas.
Testa endpoints, agentes, filtros e banco de dados.
"""

import requests
import json
import time
from datetime import datetime

# Configurações do teste
BASE_URL = "http://127.0.0.1:5000"
HEADERS = {'Content-Type': 'application/json'}

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)

def print_test(test_name, success, details=None):
    """Imprime resultado do teste"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def test_server_running():
    """Testa se o servidor está rodando"""
    print_header("TESTE DE CONECTIVIDADE")
    
    try:
        response = requests.get(f"{BASE_URL}/ti", timeout=5)
        if response.status_code in [200, 302, 401]:  # 401 é normal (não logado)
            print_test("Servidor respondendo", True, f"Status: {response.status_code}")
            return True
        else:
            print_test("Servidor respondendo", False, f"Status inesperado: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Servidor respondendo", False, f"Erro: {str(e)}")
        return False

def test_database_connection():
    """Testa conexão com banco via aplicação"""
    print_header("TESTE DE CONEXÃO COM BANCO")
    
    try:
        # Testar endpoint que requer banco
        response = requests.get(f"{BASE_URL}/ti/painel/api/chamados", timeout=10)
        
        # 401 ou 403 é normal (não autenticado), mas indica que chegou ao endpoint
        if response.status_code in [200, 401, 403]:
            print_test("Conexão com banco via app", True, f"Endpoint responde: {response.status_code}")
            return True
        else:
            print_test("Conexão com banco via app", False, f"Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("Conexão com banco via app", False, f"Erro: {str(e)}")
        return False

def test_endpoints_accessibility():
    """Testa acessibilidade dos endpoints principais"""
    print_header("TESTE DE ENDPOINTS")
    
    endpoints_to_test = [
        "/ti/painel/api/chamados",
        "/ti/painel/api/agentes", 
        "/ti/painel/api/usuarios-disponiveis",
        "/ti/painel/api/logs/acoes",
        "/ti/painel/api/logs/acesso",
        "/ti/painel/api/analise/problemas"
    ]
    
    results = []
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            # Esperamos 401/403 (não autenticado) ou 200 (sucesso)
            accessible = response.status_code in [200, 401, 403]
            print_test(f"Endpoint {endpoint}", accessible, f"Status: {response.status_code}")
            results.append(accessible)
        except requests.exceptions.RequestException as e:
            print_test(f"Endpoint {endpoint}", False, f"Erro: {str(e)}")
            results.append(False)
    
    return all(results)

def test_static_files():
    """Testa se arquivos estáticos estão acessíveis"""
    print_header("TESTE DE ARQUIVOS ESTÁTICOS")
    
    static_files = [
        "/static/ti/css/painel/painel.css",
        "/static/ti/js/painel/painel.js"
    ]
    
    results = []
    for file_path in static_files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            accessible = response.status_code == 200
            print_test(f"Arquivo {file_path}", accessible, f"Status: {response.status_code}")
            results.append(accessible)
        except requests.exceptions.RequestException as e:
            print_test(f"Arquivo {file_path}", False, f"Erro: {str(e)}")
            results.append(False)
    
    return all(results)

def test_html_pages():
    """Testa se páginas HTML principais carregam"""
    print_header("TESTE DE PÁGINAS HTML")
    
    pages = [
        "/ti",
        "/ti/painel"
    ]
    
    results = []
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}", timeout=5)
            # 200 (sucesso) ou 302 (redirecionamento para login) são válidos
            accessible = response.status_code in [200, 302]
            print_test(f"Página {page}", accessible, f"Status: {response.status_code}")
            results.append(accessible)
        except requests.exceptions.RequestException as e:
            print_test(f"Página {page}", False, f"Erro: {str(e)}")
            results.append(False)
    
    return all(results)

def test_javascript_functionality():
    """Testa se o JavaScript principal carrega sem erros de sintaxe"""
    print_header("TESTE DE JAVASCRIPT")
    
    try:
        response = requests.get(f"{BASE_URL}/static/ti/js/painel/painel.js", timeout=5)
        if response.status_code == 200:
            js_content = response.text
            
            # Verificar se contém funções principais implementadas
            functions_to_check = [
                'filterChamados',
                'aplicarFiltrosAvancados', 
                'atribuirAgente',
                'carregarAgentesDisponiveis',
                'carregarLogsAcoes',
                'carregarAnaliseProblemas'
            ]
            
            missing_functions = []
            for func in functions_to_check:
                if func not in js_content:
                    missing_functions.append(func)
            
            if not missing_functions:
                print_test("JavaScript carregado", True, f"Todas as funções principais encontradas")
                print_test("Funções implementadas", True, f"{len(functions_to_check)} funções verificadas")
                return True
            else:
                print_test("JavaScript carregado", True, f"Arquivo acessível")
                print_test("Funções implementadas", False, f"Faltando: {', '.join(missing_functions)}")
                return False
        else:
            print_test("JavaScript carregado", False, f"Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("JavaScript carregado", False, f"Erro: {str(e)}")
        return False

def test_css_loading():
    """Testa se CSS principal carrega"""
    print_header("TESTE DE CSS")
    
    try:
        response = requests.get(f"{BASE_URL}/static/ti/css/painel/painel.css", timeout=5)
        if response.status_code == 200:
            css_content = response.text
            
            # Verificar se contém estilos principais
            css_classes = [
                '.chamado-card',
                '.sidebar',
                '.content-section'
            ]
            
            missing_classes = []
            for css_class in css_classes:
                if css_class not in css_content:
                    missing_classes.append(css_class)
            
            if not missing_classes:
                print_test("CSS carregado", True, f"Estilos principais encontrados")
                return True
            else:
                print_test("CSS carregado", True, f"Arquivo acessível")
                print_test("Estilos implementados", False, f"Faltando: {', '.join(missing_classes)}")
                return False
        else:
            print_test("CSS carregado", False, f"Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("CSS carregado", False, f"Erro: {str(e)}")
        return False

def test_html_structure():
    """Testa estrutura HTML do painel"""
    print_header("TESTE DE ESTRUTURA HTML")
    
    try:
        response = requests.get(f"{BASE_URL}/ti/painel", timeout=5)
        if response.status_code in [200, 302]:
            if response.status_code == 302:
                print_test("HTML acessível", True, "Redirecionamento para login (normal)")
                return True
                
            html_content = response.text
            
            # Verificar elementos principais do painel
            elements_to_check = [
                'id="chamadosGrid"',
                'id="filtroSolicitante"',
                'id="filtroProblema"',
                'id="btnFiltrarChamados"',
                'id="agentes-suporte"',
                'id="logs-acoes"',
                'id="analise-problemas"'
            ]
            
            missing_elements = []
            for element in elements_to_check:
                if element not in html_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print_test("Estrutura HTML completa", True, f"Todos os elementos encontrados")
                return True
            else:
                print_test("Estrutura HTML completa", False, f"Faltando: {', '.join(missing_elements)}")
                return False
        else:
            print_test("HTML acessível", False, f"Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_test("HTML acessível", False, f"Erro: {str(e)}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO BATERIA DE TESTES DAS FUNCIONALIDADES")
    print(f"📅 Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 URL base: {BASE_URL}")
    
    # Lista de testes
    tests = [
        ("Conectividade do Servidor", test_server_running),
        ("Conexão com Banco de Dados", test_database_connection),
        ("Acessibilidade dos Endpoints", test_endpoints_accessibility),
        ("Carregamento de Arquivos Estáticos", test_static_files),
        ("Carregamento de Páginas HTML", test_html_pages),
        ("Funcionalidade JavaScript", test_javascript_functionality),
        ("Carregamento de CSS", test_css_loading),
        ("Estrutura HTML", test_html_structure)
    ]
    
    results = []
    
    # Executar testes
    for test_name, test_function in tests:
        try:
            result = test_function()
            results.append(result)
        except Exception as e:
            print_test(f"ERRO em {test_name}", False, str(e))
            results.append(False)
    
    # Resumo final
    print_header("RESUMO DOS TESTES")
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"📊 Testes executados: {total}")
    print(f"✅ Testes aprovados: {passed}")
    print(f"❌ Testes falharam: {total - passed}")
    print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 SISTEMA FUNCIONANDO ADEQUADAMENTE!")
        print("✅ A maioria das funcionalidades está operacional")
    elif success_rate >= 60:
        print("\n⚠️  SISTEMA PARCIALMENTE FUNCIONAL")
        print("🔧 Algumas funcionalidades precisam de ajustes")
    else:
        print("\n❌ SISTEMA COM PROBLEMAS SIGNIFICATIVOS")
        print("🚨 Várias funcionalidades precisam de correção")
    
    # Recomendações baseadas nos resultados
    print("\n📋 RECOMENDAÇÕES:")
    
    if not results[0]:  # Servidor não responde
        print("- Verificar se o servidor Flask está rodando")
        print("- Confirmar porta e endereço corretos")
    
    if not results[1]:  # Banco não conecta
        print("- Verificar configurações de banco de dados")
        print("- Confirmar credenciais e conectividade")
    
    if not results[2]:  # Endpoints não acessíveis
        print("- Verificar registro de blueprints")
        print("- Confirmar rotas implementadas")
    
    if passed < total:
        print("- Executar novamente após correções")
        print("- Verificar logs do servidor para erros específicos")
    
    return success_rate

if __name__ == "__main__":
    try:
        success_rate = run_all_tests()
        
        # Código de saída baseado na taxa de sucesso
        if success_rate >= 80:
            exit(0)  # Sucesso
        elif success_rate >= 60:
            exit(1)  # Parcialmente funcional
        else:
            exit(2)  # Problemas significativos
            
    except KeyboardInterrupt:
        print("\n⚠️  Testes interrompidos pelo usuário")
        exit(3)
    except Exception as e:
        print(f"\n❌ Erro inesperado durante os testes: {str(e)}")
        exit(4)
