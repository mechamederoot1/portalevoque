from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash, Response
from database import Chamado, Unidade, User, db, ProblemaReportado, get_brazil_time, utc_to_brazil
from database import HistoricoTicket, Configuracao
from sqlalchemy.exc import IntegrityError
import logging
import random
import string
from flask_login import LoginManager, login_required, current_user, logout_user
from auth.auth_helpers import setor_required
import os
from setores.ti.routes import enviar_email
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, case, extract
import json
import pytz
import traceback

painel_bp = Blueprint('painel', __name__, template_folder='templates')

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Timezone do Brasil
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')

# Configurações padrão do sistema
CONFIGURACOES_PADRAO = {
    'sla': {
        'primeira_resposta': 4,
        'resolucao_critico': 2,
        'resolucao_alto': 8,
        'resolucao_normal': 24,
        'resolucao_baixo': 72
    },
    'notificacoes': {
        'email_novo_chamado': True,
        'email_status_mudou': True,
        'notificar_sla_risco': True,
        'notificar_novos_usuarios': True,
        'som_habilitado': True,
        'intervalo_verificacao': 15
    },
    'email': {
        'servidor_smtp': 'smtp.gmail.com',
        'porta': 587,
        'usar_tls': True,
        'email_sistema': 'sistema@evoquefitness.com'
    },
    'sistema': {
        'timeout_sessao': 30,
        'maximo_tentativas_login': 5,
        'backup_automatico': True,
        'log_nivel': 'INFO'
    },
    'chamados': {
        'auto_atribuicao': False,
        'escalacao': True,
        'lembretes_sla': False,
        'prazo_padrao_sla': 24,
        'prioridade_padrao': 'Normal'
    }
}

def json_response(data, status=200):
    """Wrapper para garantir resposta JSON válida"""
    try:
        response = jsonify(data)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, status
    except Exception as e:
        logger.error(f"Erro ao criar resposta JSON: {str(e)}")
        error_response = jsonify({'error': 'Erro interno de serialização'})
        error_response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return error_response, 500

def error_response(message, status=500, details=None):
    """Wrapper para respostas de erro padronizadas"""
    error_data = {'error': message}
    if details:
        error_data['details'] = details
    return json_response(error_data, status)

def carregar_configuracoes():
    """Carrega configurações do banco de dados ou retorna padrões"""
    try:
        config_final = CONFIGURACOES_PADRAO.copy()
        
        # Buscar todas as configurações do banco
        configs_db = Configuracao.query.all()
        
        for config in configs_db:
            try:
                valor = json.loads(config.valor)
                # Atualizar apenas seções existentes
                if config.chave in config_final and isinstance(valor, dict):
                    config_final[config.chave].update(valor)
                else:
                    config_final[config.chave] = valor
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar configuração {config.chave}")
                continue
        
        return config_final
        
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        return CONFIGURACOES_PADRAO.copy()

def salvar_configuracoes_db(config):
    """Salva configurações no banco de dados"""
    try:
        # Validar estrutura antes de salvar
        if not isinstance(config, dict):
            logger.error("Configuração inválida para salvar")
            return False
        
        # Carregar configurações existentes
        config_existente = carregar_configuracoes()
        
        # Atualizar apenas as seções fornecidas
        for chave, valor in config.items():
            if chave in config_existente and isinstance(valor, dict) and isinstance(config_existente[chave], dict):
                config_existente[chave].update(valor)
            else:
                config_existente[chave] = valor
        
        # Salvar cada seção de configuração
        for chave, valor in config_existente.items():
            config_db = Configuracao.query.filter_by(chave=chave).first()
            
            if config_db:
                config_db.valor = json.dumps(valor)
                config_db.data_atualizacao = get_brazil_time().replace(tzinfo=None)
            else:
                nova_config = Configuracao(
                    chave=chave,
                    valor=json.dumps(valor)
                )
                db.session.add(nova_config)
        
        db.session.commit()
        logger.info("Configurações salvas com sucesso no banco de dados")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar configurações no banco: {str(e)}")
        return False

def calcular_sla_chamado(chamado, config_sla):
    """Calcula informações de SLA para um chamado específico"""
    agora_brazil = get_brazil_time()
    
    # Se não tem data de abertura, retorna valores padrão
    if not chamado.data_abertura:
        return {
            'horas_decorridas': 0,
            'tempo_primeira_resposta': None,
            'tempo_resolucao': None,
            'sla_limite': config_sla['resolucao_normal'],
            'sla_status': 'Indefinido',
            'violacao_primeira_resposta': False,
            'violacao_resolucao': False
        }
    
    # Obter data de abertura no timezone do Brasil
    data_abertura_brazil = chamado.get_data_abertura_brazil()
    if not data_abertura_brazil:
        # Fallback: assumir que está em UTC e converter
        data_abertura_brazil = pytz.utc.localize(chamado.data_abertura).astimezone(BRAZIL_TZ)
    
    # Calcular tempo decorrido desde abertura
    tempo_decorrido = agora_brazil - data_abertura_brazil
    horas_decorridas = tempo_decorrido.total_seconds() / 3600
    
    # Determinar prioridade (usar Normal como padrão se não definida)
    prioridade = getattr(chamado, 'prioridade', 'Normal')
    
    # Mapear prioridade para limite SLA
    sla_limite_map = {
        'Crítica': config_sla['resolucao_critico'],
        'Urgente': config_sla['resolucao_critico'],  # Urgente usa mesmo SLA que Crítica
        'Alta': config_sla['resolucao_alto'], 
        'Normal': config_sla['resolucao_normal'],
        'Baixa': config_sla['resolucao_baixo']
    }
    sla_limite = sla_limite_map.get(prioridade, config_sla['resolucao_normal'])
    
    # Calcular tempo de primeira resposta
    tempo_primeira_resposta = None
    violacao_primeira_resposta = False
    
    if chamado.data_primeira_resposta:
        data_primeira_resposta_brazil = chamado.get_data_primeira_resposta_brazil()
        if not data_primeira_resposta_brazil:
            data_primeira_resposta_brazil = pytz.utc.localize(chamado.data_primeira_resposta).astimezone(BRAZIL_TZ)
        
        tempo_primeira_resposta = (data_primeira_resposta_brazil - data_abertura_brazil).total_seconds() / 3600
        violacao_primeira_resposta = tempo_primeira_resposta > config_sla['primeira_resposta']
    elif chamado.status != 'Aberto':
        # Se mudou de status mas não tem data_primeira_resposta, usar tempo atual
        tempo_primeira_resposta = horas_decorridas
        violacao_primeira_resposta = tempo_primeira_resposta > config_sla['primeira_resposta']
    else:
        # Ainda está aberto, verificar se já passou do tempo de primeira resposta
        violacao_primeira_resposta = horas_decorridas > config_sla['primeira_resposta']
    
    # Calcular tempo de resolução
    tempo_resolucao = None
    violacao_resolucao = False
    
    if chamado.status in ['Concluido', 'Cancelado']:
        if chamado.data_conclusao:
            data_conclusao_brazil = chamado.get_data_conclusao_brazil()
            if not data_conclusao_brazil:
                data_conclusao_brazil = pytz.utc.localize(chamado.data_conclusao).astimezone(BRAZIL_TZ)
            
            tempo_resolucao = (data_conclusao_brazil - data_abertura_brazil).total_seconds() / 3600
        else:
            tempo_resolucao = horas_decorridas
        violacao_resolucao = tempo_resolucao > sla_limite
    else:
        # Chamado ainda não resolvido, verificar se já passou do SLA
        violacao_resolucao = horas_decorridas > sla_limite
    
    # Determinar status do SLA
    if chamado.status in ['Concluido', 'Cancelado']:
        if violacao_resolucao:
            sla_status = 'Violado'
        else:
            sla_status = 'Cumprido'
    else:
        if violacao_resolucao:
            sla_status = 'Violado'
        elif horas_decorridas > (sla_limite * 0.8):
            sla_status = 'Em Risco'
        else:
            sla_status = 'Dentro do Prazo'
    
    return {
        'horas_decorridas': round(horas_decorridas, 2),
        'tempo_primeira_resposta': round(tempo_primeira_resposta, 2) if tempo_primeira_resposta else None,
        'tempo_resolucao': round(tempo_resolucao, 2) if tempo_resolucao else None,
        'sla_limite': sla_limite,
        'sla_status': sla_status,
        'violacao_primeira_resposta': violacao_primeira_resposta,
        'violacao_resolucao': violacao_resolucao,
        'prioridade': prioridade
    }

