#!/usr/bin/env python3
"""
Script para verificar dados existentes no banco
"""
from app import app
from database import db, Chamado, User, Unidade

def verificar_banco():
    with app.app_context():
        print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
        
        try:
            # Testar conexão
            db.session.execute("SELECT 1")
            print("✅ Conexão com banco estabelecida")
            
            # Contar registros
            total_chamados = Chamado.query.count()
            total_usuarios = User.query.count()
            total_unidades = Unidade.query.count()
            
            print(f"📝 Total de Chamados: {total_chamados}")
            print(f"👥 Total de Usuários: {total_usuarios}")
            print(f"🏢 Total de Unidades: {total_unidades}")
            
            if total_chamados > 0:
                print("\n=== AMOSTRA DE CHAMADOS ===")
                chamados = Chamado.query.limit(5).all()
                for c in chamados:
                    print(f"ID: {c.id} | Código: {c.codigo} | Status: {c.status} | Solicitante: {c.solicitante}")
                
                print("\n=== CONTAGEM POR STATUS ===")
                status_counts = {}
                for chamado in Chamado.query.all():
                    status = chamado.status
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    print(f"{status}: {count}")
            else:
                print("⚠️  Nenhum chamado encontrado no banco")
                print("\n💡 Para criar dados de teste, execute: python3 criar_dados_teste.py")
                
        except Exception as e:
            print(f"❌ Erro ao verificar banco: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verificar_banco()
