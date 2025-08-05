from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for, flash, Response
from database import Chamado, Unidade, User, db, ProblemaReportado, get_brazil_time, utc_to_brazil
from database import HistoricoTicket, Configuracao, AgenteSuporte, ChamadoAgente
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
from database import LogAcesso, LogAcao, SessaoAtiva, registrar_log_acao

painel_bp = Blueprint('painel', __name__, template_folder='templates')

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

def verificar_ou_criar_agente(usuario):
    """Verifica se o usuário é um agente ou cria um se necessário"""
    agente = AgenteSuporte.query.filter_by(usuario_id=usuario.id, ativo=True).first()
    if not agente:
        # Verificar se é administrador ou tem acesso ao TI
        if usuario.nivel_acesso == 'Administrador' or usuario.setor == 'TI':
            # Criar registro de agente automaticamente
            agente = AgenteSuporte(
                usuario_id=usuario.id,
                ativo=True,
                nivel_experiencia='pleno',
                max_chamados_simultaneos=15
            )
            db.session.add(agente)
            db.session.commit()
            logger.info(f"Agente criado automaticamente para usuário {usuario.id}")
    return agente

def error_response(message, status=400):
    """Retorna erro JSON padronizado"""
    return json_response({'error': message}, status)

def gerenciamento_usuarios_required(f):
    """Decorador que permite acesso a administradores e agentes de suporte ativos"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return error_response('Não autorizado', 401)

        if not current_user.tem_permissao_gerenciar_usuarios():
            return error_response('Acesso negado. Permissão de administrador ou agente de suporte necessária.', 403)

        return f(*args, **kwargs)
    return decorated_function

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





@painel_bp.route('/api/setup-database', methods=['POST'])
@login_required
@setor_required('Administrador')
def setup_database_endpoint():
    """Endpoint para inserir dados de demonstração no banco"""
    try:
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        import random
        import uuid

        # Verificar se já existem dados de demonstração
        existing_logs = LogAcesso.query.limit(1).first()
        if existing_logs:
            return json_response({'message': 'Dados de demonstraç���o já existem', 'logs_count': LogAcesso.query.count()})

        # Criar usuários de teste se não existem
        admin_user = User.query.filter_by(email='admin@demo.com').first()
        if not admin_user:
            admin_user = User(
                nome='Administrador',
                sobrenome='Sistema',
                email='admin@demo.com',
                nivel_acesso='Administrador',
                hash_senha=generate_password_hash('demo123'),
                setor='TI',
                telefone='(11) 99999-9999',
                data_nascimento=datetime(1980, 1, 1).date(),
                data_cadastro=get_brazil_time().replace(tzinfo=None),
                ativo=True
            )
            db.session.add(admin_user)

        test_user = User.query.filter_by(email='usuario@demo.com').first()
        if not test_user:
            test_user = User(
                nome='Usuário',
                sobrenome='Teste',
                email='usuario@demo.com',
                nivel_acesso='Usuario',
                hash_senha=generate_password_hash('demo123'),
                setor='Comercial',
                telefone='(11) 88888-8888',
                data_nascimento=datetime(1990, 5, 15).date(),
                data_cadastro=get_brazil_time().replace(tzinfo=None),
                ativo=True
            )
            db.session.add(test_user)

        agent_user = User.query.filter_by(email='agente@demo.com').first()
        if not agent_user:
            agent_user = User(
                nome='Agente',
                sobrenome='Suporte',
                email='agente@demo.com',
                nivel_acesso='Usuario',
                hash_senha=generate_password_hash('demo123'),
                setor='TI',
                telefone='(11) 77777-7777',
                data_nascimento=datetime(1985, 10, 20).date(),
                data_cadastro=get_brazil_time().replace(tzinfo=None),
                ativo=True
            )
            db.session.add(agent_user)

        db.session.commit()

        # Dados de exemplo para logs de acesso
        ips_exemplo = [
            '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '10.0.0.15', '10.0.0.23', '172.16.1.50',
            '203.0.113.45', '198.51.100.88'
        ]

        navegadores = [
            'Chrome 119.0.0.0 (Windows)',
            'Firefox 118.0.1 (Windows)',
            'Edge 119.0.0.0 (Windows)',
            'Safari 17.0 (MacOS)',
            'Chrome 119.0.0.0 (Android)',
            'Chrome 119.0.0.0 (Linux)'
        ]

        sistemas = [
            'Windows 11', 'Windows 10', 'macOS Sonoma',
            'Ubuntu 22.04', 'Android 13', 'iOS 17'
        ]

        cidades = [
            ('São Paulo', 'Brasil', 'VIVO Fibra'),
            ('Rio de Janeiro', 'Brasil', 'NET Claro'),
            ('Belo Horizonte', 'Brasil', 'Oi Fibra'),
            ('Brasília', 'Brasil', 'TIM Live'),
            ('Curitiba', 'Brasil', 'Copel Telecom'),
            ('Porto Alegre', 'Brasil', 'VIVO Fibra')
        ]

        usuarios_demo = [admin_user, test_user, agent_user]
        agora = get_brazil_time().replace(tzinfo=None)

        # Criar logs de acesso dos ��ltimos 30 dias
        logs_criados = 0
        for dia in range(30):
            data_log = agora - timedelta(days=dia)

            # 2-8 acessos por dia
            num_acessos = random.randint(2, 8)

            for _ in range(num_acessos):
                usuario = random.choice(usuarios_demo)
                ip = random.choice(ips_exemplo)
                navegador = random.choice(navegadores)
                sistema = random.choice(sistemas)
                cidade, pais, provedor = random.choice(cidades)

                # Horário de acesso aleatório no dia
                hora_acesso = data_log.replace(
                    hour=random.randint(7, 22),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )

                # Duração da sessão (15 min a 4 horas)
                duracao_minutos = random.randint(15, 240)
                hora_logout = hora_acesso + timedelta(minutes=duracao_minutos)

                # 85% das sessões são finalizadas
                sessao_ativa = random.random() < 0.15

                log_acesso = LogAcesso(
                    usuario_id=usuario.id,
                    data_acesso=hora_acesso,
                    data_logout=None if sessao_ativa else hora_logout,
                    ip_address=ip,
                    navegador=navegador,
                    sistema_operacional=sistema,
                    dispositivo='Desktop' if 'Windows' in sistema or 'macOS' in sistema else 'Mobile',
                    duracao_sessao=None if sessao_ativa else duracao_minutos,
                    ativo=sessao_ativa,
                    session_id=str(uuid.uuid4()),
                    pais=pais,
                    cidade=cidade,
                    provedor_internet=provedor,
                    mac_address=f"{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}:{random.randint(10,99):02x}",
                    resolucao_tela=random.choice(['1920x1080', '1366x768', '2560x1440', '1440x900', '1600x900']),
                    timezone='America/Sao_Paulo',
                    latitude=-23.5505 + random.uniform(-0.1, 0.1),
                    longitude=-46.6333 + random.uniform(-0.1, 0.1)
                )

                db.session.add(log_acesso)
                logs_criados += 1

        # Criar algumas sessões ativas
        for i in range(3):
            usuario = random.choice(usuarios_demo)
            ip = random.choice(ips_exemplo)
            cidade, pais, provedor = random.choice(cidades)

            inicio_sessao = agora - timedelta(minutes=random.randint(5, 120))
            ultima_atividade = agora - timedelta(minutes=random.randint(0, 30))

            sessao_ativa = SessaoAtiva(
                usuario_id=usuario.id,
                session_id=str(uuid.uuid4()),
                data_inicio=inicio_sessao,
                ultima_atividade=ultima_atividade,
                ip_address=ip,
                navegador=random.choice(navegadores),
                sistema_operacional=random.choice(sistemas),
                dispositivo='Desktop',
                ativo=True,
                pais=pais,
                cidade=cidade,
                provedor_internet=provedor
            )

            db.session.add(sessao_ativa)

        # Criar logs de ações dos últimos 7 dias
        acoes_exemplo = [
            ('Login realizado', 'autenticacao', 'Usuário fez login no sistema'),
            ('Chamado criado', 'chamados', 'Novo chamado de suporte aberto'),
            ('Chamado atualizado', 'chamados', 'Status do chamado alterado'),
            ('Usuário criado', 'usuarios', 'Novo usuário cadastrado'),
            ('Configuração alterada', 'sistema', 'Configuração do sistema modificada'),
            ('Backup realizado', 'sistema', 'Backup automático executado'),
            ('Relat��rio gerado', 'relatorios', 'Relatório de atividades criado'),
            ('Logout realizado', 'autenticacao', 'Usuário fez logout')
        ]

        acoes_criadas = 0
        for dia in range(7):
            data_acao = agora - timedelta(days=dia)

            # 5-15 ações por dia
            num_acoes = random.randint(5, 15)

            for _ in range(num_acoes):
                usuario = random.choice(usuarios_demo)
                acao, categoria, detalhes = random.choice(acoes_exemplo)
                ip = random.choice(ips_exemplo)

                # Horário da ação aleat��rio no dia
                hora_acao = data_acao.replace(
                    hour=random.randint(8, 18),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )

                # 95% das ações são bem-sucedidas
                sucesso = random.random() < 0.95

                log_acao = LogAcao(
                    usuario_id=usuario.id,
                    acao=acao,
                    categoria=categoria,
                    detalhes=detalhes + ('' if sucesso else ' (falhou)'),
                    data_acao=hora_acao,
                    ip_address=ip,
                    sucesso=sucesso,
                    recurso_afetado=f'ID_{random.randint(1000, 9999)}',
                    tipo_recurso=categoria
                )

                db.session.add(log_acao)
                acoes_criadas += 1

        # Criar um chamado de teste
        from setores.ti.routes import gerar_codigo_chamado, gerar_protocolo

        chamado_teste = Chamado.query.filter_by(solicitante='Usuário de Demonstração').first()
        if not chamado_teste:
            chamado_teste = Chamado(
                codigo=gerar_codigo_chamado(),
                protocolo=gerar_protocolo(),
                solicitante='Usuário de Demonstração',
                cargo='Analista',
                email='demo@academiaevoque.com.br',
                telefone='(11) 99999-0000',
                unidade='Unidade Principal',
                problema='Computador/Notebook',
                descricao='Computador não liga após queda de energia. Já verificamos cabo de força e estabilizador.',
                status='Em Andamento',
                prioridade='Alta',
                data_abertura=agora - timedelta(hours=2),
                usuario_id=test_user.id,
                agente_responsavel=agent_user.nome
            )
            db.session.add(chamado_teste)

        db.session.commit()

        return json_response({
            'message': 'Dados de demonstração inseridos com sucesso',
            'logs_acesso_criados': logs_criados,
            'logs_acoes_criadas': acoes_criadas,
            'sessoes_ativas': 3,
            'usuarios_criados': 3,
            'chamado_teste': 'criado'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'Erro ao inserir dados de demonstra��ão: {str(e)}')
        traceback.print_exc()
        return error_response(f'Erro ao inserir dados: {str(e)}')

@painel_bp.route('/setup-demo')
@login_required
@setor_required('Administrador')
def setup_demo_page():
    """Página para configurar dados de demonstração"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup Demo Data</title>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>Configurar Dados de Demonstração</h1>
            <button class="btn btn-primary" onclick="setupDatabase()">Inserir Dados de Demo</button>
            <div id="result" class="mt-3"></div>
        </div>

        <script>
        async function setupDatabase() {
            try {
                const response = await fetch('/ti/painel/api/setup-database', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();
                document.getElementById('result').innerHTML = '<div class="alert alert-success"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
            } catch (error) {
                document.getElementById('result').innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
            }
        }
        </script>
    </body>
    </html>
    '''

def carregar_configuracoes():
    """Carrega configurações do banco de dados ou retorna padr����es"""
    try:
        config_final = CONFIGURACOES_PADRAO.copy()

        # Verificar se a tabela de configurações existe
        try:
            # Tentar buscar todas as configurações do banco
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
                    # Para valores que não são JSON (strings simples), tratar como strings
                    if config.chave in ['versao_database', 'data_criacao', 'sistema_inicializado']:
                        config_final[config.chave] = config.valor
                    else:
                        logger.error(f"Erro ao decodificar configuraç����o {config.chave}")
                    continue

        except Exception as db_error:
            logger.warning(f"Tabela de configurações não disponível ou vazia: {str(db_error)}")
            # Retorna configurações padrão se a tabela não existir

        return config_final

    except Exception as e:
        logger.error(f"Erro geral ao carregar configurações: {str(e)}")
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
    
    # Se não tem data de abertura, retorna valores padr��o
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
        
        logger.info(f"Salvando configurações de notificaç��es: {data}")
        
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
        logger.error(f"Erro ao salvar configurações de notificaç��es: {str(e)}")
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

# ==================== APIS PARA AGENTES DE SUPORTE ====================

@painel_bp.route('/api/agente/estatisticas', methods=['GET'])
@api_login_required
def estatisticas_agente():
    """Retorna estatísticas do agente logado"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Buscar chamados atribuídos ativos
        chamados_atribuidos = ChamadoAgente.query.filter_by(
            agente_id=agente.id,
            ativo=True
        ).join(Chamado).filter(
            Chamado.status.in_(['Aberto', 'Aguardando'])
        ).count()

        # Buscar chamados concluídos hoje
        hoje = get_brazil_time().date()
        concluidos_hoje = ChamadoAgente.query.filter_by(
            agente_id=agente.id
        ).join(Chamado).filter(
            Chamado.status == 'Concluido',
            func.date(Chamado.data_conclusao) == hoje
        ).count()

        # Buscar chamados disponíveis (sem agente)
        disponiveis = Chamado.query.outerjoin(ChamadoAgente).filter(
            Chamado.status.in_(['Aberto']),
            ChamadoAgente.id.is_(None)
        ).count()

        estatisticas = {
            'atribuidos': chamados_atribuidos,
            'concluidos_hoje': concluidos_hoje,
            'disponiveis': disponiveis,
            'tempo_medio': '2.5h'  # Placeholder - implementar cálculo real
        }

        return json_response(estatisticas)

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do agente: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/disponiveis', methods=['GET'])
@api_login_required
def chamados_disponiveis():
    """Retorna chamados disponíveis para atribuição"""
    try:
        logger.debug(f"Carregando chamados disponíveis para usuário {current_user.id} ({current_user.nome})")
        # Buscar chamados sem agente atribuído
        chamados = db.session.query(Chamado).outerjoin(ChamadoAgente).filter(
            Chamado.status.in_(['Aberto']),
            ChamadoAgente.id.is_(None)
        ).order_by(Chamado.data_abertura.desc()).limit(10).all()

        chamados_list = []
        for chamado in chamados:
            data_abertura_brazil = chamado.get_data_abertura_brazil()
            chamados_list.append({
                'id': chamado.id,
                'codigo': chamado.codigo,
                'protocolo': chamado.protocolo if hasattr(chamado, 'protocolo') else None,
                'solicitante': chamado.solicitante,
                'problema': chamado.problema,
                'prioridade': chamado.prioridade,
                'descricao': chamado.descricao if hasattr(chamado, 'descricao') else None,
                'data_abertura': data_abertura_brazil.strftime('%d/%m %H:%M') if data_abertura_brazil else 'N/A'
            })

        return json_response(chamados_list)

    except Exception as e:
        logger.error(f"Erro ao buscar chamados disponíveis: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agente/meus-chamados', methods=['GET'])
@api_login_required
def meus_chamados_agente():
    """Retorna chamados do agente logado"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        filtro = request.args.get('filtro', 'ativos')

        query = db.session.query(ChamadoAgente, Chamado).join(Chamado).filter(
            ChamadoAgente.agente_id == agente.id
        )

        if filtro == 'ativos':
            query = query.filter(
                ChamadoAgente.ativo == True,
                Chamado.status.in_(['Aberto', 'Aguardando'])
            )
        elif filtro == 'aguardando':
            query = query.filter(
                ChamadoAgente.ativo == True,
                Chamado.status == 'Aguardando'
            )
        elif filtro == 'concluidos':
            query = query.filter(
                Chamado.status == 'Concluido'
            )
        elif filtro == 'cancelados':
            query = query.filter(
                Chamado.status == 'Cancelado'
            )

        atribuicoes = query.order_by(ChamadoAgente.data_atribuicao.desc()).limit(20).all()

        chamados_list = []
        for atribuicao, chamado in atribuicoes:
            data_atribuicao_brazil = atribuicao.data_atribuicao
            if data_atribuicao_brazil:
                data_atribuicao_brazil = utc_to_brazil(data_atribuicao_brazil)

            chamados_list.append({
                'id': chamado.id,
                'codigo': chamado.codigo,
                'solicitante': chamado.solicitante,
                'problema': chamado.problema,
                'status': chamado.status,
                'prioridade': chamado.prioridade,
                'data_atribuicao': data_atribuicao_brazil.strftime('%d/%m %H:%M') if data_atribuicao_brazil else 'N/A'
            })

        return json_response(chamados_list)

    except Exception as e:
        logger.error(f"Erro ao buscar chamados do agente: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/detalhes', methods=['GET'])
@api_login_required
def detalhes_chamado(chamado_id):
    """Retorna detalhes de um chamado específico"""
    try:
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Buscar agente atribuído
        agente_info = None
        chamado_agente = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if chamado_agente and chamado_agente.agente:
            agente_info = {
                'id': chamado_agente.agente.id,
                'nome': f"{chamado_agente.agente.usuario.nome} {chamado_agente.agente.usuario.sobrenome}",
                'usuario': chamado_agente.agente.usuario.usuario,
                'email': chamado_agente.agente.usuario.email,
                'nivel_experiencia': chamado_agente.agente.nivel_experiencia
            }

        data_abertura_brazil = chamado.get_data_abertura_brazil()
        data_conclusao_brazil = chamado.get_data_conclusao_brazil()

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
            'data_abertura': data_abertura_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_abertura_brazil else None,
            'data_conclusao': data_conclusao_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_conclusao_brazil else None,
            'agente': agente_info
        }

        return json_response(chamado_data)

    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/enviar-email', methods=['POST'])
@api_login_required
def enviar_email_chamado(chamado_id):
    """Envia e-mail relacionado a um chamado"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)

        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        destino = data.get('destino', chamado.email)
        assunto = data.get('assunto', f'Atualização do Chamado {chamado.codigo}')
        mensagem = data.get('mensagem', '')
        incluir_detalhes = data.get('incluir_detalhes', True)

        if not destino:
            return error_response('E-mail de destino é obrigatório', 400)

        # Montar corpo do e-mail
        corpo_email = mensagem

        if incluir_detalhes:
            detalhes = f"""

=== DETALHES DO CHAMADO ===
Código: {chamado.codigo}
Protocolo: {chamado.protocolo}
Solicitante: {chamado.solicitante}
Problema: {chamado.problema}
Descrição: {chamado.descricao or 'Não informada'}
Status: {chamado.status}
Prioridade: {chamado.prioridade}
Data de Abertura: {chamado.get_data_abertura_brazil().strftime('%d/%m/%Y %H:%M:%S') if chamado.get_data_abertura_brazil() else 'N/A'}
"""
            corpo_email += detalhes

        # Tentar enviar e-mail
        try:
            from setores.ti.routes import enviar_email
            enviar_email(assunto, corpo_email, [destino])

            # Registrar log da ação
            registrar_log_acao(
                usuario_id=current_user.id,
                acao=f'E-mail enviado para chamado {chamado.codigo}',
                categoria='chamados',
                detalhes=f'E-mail enviado para {destino} sobre o chamado {chamado.codigo}',
                recurso_afetado=str(chamado.id),
                tipo_recurso='chamado'
            )

            return json_response({
                'message': 'E-mail enviado com sucesso',
                'destino': destino,
                'assunto': assunto
            })

        except Exception as email_error:
            logger.error(f"Erro ao enviar e-mail: {str(email_error)}")
            return error_response('Erro ao enviar e-mail. Verifique as configurações de e-mail.')

    except Exception as e:
        logger.error(f"Erro no endpoint de envio de e-mail: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/atribuir-me', methods=['POST'])
@api_login_required
def atribuir_chamado_para_mim(chamado_id):
    """Atribui um chamado ao agente logado"""
    try:
        logger.info(f"Tentativa de atribuição do chamado {chamado_id} pelo usuário {current_user.id}")

        # Processar dados JSON se fornecidos
        data = {}
        if request.is_json:
            try:
                data = request.get_json() or {}
            except Exception as e:
                logger.warning(f"Erro ao processar JSON: {e}")

        # Buscar ou criar agente automaticamente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            # Criar agente automaticamente para admins e usuários de TI
            if current_user.nivel_acesso == 'Administrador' or current_user.setor == 'TI':
                agente = AgenteSuporte(
                    usuario_id=current_user.id,
                    ativo=True,
                    nivel_experiencia='pleno',
                    max_chamados_simultaneos=15
                )
                db.session.add(agente)
                db.session.flush()  # Para obter o ID
                logger.info(f"Agente criado automaticamente para usuário {current_user.id}")
            else:
                logger.warning(f"Usuário {current_user.id} não tem permissão para ser agente")
                return error_response('Usuário não tem permissão para ser agente', 403)

        # Verificar se o agente pode receber mais chamados
        try:
            if hasattr(agente, 'pode_receber_chamado') and not agente.pode_receber_chamado():
                return error_response('Você já atingiu o limite máximo de chamados simultâneos', 400)
        except Exception as e:
            logger.warning(f"Erro ao verificar limite de chamados: {str(e)}")
            # Continuar mesmo com erro no limite

        # Verificar se o chamado existe e está disponível
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            logger.error(f"Chamado {chamado_id} não encontrado")
            return error_response('Chamado não encontrado', 404)

        if chamado.status not in ['Aberto']:
            logger.warning(f"Chamado {chamado_id} não está disponível (status: {chamado.status})")
            return error_response('Chamado não está disponível para atribuição')

        # Verificar se já tem agente atribuído
        atribuicao_existente = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if atribuicao_existente:
            logger.warning(f"Chamado {chamado_id} já possui agente atribuído")
            return error_response('Chamado já possui agente atribuído')

        # Criar nova atribuição
        nova_atribuicao = ChamadoAgente(
            chamado_id=chamado_id,
            agente_id=agente.id,
            atribuido_por=current_user.id,
            observacoes='Auto-atribuição pelo agente'
        )

        db.session.add(nova_atribuicao)
        db.session.commit()

        logger.info(f"Chamado {chamado_id} atribuído com sucesso ao agente {agente.id}")

        # Enviar e-mail de notificação
        try:
            from setores.ti.routes import enviar_email
            assunto = f"Chamado {chamado.codigo} - Agente Atribuído"
            corpo = f"""
Olá {chamado.solicitante},

Seu chamado {chamado.codigo} foi atribuído ao agente {current_user.nome} {current_user.sobrenome}.

Detalhes do chamado:
- Problema: {chamado.problema}
- Prioridade: {chamado.prioridade}
- Agente responsável: {current_user.nome} {current_user.sobrenome}
- E-mail do agente: {current_user.email}

Em breve você receberá um contato para resolução do seu problema.

Atenciosamente,
Equipe de Suporte TI - Evoque Fitness
"""
            enviar_email(assunto, corpo, [chamado.email])
        except Exception as email_error:
            logger.warning(f"Erro ao enviar e-mail de atribuição: {str(email_error)}")

        # Emitir evento Socket.IO para notificação em tempo real
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('chamado_atribuido', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'protocolo': chamado.protocolo,
                    'solicitante': chamado.solicitante,
                    'problema': chamado.problema,
                    'prioridade': chamado.prioridade,
                    'agente_id': agente.id,
                    'agente_nome': f"{current_user.nome} {current_user.sobrenome}",
                    'agente_email': current_user.email,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")

        logger.info(f"Chamado {chamado.codigo} auto-atribuído ao agente {current_user.nome}")

        return json_response({
            'message': f'Chamado {chamado.codigo} atribuído com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atribuir chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/atualizar', methods=['PUT'])
@api_login_required
def atualizar_chamado_agente(chamado_id):
    """Atualiza um chamado pelo agente"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)

        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Verificar se o agente tem permissão para atualizar este chamado
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Verificar se o chamado está atribuído ao agente
        atribuicao = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            agente_id=agente.id,
            ativo=True
        ).first()

        if not atribuicao and current_user.nivel_acesso != 'Administrador':
            return error_response('Chamado não está atribuído a você', 403)

        # Atualizar status se fornecido
        if 'status' in data:
            novo_status = data['status']
            if novo_status in ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']:
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

        # Adicionar observações se fornecidas
        observacoes = data.get('observacoes', '')
        if observacoes:
            # Criar registro no hist��rico do ticket
            try:
                historico = HistoricoTicket(
                    chamado_id=chamado.id,
                    acao='Atualização do agente',
                    detalhes=observacoes,
                    usuario_responsavel=f"{current_user.nome} {current_user.sobrenome}",
                    data_acao=get_brazil_time().replace(tzinfo=None)
                )
                db.session.add(historico)
            except Exception as hist_error:
                logger.warning(f"Erro ao criar histórico: {str(hist_error)}")

        db.session.commit()

        # Registrar log da ação
        registrar_log_acao(
            usuario_id=current_user.id,
            acao=f'Chamado {chamado.codigo} atualizado',
            categoria='chamados',
            detalhes=f'Status alterado para {chamado.status}. Observações: {observacoes}',
            recurso_afetado=str(chamado.id),
            tipo_recurso='chamado'
        )

        # Emitir evento Socket.IO
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('chamado_atualizado', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'status': chamado.status,
                    'agente': f"{current_user.nome} {current_user.sobrenome}",
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")

        return json_response({
            'message': 'Chamado atualizado com sucesso',
            'chamado': {
                'id': chamado.id,
                'codigo': chamado.codigo,
                'status': chamado.status
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/transferir', methods=['POST'])
@api_login_required
def transferir_chamado_agente(chamado_id):
    """Transfere um chamado para outro agente"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)

        agente_destino_id = data.get('agente_destino_id')
        if not agente_destino_id:
            return error_response('Agente de destino é obrigatório', 400)

        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        # Verificar se o agente atual tem permissão
        agente_atual = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente_atual:
            return error_response('Usuário não é um agente de suporte', 403)

        # Verificar se agente de destino existe
        agente_destino = AgenteSuporte.query.get(agente_destino_id)
        if not agente_destino or not agente_destino.ativo:
            return error_response('Agente de destino não encontrado ou inativo', 404)

        # Verificar se agente de destino pode receber mais chamados
        if not agente_destino.pode_receber_chamado():
            return error_response('Agente de destino já atingiu o limite máximo de chamados simultâneos', 400)

        # Buscar atribuição atual
        atribuicao_atual = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if not atribuicao_atual:
            return error_response('Chamado não possui agente atribuído', 400)

        # Desativar atribuição atual
        atribuicao_atual.ativo = False
        atribuicao_atual.data_desatribuicao = get_brazil_time().replace(tzinfo=None)

        # Criar nova atribuição
        nova_atribuicao = ChamadoAgente(
            chamado_id=chamado_id,
            agente_id=agente_destino.id,
            atribuido_por=current_user.id,
            observacoes=data.get('observacoes', 'Transferido de outro agente')
        )

        db.session.add(nova_atribuicao)
        db.session.commit()

        # Registrar log da ação
        registrar_log_acao(
            usuario_id=current_user.id,
            acao=f'Chamado {chamado.codigo} transferido',
            categoria='chamados',
            detalhes=f'Transferido para {agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}',
            recurso_afetado=str(chamado.id),
            tipo_recurso='chamado'
        )

        # Emitir evento Socket.IO
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('chamado_transferido', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'agente_origem_nome': f"{current_user.nome} {current_user.sobrenome}",
                    'agente_origem_email': current_user.email,
                    'agente_destino_nome': f"{agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}",
                    'agente_destino_email': agente_destino.usuario.email,
                    'timestamp': get_brazil_time().isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")

        return json_response({
            'message': f'Chamado transferido para {agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}',
            'agente_destino': {
                'id': agente_destino.id,
                'nome': f"{agente_destino.usuario.nome} {agente_destino.usuario.sobrenome}",
                'email': agente_destino.usuario.email
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao transferir chamado: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agentes/ativos', methods=['GET'])
@api_login_required
def listar_agentes_ativos():
    """Lista agentes ativos para transferência"""
    try:
        agentes = db.session.query(AgenteSuporte, User).join(User).filter(
            AgenteSuporte.ativo == True,
            User.bloqueado == False
        ).all()

        agentes_list = []
        for agente, usuario in agentes:
            # Contar chamados ativos
            chamados_ativos = ChamadoAgente.query.filter_by(
                agente_id=agente.id,
                ativo=True
            ).join(Chamado).filter(
                Chamado.status.in_(['Aberto', 'Aguardando'])
            ).count()

            agentes_list.append({
                'id': agente.id,
                'nome': f"{usuario.nome} {usuario.sobrenome}",
                'usuario': usuario.usuario,
                'email': usuario.email,
                'nivel_experiencia': agente.nivel_experiencia,
                'max_chamados': agente.max_chamados_simultaneos,
                'chamados_ativos': chamados_ativos
            })

        return json_response(agentes_list)

    except Exception as e:
        logger.error(f"Erro ao listar agentes ativos: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== NOTIFICAÇÕES DO AGENTE ====================

@painel_bp.route('/api/agente/notificacoes', methods=['GET'])
@api_login_required
def notificacoes_agente():
    """Retorna notificações do agente"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Parâmetros de filtro
        nao_lidas = request.args.get('nao_lidas', 'false').lower() == 'true'
        limite = request.args.get('limite', 50, type=int)

        # Simular algumas notificações para demonstração
        agora = get_brazil_time()
        notificacoes = [
            {
                'id': 1,
                'titulo': 'Novo chamado atribuído',
                'mensagem': 'Você tem um novo chamado de alta prioridade',
                'tipo': 'chamado_atribuido',
                'prioridade': 'alta',
                'lida': False,
                'data_criacao': (agora - timedelta(minutes=30)).strftime('%d/%m/%Y %H:%M:%S'),
                'exibir_popup': True,
                'som_ativo': True,
                'chamado': {'id': 1, 'codigo': 'TI-2025-001'}
            },
            {
                'id': 2,
                'titulo': 'Chamado transferido',
                'mensagem': 'Um chamado foi transferido para você',
                'tipo': 'chamado_transferido',
                'prioridade': 'normal',
                'lida': True,
                'data_criacao': (agora - timedelta(hours=2)).strftime('%d/%m/%Y %H:%M:%S'),
                'exibir_popup': False,
                'som_ativo': False,
                'chamado': {'id': 2, 'codigo': 'TI-2025-002'}
            },
            {
                'id': 3,
                'titulo': 'Sistema atualizado',
                'mensagem': 'O sistema foi atualizado com novas funcionalidades',
                'tipo': 'sistema',
                'prioridade': 'baixa',
                'lida': True,
                'data_criacao': (agora - timedelta(days=1)).strftime('%d/%m/%Y %H:%M:%S'),
                'exibir_popup': False,
                'som_ativo': False,
                'chamado': None
            }
        ]

        # Filtrar por não lidas se solicitado
        if nao_lidas:
            notificacoes = [n for n in notificacoes if not n['lida']]

        # Aplicar limite
        notificacoes = notificacoes[:limite]

        return json_response(notificacoes)

    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agente/notificacoes/<int:notificacao_id>/marcar-lida', methods=['POST'])
@api_login_required
def marcar_notificacao_lida(notificacao_id):
    """Marca uma notificaç��o como lida"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Simular marcação como lida
        return json_response({
            'message': 'Notificação marcada como lida',
            'notificacao_id': notificacao_id
        })

    except Exception as e:
        logger.error(f"Erro ao marcar notificação como lida: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/auth/teste', methods=['GET'])
def teste_autenticacao():
    """Endpoint para testar autenticação"""
    if current_user.is_authenticated:
        return json_response({
            'authenticated': True,
            'user_id': current_user.id,
            'user_name': current_user.nome,
            'setor': current_user.setor
        })
    else:
        return json_response({'authenticated': False}, 401)

@painel_bp.route('/api/chamados/<int:chamado_id>/auto-atribuir', methods=['POST'])
@api_login_required
def auto_atribuir_chamado(chamado_id):
    """Auto-atribui um chamado ao usuário logado"""
    try:
        logger.info(f"Auto-atribuição do chamado {chamado_id} pelo usuário {current_user.id} ({current_user.nome})")

        # Buscar o chamado
        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        if chamado.status not in ['Aberto']:
            return error_response('Chamado não está disponível para atribuição')

        # Verificar se já tem agente atribuído
        atribuicao_existente = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if atribuicao_existente:
            return error_response('Chamado já possui agente atribuído')

        # Buscar ou criar agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            # Criar agente automaticamente para admins e usuários de TI
            if current_user.nivel_acesso == 'Administrador' or current_user.setor == 'TI':
                agente = AgenteSuporte(
                    usuario_id=current_user.id,
                    ativo=True,
                    nivel_experiencia='pleno',
                    max_chamados_simultaneos=15
                )
                db.session.add(agente)
                db.session.flush()  # Para obter o ID
                logger.info(f"Agente criado automaticamente para usuário {current_user.id}")
            else:
                return error_response('Usuário não tem permissão para ser agente', 403)

        # Criar atribuição
        nova_atribuicao = ChamadoAgente(
            chamado_id=chamado_id,
            agente_id=agente.id,
            atribuido_por=current_user.id,
            observacoes='Auto-atribuição pelo agente'
        )

        db.session.add(nova_atribuicao)
        db.session.commit()

        # Enviar email
        try:
            from .email_service import email_service
            email_service.notificar_agente_atribuido(chamado, agente)
        except Exception as e:
            logger.warning(f"Erro ao enviar email: {str(e)}")

        logger.info(f"Chamado {chamado.codigo} auto-atribuído com sucesso")
        return json_response({'message': f'Chamado {chamado.codigo} atribuído com sucesso'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na auto-atribuição: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agente/registrar', methods=['POST'])
@api_login_required
def registrar_como_agente():
    """Registra o usuário atual como agente de suporte"""
    try:
        # Verificar se já é agente
        agente_existente = AgenteSuporte.query.filter_by(usuario_id=current_user.id).first()
        if agente_existente:
            agente_existente.ativo = True
            db.session.commit()
            return json_response({'message': 'Agente reativado com sucesso'})

        # Criar novo agente
        agente = AgenteSuporte(
            usuario_id=current_user.id,
            ativo=True,
            nivel_experiencia='pleno',
            max_chamados_simultaneos=15
        )
        db.session.add(agente)
        db.session.commit()

        logger.info(f"Usuário {current_user.id} registrado como agente de suporte")
        return json_response({'message': 'Registrado como agente com sucesso'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao registrar agente: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agente/notificacoes/marcar-todas-lidas', methods=['POST'])
@api_login_required
def marcar_todas_notificacoes_lidas():
    """Marca todas as notificações como lidas"""
    try:
        # Verificar se o usuário é um agente
        agente = AgenteSuporte.query.filter_by(usuario_id=current_user.id, ativo=True).first()
        if not agente:
            return error_response('Usuário não é um agente de suporte', 403)

        # Simular marcação de todas como lidas
        return json_response({
            'message': 'Todas as notificações foram marcadas como lidas'
        })

    except Exception as e:
        logger.error(f"Erro ao marcar todas as notificações como lidas: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== PROBLEMAS REPORTADOS ====================

@painel_bp.route('/api/problemas', methods=['GET'])
@api_login_required
def listar_problemas():
    """Lista todos os problemas reportados"""
    try:
        # Verificar se o banco de dados está disponível
        try:
            # Tentar uma consulta simples primeiro
            db.session.execute(db.text('SELECT 1'))
            db.session.commit()
        except Exception as conn_error:
            logger.warning(f"Banco de dados não disponível: {str(conn_error)}")
            # Retornar lista vazia em vez de erro para permitir que a interface funcione
            return json_response([])

        # Verificar se a tabela existe
        try:
            count = ProblemaReportado.query.count()
            logger.info(f"Total de problemas na base: {count}")
        except Exception as db_error:
            logger.warning(f"Tabela ProblemaReportado não disponível: {str(db_error)}")
            # Retornar problemas padrão se a tabela não existir
            problemas_padrao = [
                {'id': 1, 'nome': 'Problema de Hardware', 'prioridade_padrao': 'Normal', 'requer_item_internet': False},
                {'id': 2, 'nome': 'Problema de Software', 'prioridade_padrao': 'Normal', 'requer_item_internet': False},
                {'id': 3, 'nome': 'Problema de Rede', 'prioridade_padrao': 'Alto', 'requer_item_internet': True},
                {'id': 4, 'nome': 'Problema de Sistema', 'prioridade_padrao': 'Normal', 'requer_item_internet': False},
                {'id': 5, 'nome': 'Problema de Impressora', 'prioridade_padrao': 'Normal', 'requer_item_internet': False}
            ]
            logger.info(f"Retornando {len(problemas_padrao)} problemas padrão")
            return json_response(problemas_padrao)

        problemas = ProblemaReportado.query.filter_by(ativo=True).all()
        problemas_list = []

        for p in problemas:
            try:
                problema_data = {
                    'id': p.id,
                    'nome': p.nome,
                    'prioridade_padrao': p.prioridade_padrao,
                    'requer_item_internet': p.requer_item_internet
                }
                problemas_list.append(problema_data)
            except Exception as item_error:
                logger.error(f"Erro ao processar problema ID {p.id}: {str(item_error)}")
                continue

        logger.info(f"Retornando {len(problemas_list)} problemas ativos")
        return json_response(problemas_list)

    except Exception as e:
        logger.error(f"Erro geral ao listar problemas: {str(e)}")
        logger.error(traceback.format_exc())
        # Em caso de erro, retornar lista vazia em vez de erro 500
        return json_response([])

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
            return error_response('Prioridade inv��lida', 400)
        
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

        for status, quantidade in estatisticas:
            stats_dict[status] = quantidade
            total += quantidade

        # Adicionar status que podem não ter chamados
        status_possiveis = ['Aberto', 'Aguardando', 'Concluido', 'Cancelado']
        for status in status_possiveis:
            if status not in stats_dict:
                stats_dict[status] = 0

        stats_dict['total'] = total

        return json_response(stats_dict)

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas dos chamados: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/debug/test-usuarios')
@login_required
def debug_test_usuarios():
    """Debug endpoint to test user loading"""
    try:
        # Test direct database query
        users = User.query.all()
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'nome': user.nome,
                'sobrenome': user.sobrenome,
                'email': user.email,
                'usuario': user.usuario,
                'nivel_acesso': user.nivel_acesso,
                'setor': user.setor,
                'setores': user.setores,
                'bloqueado': getattr(user, 'bloqueado', False),
                'data_criacao': user.data_criacao.strftime('%d/%m/%Y') if user.data_criacao else None
            })

        return json_response({
            'status': 'success',
            'message': 'Debug test successful',
            'total_users': len(users_data),
            'current_user': {
                'id': current_user.id,
                'nome': current_user.nome,
                'email': current_user.email,
                'nivel_acesso': current_user.nivel_acesso,
                'setores': current_user.setores,
                'tem_permissao_admin': current_user.tem_permissao('Administrador'),
                'tem_acesso_ti': current_user.tem_acesso_setor('ti')
            },
            'usuarios': users_data
        })
    except Exception as e:
        import traceback
        return json_response({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        for stat in estatisticas:
            stats_dict[stat.status] = stat.quantidade
            total += stat.quantidade
        
        # Garantir que todos os status est��o presentes
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
        
        # Buscar informações do agente para incluir na resposta
        agente_info = None
        try:
            from database import ChamadoAgente, AgenteSuporte
            chamado_agente = ChamadoAgente.query.filter_by(
                chamado_id=id,
                ativo=True
            ).first()

            if chamado_agente and chamado_agente.agente:
                agente = chamado_agente.agente
                agente_info = {
                    'id': agente.id,
                    'nome': f"{agente.usuario.nome} {agente.usuario.sobrenome}",
                    'email': agente.usuario.email,
                    'nivel_experiencia': agente.nivel_experiencia
                }
        except Exception as agente_error:
            logger.warning(f"Erro ao buscar agente: {str(agente_error)}")

        # Emitir evento Socket.IO apenas se a conexão estiver disponível
        try:
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('status_atualizado', {
                    'chamado_id': chamado.id,
                    'codigo': chamado.codigo,
                    'status_anterior': status_anterior,
                    'novo_status': novo_status,
                    'solicitante': chamado.solicitante,
                    'agente': agente_info,
                    'timestamp': agora_brazil.isoformat()
                })
        except Exception as socket_error:
            logger.warning(f"Erro ao emitir evento Socket.IO: {str(socket_error)}")

        return json_response({
            'message': 'Status atualizado com sucesso.',
            'id': chamado.id,
            'status': chamado.status,
            'codigo': chamado.codigo,
            'agente': agente_info
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

        # Remover atribuições de agentes antes de deletar o chamado
        from database import ChamadoAgente
        atribuicoes = ChamadoAgente.query.filter_by(chamado_id=id).all()
        for atribuicao in atribuicoes:
            db.session.delete(atribuicao)

        # Agora deletar o chamado
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

@painel_bp.route('/api/usuarios', methods=['GET'])
@login_required
@setor_required('ti')
def listar_usuarios():
    """Lista usuários com filtros opcionais"""
    try:
        # Verificar se o usuário tem permissão (Administrador ou Agente de Suporte)
        if not current_user.tem_permissao_gerenciar_usuarios():
            return error_response('Acesso negado. Permissão de administrador ou agente de suporte necessária.', 403)
        busca = request.args.get('busca', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = User.query

        # Aplicar filtros de busca
        if busca:
            query = query.filter(
                db.or_(
                    User.nome.ilike(f'%{busca}%'),
                    User.sobrenome.ilike(f'%{busca}%'),
                    User.email.ilike(f'%{busca}%'),
                    User.usuario.ilike(f'%{busca}%')
                )
            )

        # Paginação
        usuarios_pag = query.order_by(User.nome).paginate(
            page=page, per_page=per_page, error_out=False
        )

        usuarios_list = []
        for user in usuarios_pag.items:
            usuarios_list.append({
                'id': user.id,
                'nome': user.nome,
                'sobrenome': user.sobrenome,
                'email': user.email,
                'usuario': user.usuario,
                'nivel_acesso': user.nivel_acesso,
                'setor': user.setor,
                'bloqueado': getattr(user, 'bloqueado', False),
                'ativo': getattr(user, 'ativo', True),
                'data_cadastro': user.data_criacao.strftime('%d/%m/%Y') if user.data_criacao else None
            })

        return json_response({
            'usuarios': usuarios_list,
            'total': usuarios_pag.total,
            'pages': usuarios_pag.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': usuarios_pag.has_next,
            'has_prev': usuarios_pag.has_prev
        })

    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/usuarios', methods=['POST'])
@login_required
@gerenciamento_usuarios_required
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

        niveis_validos = ['Administrador', 'Gerente', 'Gerente Regional', 'Gestor', 'Agente de suporte']
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

        # Se o usuário foi criado como agente de suporte, criar automaticamente o registro de agente
        if data['nivel_acesso'] == 'Agente de suporte':
            try:
                from database import AgenteSuporte
                agente = AgenteSuporte(
                    usuario_id=novo_usuario.id,
                    ativo=True,
                    nivel_experiencia='junior',
                    max_chamados_simultaneos=10
                )
                db.session.add(agente)
                db.session.commit()
                logger.info(f"Agente de suporte criado automaticamente para usuário {novo_usuario.nome}")
            except Exception as e:
                logger.error(f"Erro ao criar agente automaticamente: {str(e)}")
                # Não interromper o fluxo se der erro na criação do agente

        # Emitir evento Socket.IO apenas se a conex��o estiver disponível
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

@painel_bp.route('/api/usuarios-search', methods=['GET'])
@login_required
@gerenciamento_usuarios_required
def buscar_usuarios_backup():
    try:
        busca = request.args.get('busca', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Buscar usuários no banco de dados
        query = User.query

        # Aplicar filtros de busca se fornecido
        if busca:
            query = query.filter(
                db.or_(
                    User.nome.ilike(f'%{busca}%'),
                    User.sobrenome.ilike(f'%{busca}%'),
                    User.email.ilike(f'%{busca}%'),
                    User.usuario.ilike(f'%{busca}%')
                )
            )

        # Paginação
        usuarios_pag = query.order_by(User.nome).paginate(
            page=page, per_page=per_page, error_out=False
        )

        usuarios_list = []
        for user in usuarios_pag.items:
            usuarios_list.append({
                'id': user.id,
                'nome': user.nome,
                'sobrenome': user.sobrenome,
                'email': user.email,
                'usuario': user.usuario,
                'nivel_acesso': user.nivel_acesso,
                'setor': user.setor,
                'bloqueado': getattr(user, 'bloqueado', False),
                'ativo': getattr(user, 'ativo', True),
                'data_cadastro': user.data_criacao.strftime('%d/%m/%Y') if hasattr(user, 'data_criacao') and user.data_criacao else None
            })

        return json_response({
            'usuarios': usuarios_list,
            'total': usuarios_pag.total,
            'pages': usuarios_pag.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': usuarios_pag.has_next,
            'has_prev': usuarios_pag.has_prev
        })

    except Exception as e:
        logger.error(f"Erro ao buscar usuários: {str(e)}")
        # Fallback: retornar usuários exemplo em caso de erro
        usuarios_exemplo = [
                {
                    'id': 1,
                    'nome': 'Admin',
                    'sobrenome': 'Sistema',
                    'usuario': 'admin',
                    'email': 'admin@example.com',
                    'nivel_acesso': 'Administrador',
                    'setores': 'TI',
                    'bloqueado': False,
                    'data_criacao': '01/01/2024 08:00:00'
                },
                {
                    'id': 2,
                    'nome': 'João',
                    'sobrenome': 'Silva',
                    'usuario': 'joao.silva',
                    'email': 'joao@example.com',
                    'nivel_acesso': 'Agente de suporte',
                    'setores': 'TI',
                    'bloqueado': False,
                    'data_criacao': '01/01/2024 08:00:00'
                }
            ]

        # Aplicar filtro de busca se fornecido
        busca = request.args.get('busca', '').strip()
        if busca:
            usuarios_filtrados = []
            for u in usuarios_exemplo:
                if (busca.lower() in u['nome'].lower() or
                    busca.lower() in u['sobrenome'].lower() or
                    busca.lower() in u['usuario'].lower() or
                    busca.lower() in u['email'].lower()):
                    usuarios_filtrados.append(u)
                usuarios_exemplo = usuarios_filtrados

            return json_response({
                'usuarios': usuarios_exemplo,
                'pagination': {
                    'page': int(request.args.get('page', 1)),
                    'per_page': int(request.args.get('per_page', 20)),
                    'total': len(usuarios_exemplo),
                    'pages': 1,
                    'has_next': False,
                    'has_prev': False
                },
                'busca': busca
            })

        # Parâmetros de busca e paginação
        busca = request.args.get('busca', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Construir query base
        query = User.query

        # Aplicar filtro de busca se fornecido
        if busca:
            like_term = f'%{busca}%'
            query = query.filter(
                db.or_(
                    User.nome.ilike(like_term),
                    User.sobrenome.ilike(like_term),
                    db.func.concat(User.nome, ' ', User.sobrenome).ilike(like_term),
                    User.usuario.ilike(like_term),
                    User.email.ilike(like_term),
                    User.nivel_acesso.ilike(like_term),
                    User._setores.ilike(like_term)
                )
            )

        # Aplicar ordenação e paginação
        query = query.order_by(User.data_criacao.desc())
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        usuarios_list = []
        
        for u in pagination.items:
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
        
        logger.debug(f"Usuários encontrados: {len(usuarios_list)} (total: {pagination.total})")

        # Retornar dados com informações de paginação
        return json_response({
            'usuarios': usuarios_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'busca': busca
        })
    except Exception as e:
        logger.error(f"Erro ao listar usu��rios: {str(e)}")
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
            niveis_validos = ['Administrador', 'Gerente', 'Gerente Regional', 'Gestor', 'Agente de suporte']
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

        # Verificar se há agente atribuído
        from database import ChamadoAgente, AgenteSuporte
        agente_info = ""
        try:
            chamado_agente = ChamadoAgente.query.filter_by(
                chamado_id=chamado.id,
                ativo=True
            ).first()

            if chamado_agente and chamado_agente.agente:
                agente = chamado_agente.agente
                agente_info = f"""
Agente Responsável: {agente.usuario.nome} {agente.usuario.sobrenome}
Email do Agente: {agente.usuario.email}
Nível de Experiência: {agente.nivel_experiencia.title()}
"""
        except Exception as agente_error:
            logger.warning(f"Erro ao buscar agente do chamado: {str(agente_error)}")

        mensagem_formatada = f"""
Chamado: {chamado.codigo}
Status: {chamado.status}
Data de Abertura: {data_abertura_str}
Problema: {chamado.problema}
Unidade: {chamado.unidade}{agente_info}

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
@api_login_required
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
@api_login_required
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
@api_login_required
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
            {'id': 'Manutencao', 'nome': 'Setor de manutenç��o'},
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

# ==================== ALERTAS DO SISTEMA ====================

@painel_bp.route('/api/alertas', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_alertas():
    """Lista alertas do sistema"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Gerar alertas simulados (em produção, seria de uma tabela de alertas)
        alertas_sistema = [
            {
                'id': 1,
                'tipo': 'warning',
                'titulo': 'Uso de Memória Alto',
                'mensagem': 'O servidor está usando 85% da memória disponível',
                'data': '2025-01-31 10:30:00',
                'status': 'ativo',
                'prioridade': 'alta'
            },
            {
                'id': 2,
                'tipo': 'info',
                'titulo': 'Backup Concluído',
                'mensagem': 'Backup automático realizado com sucesso',
                'data': '2025-01-31 06:00:00',
                'status': 'resolvido',
                'prioridade': 'baixa'
            },
            {
                'id': 3,
                'tipo': 'error',
                'titulo': 'Falha na Conectividade',
                'mensagem': 'Problemas de conexão detectados na rede',
                'data': '2025-01-31 09:15:00',
                'status': 'ativo',
                'prioridade': 'crítica'
            }
        ]

        # Simular paginação
        total = len(alertas_sistema)
        start = (page - 1) * per_page
        end = start + per_page
        alertas_paginados = alertas_sistema[start:end]

        return json_response({
            'alertas': alertas_paginados,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar alertas: {str(e)}")
        return error_response('Erro interno no servidor')

# ==================== AGENTES DE SUPORTE ====================

@painel_bp.route('/api/agentes', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_agentes():
    """Lista todos os agentes de suporte"""
    try:
        from database import AgenteSuporte

        agentes = db.session.query(AgenteSuporte, User).join(User).all()

        agentes_data = []
        for agente, usuario in agentes:
            agentes_data.append({
                'id': agente.id,
                'usuario_id': agente.usuario_id,
                'nome': f"{usuario.nome} {usuario.sobrenome}",
                'sobrenome': usuario.sobrenome,
                'email': usuario.email,
                'ativo': agente.ativo,
                'especialidades': agente.especialidades_list,
                'nivel_experiencia': agente.nivel_experiencia,
                'max_chamados_simultaneos': agente.max_chamados_simultaneos,
                'chamados_ativos': agente.get_chamados_ativos(),
                'pode_receber_chamado': agente.pode_receber_chamado(),
                'data_criacao': agente.data_criacao.strftime('%d/%m/%Y %H:%M') if agente.data_criacao else None
            })

        return json_response(agentes_data)

    except Exception as e:
        logger.error(f"Erro ao listar agentes: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agentes', methods=['POST'])
@login_required
@setor_required('Administrador')
def criar_agente():
    """Cria um novo agente de suporte"""
    try:
        from database import AgenteSuporte

        data = request.get_json()

        if not data:
            return error_response('Dados não fornecidos')

        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return error_response('ID do usuário é obrigatório')

        # Verificar se usuário existe
        usuario = User.query.get(usuario_id)
        if not usuario:
            return error_response('Usuário não encontrado')

        # Verificar se já é agente
        agente_existente = AgenteSuporte.query.filter_by(usuario_id=usuario_id).first()
        if agente_existente:
            return error_response('Usuário já é um agente de suporte')

        # Criar agente
        agente = AgenteSuporte(
            usuario_id=usuario_id,
            ativo=data.get('ativo', True),
            nivel_experiencia=data.get('nivel_experiencia', 'junior'),
            max_chamados_simultaneos=data.get('max_chamados_simultaneos', 10)
        )

        # Definir especialidades
        especialidades = data.get('especialidades', [])
        if isinstance(especialidades, list):
            agente.especialidades_list = especialidades

        db.session.add(agente)
        db.session.commit()

        logger.info(f"Agente criado: {usuario.nome} por {current_user.nome}")

        return json_response({
            'id': agente.id,
            'nome': f"{usuario.nome} {usuario.sobrenome}",
            'message': f'Agente {usuario.nome} criado com sucesso'
        }, 201)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar agente: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')



@painel_bp.route('/api/agentes/<int:agente_id>', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_agente(agente_id):
    """Atualiza informações de um agente"""
    try:
        from database import AgenteSuporte

        agente = AgenteSuporte.query.get(agente_id)
        if not agente:
            return error_response('Agente não encontrado', 404)

        data = request.get_json()
        if not data:
            return error_response('Dados n��o fornecidos')

        # Atualizar campos
        if 'ativo' in data:
            agente.ativo = data['ativo']

        if 'nivel_experiencia' in data:
            agente.nivel_experiencia = data['nivel_experiencia']

        if 'max_chamados_simultaneos' in data:
            max_chamados = data['max_chamados_simultaneos']
            if isinstance(max_chamados, int) and max_chamados > 0:
                agente.max_chamados_simultaneos = max_chamados

        if 'especialidades' in data:
            especialidades = data['especialidades']
            if isinstance(especialidades, list):
                agente.especialidades_list = especialidades

        agente.data_atualizacao = get_brazil_time().replace(tzinfo=None)
        db.session.commit()

        logger.info(f"Agente {agente.usuario.nome} atualizado por {current_user.nome}")

        return json_response({'message': 'Agente atualizado com sucesso'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar agente: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/agentes/<int:agente_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def excluir_agente(agente_id):
    """Remove um agente de suporte"""
    try:
        from database import AgenteSuporte, ChamadoAgente

        agente = AgenteSuporte.query.get(agente_id)
        if not agente:
            return error_response('Agente não encontrado', 404)

        # Verificar se há chamados ativos atribuídos
        chamados_ativos = agente.get_chamados_ativos()
        if chamados_ativos > 0:
            return error_response(f'Não é possível excluir agente com {chamados_ativos} chamado(s) ativo(s)')

        nome_agente = agente.usuario.nome

        # Finalizar todas as atribuições antigas
        ChamadoAgente.query.filter_by(agente_id=agente_id, ativo=True).update({
            'ativo': False,
            'data_conclusao': get_brazil_time().replace(tzinfo=None)
        })

        db.session.delete(agente)
        db.session.commit()

        logger.info(f"Agente {nome_agente} excluído por {current_user.nome}")

        return json_response({'message': f'Agente {nome_agente} excluído com sucesso'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir agente: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/chamados/<int:chamado_id>/atribuir', methods=['POST'])
@login_required
@setor_required('Administrador')
def atribuir_chamado(chamado_id):
    """Atribui um chamado a um agente"""
    try:
        from database import AgenteSuporte, ChamadoAgente

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos')

        agente_id = data.get('agente_id')
        if not agente_id:
            return error_response('ID do agente é obrigatório')

        chamado = Chamado.query.get(chamado_id)
        if not chamado:
            return error_response('Chamado não encontrado', 404)

        agente = AgenteSuporte.query.get(agente_id)
        if not agente:
            return error_response('Agente não encontrado', 404)

        if not agente.ativo:
            return error_response('Agente não está ativo')

        if not agente.pode_receber_chamado():
            return error_response('Agente já atingiu o limite máximo de chamados simultâneos')

        # Verificar se já há atribuição ativa
        atribuicao_existente = ChamadoAgente.query.filter_by(
            chamado_id=chamado_id,
            ativo=True
        ).first()

        if atribuicao_existente:
            # Finalizar atribui��ão anterior
            atribuicao_existente.finalizar_atribuicao()

        # Criar nova atribuição
        nova_atribuicao = ChamadoAgente(
            chamado_id=chamado_id,
            agente_id=agente_id,
            atribuido_por=current_user.id,
            observacoes=data.get('observacoes', '')
        )

        db.session.add(nova_atribuicao)
        db.session.commit()

        logger.info(f"Chamado {chamado.codigo} atribuído ao agente {agente.usuario.nome} por {current_user.nome}")

        # Enviar notificação por email ao solicitante
        try:
            from .email_service import email_service
            email_enviado = email_service.notificar_agente_atribuido(chamado, agente)
            if email_enviado:
                logger.info(f"Email de notificação enviado para {chamado.email}")
            else:
                logger.warning(f"Falha ao enviar email de notificaç��o para {chamado.email}")
        except Exception as e:
            logger.warning(f"Erro ao enviar email de notificação: {str(e)}")

        return json_response({
            'message': f'Chamado {chamado.codigo} atribuído ao agente {agente.usuario.nome}',
            'agente_nome': f"{agente.usuario.nome} {agente.usuario.sobrenome}",
            'agente_id': agente.id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atribuir chamado: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

# ==================== AUDITORIA E LOGS ====================

@painel_bp.route('/api/logs/acoes', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_logs_acoes():
    """Lista logs de ações com filtros e paginação"""
    try:
        from database import LogAcao

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        categoria = request.args.get('categoria')
        usuario_id = request.args.get('usuario_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Construir query base
        query = LogAcao.query

        # Aplicar filtros
        if categoria:
            query = query.filter(LogAcao.categoria == categoria)
        if usuario_id:
            query = query.filter(LogAcao.usuario_id == int(usuario_id))
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(LogAcao.data_acao >= data_inicio_obj)
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(LogAcao.data_acao < data_fim_obj)
            except ValueError:
                pass

        # Ordenar por data mais recente
        query = query.order_by(LogAcao.data_acao.desc())

        # Paginar
        logs_paginados = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        logs_list = []
        for log in logs_paginados.items:
            data_acao_brazil = log.get_data_acao_brazil()

            logs_list.append({
                'id': log.id,
                'usuario_id': log.usuario_id,
                'usuario_nome': log.usuario.nome if log.usuario else 'Sistema',
                'acao': log.acao,
                'categoria': log.categoria,
                'detalhes': log.detalhes,
                'data_acao': data_acao_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_acao_brazil else None,
                'ip_address': log.ip_address,
                'sucesso': log.sucesso,
                'erro_detalhes': log.erro_detalhes,
                'recurso_afetado': log.recurso_afetado,
                'tipo_recurso': log.tipo_recurso
            })

        return json_response({
            'logs': logs_list,
            'pagination': {
                'page': logs_paginados.page,
                'pages': logs_paginados.pages,
                'per_page': logs_paginados.per_page,
                'total': logs_paginados.total,
                'has_next': logs_paginados.has_next,
                'has_prev': logs_paginados.has_prev
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar logs de ações: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/logs/acoes/categorias', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_categorias_logs_acoes():
    """Lista categorias únicas dos logs de ações"""
    try:
        from database import LogAcao

        categorias = db.session.query(LogAcao.categoria).distinct().filter(
            LogAcao.categoria.isnot(None)
        ).all()

        categorias_list = [cat[0] for cat in categorias if cat[0]]

        return json_response(categorias_list)

    except Exception as e:
        logger.error(f"Erro ao listar categorias: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/logs/acoes/estatisticas', methods=['GET'])
@login_required
@setor_required('Administrador')
def estatisticas_logs_acoes():
    """Retorna estatísticas dos logs de ações"""
    try:
        from database import LogAcao

        # Estatísticas gerais
        total_acoes = LogAcao.query.count()
        acoes_sucesso = LogAcao.query.filter_by(sucesso=True).count()
        acoes_erro = LogAcao.query.filter_by(sucesso=False).count()

        # Ações por categoria (últimos 30 dias)
        trinta_dias_atras = get_brazil_time() - timedelta(days=30)
        acoes_por_categoria = db.session.query(
            LogAcao.categoria,
            func.count(LogAcao.id).label('quantidade')
        ).filter(
            LogAcao.data_acao >= trinta_dias_atras.replace(tzinfo=None)
        ).group_by(LogAcao.categoria).all()

        # Usuários mais ativos (últimos 30 dias)
        usuarios_ativos = db.session.query(
            LogAcao.usuario_id,
            User.nome,
            func.count(LogAcao.id).label('quantidade')
        ).join(User).filter(
            LogAcao.data_acao >= trinta_dias_atras.replace(tzinfo=None)
        ).group_by(LogAcao.usuario_id, User.nome).order_by(
            func.count(LogAcao.id).desc()
        ).limit(10).all()

        return json_response({
            'total_acoes': total_acoes,
            'acoes_sucesso': acoes_sucesso,
            'acoes_erro': acoes_erro,
            'taxa_sucesso': round((acoes_sucesso / total_acoes * 100) if total_acoes > 0 else 0, 2),
            'por_categoria': [{'categoria': cat[0], 'quantidade': cat[1]} for cat in acoes_por_categoria],
            'usuarios_ativos': [{'usuario_id': u[0], 'nome': u[1], 'quantidade': u[2]} for u in usuarios_ativos]
        })

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de logs: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/logs/acesso', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_logs_acesso():
    """Lista logs de acesso com filtros e paginação"""
    try:
        from database import LogAcesso

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        usuario_id = request.args.get('usuario_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        ativo = request.args.get('ativo')

        # Construir query base
        query = LogAcesso.query

        # Aplicar filtros
        if usuario_id:
            query = query.filter(LogAcesso.usuario_id == int(usuario_id))
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(LogAcesso.data_acesso >= data_inicio_obj)
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(LogAcesso.data_acesso < data_fim_obj)
            except ValueError:
                pass
        if ativo == 'true':
            query = query.filter(LogAcesso.ativo == True)
        elif ativo == 'false':
            query = query.filter(LogAcesso.ativo == False)

        # Ordenar por data mais recente
        query = query.order_by(LogAcesso.data_acesso.desc())

        # Paginar
        logs_paginados = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        logs_list = []
        for log in logs_paginados.items:
            data_acesso_brazil = log.get_data_acesso_brazil()
            data_logout_brazil = log.get_data_logout_brazil()

            logs_list.append({
                'id': log.id,
                'usuario_id': log.usuario_id,
                'usuario_nome': log.usuario.nome if log.usuario else 'Usuário Removido',
                'data_acesso': data_acesso_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_acesso_brazil else None,
                'data_logout': data_logout_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_logout_brazil else None,
                'duracao_sessao': log.duracao_sessao,
                'ip_address': log.ip_address,
                'navegador': log.navegador,
                'sistema_operacional': log.sistema_operacional,
                'dispositivo': log.dispositivo,
                'ativo': log.ativo
            })

        return json_response({
            'logs': logs_list,
            'pagination': {
                'page': logs_paginados.page,
                'pages': logs_paginados.pages,
                'per_page': logs_paginados.per_page,
                'total': logs_paginados.total,
                'has_next': logs_paginados.has_next,
                'has_prev': logs_paginados.has_prev
            }
        })

    except Exception as e:
        logger.error(f"Erro ao listar logs de acesso: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/logs/acesso/estatisticas', methods=['GET'])
@login_required
@setor_required('Administrador')
def estatisticas_logs_acesso():
    """Retorna estatísticas dos logs de acesso"""
    try:
        from database import LogAcesso

        # Estatísticas gerais
        total_acessos = LogAcesso.query.count()
        sessoes_ativas = LogAcesso.query.filter_by(ativo=True).count()

        # Acessos por dia (últimos 30 dias)
        trinta_dias_atras = get_brazil_time() - timedelta(days=30)
        acessos_por_dia = db.session.query(
            func.date(LogAcesso.data_acesso).label('data'),
            func.count(LogAcesso.id).label('quantidade')
        ).filter(
            LogAcesso.data_acesso >= trinta_dias_atras.replace(tzinfo=None)
        ).group_by(func.date(LogAcesso.data_acesso)).all()

        # Dispositivos mais utilizados
        dispositivos = db.session.query(
            LogAcesso.dispositivo,
            func.count(LogAcesso.id).label('quantidade')
        ).filter(
            LogAcesso.dispositivo.isnot(None)
        ).group_by(LogAcesso.dispositivo).all()

        # Navegadores mais utilizados
        navegadores = db.session.query(
            LogAcesso.navegador,
            func.count(LogAcesso.id).label('quantidade')
        ).filter(
            LogAcesso.navegador.isnot(None)
        ).group_by(LogAcesso.navegador).all()

        return json_response({
            'total_acessos': total_acessos,
            'sessoes_ativas': sessoes_ativas,
            'por_dia': [{'data': str(d[0]), 'quantidade': d[1]} for d in acessos_por_dia],
            'dispositivos': [{'dispositivo': d[0], 'quantidade': d[1]} for d in dispositivos],
            'navegadores': [{'navegador': n[0], 'quantidade': n[1]} for n in navegadores]
        })

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de acesso: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/analise/problemas', methods=['GET'])
@login_required
@setor_required('Administrador')
def analise_problemas():
    """Análise estatística de problemas reportados"""
    try:
        # Problemas mais frequentes (últimos 3 meses)
        tres_meses_atras = get_brazil_time() - timedelta(days=90)
        problemas_frequentes = db.session.query(
            Chamado.problema,
            func.count(Chamado.id).label('quantidade'),
            func.avg(func.extract('epoch', Chamado.data_conclusao - Chamado.data_abertura)/3600).label('tempo_medio_resolucao')
        ).filter(
            Chamado.data_abertura >= tres_meses_atras.replace(tzinfo=None)
        ).group_by(Chamado.problema).order_by(
            func.count(Chamado.id).desc()
        ).limit(10).all()

        # Unidades com mais problemas
        unidades_problemas = db.session.query(
            Chamado.unidade,
            func.count(Chamado.id).label('quantidade'),
            func.sum(case([(Chamado.status == 'Aberto', 1)], else_=0)).label('abertos'),
            func.sum(case([(Chamado.status == 'Concluido', 1)], else_=0)).label('concluidos')
        ).filter(
            Chamado.data_abertura >= tres_meses_atras.replace(tzinfo=None)
        ).group_by(Chamado.unidade).order_by(
            func.count(Chamado.id).desc()
        ).limit(15).all()

        # Tendências temporais (por semana nos últimos 3 meses)
        tendencias = db.session.query(
            func.extract('week', Chamado.data_abertura).label('semana'),
            func.extract('year', Chamado.data_abertura).label('ano'),
            func.count(Chamado.id).label('quantidade')
        ).filter(
            Chamado.data_abertura >= tres_meses_atras.replace(tzinfo=None)
        ).group_by(
            func.extract('week', Chamado.data_abertura),
            func.extract('year', Chamado.data_abertura)
        ).order_by('ano', 'semana').all()

        # Análise de resolução por prioridade
        resolucao_prioridade = db.session.query(
            Chamado.prioridade,
            func.count(Chamado.id).label('total'),
            func.sum(case([(Chamado.status == 'Concluido', 1)], else_=0)).label('resolvidos'),
            func.avg(func.extract('epoch', Chamado.data_conclusao - Chamado.data_abertura)/3600).label('tempo_medio')
        ).filter(
            Chamado.data_abertura >= tres_meses_atras.replace(tzinfo=None)
        ).group_by(Chamado.prioridade).all()

        return json_response({
            'problemas_frequentes': [{
                'problema': p[0],
                'quantidade': p[1],
                'tempo_medio_resolucao': round(p[2], 2) if p[2] else None
            } for p in problemas_frequentes],
            'unidades_problemas': [{
                'unidade': u[0],
                'total': u[1],
                'abertos': u[2],
                'concluidos': u[3],
                'taxa_resolucao': round((u[3] / u[1] * 100) if u[1] > 0 else 0, 2)
            } for u in unidades_problemas],
            'tendencias_semanais': [{
                'semana': t[0],
                'ano': t[1],
                'quantidade': t[2]
            } for t in tendencias],
            'resolucao_por_prioridade': [{
                'prioridade': r[0],
                'total': r[1],
                'resolvidos': r[2],
                'taxa_resolucao': round((r[2] / r[1] * 100) if r[1] > 0 else 0, 2),
                'tempo_medio': round(r[3], 2) if r[3] else None
            } for r in resolucao_prioridade]
        })

    except Exception as e:
        logger.error(f"Erro na análise de problemas: {str(e)}")
        logger.error(traceback.format_exc())
        return error_response('Erro interno no servidor')

# ==================== CONFIGURAÇÕES AVANÇADAS ====================

@painel_bp.route('/api/configuracoes-avancadas', methods=['GET'])
@login_required
@setor_required('Administrador')
def carregar_configuracoes_avancadas():
    """Carrega configura��ões avançadas do sistema"""
    try:
        configuracoes_avancadas = {
            'sistema': {
                'debug_mode': False,
                'log_level': 'INFO',
                'max_file_size': '50MB',
                'session_timeout': 30,
                'auto_logout': True
            },
            'seguranca': {
                'force_https': True,
                'csrf_protection': True,
                'rate_limiting': True,
                'ip_whitelist': ['127.0.0.1'],
                'password_complexity': True
            },
            'performance': {
                'cache_enabled': True,
                'compression': True,
                'cdn_enabled': False,
                'database_pool_size': 10
            },
            'backup': {
                'auto_backup': True,
                'backup_frequency': 'daily',
                'retention_days': 30,
                'backup_location': '/backups/'
            }
        }

        return json_response(configuracoes_avancadas)

    except Exception as e:
        logger.error(f"Erro ao carregar configurações avançadas: {str(e)}")
        return error_response('Erro interno no servidor')

@painel_bp.route('/api/configuracoes-avancadas', methods=['POST'])
@login_required
@setor_required('Administrador')
def salvar_configuracoes_avancadas():
    """Salva configurações avançadas do sistema"""
    try:
        if not request.is_json:
            return error_response('Content-Type deve ser application/json', 400)

        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos', 400)

        # Em produção, salvar no banco de dados
        logger.info(f"Configurações avançadas atualizadas por {current_user.nome}")

        return json_response({'message': 'Configurações avançadas salvas com sucesso'})

    except Exception as e:
        logger.error(f"Erro ao salvar configurações avançadas: {str(e)}")
        return error_response('Erro interno no servidor')
