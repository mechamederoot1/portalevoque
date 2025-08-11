#!/usr/bin/env python3
"""
Script para testar a funcionalidade de histórico SLA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, HistoricoSLA, Chamado, User

def test_sla_history():
    """Testa se a tabela HistoricoSLA foi criada corretamente"""
    with app.app_context():
        try:
            # Verificar se a tabela existe
            print("🔍 Verificando se a tabela HistoricoSLA existe...")
            
            # Tentar criar as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas com sucesso")
            
            # Verificar se conseguimos fazer uma consulta na tabela
            count = HistoricoSLA.query.count()
            print(f"📊 Registros na tabela HistoricoSLA: {count}")
            
            # Verificar se o User tem o campo 'usuario' correto
            admin_user = User.query.filter_by(usuario='admin').first()
            if admin_user:
                print(f"✅ Usuário admin encontrado: {admin_user.usuario}")
                print(f"   Nome completo: {admin_user.nome} {admin_user.sobrenome}")
                print(f"   Email: {admin_user.email}")
            else:
                print("❌ Usuário admin não encontrado")
            
            # Verificar chamados sem data de conclusão
            chamados_sem_data = Chamado.query.filter(
                Chamado.status.in_(['Concluido', 'Cancelado']),
                Chamado.data_conclusao.is_(None)
            ).count()
            print(f"📋 Chamados concluídos sem data de conclusão: {chamados_sem_data}")
            
            print("\n🎉 Teste concluído com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_sla_history()
