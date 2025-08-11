#!/usr/bin/env python3
"""
Script para debugar os cálculos de SLA e entender por que chamados aparecem como violados
"""

def debug_sla_chamados():
    """Debug dos cálculos de SLA"""
    
    try:
        from flask import Flask
        from database import db, Chamado
        from config import get_config
        from setores.ti.sla_utils import calcular_sla_chamado_correto, carregar_configuracoes_sla, carregar_configuracoes_horario_comercial
        import pytz
        
        app = Flask(__name__)
        app.config.from_object(get_config())
        db.init_app(app)
        
        BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')
        
        with app.app_context():
            print("🔍 DEBUGANDO CÁLCULOS DE SLA")
            print("=" * 80)
            
            # Carregar configurações
            config_sla = carregar_configuracoes_sla()
            config_horario = carregar_configuracoes_horario_comercial()
            
            print(f"📋 Configurações SLA:")
            for chave, valor in config_sla.items():
                print(f"   • {chave}: {valor}h")
            
            print(f"\n⏰ Horário Comercial:")
            print(f"   • Início: {config_horario.get('inicio', 'N/A')}")
            print(f"   • Fim: {config_horario.get('fim', 'N/A')}")
            print(f"   • Dias da semana: {config_horario.get('dias_semana', 'N/A')}")
            
            # Buscar alguns chamados concluídos para teste
            chamados_concluidos = Chamado.query.filter_by(status='Concluido').limit(5).all()
            
            print(f"\n🎯 Analisando {len(chamados_concluidos)} chamados concluídos:")
            print("=" * 80)
            
            for chamado in chamados_concluidos:
                print(f"\n📞 CHAMADO: {chamado.codigo}")
                print(f"   Solicitante: {chamado.solicitante}")
                print(f"   Prioridade: {chamado.prioridade}")
                print(f"   Status: {chamado.status}")
                
                # Mostrar datas
                print(f"\n📅 DATAS:")
                print(f"   Abertura: {chamado.data_abertura}")
                print(f"   Conclusão: {chamado.data_conclusao}")
                print(f"   Tem data_conclusao? {'✅ SIM' if chamado.data_conclusao else '❌ NÃO'}")
                
                if chamado.data_abertura:
                    data_abertura_brazil = chamado.get_data_abertura_brazil()
                    print(f"   Abertura (BR): {data_abertura_brazil}")
                
                if chamado.data_conclusao:
                    data_conclusao_brazil = chamado.get_data_conclusao_brazil()
                    print(f"   Conclusão (BR): {data_conclusao_brazil}")
                    
                    # Calcular diferença simples
                    if data_abertura_brazil and data_conclusao_brazil:
                        diferenca = data_conclusao_brazil - data_abertura_brazil
                        horas_totais = diferenca.total_seconds() / 3600
                        print(f"   Diferença total: {horas_totais:.2f}h ({diferenca})")
                
                # Calcular SLA
                print(f"\n🔢 CÁLCULO SLA:")
                sla_info = calcular_sla_chamado_correto(chamado, config_sla, config_horario)
                
                print(f"   Horas decorridas: {sla_info['horas_decorridas']}h")
                print(f"   Horas úteis: {sla_info['horas_uteis_decorridas']}h")
                print(f"   SLA limite: {sla_info['sla_limite']}h")
                print(f"   Status SLA: {sla_info['sla_status']}")
                print(f"   Violação resolução: {sla_info['violacao_resolucao']}")
                print(f"   Tempo resolução: {sla_info['tempo_resolucao']}h")
                print(f"   Tempo resolução úteis: {sla_info['tempo_resolucao_uteis']}h")
                
                # Verificar se está violado
                if sla_info['sla_status'] == 'Violado':
                    print(f"   ❌ PROBLEMA: SLA violado!")
                    print(f"   🔍 Análise:")
                    print(f"      • Tempo útil ({sla_info['horas_uteis_decorridas']}h) > SLA ({sla_info['sla_limite']}h)? {sla_info['horas_uteis_decorridas'] > sla_info['sla_limite']}")
                    if sla_info['tempo_resolucao_uteis']:
                        print(f"      • Tempo resolução útil ({sla_info['tempo_resolucao_uteis']}h) > SLA ({sla_info['sla_limite']}h)? {sla_info['tempo_resolucao_uteis'] > sla_info['sla_limite']}")
                else:
                    print(f"   ✅ OK: SLA cumprido!")
                
                print("-" * 40)
            
            # Verificar chamados abertos também
            print(f"\n🔄 Verificando alguns chamados abertos:")
            chamados_abertos = Chamado.query.filter_by(status='Aberto').limit(3).all()
            
            for chamado in chamados_abertos:
                print(f"\n📞 CHAMADO ABERTO: {chamado.codigo}")
                sla_info = calcular_sla_chamado_correto(chamado, config_sla, config_horario)
                print(f"   Status SLA: {sla_info['sla_status']}")
                print(f"   Horas úteis: {sla_info['horas_uteis_decorridas']}h / {sla_info['sla_limite']}h")
            
            print(f"\n✅ Debug concluído!")
            
    except Exception as e:
        print(f"❌ Erro no debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sla_chamados()
