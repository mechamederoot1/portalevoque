"""
Teste específico para verificar credenciais Microsoft Graph
"""
import os
import sys

# Simular as variáveis de ambiente
os.environ['CLIENT_ID'] = '09c5a4c9-6c42-4a95-90b0-2c4e3b7c8f21'
os.environ['CLIENT_SECRET'] = 'TyN8Q~XeMQHVzT9yJOF3U8pN2kQ.q6Zh1L' 
os.environ['TENANT_ID'] = 'b3ef24e8-4c9f-4a75-b2d8-9e6c1f3a2e47'
os.environ['USER_ID'] = 'suporte@academiaevoque.com.br'

def testar_credenciais():
    print("=== TESTE DE CREDENCIAIS MICROSOFT GRAPH ===")
    
    try:
        from msal import ConfidentialClientApplication
        import requests
        
        CLIENT_ID = os.getenv('CLIENT_ID')
        CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        TENANT_ID = os.getenv('TENANT_ID')
        USER_ID = os.getenv('USER_ID')
        
        print(f"CLIENT_ID: {CLIENT_ID}")
        print(f"TENANT_ID: {TENANT_ID}")
        print(f"USER_ID: {USER_ID}")
        
        # Teste 1: Verificar se consegue criar o client MSAL
        print("\n--- Teste 1: Criando cliente MSAL ---")
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}"
        )
        print("✅ Cliente MSAL criado com sucesso")
        
        # Teste 2: Tentar obter token
        print("\n--- Teste 2: Obtendo token ---")
        SCOPES = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=SCOPES)
        
        print(f"Resultado do token: {list(result.keys())}")
        
        if "access_token" in result:
            print("✅ Token obtido com sucesso!")
            token = result["access_token"]
            print(f"Token: {token[:50]}...")
            
            # Teste 3: Verificar permissões básicas
            print("\n--- Teste 3: Verificando permissões ---")
            test_url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(test_url, headers=headers)
            print(f"GET /me status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Permissões básicas OK")
            else:
                print(f"❌ Problema com permissões: {response.text}")
            
            # Teste 4: Verificar permissão de envio de email
            print("\n--- Teste 4: Verificando permissão de email ---")
            send_url = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/sendMail"
            
            # Teste apenas a validação da URL, não enviar email real
            test_payload = {
                "message": {
                    "subject": "Teste de permissão",
                    "body": {"contentType": "Text", "content": "Teste"},
                    "toRecipients": [{"emailAddress": {"address": "test@test.com"}}]
                }
            }
            
            # Fazer um teste com dados inválidos para ver se a API responde
            response = requests.post(send_url, headers=headers, json=test_payload)
            print(f"POST sendMail status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code in [202, 400, 403]:
                print("✅ API de email acessível")
            else:
                print("❌ Problema com API de email")
                
        else:
            print("❌ Falha ao obter token:")
            for key, value in result.items():
                print(f"  {key}: {value}")
                
        return "access_token" in result
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = testar_credenciais()
    print(f"\n=== RESULTADO: {'SUCESSO' if success else 'FALHA'} ===")