@painel_bp.route('/')
@login_required
@setor_required('Administrador')
def index():
    try:
        todos_chamados = Chamado.query.order_by(Chamado.data_abertura.desc()).all()
        logger.debug(f"Total de chamados encontrados: {len(todos_chamados)}")
        return render_template('painel.html', chamados=todos_chamados)
    except Exception as e:
        logger.error(f"Erro ao buscar chamados: {str(e)}")
        abort(500)

# ==================== CONFIGURAÇÕES ====================

@painel_bp.app_errorhandler(401)
def unauthorized_error(error):
    return error_response('Não autorizado', 401)

@painel_bp.app_errorhandler(403)
def forbidden_error(error):
    return error_response('Proibido', 403)

@painel_bp.route('/api/configuracoes', methods=['GET'])
@login_required
@setor_required('Administrador')
def carregar_configuracoes_api():
    """Carrega as configurações do sistema"""
    try:
        config = carregar_configuracoes()
        logger.info(f"Configurações carregadas com sucesso")
        return json_response(config)
        
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        return error_response(f'Erro ao carregar configurações: {str(e)}')

@painel_bp.route('/api/configuracoes', methods=['POST'])
@login_required
@setor_required('Administrador')
def salvar_configuracoes_api():
    """Salva as configurações do sistema"""
    try:
        # Garantir que o conteúdo é JSON
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
        
        logger.info(f"Dados recebidos para salvar configurações: {list(data.keys())}")
        
        # Validar estrutura básica - tornar mais flexível
        if 'sla' in data:
            sla_config = data['sla']
            campos_sla = ['primeira_resposta', 'resolucao_critico', 'resolucao_alto', 'resolucao_normal', 'resolucao_baixo']
            for campo in campos_sla:
                if campo in sla_config:
                    if not isinstance(sla_config[campo], (int, float)) or sla_config[campo] <= 0:
                        return error_response(f'Campo SLA {campo} deve ser um número positivo', 400)
        
        # Validar configurações de notificações
        if 'notificacoes' in data:
            notif_config = data['notificacoes']
            campos_bool = ['email_novo_chamado', 'email_status_mudou', 'notificar_sla_risco', 'notificar_novos_usuarios', 'som_habilitado']
            for campo in campos_bool:
                if campo in notif_config and not isinstance(notif_config[campo], bool):
                    return error_response(f'Campo de notificação {campo} deve ser booleano', 400)
        
        # Salvar no banco de dados
        sucesso = salvar_configuracoes_db(data)
        
        if not sucesso:
            return error_response('Erro ao salvar configurações no banco de dados')
        
        # Emitir evento Socket.IO para notificar outros usuários sobre mudança de configurações
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('configuracoes_atualizadas', {
                    'usuario': current_user.nome,
                    'secoes': list(data.keys()),
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'message': 'Configurações salvas com sucesso',
            'config': data,
            'timestamp': get_brazil_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response(f'Erro interno no servidor: {str(e)}')

@painel_bp.route('/api/configuracoes/notificacoes', methods=['POST'])
@login_required
@setor_required('Administrador')
def salvar_configuracoes_notificacoes():
    """Endpoint específico para salvar configurações de notificações"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
        
        logger.info(f"Salvando configurações de notificações: {data}")
        
        # Validar campos obrigatórios
        campos_esperados = ['email_novo_chamado', 'email_status_mudou', 'notificar_sla_risco', 'notificar_novos_usuarios', 'som_habilitado']
        for campo in campos_esperados:
            if campo not in data:
                return error_response(f'Campo obrigatório ausente: {campo}', 400)
            if not isinstance(data[campo], bool):
                return error_response(f'Campo {campo} deve ser booleano', 400)
        
        # Preparar dados para salvar
        config_notificacoes = {
            'notificacoes': data
        }
        
        # Salvar no banco
        sucesso = salvar_configuracoes_db(config_notificacoes)
        
        if not sucesso:
            return error_response('Erro ao salvar configurações de notificações')
        
        # Emitir evento Socket.IO
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('notificacoes_configuradas', {
                    'usuario': current_user.nome,
                    'configuracoes': data,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'message': 'Configurações de notificações salvas com sucesso',
            'configuracoes': data,
            'timestamp': get_brazil_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações de notificações: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response(f'Erro interno no servidor: {str(e)}')

@painel_bp.route('/api/configuracoes/notificacoes', methods=['GET'])
@login_required
@setor_required('Administrador')
def carregar_configuracoes_notificacoes():
    """Endpoint específico para carregar configurações de notificações"""
    try:
        config = carregar_configuracoes()
        notificacoes = config.get('notificacoes', CONFIGURACOES_PADRAO['notificacoes'])
        
        logger.info(f"Configurações de notificações carregadas: {notificacoes}")
        
        return json_response({
            'notificacoes': notificacoes,
            'timestamp': get_brazil_time().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao carregar configurações de notificações: {str(e)}")
        return error_response(f'Erro ao carregar configurações de notificações: {str(e)}')

# ==================== PROBLEMAS REPORTADOS ====================

@painel_bp.route('/api/problemas', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_problemas():
    """Lista todos os problemas reportados"""
    try:
        problemas = ProblemaReportado.query.filter_by(ativo=True).all()
        problemas_list = []
        for p in problemas:
            problemas_list.append({
                'id': p.id,
                'nome': p.nome,
                'prioridade_padrao': p.prioridade_padrao,
                'requer_item_internet': p.requer_item_internet
            })
        return json_response(problemas_list)
    except Exception as e:
        logger.error(f"Erro ao listar problemas: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/problemas', methods=['POST'])
@login_required
@setor_required('Administrador')
def adicionar_problema():
    """Adiciona um novo problema reportado"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data or 'nome' not in data:
            return error_response('Nome do problema é obrigatório', 400)
        
        nome = data['nome'].strip()
        if not nome:
            return error_response('Nome do problema não pode ser vazio', 400)
        
        # Verificar se já existe
        if ProblemaReportado.query.filter_by(nome=nome).first():
            return error_response('Problema com este nome já existe', 400)
        
        prioridade_padrao = data.get('prioridade_padrao', 'Normal')
        requer_item_internet = data.get('requer_item_internet', False)
        
        # Validar prioridade
        prioridades_validas = ['Baixa', 'Normal', 'Alta', 'Urgente', 'Crítica']
        if prioridade_padrao not in prioridades_validas:
            return error_response('Prioridade inválida', 400)
        
        novo_problema = ProblemaReportado(
            nome=nome,
            prioridade_padrao=prioridade_padrao,
            requer_item_internet=requer_item_internet
        )
        
        db.session.add(novo_problema)
        db.session.commit()
        
        return json_response({
            'message': 'Problema adicionado com sucesso',
            'problema': {
                'id': novo_problema.id,
                'nome': novo_problema.nome,
                'prioridade_padrao': novo_problema.prioridade_padrao,
                'requer_item_internet': novo_problema.requer_item_internet
            }
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar problema: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/problemas/<int:problema_id>/prioridade', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_prioridade_problema(problema_id):
    """Atualiza a prioridade padrão de um problema"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data or 'prioridade' not in data:
            return error_response('Prioridade não fornecida', 400)
        
        nova_prioridade = data['prioridade']
        prioridades_validas = ['Baixa', 'Normal', 'Alta', 'Urgente', 'Crítica']
        
        if nova_prioridade not in prioridades_validas:
            return error_response('Prioridade inválida', 400)
        
        problema = ProblemaReportado.query.get(problema_id)
        if not problema:
            return error_response('Problema não encontrado', 404)
        
        problema.prioridade_padrao = nova_prioridade
        db.session.commit()
        
        return json_response({
            'message': 'Prioridade atualizada com sucesso',
            'problema': {
                'id': problema.id,
                'nome': problema.nome,
                'prioridade_padrao': problema.prioridade_padrao
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar prioridade do problema {problema_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/problemas/<int:problema_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def remover_problema(problema_id):
    """Remove um problema reportado"""
    try:
        problema = ProblemaReportado.query.get(problema_id)
        if not problema:
            return error_response('Problema não encontrado', 404)
        
        # Verificar se há chamados usando este problema
        chamados_usando = Chamado.query.filter_by(problema=problema.nome).count()
        if chamados_usando > 0:
            # Em vez de deletar, marcar como inativo
            problema.ativo = False
            db.session.commit()
            return json_response({
                'message': f'Problema "{problema.nome}" foi desativado pois há chamados associados'
            })
        else:
            # Pode deletar completamente
            nome_problema = problema.nome
            db.session.delete(problema)
            db.session.commit()
            return json_response({
                'message': f'Problema "{nome_problema}" foi removido com sucesso'
            })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover problema {problema_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

# ==================== UNIDADES ====================

@painel_bp.route('/api/unidades', methods=['GET'])
def listar_unidades():
    try:
        unidades = Unidade.query.order_by(Unidade.nome).all()
        unidades_list = [{'id': u.id, 'nome': u.nome} for u in unidades]
        return json_response(unidades_list)
    except Exception as e:
        logger.error(f"Erro ao listar unidades: {str(e)}")
        return error_response('Erro interno ao listar unidades')

@painel_bp.route('/api/unidades', methods=['POST'])
def adicionar_unidade():
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data or 'nome' not in data:
            return error_response('Nome da unidade é obrigatório.', 400)
        
        nome = data['nome'].strip()
        if not nome:
            return error_response('Nome da unidade não pode ser vazio.', 400)
        
        if Unidade.query.filter_by(nome=nome).first():
            return error_response('Unidade com este nome já existe.', 400)
        
        id_unidade = data.get('id')
        if id_unidade:
            try:
                id_unidade = int(id_unidade)
            except ValueError:
                return error_response('ID deve ser um número válido.', 400)
            
            if Unidade.query.get(id_unidade):
                return error_response(f'Unidade com ID {id_unidade} já existe.', 400)
            
            nova_unidade = Unidade(id=id_unidade, nome=nome)
        else:
            ultima_unidade = Unidade.query.order_by(Unidade.id.desc()).first()
            id_unidade = (ultima_unidade.id + 1) if ultima_unidade else 1
            nova_unidade = Unidade(id=id_unidade, nome=nome)
        
        db.session.add(nova_unidade)
        db.session.commit()
        
        atualizar_database_py(nova_unidade.id, nova_unidade.nome)
        
        return json_response({
            'id': nova_unidade.id,
            'nome': nova_unidade.nome,
            'message': 'Unidade adicionada com sucesso!'
        }, 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar unidade: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno ao adicionar unidade')

def atualizar_database_py(id_unidade, nome_unidade):
    """Atualiza o arquivo database.py com a nova unidade"""
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'database.py')
        
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.readlines()
            
            start_index = None
            end_index = None
            for i, line in enumerate(content):
                if 'unidades = [' in line:
                    start_index = i
                if start_index is not None and ']' in line and i > start_index:
                    end_index = i
                    break
            
            if start_index is not None and end_index is not None:
                unidade_str = f'({id_unidade}, "{nome_unidade}"),'
                exists = any(unidade_str in line for line in content[start_index:end_index+1])
                
                if not exists:
                    content.insert(end_index, f'        {unidade_str}\n')
                    
                    file.seek(0)
                    file.writelines(content)
                    file.truncate()
                    
                    logger.info(f"Unidade {id_unidade} - {nome_unidade} adicionada ao database.py")
    except Exception as e:
        logger.error(f"Erro ao atualizar database.py: {str(e)}")

@painel_bp.route('/api/unidades/<int:id>', methods=['DELETE'])
def remover_unidade(id):
    try:
        unidade = Unidade.query.get(id)
        if not unidade:
            return error_response('Unidade não encontrada.', 404)
        db.session.delete(unidade)
        db.session.commit()
        return json_response({'message': 'Unidade removida com sucesso.'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover unidade ID {id}: {str(e)}")
        return error_response('Erro interno ao remover unidade')

# ==================== CHAMADOS ====================

@painel_bp.route('/api/chamados', methods=['GET'])
def listar_chamados():
    try:
        logger.debug("Iniciando consulta de chamados...")
        from database import ChamadoAgente, AgenteSuporte, User

        # Fazer join com agentes se existir
        chamados = db.session.query(Chamado).outerjoin(
            ChamadoAgente, (Chamado.id == ChamadoAgente.chamado_id) & (ChamadoAgente.ativo == True)
        ).outerjoin(
            AgenteSuporte, ChamadoAgente.agente_id == AgenteSuporte.id
        ).outerjoin(
            User, AgenteSuporte.usuario_id == User.id
        ).order_by(Chamado.data_abertura.desc()).all()

        logger.debug(f"Total de chamados encontrados: {len(chamados)}")

        chamados_list = []
        for c in chamados:
            try:
                # Converter data de abertura para timezone do Brasil
                data_abertura_brazil = c.get_data_abertura_brazil()
                data_abertura_str = data_abertura_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_abertura_brazil else None

                # Converter data de visita se existir
                data_visita_str = c.data_visita.strftime('%d/%m/%Y') if c.data_visita else None

                # Buscar agente atribuído
                agente_info = None
                chamado_agente = ChamadoAgente.query.filter_by(
                    chamado_id=c.id,
                    ativo=True
                ).first()

                if chamado_agente and chamado_agente.agente:
                    agente_info = {
                        'id': chamado_agente.agente.id,
                        'nome': f"{chamado_agente.agente.usuario.nome} {chamado_agente.agente.usuario.sobrenome}",
                        'usuario': chamado_agente.agente.usuario.usuario,
                        'nivel_experiencia': chamado_agente.agente.nivel_experiencia
                    }

                chamado_data = {
                    'id': c.id,
                    'codigo': c.codigo if hasattr(c, 'codigo') else None,
                    'protocolo': c.protocolo if hasattr(c, 'protocolo') else None,
                    'solicitante': c.solicitante if hasattr(c, 'solicitante') else None,
                    'email': c.email if hasattr(c, 'email') else None,
                    'cargo': c.cargo if hasattr(c, 'cargo') else None,
                    'telefone': c.telefone if hasattr(c, 'telefone') else None,
                    'unidade': c.unidade if hasattr(c, 'unidade') else None,
                    'problema': c.problema if hasattr(c, 'problema') else None,
                    'descricao': c.descricao if hasattr(c, 'descricao') else None,
                    'internet_item': c.internet_item if hasattr(c, 'internet_item') else None,
                    'data_visita': data_visita_str,
                    'data_abertura': data_abertura_str,
                    'status': c.status if hasattr(c, 'status') else 'Aberto',
                    'prioridade': c.prioridade if hasattr(c, 'prioridade') else 'Normal',
                    'visita_tecnica': c.visita_tecnica if hasattr(c, 'visita_tecnica') else False,
                    'agente': agente_info,
                    'agente_id': agente_info['id'] if agente_info else None
                }
                chamados_list.append(chamado_data)
                logger.debug(f"Chamado {c.id} formatado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao formatar chamado {c.id}: {str(e)}")
                continue

        logger.debug("Retornando lista de chamados")
        return json_response(chamados_list)
    except Exception as e:
        logger.error(f"Erro ao listar chamados: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno ao listar chamados', details=str(e))

@painel_bp.route('/api/chamados/estatisticas', methods=['GET'])
def obter_estatisticas_chamados():
    """Retorna estatísticas dos chamados por status"""
    try:
        # Contar chamados por status
        estatisticas = db.session.query(
            Chamado.status,
            func.count(Chamado.id).label('quantidade')
        ).group_by(Chamado.status).all()
        
        # Converter para dicionário
        stats_dict = {}
        total = 0
        for stat in estatisticas:
            stats_dict[stat.status] = stat.quantidade
            total += stat.quantidade
        
        # Garantir que todos os status estão presentes
        status_padrao = ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']
        for status in status_padrao:
            if status not in stats_dict:
                stats_dict[status] = 0
        
        stats_dict['total'] = total
        
        return json_response(stats_dict)
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:id>/status', methods=['PUT'])
def atualizar_status_chamado(id):
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data or 'status' not in data:
            return error_response('Status não fornecido.', 400)
        novo_status = data['status'].strip()
        if novo_status not in ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']:
            return error_response('Status inválido.', 400)
        chamado = Chamado.query.get(id)
        if not chamado:
            return error_response('Chamado não encontrado.', 404)
        
        status_anterior = chamado.status
        chamado.status = novo_status
        
        # Atualizar campos de SLA baseado na mudança de status
        agora_brazil = get_brazil_time()
        
        # Se estava "Aberto" e mudou para outro status, registrar primeira resposta
        if status_anterior == 'Aberto' and novo_status != 'Aberto' and not chamado.data_primeira_resposta:
            chamado.data_primeira_resposta = agora_brazil.replace(tzinfo=None)
        
        # Se mudou para "Concluido" ou "Cancelado", registrar conclusão
        if novo_status in ['Concluido', 'Cancelado'] and not chamado.data_conclusao:
            chamado.data_conclusao = agora_brazil.replace(tzinfo=None)
        
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('status_atualizado', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'status_anterior': status_anterior,
                    'novo_status': novo_status,
                    'solicitante': chamado.solicitante,
                    'timestamp': agora_brazil.isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'message': 'Status atualizado com sucesso.',
            'id': chamado.id,
            'status': chamado.status,
            'codigo': chamado.codigo
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status do chamado {id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno ao atualizar status.')

@painel_bp.route('/api/chamados/<int:id>', methods=['DELETE'])
def deletar_chamado(id):
    try:
        chamado = Chamado.query.get(id)
        if not chamado:
            return error_response('Chamado não encontrado.', 404)
        
        codigo_chamado = chamado.codigo
        db.session.delete(chamado)
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('chamado_deletado', {
                    'id': id,
                    'codigo': codigo_chamado,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'message': 'Chamado excluído com sucesso.',
            'codigo': codigo_chamado
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir chamado {id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno ao excluir chamado.')

# ==================== USUÁRIOS ====================

@painel_bp.route('/api/usuarios', methods=['POST'])
@login_required
@setor_required('Administrador')
def criar_usuario():
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
            
        required_fields = ['nome', 'sobrenome', 'usuario', 'email', 'senha', 'nivel_acesso', 'setor']
        for field in required_fields:
            if not data.get(field):
                return error_response(f'Campo {field} é obrigatório', 400)
        
        niveis_validos = ['Administrador', 'Gerente', 'Gerente Regional', 'Gestor']
        if data['nivel_acesso'] not in niveis_validos:
            return error_response('Nível de acesso inválido', 400)

        if User.query.filter_by(usuario=data['usuario']).first():
            return error_response('Nome de usuário já existe', 400)
        if User.query.filter_by(email=data['email']).first():
            return error_response('Email já cadastrado', 400)

        novo_usuario = User(
            nome=data['nome'],
            sobrenome=data['sobrenome'],
            usuario=data['usuario'],
            email=data['email'],
            nivel_acesso=data['nivel_acesso'],
            alterar_senha_primeiro_acesso=data.get('alterar_senha_primeiro_acesso', True),
            bloqueado=data.get('bloqueado', False)
        )
        
        novo_usuario.setores = data['setor']
        novo_usuario.set_password(data['senha'])

        db.session.add(novo_usuario)
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('usuario_criado', {
                    'id': novo_usuario.id,
                    'nome': novo_usuario.nome,
                    'sobrenome': novo_usuario.sobrenome,
                    'usuario': novo_usuario.usuario,
                    'nivel_acesso': novo_usuario.nivel_acesso,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'id': novo_usuario.id,
            'nome': novo_usuario.nome,
            'sobrenome': novo_usuario.sobrenome,
            'usuario': novo_usuario.usuario,
            'email': novo_usuario.email,
            'nivel_acesso': novo_usuario.nivel_acesso,
            'setor': novo_usuario.setor,
            'setores': novo_usuario.setores,
            'message': 'Usuário criado com sucesso!'
        }, 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response(f'Erro ao criar usuário: {str(e)}')

@painel_bp.route('/api/usuarios', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_usuarios():
    try:
        usuarios = User.query.order_by(User.data_criacao.desc()).all()
        usuarios_list = []
        
        for u in usuarios:
            # Converter data de criação para timezone do Brasil
            data_criacao_str = None
            if u.data_criacao:
                if u.data_criacao.tzinfo:
                    data_criacao_brazil = u.data_criacao.astimezone(BRAZIL_TZ)
                else:
                    data_criacao_brazil = pytz.utc.localize(u.data_criacao).astimezone(BRAZIL_TZ)
                data_criacao_str = data_criacao_brazil.strftime('%d/%m/%Y %H:%M:%S')
            
            usuarios_list.append({
                'id': u.id,
                'nome': u.nome,
                'sobrenome': u.sobrenome,
                'usuario': u.usuario,
                'email': u.email,
                'nivel_acesso': u.nivel_acesso,
                'setores': u.setores,
                'bloqueado': u.bloqueado,
                'data_criacao': data_criacao_str
            })
        
        logger.debug(f"Usuários encontrados: {len(usuarios_list)}")
        
        return json_response(usuarios_list)
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response(f'Erro ao listar usuários: {str(e)}')

@painel_bp.route('/api/usuarios/<int:user_id>', methods=['GET'])
@login_required
@setor_required('Administrador')
def buscar_usuario(user_id):
    try:
        usuario = User.query.get(user_id)
        if not usuario:
            return error_response('Usuário não encontrado', 404)
            
        # Converter data de criação para timezone do Brasil
        data_criacao_str = None
        if usuario.data_criacao:
            if usuario.data_criacao.tzinfo:
                data_criacao_brazil = usuario.data_criacao.astimezone(BRAZIL_TZ)
            else:
                data_criacao_brazil = pytz.utc.localize(usuario.data_criacao).astimezone(BRAZIL_TZ)
            data_criacao_str = data_criacao_brazil.strftime('%d/%m/%Y %H:%M:%S')
            
        return json_response({
            'id': usuario.id,
            'nome': usuario.nome,
            'sobrenome': usuario.sobrenome,
            'usuario': usuario.usuario,
            'email': usuario.email,
            'nivel_acesso': usuario.nivel_acesso,
            'setor': usuario.setor,
            'bloqueado': usuario.bloqueado,
            'alterar_senha_primeiro_acesso': usuario.alterar_senha_primeiro_acesso,
            'data_criacao': data_criacao_str
        })
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {user_id}: {str(e)}")
        return error_response('Erro ao buscar usuário')

@painel_bp.route('/api/usuarios/<int:user_id>/bloquear', methods=['PUT'])
@login_required
@setor_required('Administrador')
def toggle_bloqueio_usuario(user_id):
    try:
        usuario = User.query.get(user_id)
        if not usuario:
            return error_response('Usuário não encontrado', 404)
        
        status_anterior = usuario.bloqueado
        usuario.bloqueado = not usuario.bloqueado
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('usuario_bloqueio_alterado', {
                    'usuario_id': usuario.id,
                    'nome': usuario.nome,
                    'status_anterior': status_anterior,
                    'novo_status': usuario.bloqueado,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        if current_user.is_authenticated and current_user.id == user_id and usuario.bloqueado:
            logout_user()
            return json_response({
                'message': 'Usuário bloqueado e desconectado com sucesso.',
                'bloqueado': usuario.bloqueado,
                'desconectado': True
            })
        
        status = 'bloqueado' if usuario.bloqueado else 'desbloqueado'
        return json_response({
            'message': f'Usuário {status} com sucesso',
            'bloqueado': usuario.bloqueado,
            'desconectado': False
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao alterar status do usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro ao alterar status do usuário')

@painel_bp.route('/api/usuarios/<int:user_id>/gerar-senha', methods=['POST'])
@login_required
@setor_required('Administrador')
def gerar_nova_senha(user_id):
    try:
        usuario = User.query.get(user_id)
        if not usuario:
            return error_response('Usuário não encontrado', 404)
        
        caracteres = string.ascii_letters + string.digits
        nova_senha = ''.join(random.choice(caracteres) for _ in range(8))
        usuario.set_password(nova_senha)
        usuario.alterar_senha_primeiro_acesso = True
        
        db.session.commit()
        
        return json_response({
            'message': 'Nova senha gerada com sucesso',
            'nova_senha': nova_senha
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao gerar nova senha: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro ao gerar nova senha')

@painel_bp.route('/api/usuarios/<int:user_id>', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_usuario(user_id):
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        usuario = User.query.get(user_id)
        if not usuario:
            return error_response('Usuário não encontrado', 404)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
        
        # Atualizar campos se fornecidos
        if 'nome' in data:
            usuario.nome = data['nome']
        if 'sobrenome' in data:
            usuario.sobrenome = data['sobrenome']
        if 'usuario' in data:
            # Verificar se nome de usuário não está em uso por outro usuário
            existing_user = User.query.filter(User.usuario == data['usuario'], User.id != user_id).first()
            if existing_user:
                return error_response('Nome de usuário já está em uso por outro usuário', 400)
            usuario.usuario = data['usuario']
        if 'email' in data:
            # Verificar se email não está em uso por outro usuário
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return error_response('Email já está em uso por outro usuário', 400)
            usuario.email = data['email']
        if 'nivel_acesso' in data:
            niveis_validos = ['Administrador', 'Gerente', 'Gerente Regional', 'Gestor']
            if data['nivel_acesso'] not in niveis_validos:
                return error_response('Nível de acesso inválido', 400)
            usuario.nivel_acesso = data['nivel_acesso']
        if 'setores' in data:
            usuario.setores = data['setores']
        if 'bloqueado' in data:
            usuario.bloqueado = data['bloqueado']
        
        db.session.commit()
        
        return json_response({
            'message': 'Usuário atualizado com sucesso',
            'id': usuario.id,
            'nome': usuario.nome,
            'sobrenome': usuario.sobrenome,
            'usuario': usuario.usuario,
            'email': usuario.email,
            'nivel_acesso': usuario.nivel_acesso,
            'setores': usuario.setores,
            'bloqueado': usuario.bloqueado
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar usuário {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro ao atualizar usuário')

@painel_bp.route('/api/usuarios/<int:user_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def deletar_usuario(user_id):
    try:
        usuario = User.query.get(user_id)
        if not usuario:
            return error_response('Usuário não encontrado', 404)
            
        nome_usuario = usuario.usuario
        db.session.delete(usuario)
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('usuario_deletado', {
                    'id': user_id,
                    'usuario': nome_usuario,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        logger.info(f"Usuário {nome_usuario} foi deletado")
        return json_response({'message': 'Usuário deletado com sucesso'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar usuário {user_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro ao deletar usuário')

@painel_bp.route('/criar-usuario')
@login_required
@setor_required('Administrador')
def criar_usuario_view():
    return render_template('painel.html', section='criar-usuario')

# =========== GERADOR DE SENHA ===========

@painel_bp.route('/api/gerar-senha', methods=['GET'])
@login_required
@setor_required('Administrador')
def gerar_senha():
    try:
        import string
        import random
        caracteres = string.ascii_letters + string.digits
        senha = ''.join(random.choice(caracteres) for _ in range(6))
        forca = calcular_forca_senha(senha)
        return json_response({'senha': senha, 'forca': forca})
    except Exception as e:
        logger.error(f"Erro ao gerar senha: {str(e)}")
        return error_response('Erro ao gerar senha')

def calcular_forca_senha(senha):
    pontos = 0
    if len(senha) >= 6:
        pontos += 1
    if any(c.isupper() for c in senha):
        pontos += 1
    if any(c.islower() for c in senha):
        pontos += 1
    if any(c.isdigit() for c in senha):
        pontos += 1
    if pontos <= 2:
        return 'fraca'
    elif pontos == 3:
        return 'média'
    else:
        return 'forte'

# ==================== NOTIFICAÇÕES ====================
        
@painel_bp.route('/api/chamados/<int:id>/notificar', methods=['POST'])
@login_required
@setor_required('Administrador')
def notificar_status_chamado(id):
    try:
        chamado = Chamado.query.get(id)
        if not chamado:
            return error_response('Chamado não encontrado.', 404)
        
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        novo_status = data.get('status')
        if not novo_status:
            return error_response('Status não fornecido.', 400)
        
        assunto = f"ATUALIZAÇÃO DO CHAMADO {chamado.codigo}"
        corpo = f"""
Prezado(a), {chamado.solicitante}

O status do seu chamado foi alterado para: {novo_status}

Atenciosamente,
Suporte Evoque.
"""
        
        enviado = enviar_email(assunto, corpo, [chamado.email])
        
        if enviado:
            return json_response({'message': 'E-mail enviado com sucesso'})
        else:
            return error_response('Falha ao enviar e-mail')
            
    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno ao enviar notificação')

@painel_bp.route('/api/chamados/<int:id>/ticket', methods=['POST'])
@login_required
@setor_required('Administrador')
def enviar_ticket(id):
    try:
        chamado = Chamado.query.get_or_404(id)
        
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
        
        assunto = data.get('assunto', f"Atualização do Chamado {chamado.codigo}")
        mensagem = data.get('mensagem')
        enviar_copia = data.get('enviar_copia', False)
        prioridade = data.get('prioridade', False)
        
        if not mensagem:
            return error_response('A mensagem é obrigatória', 400)

        destinatarios = [chamado.email]
        if enviar_copia and current_user.email:
            destinatarios.append(current_user.email)

        if prioridade:
            assunto = f"[PRIORITÁRIO] {assunto}"

        # Usar data de abertura no timezone do Brasil
        data_abertura_brazil = chamado.get_data_abertura_brazil()
        data_abertura_str = data_abertura_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_abertura_brazil else 'N/A'

        mensagem_formatada = f"""
Chamado: {chamado.codigo}
Status: {chamado.status}
Data de Abertura: {data_abertura_str}
Problema: {chamado.problema}
Unidade: {chamado.unidade}

{mensagem}

Atenciosamente,
Equipe de Suporte TI - Evoque Fitness
"""

        sucesso = enviar_email(
            assunto=assunto,
            corpo=mensagem_formatada,
            destinatarios=destinatarios
        )

        if sucesso:
            historico = HistoricoTicket(
                chamado_id=chamado.id,
                usuario_id=current_user.id,
                assunto=assunto,
                mensagem=mensagem,
                destinatarios=", ".join(destinatarios)
            )
            db.session.add(historico)
            db.session.commit()
            
            # Emitir evento Socket.IO apenas se a conexão estiver disponível
            try:
                if hasattr(current_app, 'socketio'):
                    current_app.socketio.emit('ticket_enviado', {
                        'chamado_id': chamado.id,
                        'codigo': chamado.codigo,
                        'assunto': assunto,
                        'destinatarios': destinatarios,
                        'timestamp': get_brazil_time().isoformat()
                    })
            except Exception as socket_error:
                logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
            
            return json_response({
                'message': 'Ticket enviado com sucesso',
                'chamado_id': chamado.id,
                'destinatarios': destinatarios
            })
        else:
            raise Exception('Falha ao enviar e-mail')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao enviar ticket: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response(str(e))

@painel_bp.route('/api/notificacoes/recentes')
@login_required
@setor_required('Administrador')
def notificacoes_recentes():
    """Retorna chamados criados nos últimos 5 minutos"""
    try:
        cinco_minutos_atras = get_brazil_time() - timedelta(minutes=5)
        
        chamados_recentes = Chamado.query.filter(
            Chamado.data_abertura >= cinco_minutos_atras.replace(tzinfo=None)
        ).order_by(Chamado.data_abertura.desc()).limit(10).all()
        
        notificacoes = []
        for c in chamados_recentes:
            data_abertura_brazil = c.get_data_abertura_brazil()
            notificacoes.append({
                'id': c.id,
                'codigo': c.codigo,
                'solicitante': c.solicitante,
                'problema': c.problema,
                'data_abertura': data_abertura_brazil.strftime('%Y-%m-%d %H:%M:%S') if data_abertura_brazil else None,
                'status': c.status
            })
        
        return json_response(notificacoes)
    except Exception as e:
        logger.error(f"Erro ao buscar notificações recentes: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== SLA ENDPOINTS ====================

@painel_bp.route('/api/sla/metricas', methods=['GET'])
@login_required
@setor_required('Administrador')
def obter_metricas_sla():
    """Retorna métricas gerais de SLA"""
    try:
        config = carregar_configuracoes()
        sla_config = config.get('sla', CONFIGURACOES_PADRAO['sla'])
        
        # Garantir que temos todos os campos necessários
        campos_necessarios = ['primeira_resposta', 'resolucao_critico', 'resolucao_alto', 
                             'resolucao_normal', 'resolucao_baixo']
        for campo in campos_necessarios:
            if campo not in sla_config:
                sla_config[campo] = CONFIGURACOES_PADRAO['sla'][campo]
        
        chamados = Chamado.query.all()
        
        # Inicializar contadores
        metricas = {
            'total_chamados': len(chamados),
            'chamados_abertos': 0,
            'chamados_aguardando': 0,
            'chamados_concluidos': 0,
            'chamados_cancelados': 0,
            'tempo_medio_resposta': 0,
            'tempo_medio_resolucao': 0,
            'sla_cumprimento': 100,
            'sla_violacoes': 0,
            'chamados_risco': 0,
            'violacoes_primeira_resposta': 0,
            'violacoes_resolucao': 0
        }
        
        tempos_primeira_resposta = []
        tempos_resolucao = []
        
        for chamado in chamados:
            # Contar por status
            if chamado.status == 'Aberto':
                metricas['chamados_abertos'] += 1
            elif chamado.status == 'Aguardando':
                metricas['chamados_aguardando'] += 1
            elif chamado.status == 'Concluido':
                metricas['chamados_concluidos'] += 1
            elif chamado.status == 'Cancelado':
                metricas['chamados_cancelados'] += 1
            
            sla_info = calcular_sla_chamado(chamado, sla_config)
            
            if sla_info['tempo_primeira_resposta'] is not None:
                tempos_primeira_resposta.append(sla_info['tempo_primeira_resposta'])
                if sla_info['violacao_primeira_resposta']:
                    metricas['violacoes_primeira_resposta'] += 1
            
            if sla_info['tempo_resolucao'] is not None:
                tempos_resolucao.append(sla_info['tempo_resolucao'])
                if sla_info['violacao_resolucao']:
                    metricas['violacoes_resolucao'] += 1
            
            if chamado.status in ['Aberto', 'Aguardando'] and sla_info['sla_status'] == 'Em Risco':
                metricas['chamados_risco'] += 1
        
        # Calcular médias
        if tempos_primeira_resposta:
            metricas['tempo_medio_resposta'] = sum(tempos_primeira_resposta) / len(tempos_primeira_resposta)
        
        if tempos_resolucao:
            metricas['tempo_medio_resolucao'] = sum(tempos_resolucao) / len(tempos_resolucao)
        
        # Calcular percentual de SLA cumprido
        total_finalizados = metricas['chamados_concluidos'] + metricas['chamados_cancelados']
        if total_finalizados > 0:
            metricas['sla_cumprimento'] = ((total_finalizados - metricas['violacoes_resolucao']) / total_finalizados) * 100
        
        metricas['sla_violacoes'] = metricas['violacoes_primeira_resposta'] + metricas['violacoes_resolucao']
        
        return json_response({
            'metricas_gerais': metricas,
            'sla_config': sla_config
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas SLA: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/sla/grafico-semanal', methods=['GET'])
@login_required
@setor_required('Administrador')
def obter_grafico_semanal():
    """Retorna dados para gráfico semanal de chamados"""
    try:
        hoje = get_brazil_time().date()
        inicio_periodo = hoje - timedelta(days=27)  # 4 semanas = 28 dias
        
        # Buscar chamados por dia
        chamados_por_dia = db.session.query(
            func.date(Chamado.data_abertura).label('data'),
            func.count(Chamado.id).label('quantidade')
        ).filter(
            Chamado.data_abertura >= inicio_periodo
        ).group_by(
            func.date(Chamado.data_abertura)
        ).all()
        
        # Criar lista com todos os dias do período
        dados_grafico = []
        for i in range(28):
            data_atual = inicio_periodo + timedelta(days=i)
            quantidade = 0
            
            # Procurar quantidade para esta data
            for registro in chamados_por_dia:
                if registro.data == data_atual:
                    quantidade = registro.quantidade
                    break
            
            dados_grafico.append({
                'data': data_atual.strftime('%Y-%m-%d'),
                'quantidade': quantidade
            })
        
        # Distribuição por status (últimas 4 semanas)
        status_counts = db.session.query(
            Chamado.status,
            func.count(Chamado.id).label('quantidade')
        ).filter(
            Chamado.data_abertura >= inicio_periodo
        ).group_by(Chamado.status).all()
        
        dados_status = [{'status': s.status, 'quantidade': s.quantidade} for s in status_counts]
        
        return json_response({
            'grafico_semanal': dados_grafico,
            'distribuicao_status': dados_status
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter dados do gráfico semanal: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/sla/chamados-detalhados', methods=['GET'])
@login_required
@setor_required('Administrador')
def obter_chamados_detalhados_sla():
    """Retorna lista detalhada de chamados com informações de SLA"""
    try:
        config = carregar_configuracoes()
        sla_config = config['sla']
        
        chamados = Chamado.query.order_by(Chamado.data_abertura.desc()).all()
        
        chamados_detalhados = []
        for chamado in chamados:
            if not chamado.data_abertura:
                continue
            
            sla_info = calcular_sla_chamado(chamado, sla_config)
            
            # Converter data de abertura para timezone do Brasil
            data_abertura_brazil = chamado.get_data_abertura_brazil()
            data_abertura_str = data_abertura_brazil.strftime('%d/%m/%Y %H:%M') if data_abertura_brazil else 'N/A'
            
            chamados_detalhados.append({
                'id': chamado.id,
                'codigo': chamado.codigo,
                'solicitante': chamado.solicitante,
                'problema': chamado.problema,
                'status': chamado.status,
                'data_abertura': data_abertura_str,
                'horas_decorridas': sla_info['horas_decorridas'],
                'sla_limite': sla_info['sla_limite'],
                'sla_status': sla_info['sla_status'],
                'prioridade': sla_info['prioridade'],
                'tempo_primeira_resposta': sla_info['tempo_primeira_resposta'],
                'tempo_resolucao': sla_info['tempo_resolucao'],
                'violacao_primeira_resposta': sla_info['violacao_primeira_resposta'],
                'violacao_resolucao': sla_info['violacao_resolucao']
            })
        
        return json_response(chamados_detalhados)
        
    except Exception as e:
        logger.error(f"Erro ao obter chamados detalhados: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/prioridade-padrao', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_prioridade_padrao():
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data or 'prioridade' not in data:
            return error_response('Prioridade não fornecida', 400)
        
        nova_prioridade = data['prioridade']
        prioridades_validas = ['Baixa', 'Normal', 'Alta', 'Urgente', 'Crítica']
        
        if nova_prioridade not in prioridades_validas:
            return error_response('Prioridade inválida', 400)
        
        # Atualizar configurações
        config = carregar_configuracoes()
        config['chamados']['prioridade_padrao'] = nova_prioridade
        salvar_configuracoes_db({'chamados': config['chamados']})
        
        return json_response({
            'message': 'Prioridade padrão atualizada com sucesso',
            'prioridade': nova_prioridade
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar prioridade padrão: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== NOVA ROTA PARA CORRIGIR O ERRO 404 ====================

@painel_bp.route('/api/setores', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_setores():
    """Lista todos os setores disponíveis"""
    try:
        setores = [
            {'id': 'TI', 'nome': 'Setor de TI'},
            {'id': 'Compras', 'nome': 'Setor de compras'},
            {'id': 'Manutencao', 'nome': 'Setor de manutenção'},
            {'id': 'Financeiro', 'nome': 'Setor financeiro'},
            {'id': 'Marketing', 'nome': 'Setor de produtos'},
            {'id': 'Comercial', 'nome': 'Setor comercial'},
            {'id': 'Outros', 'nome': 'Outros serviços'},
            {'id': 'Administracao', 'nome': 'Administração geral'}
        ]
        return json_response(setores)
    except Exception as e:
        logger.error(f"Erro ao listar setores: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/niveis-acesso', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_niveis_acesso():
    """Lista todos os níveis de acesso disponíveis"""
    try:
        niveis = [
            {'id': 'Administrador', 'nome': 'Administrador'},
            {'id': 'Gerente', 'nome': 'Gerente'},
            {'id': 'Gerente Regional', 'nome': 'Gerente Regional'},
            {'id': 'Gestor', 'nome': 'Gestor'}
        ]
        return json_response(niveis)
    except Exception as e:
        logger.error(f"Erro ao listar níveis de acesso: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== ROTA CORRIGIDA PARA O ERRO 404 ====================

@painel_bp.route('/api/chamados/setorUsuario/status', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_status_setor_usuario():
    """Atualiza status de chamado por setor/usuário - ROTA CORRIGIDA"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)
            
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)
        
        # Validar dados obrigatórios
        required_fields = ['chamado_id', 'status']
        for field in required_fields:
            if field not in data:
                return error_response(f'Campo {field} é obrigatório', 400)
        
        chamado_id = data['chamado_id']
        novo_status = data['status']
        
        # Validar status
        status_validos = ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']
        if novo_status not in status_validos:
            return error_response('Status inválido', 400)
        
        # Buscar chamado
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)
        
        # Verificar se o usuário tem permissão para alterar este chamado
        # (adicione aqui sua lógica de verificação de permissão se necessário)
        
        status_anterior = chamado.status
        chamado.status = novo_status
        
        # Atualizar campos de SLA baseado na mudança de status
        agora_brazil = get_brazil_time()
        
        # Se estava "Aberto" e mudou para outro status, registrar primeira resposta
        if status_anterior == 'Aberto' and novo_status != 'Aberto' and not chamado.data_primeira_resposta:
            chamado.data_primeira_resposta = agora_brazil.replace(tzinfo=None)
        
        # Se mudou para "Concluido" ou "Cancelado", registrar conclusão
        if novo_status in ['Concluido', 'Cancelado'] and not chamado.data_conclusao:
            chamado.data_conclusao = agora_brazil.replace(tzinfo=None)
        
        db.session.commit()
        
        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('status_atualizado_setor', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'status_anterior': status_anterior,
                    'novo_status': novo_status,
                    'solicitante': chamado.solicitante,
                    'usuario_alteracao': current_user.nome,
                    'setor_usuario': current_user.setores,
                    'timestamp': agora_brazil.isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")
        
        return json_response({
            'message': 'Status atualizado com sucesso por setor/usuário',
            'chamado_id': chamado.id,
            'codigo': chamado.codigo,
            'status_anterior': status_anterior,
            'novo_status': novo_status,
            'usuario': current_user.nome,
            'setor': current_user.setores
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status por setor/usuário: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')
