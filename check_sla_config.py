#!/usr/bin/env python3
"""
Script para verificar configurações SLA no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, Configuracao
import json

def verificar_configuracoes_sla():
    """Verifica se as configurações SLA estão no banco"""
    with app.app_context():
        try:
            print("🔍 VERIFICANDO CONFIGURAÇÕES SLA NO BANCO")
            print("=" * 50)
            
            # Verificar configuração de SLA
            config_sla = Configuracao.query.filter_by(chave='sla').first()
            if config_sla:
                dados_sla = json.loads(config_sla.valor)
                print("✅ CONFIGURAÇÕES SLA ENCONTRADAS:")
                for chave, valor in dados_sla.items():
                    print(f"   {chave}: {valor}h")
            else:
                print("❌ CONFIGURAÇÕES SLA NÃO ENCONTRADAS!")
            
            print()
            
            # Verificar configuração de horário comercial
            config_horario = Configuracao.query.filter_by(chave='horario_comercial').first()
            if config_horario:
                dados_horario = json.loads(config_horario.valor)
                print("✅ CONFIGURAÇÕES HORÁRIO COMERCIAL ENCONTRADAS:")
                for chave, valor in dados_horario.items():
                    if chave == 'dias_semana':
                        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                        dias_trabalho = [dias[i] for i in valor]
                        print(f"   {chave}: {dias_trabalho}")
                    else:
                        print(f"   {chave}: {valor}")
            else:
                print("❌ CONFIGURAÇÕES HORÁRIO COMERCIAL NÃO ENCONTRADAS!")
            
            print()
            
            # Listar todas as configurações
            todas_configs = Configuracao.query.all()
            print(f"📊 TOTAL DE CONFIGURAÇÕES: {len(todas_configs)}")
            print("Chaves existentes:")
            for config in todas_configs:
                print(f"   - {config.chave}")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    verificar_configuracoes_sla()
