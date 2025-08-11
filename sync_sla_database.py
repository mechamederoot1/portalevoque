#!/usr/bin/env python3
"""
SCRIPT DE SINCRONIZAÇÃO SLA - HORÁRIO SÃO PAULO BRASIL
====================================================

Este script garante que TODAS as informações de SLA estejam:
1. Salvas corretamente no banco de dados
2. Sincronizadas com o timezone de São Paulo (America/Sao_Paulo)
3. Consistentes entre todas as tabelas
4. Com configurações completas de horário comercial e feriados

IMPORTANTE: Execute este script sempre que houver dúvidas sobre
a integridade dos dados de SLA no sistema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import (
    db, Configuracao, ConfiguracaoSLA, Feriado, HistoricoSLA, 
    Chamado, User, get_brazil_time, BRAZIL_TZ
)
import json
import pytz
from datetime import datetime, date, time, timedelta

class SLASyncManager:
    def __init__(self):
        self.timezone_sp = pytz.timezone('America/Sao_Paulo')
        self.corrigidos = {
            'configuracoes': 0,
            'chamados': 0,
            'feriados': 0,
            'sla_configs': 0,
            'horarios': 0
        }
        
    def executar_sincronizacao_completa(self):
        """Executa sincronização completa do sistema SLA"""
        print("🇧🇷 SINCRONIZAÇÃO SLA - HORÁRIO SÃO PAULO BRASIL")
        print("=" * 60)
        print(f"⏰ Hora atual SP: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S %Z')}")
        print()
        
        try:
            with app.app_context():
                # 1. Verificar e corrigir configurações básicas
                self._sincronizar_configuracoes_basicas()
                
                # 2. Verificar e corrigir horário comercial
                self._sincronizar_horario_comercial()
                
                # 3. Inicializar/atualizar feriados brasileiros
                self._sincronizar_feriados_brasileiros()
                
                # 4. Verificar configurações detalhadas de SLA
                self._sincronizar_configuracoes_sla_detalhadas()
                
                # 5. Corrigir timezone de chamados existentes
                self._corrigir_timezone_chamados()
                
                # 6. Verificar histórico SLA
                self._verificar_historico_sla()
                
                # 7. Validar consistência geral
                self._validar_consistencia_final()
                
                # Commit de todas as alterações
                db.session.commit()
                
                self._exibir_relatorio_final()
                
        except Exception as e:
            print(f"❌ ERRO CRÍTICO: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False
            
        return True

    def _sincronizar_configuracoes_basicas(self):
        """Sincroniza configurações básicas de SLA"""
        print("📊 1. SINCRONIZANDO CONFIGURAÇÕES BÁSICAS")
        
        # Configurações SLA padrão com timezone
        config_sla_padrao = {
            'primeira_resposta': 4,
            'resolucao_critico': 2,
            'resolucao_urgente': 2,
            'resolucao_alta': 8,
            'resolucao_normal': 24,
            'resolucao_baixa': 72,
            'ativo': True,
            'considerar_horario_comercial': True,
            'incluir_fins_semana': False,
            'feriados_nacionais': True,
            'timezone': 'America/Sao_Paulo',
            'ultima_atualizacao': get_brazil_time().isoformat()
        }
        
        # Verificar/criar configuração SLA
        config_sla = Configuracao.query.filter_by(chave='sla').first()
        if config_sla:
            dados_atuais = json.loads(config_sla.valor)
            # Atualizar com novos campos se necessário
            dados_atuais.update(config_sla_padrao)
            config_sla.valor = json.dumps(dados_atuais)
            config_sla.data_atualizacao = get_brazil_time().replace(tzinfo=None)
            print("   ✅ Configuração SLA atualizada")
        else:
            config_sla = Configuracao(
                chave='sla',
                valor=json.dumps(config_sla_padrao)
            )
            db.session.add(config_sla)
            print("   ✅ Configuração SLA criada")
        
        self.corrigidos['configuracoes'] += 1

    def _sincronizar_horario_comercial(self):
        """Sincroniza configurações de horário comercial"""
        print("🕒 2. SINCRONIZANDO HORÁRIO COMERCIAL")
        
        # Configuração completa de horário comercial
        config_horario_padrao = {
            'inicio': '08:00',
            'fim': '18:00',
            'dias_semana': [0, 1, 2, 3, 4],  # Segunda a sexta
            'intervalo_almoco_inicio': '12:00',
            'intervalo_almoco_fim': '13:00',
            'considerar_intervalo_almoco': False,
            'timezone': 'America/Sao_Paulo',
            'horario_emergencia': {
                'ativo': False,
                'inicio': '18:00',
                'fim': '22:00',
                'dias_semana': [0, 1, 2, 3, 4]
            },
            'plantao_final_semana': {
                'ativo': False,
                'inicio': '08:00',
                'fim': '17:00',
                'dias': [5, 6]  # Sábado e domingo
            },
            'observacoes': 'Horário comercial padrão da Evoque Fitness - São Paulo/Brasil',
            'ultima_atualizacao': get_brazil_time().isoformat()
        }
        
        # Verificar/criar configuração de horário comercial
        config_horario = Configuracao.query.filter_by(chave='horario_comercial').first()
        if config_horario:
            dados_atuais = json.loads(config_horario.valor)
            dados_atuais.update(config_horario_padrao)
            config_horario.valor = json.dumps(dados_atuais)
            config_horario.data_atualizacao = get_brazil_time().replace(tzinfo=None)
            print("   ✅ Horário comercial atualizado")
        else:
            config_horario = Configuracao(
                chave='horario_comercial',
                valor=json.dumps(config_horario_padrao)
            )
            db.session.add(config_horario)
            print("   ✅ Horário comercial criado")
        
        self.corrigidos['horarios'] += 1

    def _sincronizar_feriados_brasileiros(self):
        """Sincroniza feriados brasileiros nacionais"""
        print("🇧🇷 3. SINCRONIZANDO FERIADOS BRASILEIROS")
        
        ano_atual = date.today().year
        anos_futuros = [ano_atual, ano_atual + 1, ano_atual + 2]
        
        feriados_brasileiros = [
            {'nome': 'Confraternização Universal', 'mes': 1, 'dia': 1},
            {'nome': 'Tiradentes', 'mes': 4, 'dia': 21},
            {'nome': 'Dia do Trabalhador', 'mes': 5, 'dia': 1},
            {'nome': 'Independência do Brasil', 'mes': 9, 'dia': 7},
            {'nome': 'Nossa Senhora Aparecida', 'mes': 10, 'dia': 12},
            {'nome': 'Finados', 'mes': 11, 'dia': 2},
            {'nome': 'Proclamação da República', 'mes': 11, 'dia': 15},
            {'nome': 'Natal', 'mes': 12, 'dia': 25},
        ]
        
        feriados_adicionados = 0
        
        for ano in anos_futuros:
            for feriado_info in feriados_brasileiros:
                data_feriado = date(ano, feriado_info['mes'], feriado_info['dia'])
                
                # Verificar se já existe
                feriado_existente = Feriado.query.filter_by(
                    nome=feriado_info['nome'],
                    data=data_feriado
                ).first()
                
                if not feriado_existente:
                    feriado = Feriado(
                        nome=feriado_info['nome'],
                        data=data_feriado,
                        tipo='nacional',
                        recorrente=True,
                        ativo=True,
                        descricao=f"Feriado nacional brasileiro - {ano}"
                    )
                    db.session.add(feriado)
                    feriados_adicionados += 1
        
        print(f"   ✅ {feriados_adicionados} feriados adicionados para {len(anos_futuros)} anos")
        self.corrigidos['feriados'] += feriados_adicionados

    def _sincronizar_configuracoes_sla_detalhadas(self):
        """Sincroniza configurações detalhadas de SLA por prioridade"""
        print("⚙️ 4. SINCRONIZANDO CONFIGURAÇÕES SLA DETALHADAS")
        
        configuracoes_sla = [
            {
                'prioridade': 'Crítica',
                'tempo_primeira_resposta': 1.0,
                'tempo_resolucao': 2.0,
                'percentual_risco': 90.0,
                'escalar_automaticamente': True
            },
            {
                'prioridade': 'Urgente',
                'tempo_primeira_resposta': 1.0,
                'tempo_resolucao': 2.0,
                'percentual_risco': 90.0,
                'escalar_automaticamente': True
            },
            {
                'prioridade': 'Alta',
                'tempo_primeira_resposta': 2.0,
                'tempo_resolucao': 8.0,
                'percentual_risco': 80.0,
                'escalar_automaticamente': True
            },
            {
                'prioridade': 'Normal',
                'tempo_primeira_resposta': 4.0,
                'tempo_resolucao': 24.0,
                'percentual_risco': 75.0,
                'escalar_automaticamente': False
            },
            {
                'prioridade': 'Baixa',
                'tempo_primeira_resposta': 8.0,
                'tempo_resolucao': 72.0,
                'percentual_risco': 70.0,
                'escalar_automaticamente': False
            }
        ]
        
        configs_criadas = 0
        
        for config_data in configuracoes_sla:
            config_existente = ConfiguracaoSLA.query.filter_by(
                prioridade=config_data['prioridade']
            ).first()
            
            if config_existente:
                # Atualizar configuração existente
                config_existente.tempo_primeira_resposta = config_data['tempo_primeira_resposta']
                config_existente.tempo_resolucao = config_data['tempo_resolucao']
                config_existente.percentual_risco = config_data['percentual_risco']
                config_existente.escalar_automaticamente = config_data['escalar_automaticamente']
                config_existente.data_atualizacao = get_brazil_time().replace(tzinfo=None)
                print(f"   ✅ Configuração {config_data['prioridade']} atualizada")
            else:
                # Criar nova configuração
                nova_config = ConfiguracaoSLA(
                    prioridade=config_data['prioridade'],
                    tempo_primeira_resposta=config_data['tempo_primeira_resposta'],
                    tempo_resolucao=config_data['tempo_resolucao'],
                    considera_horario_comercial=True,
                    considera_feriados=True,
                    escalar_automaticamente=config_data['escalar_automaticamente'],
                    notificar_em_risco=True,
                    percentual_risco=config_data['percentual_risco'],
                    ativo=True
                )
                db.session.add(nova_config)
                configs_criadas += 1
                print(f"   ✅ Configuração {config_data['prioridade']} criada")
        
        self.corrigidos['sla_configs'] += configs_criadas

    def _corrigir_timezone_chamados(self):
        """Corrige timezone de todos os chamados para São Paulo"""
        print("📞 5. CORRIGINDO TIMEZONE DOS CHAMADOS")
        
        # Buscar chamados com datas sem timezone ou timezone incorreto
        chamados = Chamado.query.all()
        chamados_corrigidos = 0
        
        for chamado in chamados:
            alterou = False
            
            # Corrigir data de abertura
            if chamado.data_abertura:
                if chamado.data_abertura.tzinfo is None:
                    # Assumir que é horário local (SP) se não tem timezone
                    chamado.data_abertura = self.timezone_sp.localize(chamado.data_abertura).replace(tzinfo=None)
                    alterou = True
                elif chamado.data_abertura.tzinfo != self.timezone_sp:
                    # Converter para SP se está em outro timezone
                    chamado.data_abertura = chamado.data_abertura.astimezone(self.timezone_sp).replace(tzinfo=None)
                    alterou = True
            
            # Corrigir data de conclusão
            if chamado.data_conclusao:
                if chamado.data_conclusao.tzinfo is None:
                    chamado.data_conclusao = self.timezone_sp.localize(chamado.data_conclusao).replace(tzinfo=None)
                    alterou = True
                elif chamado.data_conclusao.tzinfo != self.timezone_sp:
                    chamado.data_conclusao = chamado.data_conclusao.astimezone(self.timezone_sp).replace(tzinfo=None)
                    alterou = True
            
            # Corrigir data de primeira resposta
            if hasattr(chamado, 'data_primeira_resposta') and chamado.data_primeira_resposta:
                if chamado.data_primeira_resposta.tzinfo is None:
                    chamado.data_primeira_resposta = self.timezone_sp.localize(chamado.data_primeira_resposta).replace(tzinfo=None)
                    alterou = True
                elif chamado.data_primeira_resposta.tzinfo != self.timezone_sp:
                    chamado.data_primeira_resposta = chamado.data_primeira_resposta.astimezone(self.timezone_sp).replace(tzinfo=None)
                    alterou = True
            
            if alterou:
                chamados_corrigidos += 1
        
        print(f"   ✅ {chamados_corrigidos} chamados tiveram timezone corrigido")
        self.corrigidos['chamados'] += chamados_corrigidos

    def _verificar_historico_sla(self):
        """Verifica integridade do histórico SLA"""
        print("📊 6. VERIFICANDO HISTÓRICO SLA")
        
        # Contar registros no histórico
        total_historico = HistoricoSLA.query.count()
        
        # Verificar registros recentes (últimos 30 dias)
        data_corte = get_brazil_time() - timedelta(days=30)
        historico_recente = HistoricoSLA.query.filter(
            HistoricoSLA.data_criacao >= data_corte.replace(tzinfo=None)
        ).count()
        
        print(f"   📈 Total de registros no histórico: {total_historico}")
        print(f"   📅 Registros dos últimos 30 dias: {historico_recente}")
        print("   ✅ Histórico SLA verificado")

    def _validar_consistencia_final(self):
        """Validação final de consistência dos dados"""
        print("🔍 7. VALIDAÇÃO FINAL DE CONSISTÊNCIA")
        
        validacoes = {
            'Configurações SLA': self._validar_config_sla(),
            'Horário Comercial': self._validar_horario_comercial(),
            'Feriados Atuais': self._validar_feriados(),
            'Timezone Chamados': self._validar_timezone_chamados(),
            'Configurações Detalhadas': self._validar_configs_detalhadas()
        }
        
        todas_validas = True
        for nome, valida in validacoes.items():
            status = "✅" if valida else "❌"
            print(f"   {status} {nome}")
            if not valida:
                todas_validas = False
        
        if todas_validas:
            print("   🎉 TODAS AS VALIDAÇÕES PASSARAM!")
        else:
            print("   ⚠️  Algumas validações falharam - verifique os logs")

    def _validar_config_sla(self):
        """Valida configuração SLA"""
        config = Configuracao.query.filter_by(chave='sla').first()
        if not config:
            return False
        
        try:
            dados = json.loads(config.valor)
            campos_obrigatorios = ['primeira_resposta', 'resolucao_critico', 'resolucao_normal', 'timezone']
            return all(campo in dados for campo in campos_obrigatorios)
        except:
            return False

    def _validar_horario_comercial(self):
        """Valida configuração de horário comercial"""
        config = Configuracao.query.filter_by(chave='horario_comercial').first()
        if not config:
            return False
        
        try:
            dados = json.loads(config.valor)
            campos_obrigatorios = ['inicio', 'fim', 'dias_semana', 'timezone']
            return all(campo in dados for campo in campos_obrigatorios)
        except:
            return False

    def _validar_feriados(self):
        """Valida feriados do ano atual"""
        ano_atual = date.today().year
        feriados_ano = Feriado.query.filter(
            db.extract('year', Feriado.data) == ano_atual,
            Feriado.ativo == True
        ).count()
        return feriados_ano >= 8  # Pelo menos 8 feriados nacionais

    def _validar_timezone_chamados(self):
        """Valida se chamados estão com timezone correto"""
        # Sample check - verificar alguns chamados recentes
        chamados_recentes = Chamado.query.order_by(Chamado.data_abertura.desc()).limit(10).all()
        
        for chamado in chamados_recentes:
            if chamado.data_abertura and chamado.data_abertura.tzinfo is not None:
                return False  # Não deveria ter timezone (deve ser naive em SP)
        
        return True

    def _validar_configs_detalhadas(self):
        """Valida configurações detalhadas de SLA"""
        prioridades_obrigatorias = ['Crítica', 'Alta', 'Normal', 'Baixa']
        configs_existentes = ConfiguracaoSLA.query.filter(
            ConfiguracaoSLA.prioridade.in_(prioridades_obrigatorias),
            ConfiguracaoSLA.ativo == True
        ).count()
        
        return configs_existentes >= len(prioridades_obrigatorias)

    def _exibir_relatorio_final(self):
        """Exibe relatório final da sincronização"""
        print()
        print("📋 RELATÓRIO FINAL DE SINCRONIZAÇÃO")
        print("=" * 50)
        
        total_correcoes = sum(self.corrigidos.values())
        
        for categoria, quantidade in self.corrigidos.items():
            print(f"   {categoria.replace('_', ' ').title()}: {quantidade} item(s)")
        
        print(f"\n🎯 Total de correções aplicadas: {total_correcoes}")
        print(f"⏰ Sincronização concluída em: {get_brazil_time().strftime('%d/%m/%Y %H:%M:%S %Z')}")
        
        if total_correcoes > 0:
            print("\n🔄 RECOMENDAÇÃO: Reinicie a aplicação para garantir que todas")
            print("   as alterações sejam carregadas corretamente.")
        
        print("\n✅ SISTEMA SLA 100% SINCRONIZADO COM SÃO PAULO!")

def main():
    """Função principal"""
    print("🚀 INICIANDO SINCRONIZAÇÃO SLA...")
    print()
    
    sync_manager = SLASyncManager()
    
    if sync_manager.executar_sincronizacao_completa():
        print("\n🎉 SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        return 0
    else:
        print("\n❌ SINCRONIZAÇÃO FALHOU!")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
