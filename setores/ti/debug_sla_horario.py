#!/usr/bin/env python3
"""
Script para debugar e verificar cálculo de SLA considerando horário comercial
"""
from datetime import datetime, timedelta
import pytz
from setores.ti.sla_utils import calcular_horas_uteis, eh_horario_comercial, BRAZIL_TZ

def debug_chamado_ronaldo():
    """Debug do chamado específico que está mostrando 17.5h"""
    print("=== DEBUG CHAMADO RONALDO ===")
    
    # Simular o chamado criado ontem às 16:00
    agora = datetime.now(BRAZIL_TZ)
    print(f"Horário atual: {agora.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Data de abertura: ontem às 16:00
    ontem_16h = agora.replace(hour=16, minute=0, second=0, microsecond=0) - timedelta(days=1)
    print(f"Data abertura: {ontem_16h.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar se 16:00 está em horário comercial
    print(f"16:00 é horário comercial? {eh_horario_comercial(ontem_16h)}")
    
    # Calcular horas totais (sem considerar horário comercial)
    tempo_total = agora - ontem_16h
    horas_totais = tempo_total.total_seconds() / 3600
    print(f"Horas totais (sem pausa): {horas_totais:.1f}h")
    
    # Calcular horas úteis (considerando horário comercial)
    horas_uteis = calcular_horas_uteis(ontem_16h, agora)
    print(f"Horas úteis (com pausa): {horas_uteis:.1f}h")
    
    # Detalhar o cálculo dia por dia
    print("\n=== DETALHAMENTO ===")
    data_atual = ontem_16h.replace(hour=0, minute=0, second=0)
    
    while data_atual.date() <= agora.date():
        print(f"\n📅 {data_atual.strftime('%d/%m/%Y')} ({['Seg','Ter','Qua','Qui','Sex','Sab','Dom'][data_atual.weekday()]})")
        
        # Verificar se é dia útil
        if data_atual.weekday() not in [0, 1, 2, 3, 4]:  # Segunda a sexta
            print("   ❌ Fim de semana - não conta")
            data_atual += timedelta(days=1)
            continue
        
        # Horário comercial: 08:00 às 18:00
        inicio_comercial = data_atual.replace(hour=8, minute=0)
        fim_comercial = data_atual.replace(hour=18, minute=0)
        
        # Período efetivo para este dia
        if data_atual.date() == ontem_16h.date():
            # Primeiro dia - começar às 16:00
            periodo_inicio = ontem_16h
            periodo_fim = min(agora, fim_comercial)
            print(f"   📍 Primeiro dia: {periodo_inicio.strftime('%H:%M')} até {periodo_fim.strftime('%H:%M')}")
        elif data_atual.date() == agora.date():
            # Último dia - até agora
            periodo_inicio = max(agora.replace(hour=8, minute=0), inicio_comercial)
            periodo_fim = min(agora, fim_comercial)
            print(f"   📍 Último dia: {periodo_inicio.strftime('%H:%M')} até {periodo_fim.strftime('%H:%M')}")
        else:
            # Dia completo
            periodo_inicio = inicio_comercial
            periodo_fim = fim_comercial
            print(f"   📍 Dia completo: {periodo_inicio.strftime('%H:%M')} até {periodo_fim.strftime('%H:%M')}")
        
        if periodo_inicio < periodo_fim:
            delta = periodo_fim - periodo_inicio
            horas_dia = delta.total_seconds() / 3600
            print(f"   ✅ Horas úteis do dia: {horas_dia:.1f}h")
        else:
            print(f"   ❌ Nenhuma hora útil (fora do horário comercial)")
        
        data_atual += timedelta(days=1)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Horas totais: {horas_totais:.1f}h")
    print(f"   Horas úteis: {horas_uteis:.1f}h")
    print(f"   SLA Crítica: 2h")
    print(f"   Status: {'✅ Dentro do prazo' if horas_uteis <= 2 else '❌ Violado'}")

if __name__ == "__main__":
    debug_chamado_ronaldo()
