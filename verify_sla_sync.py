#!/usr/bin/env python3
"""
SCRIPT DE VERIFICAÇÃO RÁPIDA - SLA SYNC
======================================

Script para verificar rapidamente se todas as configurações
SLA estão sincronizadas com o horário de São Paulo.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, Configuracao, ConfiguracaoSLA, Feriado, Chamado, get_brazil_time
import json
from datetime import date

def verificacao_rapida():
    """Executa verificação rápida do sistema SLA"""
    with app.app_context():
        print("🔍 VERIFICAÇÃO RÁPIDA - SISTEMA SLA")
        print("=" * 40)
        print(f"⏰ Horário atual SP: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S %Z')}")
        print()
        
        status = {
            'configuracoes_sla': False,
            'horario_comercial': False,
            'feriados': False,
            'configs_detalhadas': False,
            'chamados_recentes': False
        }
        
        # 1. Verificar configurações SLA
        config_sla = Configuracao.query.filter_by(chave='sla').first()
        if config_sla:
            try:
                dados = json.loads(config_sla.valor)
                if 'timezone' in dados and dados['timezone'] == 'America/Sao_Paulo':
                    status['configuracoes_sla'] = True
                    print("✅ Configurações SLA: OK")
                else:
                    print("❌ Configurações SLA: Timezone incorreto ou ausente")
            except:
                print("❌ Configurações SLA: Erro ao processar dados")
        else:
            print("❌ Configurações SLA: Não encontradas")
        
        # 2. Verificar horário comercial
        config_horario = Configuracao.query.filter_by(chave='horario_comercial').first()
        if config_horario:
            try:
                dados = json.loads(config_horario.valor)
                if 'timezone' in dados and dados['timezone'] == 'America/Sao_Paulo':
                    status['horario_comercial'] = True
                    print("✅ Horário Comercial: OK")
                else:
                    print("❌ Horário Comercial: Timezone incorreto ou ausente")
            except:
                print("❌ Horário Comercial: Erro ao processar dados")
        else:
            print("❌ Horário Comercial: Não encontrado")
        
        # 3. Verificar feriados
        ano_atual = date.today().year
        feriados_count = Feriado.query.filter(
            db.extract('year', Feriado.data) == ano_atual,
            Feriado.ativo == True
        ).count()
        
        if feriados_count >= 8:
            status['feriados'] = True
            print(f"✅ Feriados: {feriados_count} feriados cadastrados")
        else:
            print(f"❌ Feriados: Apenas {feriados_count} feriados (mínimo 8)")
        
        # 4. Verificar configurações detalhadas
        configs_sla_count = ConfiguracaoSLA.query.filter_by(ativo=True).count()
        if configs_sla_count >= 4:
            status['configs_detalhadas'] = True
            print(f"✅ Configurações Detalhadas: {configs_sla_count} prioridades configuradas")
        else:
            print(f"❌ Configurações Detalhadas: Apenas {configs_sla_count} (mínimo 4)")
        
        # 5. Verificar chamados recentes
        chamados_recentes = Chamado.query.order_by(Chamado.data_abertura.desc()).limit(5).all()
        chamados_com_timezone_correto = 0
        
        for chamado in chamados_recentes:
            if chamado.data_abertura and chamado.data_abertura.tzinfo is None:
                chamados_com_timezone_correto += 1
        
        if len(chamados_recentes) == 0 or chamados_com_timezone_correto == len(chamados_recentes):
            status['chamados_recentes'] = True
            print(f"✅ Chamados Recentes: {len(chamados_recentes)} chamados com timezone correto")
        else:
            print(f"❌ Chamados Recentes: {len(chamados_recentes) - chamados_com_timezone_correto} com timezone incorreto")
        
        print()
        print("📊 RESUMO DA VERIFICAÇÃO")
        print("-" * 30)
        
        total_checks = len(status)
        checks_ok = sum(1 for v in status.values() if v)
        
        print(f"Verificações OK: {checks_ok}/{total_checks}")
        print(f"Status Geral: {'✅ SISTEMA OK' if checks_ok == total_checks else '❌ NECESSITA CORREÇÃO'}")
        
        if checks_ok < total_checks:
            print()
            print("🔧 RECOMENDAÇÃO:")
            print("Execute o script 'sync_sla_database.py' para corrigir os problemas")
        
        return checks_ok == total_checks

if __name__ == '__main__':
    if verificacao_rapida():
        print("\n🎉 SISTEMA 100% SINCRONIZADO!")
        sys.exit(0)
    else:
        print("\n⚠️  SISTEMA NECESSITA SINCRONIZAÇÃO!")
        sys.exit(1)
