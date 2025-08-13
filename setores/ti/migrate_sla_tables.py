#!/usr/bin/env python3
"""
Script para migrar e inicializar as novas tabelas de SLA e horário comercial
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import app
from database import db, ConfiguracaoSLA, HorarioComercial, get_brazil_time
from datetime import time

def migrar_configuracoes_sla():
    """Migra configurações existentes para as novas tabelas"""
    print("🔄 Iniciando migração das configurações de SLA...")
    
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas")
            
            # Verificar se já existem configurações SLA
            slas_existentes = ConfiguracaoSLA.query.count()
            if slas_existentes > 0:
                print(f"✅ Já existem {slas_existentes} configurações SLA")
            else:
                # Criar configurações SLA padrão
                slas_padrao = [
                    {'prioridade': 'Crítica', 'tempo_resolucao': 2.0, 'tempo_primeira_resposta': 1.0},
                    {'prioridade': 'Urgente', 'tempo_resolucao': 2.0, 'tempo_primeira_resposta': 1.0},
                    {'prioridade': 'Alta', 'tempo_resolucao': 8.0, 'tempo_primeira_resposta': 2.0},
                    {'prioridade': 'Normal', 'tempo_resolucao': 24.0, 'tempo_primeira_resposta': 4.0},
                    {'prioridade': 'Baixa', 'tempo_resolucao': 72.0, 'tempo_primeira_resposta': 8.0}
                ]
                
                for sla_config in slas_padrao:
                    new_sla = ConfiguracaoSLA(
                        prioridade=sla_config['prioridade'],
                        tempo_resolucao=sla_config['tempo_resolucao'],
                        tempo_primeira_resposta=sla_config['tempo_primeira_resposta'],
                        considera_horario_comercial=True,
                        considera_feriados=True,
                        ativo=True
                    )
                    db.session.add(new_sla)
                
                db.session.commit()
                print(f"✅ {len(slas_padrao)} configurações SLA criadas")
            
            # Verificar se já existe horário comercial
            horarios_existentes = HorarioComercial.query.count()
            if horarios_existentes > 0:
                print(f"✅ Já existem {horarios_existentes} configurações de horário comercial")
            else:
                # Criar horário comercial padrão
                horario_padrao = HorarioComercial(
                    nome='Horário Padrão',
                    descricao='Horário comercial padrão da empresa (08:00 às 18:00, segunda a sexta)',
                    hora_inicio=time(8, 0),
                    hora_fim=time(18, 0),
                    segunda=True,
                    terca=True,
                    quarta=True,
                    quinta=True,
                    sexta=True,
                    sabado=False,
                    domingo=False,
                    considera_almoco=False,
                    emergencia_ativo=False,
                    ativo=True,
                    padrao=True
                )
                db.session.add(horario_padrao)
                db.session.commit()
                print("✅ Horário comercial padrão criado")
            
            # Verificar configurações criadas
            print("\n📊 Configurações SLA:")
            slas = ConfiguracaoSLA.query.all()
            for sla in slas:
                print(f"   {sla.prioridade}: {sla.tempo_resolucao}h resolução, {sla.tempo_primeira_resposta}h primeira resposta")
            
            print("\n📅 Horário Comercial:")
            horario = HorarioComercial.query.filter_by(padrao=True).first()
            if horario:
                dias = []
                if horario.segunda: dias.append('Seg')
                if horario.terca: dias.append('Ter')
                if horario.quarta: dias.append('Qua')
                if horario.quinta: dias.append('Qui')
                if horario.sexta: dias.append('Sex')
                if horario.sabado: dias.append('Sáb')
                if horario.domingo: dias.append('Dom')
                
                print(f"   {horario.nome}: {horario.hora_inicio} às {horario.hora_fim}")
                print(f"   Dias: {', '.join(dias)}")
                print(f"   Considera almoço: {'Sim' if horario.considera_almoco else 'Não'}")
                print(f"   Emergência ativo: {'Sim' if horario.emergencia_ativo else 'Não'}")
            
            print("\n🎉 Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def verificar_integridade():
    """Verifica a integridade das configurações"""
    print("\n🔍 Verificando integridade das configurações...")
    
    with app.app_context():
        try:
            # Testar funções de carregamento
            from database import obter_configuracoes_sla_dict, obter_horario_comercial_dict
            
            sla_config = obter_configuracoes_sla_dict()
            horario_config = obter_horario_comercial_dict()
            
            print("✅ Configurações SLA carregadas:")
            for chave, valor in sla_config.items():
                print(f"   {chave}: {valor}")
            
            print("✅ Configurações de horário carregadas:")
            for chave, valor in horario_config.items():
                if chave == 'dias_semana':
                    dias_nomes = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
                    dias_ativos = [dias_nomes[i] for i in valor]
                    print(f"   {chave}: {', '.join(dias_ativos)}")
                else:
                    print(f"   {chave}: {valor}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na verificação: {str(e)}")
            return False

if __name__ == "__main__":
    print("🏗️  MIGRAÇÃO DE CONFIGURAÇÕES SLA")
    print("=" * 50)
    
    if migrar_configuracoes_sla():
        if verificar_integridade():
            print("\n✅ Processo de migração completado com sucesso!")
            print("\nAgora as configurações de SLA e horário comercial estão armazenadas no banco de dados.")
            print("Elas podem ser consultadas e alteradas através dos endpoints da API.")
        else:
            print("\n⚠️  Migração realizada, mas houve problemas na verificação.")
    else:
        print("\n❌ Falha na migração.")
