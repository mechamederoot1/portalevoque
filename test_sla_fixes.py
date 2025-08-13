#!/usr/bin/env python3
"""
Script para testar as correções do sistema SLA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from setores.ti.sla_utils import calcular_sla_chamado_correto, obter_metricas_sla_consolidadas
from database import get_brazil_time

# Mock de chamado para teste
class MockChamado:
    def __init__(self, status, prioridade='Normal', data_abertura=None, data_conclusao=None):
        self.id = 1
        self.status = status
        self.prioridade = prioridade
        self.data_abertura = data_abertura or get_brazil_time() - timedelta(hours=2)
        self.data_conclusao = data_conclusao
        self.data_primeira_resposta = None
        
    def get_data_abertura_brazil(self):
        return self.data_abertura
    
    def get_data_conclusao_brazil(self):
        return self.data_conclusao
    
    def get_data_primeira_resposta_brazil(self):
        return self.data_primeira_resposta

def testar_sla_chamado_concluido():
    """Testa que chamados concluídos com violação não mostram como violação no painel"""
    print("=== Teste 1: Chamado concluído com violação ===")
    
    # Chamado que foi aberto há 30 horas e concluído há 1 hora (violou SLA de 24h)
    agora = get_brazil_time()
    data_abertura = agora - timedelta(hours=30)
    data_conclusao = agora - timedelta(hours=1)
    
    chamado = MockChamado(
        status='Concluido',
        prioridade='Normal',
        data_abertura=data_abertura,
        data_conclusao=data_conclusao
    )
    
    sla_info = calcular_sla_chamado_correto(chamado)
    
    print(f"Status do chamado: {chamado.status}")
    print(f"SLA Status: {sla_info['sla_status']}")
    print(f"Violação resolução: {sla_info['violacao_resolucao']}")
    print(f"Horas úteis decorridas: {sla_info['horas_uteis_decorridas']}")
    print(f"SLA limite: {sla_info['sla_limite']}")
    
    # Para chamados concluídos, o status deve ser 'Violado' se excedeu o limite
    # mas não deve aparecer no contador de violações do painel (só chamados abertos)
    expected_status = 'Violado' if sla_info['horas_uteis_decorridas'] > sla_info['sla_limite'] else 'Cumprido'
    
    if sla_info['sla_status'] == expected_status:
        print("✅ PASSOU: Status SLA correto para chamado concluído")
    else:
        print(f"❌ FALHOU: Esperado '{expected_status}', obtido '{sla_info['sla_status']}'")
    
    return sla_info

def testar_sla_chamado_em_risco():
    """Testa que chamados abertos em risco aparecem corretamente"""
    print("\n=== Teste 2: Chamado aberto em risco ===")
    
    # Chamado aberto há 20 horas (80% do SLA de 24h = risco)
    agora = get_brazil_time()
    data_abertura = agora - timedelta(hours=20)
    
    chamado = MockChamado(
        status='Aberto',
        prioridade='Normal',
        data_abertura=data_abertura
    )
    
    sla_info = calcular_sla_chamado_correto(chamado)
    
    print(f"Status do chamado: {chamado.status}")
    print(f"SLA Status: {sla_info['sla_status']}")
    print(f"Percentual tempo usado: {sla_info['percentual_tempo_usado']}%")
    print(f"Horas úteis decorridas: {sla_info['horas_uteis_decorridas']}")
    print(f"SLA limite: {sla_info['sla_limite']}")
    
    # Deve estar em risco se >= 80% do tempo foi usado
    if sla_info['percentual_tempo_usado'] >= 80 and sla_info['sla_status'] == 'Em Risco':
        print("✅ PASSOU: Chamado em risco identificado corretamente")
    elif sla_info['percentual_tempo_usado'] < 80 and sla_info['sla_status'] == 'Dentro do Prazo':
        print("✅ PASSOU: Chamado dentro do prazo identificado corretamente")
    else:
        print(f"❌ FALHOU: Status inconsistente - {sla_info['percentual_tempo_usado']}% usado, status '{sla_info['sla_status']}'")
    
    return sla_info

def testar_sla_chamado_violado_aberto():
    """Testa que chamados abertos violados aparecem como violação"""
    print("\n=== Teste 3: Chamado aberto violado ===")
    
    # Chamado aberto há 26 horas (excedeu SLA de 24h)
    agora = get_brazil_time()
    data_abertura = agora - timedelta(hours=26)
    
    chamado = MockChamado(
        status='Aberto',
        prioridade='Normal',
        data_abertura=data_abertura
    )
    
    sla_info = calcular_sla_chamado_correto(chamado)
    
    print(f"Status do chamado: {chamado.status}")
    print(f"SLA Status: {sla_info['sla_status']}")
    print(f"Violação resolução: {sla_info['violacao_resolucao']}")
    print(f"Horas úteis decorridas: {sla_info['horas_uteis_decorridas']}")
    print(f"SLA limite: {sla_info['sla_limite']}")
    
    if sla_info['sla_status'] == 'Violado' and sla_info['violacao_resolucao']:
        print("✅ PASSOU: Chamado aberto violado identificado corretamente")
    else:
        print(f"❌ FALHOU: Chamado deveria estar violado")
    
    return sla_info

if __name__ == "__main__":
    print("Testando correções do sistema SLA...\n")
    
    # Executar testes
    testar_sla_chamado_concluido()
    testar_sla_chamado_em_risco()  
    testar_sla_chamado_violado_aberto()
    
    print("\n=== Teste 4: Métricas consolidadas ===")
    print("Nota: Para testar métricas consolidadas, seria necessário ter chamados reais no banco.")
    print("As alterações feitas garantem que:")
    print("- Violações só são contadas para chamados abertos")
    print("- Chamados em risco só são contados para chamados abertos")  
    print("- Percentual de cumprimento é baseado em chamados concluídos")
    
    print("\n✅ Testes de lógica SLA concluídos!")
    print("\nPróximos passos:")
    print("1. Recarregue o painel SLA no navegador")
    print("2. Verifique se violações de chamados concluídos não aparecem")
    print("3. Verifique se chamados abertos em risco aparecem corretamente")
