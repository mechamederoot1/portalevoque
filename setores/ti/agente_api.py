from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db, Chamado, AgenteSuporte, ChamadoAgente, User, get_brazil_time
from sqlalchemy import func
import logging
import traceback

agente_api_bp = Blueprint('agente_api', __name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def api_login_required(f):
    """Decorador que retorna erro JSON se não autenticado"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def json_response(data, status=200):
    """Retorna resposta JSON padronizada"""
    response = jsonify(data)
    response.status_code = status
    response.headers['Content-Type'] = 'application/json'
    return response

def error_response(message, status=400):
    """Retorna erro JSON padronizado"""
    return json_response({'error': message}, status)

@agente_api_bp.route('/api/chamados/<int:chamado_id>/detalhes', methods=['GET'])
@api_login_required
def detalhes_chamado(chamado_id):
    """Retorna detalhes completos de um chamado"""
    try:
        # Buscar chamado com informações do agente
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Buscar agente atribuído
        chamado_agente = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        agente_info = None
        if chamado_agente and chamado_agente.agente:
            agente_info = {
                'id': chamado_agente.agente.id,
                'nome': f"{chamado_agente.agente.usuario.nome} {chamado_agente.agente.usuario.sobrenome}",
                'email': chamado_agente.agente.usuario.email,
                'nivel_experiencia': chamado_agente.agente.nivel_experiencia
            }

        data_abertura_brazil = chamado.get_data_abertura_brazil()
        
        chamado_data = {
            'id': chamado.id,
            'codigo': chamado.codigo,
            'protocolo': chamado.protocolo,
            'solicitante': chamado.solicitante,
            'email': chamado.email,
            'telefone': chamado.telefone,
            'unidade': chamado.unidade,
            'problema': chamado.problema,
            'descricao': chamado.descricao,
            'status': chamado.status,
            'prioridade': chamado.prioridade,
            'data_abertura': data_abertura_brazil.strftime('%d/%m/%Y %H:%M') if data_abertura_brazil else 'N/A',
            'agente': agente_info
        }

        return json_response(chamado_data)

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@agente_api_bp.route('/api/chamados/<int:chamado_id>/atualizar', methods=['PUT'])
@api_login_required
def atualizar_chamado_agente(chamado_id):
    """Atualiza um chamado pelo agente"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Verificar se o chamado existe
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Verificar se o agente tem o chamado atribuído (opcional - pode permitir admin atualizar qualquer)
        if current_user.nivel_acesso != 'Administrador':
            chamado_agente = ChamadoAgente.query.filter_by(
                chamado_id=chamado_id,
                agente_id=agente.id,
                ativo=True
            ).first()
            if not chamado_agente:
                return error_response('Você não tem permissão para atualizar este chamado', 403)

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)

        status_anterior = chamado.status
        novo_status = data.get('status')
        observacoes = data.get('observacoes', '')

        if novo_status and novo_status in ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']:
            chamado.status = novo_status
            
            # Atualizar campos de SLA baseado na mudança de status
            agora_brazil = get_brazil_time()
            
            # Se estava "Aberto" e mudou para outro status, registrar primeira resposta
            if status_anterior == 'Aberto' and novo_status != 'Aberto' and not chamado.data_primeira_resposta:
                chamado.data_primeira_resposta = agora_brazil.replace(tzinfo=None)
            
            # Se mudou para "Concluido" ou "Cancelado", registrar conclusão
            if novo_status in ['Concluido', 'Cancelado'] and not chamado.data_conclusao:
                chamado.data_conclusao = agora_brazil.replace(tzinfo=None)
                
                # Finalizar atribuição
                chamado_agente = ChamadoAgente.query.filter_by(
                    chamado_id=chamado_id,
                    ativo=True
                ).first()
                if chamado_agente:
                    chamado_agente.finalizar_atribuicao()

        db.session.commit()

        # Enviar e-mail de notificação
        try:
            from setores.ti.routes import enviar_email
            assunto = f"Atualização do Chamado {chamado.codigo}"
            corpo = f"""
Olá {chamado.solicitante},

Seu chamado {chamado.codigo} foi atualizado.

Detalhes da atualização:
- Status anterior: {status_anterior}
- Novo status: {novo_status}
- Responsável: {current_user.nome} {current_user.sobrenome}
"""
            if observacoes:
                corpo += f"\n- Observações: {observacoes}"
                
            corpo += f"""

Para acompanhar seu chamado, acesse o sistema ou entre em contato conosco.

Atenciosamente,
Equipe de Suporte TI - Evoque Fitness
"""
            enviar_email(assunto, corpo, [chamado.email])
        except Exception as email_error:
            logger.warning(f"Erro ao enviar e-mail de atualização: {str(email_error)}")

        logger.info(f"Chamado {chamado.codigo} atualizado por agente {current_user.nome} - Status: {status_anterior} -> {novo_status}")

        return json_response({
            'message': 'Chamado atualizado com sucesso',
            'status': chamado.status
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@agente_api_bp.route('/api/chamados/<int:chamado_id>/transferir', methods=['POST'])
@api_login_required
def transferir_chamado(chamado_id):
    """Transfere um chamado para outro agente"""
    try:
        # Verificar se o usuário é um agente
        agente_origem = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente_origem:
            return error_response('Usuário não é um agente de suporte', 403)

        data = request.get_json()
        if not data or 'agente_destino_id' not in data:
            return error_response('ID do agente destino é obrigatório', 400)

        agente_destino_id = data['agente_destino_id']
        observacoes = data.get('observacoes', '')

        # Verificar se o chamado existe
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Verificar se o agente destino existe e está ativo
        agente_destino = AgenteSuporte.query.filter_by(id=agente_destino_id, ativo=True).first()
        if not agente_destino:
            return error_response('Agente destino não encontrado ou inativo', 404)

        # Verificar se o agente destino pode receber mais chamados
        if not agente_destino.pode_receber_chamado():
            return error_response(f'Agente {agente_destino.usuario.nome} já atingiu o limite máximo de chamados simultâneos')

        # Verificar se existe atribuição atual
        atribuicao_atual = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if not atribuicao_atual:
            return error_response('Chamado não possui agente atribuído', 400)

        # Verificar se o agente atual é o mesmo que está fazendo a transferência (ou admin)
        if current_user.nivel_acesso != 'Administrador' and atribuicao_atual.agente_id != agente_origem.id:
            return error_response('Você não tem permissão para transferir este chamado', 403)

        # Finalizar atribuição atual
        atribuicao_atual.ativo = False
        atribuicao_atual.data_conclusao = get_brazil_time().replace(tzinfo=None)
        if observacoes:
            atribuicao_atual.observacoes = f"{atribuicao_atual.observacoes or ''}\n[TRANSFERÊNCIA] {observacoes}"

        # Criar nova atribuição
        nova_atribuicao = ChamadoAgente(
            chamado_id=chamado_id,
            agente_id=agente_destino_id,
            atribuido_por=current_user.id,
            observacoes=f'Transferido de {agente_origem.usuario.nome} {agente_origem.usuario.sobrenome}. {observacoes}'
        )

        db.session.add(nova_atribuicao)
        db.session.commit()

        # Enviar e-mails de notificação
        try:
            from setores.ti.routes import enviar_email
            
            # E-mail para o solicitante
            assunto_cliente = f"Chamado {chamado.codigo} - Transferência de Agente"
            corpo_cliente = f"""
Olá {chamado.solicitante},

Seu chamado {chamado.codigo} foi transferido para um novo agente.

Detalhes da transferência:
- Agente anterior: {agente_origem.usuario.nome} {agente_origem.usuario.sobrenome}
- Novo agente: {agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}
- E-mail do novo agente: {agente_destino.usuario.email}
"""
            if observacoes:
                corpo_cliente += f"\n- Motivo da transferência: {observacoes}"
                
            corpo_cliente += f"""

O novo agente entrará em contato em breve para dar continuidade ao atendimento.

Atenciosamente,
Equipe de Suporte TI - Evoque Fitness
"""
            enviar_email(assunto_cliente, corpo_cliente, [chamado.email])
            
            # E-mail para o agente destino
            assunto_agente = f"Novo Chamado Atribuído - {chamado.codigo}"
            corpo_agente = f"""
Olá {agente_destino.usuario.nome},

Você recebeu um novo chamado por transferência.

Detalhes do chamado:
- Código: {chamado.codigo}
- Protocolo: {chamado.protocolo}
- Solicitante: {chamado.solicitante}
- E-mail: {chamado.email}
- Telefone: {chamado.telefone}
- Problema: {chamado.problema}
- Prioridade: {chamado.prioridade}
- Transferido por: {agente_origem.usuario.nome} {agente_origem.usuario.sobrenome}
"""
            if observacoes:
                corpo_agente += f"\n- Observações da transferência: {observacoes}"
                
            corpo_agente += f"""

Descrição do problema:
{chamado.descricao or 'Não informada'}

Acesse o painel para gerenciar este chamado.

Atenciosamente,
Sistema de Suporte TI
"""
            enviar_email(assunto_agente, corpo_agente, [agente_destino.usuario.email])
            
        except Exception as email_error:
            logger.warning(f"Erro ao enviar e-mails de transferência: {str(email_error)}")

        # Emitir evento Socket.IO para notificação em tempo real
        try:
            from flask import current_app
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('chamado_transferido', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'protocolo': chamado.protocolo,
                    'solicitante': chamado.solicitante,
                    'problema': chamado.problema,
                    'prioridade': chamado.prioridade,
                    'agente_origem_id': agente_origem.id,
                    'agente_origem_nome': f"{agente_origem.usuario.nome} {agente_origem.usuario.sobrenome}",
                    'agente_destino_id': agente_destino.id,
                    'agente_destino_nome': f"{agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}",
                    'agente_destino_email': agente_destino.usuario.email,
                    'transferido_por': f"{current_user.nome} {current_user.sobrenome}",
                    'observacoes': observacoes,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")

        logger.info(f"Chamado {chamado.codigo} transferido de {agente_origem.usuario.nome} para {agente_destino.usuario.nome}")

        return json_response({
            'message': f'Chamado transferido com sucesso para {agente_destino.usuario.nome}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao transferir chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@agente_api_bp.route('/api/agentes/ativos', methods=['GET'])
@api_login_required
def listar_agentes_ativos():
    """Lista agentes ativos para transferência"""
    try:
        agentes = db.session.query(AgenteSuporte, User).join(
            User, AgenteSuporte.usuario_id == User.id
        ).filter(
            AgenteSuporte.ativo == True
        ).all()

        agentes_list = []
        for agente, usuario in agentes:
            chamados_ativos = agente.get_chamados_ativos()
            
            agentes_list.append({
                'id': agente.id,
                'nome': f"{usuario.nome} {usuario.sobrenome}",
                'email': usuario.email,
                'nivel_experiencia': agente.nivel_experiencia,
                'max_chamados': agente.max_chamados_simultaneos,
                'chamados_ativos': chamados_ativos,
                'pode_receber': agente.pode_receber_chamado()
            })

        return json_response(agentes_list)

    except Exception as e:
        logger.error(f"Erro ao listar agentes ativos: {str(e)}")
        return error_response('Erro interno no servidor')

@agente_api_bp.route('/api/agente/estatisticas-detalhadas', methods=['GET'])
@api_login_required
def estatisticas_detalhadas_agente():
    """Retorna estatísticas detalhadas do agente logado"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Estatísticas do mês atual
        hoje = get_brazil_time().date()
        inicio_mes = hoje.replace(day=1)
        
        total_atendidos = ChamadoAgente.query.filter_by(
            agente_id=agente.id
        ).join(Chamado).filter(
            Chamado.status.in_(['Concluido', 'Cancelado']),
            func.date(ChamadoAgente.data_atribuicao) >= inicio_mes
        ).count()

        # Atendimentos hoje
        atendimentos_hoje = ChamadoAgente.query.filter_by(
            agente_id=agente.id
        ).join(Chamado).filter(
            Chamado.status == 'Concluido',
            func.date(Chamado.data_conclusao) == hoje
        ).count()

        # Tempo médio de resolução (placeholder)
        tempo_medio = '2.5h'
        
        # Avaliação média (placeholder)
        avaliacao_media = '4.8'

        estatisticas = {
            'total_atendidos': total_atendidos,
            'tempo_medio': tempo_medio,
            'atendimentos_hoje': atendimentos_hoje,
            'avaliacao_media': avaliacao_media
        }

        return json_response(estatisticas)

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas detalhadas: {str(e)}")
        return error_response('Erro interno no servidor')

@agente_api_bp.route('/api/agente/perfil', methods=['GET'])
@api_login_required
def perfil_agente():
    """Retorna perfil do agente logado"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        perfil = {
            'nome': f"{current_user.nome} {current_user.sobrenome}",
            'email': current_user.email,
            'telefone': getattr(current_user, 'telefone', ''),
            'especialidades': ', '.join(agente.especialidades_list) if agente.especialidades_list else '',
            'nivel_experiencia': agente.nivel_experiencia,
            'max_chamados': agente.max_chamados_simultaneos,
            'notificacoes': True,  # Placeholder
            'auto_atribuicao': False  # Placeholder
        }

        return json_response(perfil)

    except Exception as e:
        logger.error(f"Erro ao buscar perfil do agente: {str(e)}")
        return error_response('Erro interno no servidor')
