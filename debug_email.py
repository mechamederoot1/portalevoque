#!/usr/bin/env python3
"""
Script de debug para testar o sistema de email
"""
import os
import sys
import traceback

def verificar_variaveis_ambiente():
    print("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
    vars_necessarias = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID', 'USER_ID', 'EMAIL_TI']
    
    for var in vars_necessarias:
        valor = os.getenv(var)
        if valor:
            print(f"✅ {var}: {valor[:8]}... (configurada)")
        else:
            print(f"❌ {var}: NÃO CONFIGURADA")
    
    return all(os.getenv(var) for var in vars_necessarias)

def testar_imports():
    print("\n=== TESTANDO IMPORTS ===")
    try:
        import requests
        print("✅ requests: OK")
    except Exception as e:
        print(f"❌ requests: ERRO - {e}")
        return False
    
    try:
        from msal import ConfidentialClientApplication
        print("✅ msal: OK")
    except Exception as e:
        print(f"❌ msal: ERRO - {e}")
        return False
    
    return True

def testar_token():
    print("\n=== TESTANDO OBTENÇÃO DE TOKEN ===")
    try:
        from msal import ConfidentialClientApplication
        
        CLIENT_ID = os.getenv('CLIENT_ID')
        CLIENT_SECRET = os.getenv('CLIENT_SECRET') 
        TENANT_ID = os.getenv('TENANT_ID')
        
        print(f"🔑 CLIENT_ID: {CLIENT_ID[:8]}...")
        print(f"🔑 TENANT_ID: {TENANT_ID}")
        
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}"
        )
        
        SCOPES = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=SCOPES)
        
        if "access_token" in result:
            print("✅ Token obtido com sucesso!")
            return result["access_token"]
        else:
            print(f"❌ Erro ao obter token: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Exceção ao obter token: {e}")
        traceback.print_exc()
        return None

def testar_envio_email(token):
    print("\n=== TESTANDO ENVIO DE EMAIL ===")
    try:
        import requests
        
        USER_ID = os.getenv('USER_ID')
        
        endpoint = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/sendMail"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        email_data = {
            "message": {
                "subject": "TESTE - Sistema Evoque",
                "body": {
                    "contentType": "Text",
                    "content": "Este é um email de teste do sistema de debug."
                },
                "toRecipients": [
                    {"emailAddress": {"address": "admin@evoquefitness.com"}}
                ]
            },
            "saveToSentItems": "false"
        }
        
        print(f"📤 Enviando para: {endpoint}")
        print(f"📧 Destinatário: admin@evoquefitness.com")
        
        response = requests.post(endpoint, headers=headers, json=email_data)
        
        print(f"📊 Status HTTP: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 202:
            print("✅ Email enviado com sucesso!")
            return True
        else:
            print(f"❌ Falha no envio: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no envio: {e}")
        traceback.print_exc()
        return False

def main():
    print("🔍 INICIANDO DEBUG DO SISTEMA DE EMAIL\n")
    
    # Verificar variáveis
    if not verificar_variaveis_ambiente():
        print("\n❌ ERRO: Variáveis de ambiente não configuradas corretamente!")
        return False
    
    # Testar imports
    if not testar_imports():
        print("\n❌ ERRO: Problemas com imports!")
        return False
    
    # Testar token
    token = testar_token()
    if not token:
        print("\n❌ ERRO: Não foi possível obter token!")
        return False
    
    # Testar envio
    if not testar_envio_email(token):
        print("\n❌ ERRO: Falha no envio de email!")
        return False
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        traceback.print_exc()
        sys.exit(1)
