#!/usr/bin/env python3
"""
Debug utility para investigar violações de SLA que persistem após limpeza de histórico
"""

from datetime import datetime, timedelta
from flask import current_app
from ..sla_utils import verificar_sla_chamado, get_brazil_time
from database import Chamado, db
import pytz

def debug_sla_violations():
    """
    Debug das violações de SLA que persistem
    """
    print("=== DEBUG SLA VIOLATIONS ===")
    
    # Buscar chamados concluídos que ainda aparecem como violados
    chamados_concluidos = Chamado.query.filter(
        Chamado.status.in_(['Concluido', 'Cancelado'])
    ).limit(10).all()
    
    violations_found = []
    
    for chamado in chamados_concluidos:
        print(f"\n--- Chamado {chamado.codigo} ---")
        print(f"Status: {chamado.status}")
        print(f"Prioridade: {chamado.prioridade}")
        print(f"Data Abertura: {chamado.data_abertura}")
        print(f"Data Conclusão: {chamado.data_conclusao}")
        
        if not chamado.data_conclusao and chamado.status in ['Concluido', 'Cancelado']:
            print("⚠️  PROBLEMA: Chamado concluído sem data de conclusão!")
            violations_found.append({
                'codigo': chamado.codigo,
                'problema': 'Sem data de conclusão',
                'status': chamado.status
            })
            continue
            
        try:
            # Verificar SLA atual
            sla_info = verificar_sla_chamado(chamado)
            print(f"SLA Status: {sla_info.get('status', 'N/A')}")
            print(f"Tempo Decorrido: {sla_info.get('tempo_decorrido_formatado', 'N/A')}")
            print(f"SLA Limite: {sla_info.get('sla_limite_formatado', 'N/A')}")
            
            if sla_info.get('status') == 'Violado' and chamado.status in ['Concluido', 'Cancelado']:
                print("🔴 VIOLAÇÃO ENCONTRADA em chamado concluído!")
                violations_found.append({
                    'codigo': chamado.codigo,
                    'problema': 'Violação em chamado concluído',
                    'status': chamado.status,
                    'sla_info': sla_info
                })
                
        except Exception as e:
            print(f"❌ Erro ao verificar SLA: {e}")
            violations_found.append({
                'codigo': chamado.codigo,
                'problema': f'Erro de cálculo: {e}',
                'status': chamado.status
            })
    
    print(f"\n=== RESUMO ===")
    print(f"Violações encontradas: {len(violations_found)}")
    
    for violation in violations_found:
        print(f"- {violation['codigo']}: {violation['problema']}")
    
    return violations_found

if __name__ == "__main__":
    debug_sla_violations()
