import os
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from auth.auth_helpers import setor_required
from database import db, Chamado, User, Unidade, ProblemaReportado, ItemInternet, seed_unidades, get_brazil_time
import requests
from msal import ConfidentialClientApplication

ti_bp = Blueprint('ti', __name__, template_folder='templates')

# Configurações do Microsoft Graph API obtidas das variáveis de ambiente
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
USER_ID = os.getenv('USER_ID')
EMAIL_TI = os.getenv('EMAIL_TI', 'ti@academiaevoque.com.br')

# Verificar se as variáveis de ambiente estão configuradas (não obrigatórias para desenvolvimento)
EMAIL_ENABLED = all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, USER_ID])

if EMAIL_ENABLED:
    SCOPES = ["https://graph.microsoft.com/.default"]
    ENDPOINT = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/sendMail"
    print("✅ Configurações de email Microsoft Graph carregadas")
else:
    SCOPES = []
    ENDPOINT = None
    print("⚠️  Email desabilitado: Variáveis de ambiente do Microsoft Graph não configuradas")

def get_access_token():
    if not EMAIL_ENABLED:
        current_app.logger.warning("⚠️  Tentativa de obter token com email desabilitado")
        return None

    try:
        app = ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}"
        )
        result = app.acquire_token_for_client(scopes=SCOPES)

        if "access_token" in result:
            current_app.logger.info("✅ Token obtido com sucesso!")
            return result["access_token"]
        else:
            current_app.logger.error(f"❌ Erro ao obter token: {result.get('error')}")
            return None
    except Exception as e:
        current_app.logger.error(f"❌ Exceção ao obter token: {str(e)}")
        return None

def enviar_email(assunto, corpo, destinatarios=None):
    if destinatarios is None:
        destinatarios = [EMAIL_TI]

    token = get_access_token()
    if not token:
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    email_data = {
        "message": {
            "subject": assunto,
            "body": {
                "contentType": "Text",
                "content": corpo
            },
            "toRecipients": [
                {"emailAddress": {"address": addr}} for addr in destinatarios
            ]
        },
        "saveToSentItems": "false"
    }

    try:
        response = requests.post(ENDPOINT, headers=headers, json=email_data)
        if response.status_code == 202:
            current_app.logger.info("🎉 E-mail enviado com sucesso!")
            return True
        else:
            current_app.logger.error(f"❌ Falha ao enviar e-mail. Status: {response.status_code}")
            return False
    except Exception as e:
        current_app.logger.error(f"❌ Erro na requisição: {str(e)}")
        return False

def gerar_codigo_chamado():
    ultimo_chamado = Chamado.query.order_by(Chamado.id.desc()).first()
    if ultimo_chamado and ultimo_chamado.codigo.startswith("EVQ-"):
        try:
            ultimo_numero = int(ultimo_chamado.codigo.split("-")[1])
        except:
            ultimo_numero = 0
    else:
        ultimo_numero = 0
    
    novo_numero = ultimo_numero + 1
    numero_formatado = str(novo_numero).zfill(4)
    return f"EVQ-{numero_formatado}"

def gerar_protocolo():
    # Usar horário do Brasil para gerar protocolo
    data_brazil = get_brazil_time()
    data_str = data_brazil.strftime("%Y%m%d")
    count = Chamado.query.filter(Chamado.protocolo.like(f"{data_str}-%")).count()
    novo_num = count + 1
    return f"{data_str}-{novo_num}"

@ti_bp.route('/')
@login_required
@setor_required('ti')
def index():
    try:
        # Buscar chamados do usuário logado usando o relacionamento
        meus_chamados = Chamado.query.filter_by(usuario_id=current_user.id).order_by(Chamado.data_abertura.desc()).all()
        
        # Se não encontrar chamados pelo usuario_id, buscar pelo email (fallback para dados antigos)
        if not meus_chamados:
            meus_chamados = Chamado.query.filter_by(email=current_user.email).order_by(Chamado.data_abertura.desc()).all()
            
            # Vincular esses chamados ao usuário atual
            for chamado in meus_chamados:
                if not chamado.usuario_id:
                    chamado.usuario_id = current_user.id
            
            if meus_chamados:
                db.session.commit()
        
        return render_template('index.html', meus_chamados=meus_chamados)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados do usuário: {str(e)}")
        flash("Ocorreu um erro ao carregar seu histórico de chamados.", "danger")
        return render_template('index.html', meus_chamados=[])

@ti_bp.route('/painel')
@login_required
@setor_required('ti')
def painel():
    if not current_user.tem_permissao('Administrador'):
        flash('Você não tem permissão para acessar o painel administrativo.', 'danger')
        return redirect(url_for('ti.index'))
    return render_template('painel.html')

@ti_bp.route('/abrir-chamado', methods=['GET', 'POST'])
@login_required
@setor_required('ti')
def abrir_chamado():
    try:
        unidades = Unidade.query.order_by(Unidade.nome).all()
        problemas = ProblemaReportado.query.filter_by(ativo=True).order_by(ProblemaReportado.nome).all()
        itens_internet = ItemInternet.query.filter_by(ativo=True).order_by(ItemInternet.nome).all()
        
        if not unidades:
            seed_unidades()
            unidades = Unidade.query.order_by(Unidade.nome).all()
            problemas = ProblemaReportado.query.filter_by(ativo=True).order_by(ProblemaReportado.nome).all()
            itens_internet = ItemInternet.query.filter_by(ativo=True).order_by(ItemInternet.nome).all()
            
        if request.method == 'POST':
            try:
                codigo_gerado = gerar_codigo_chamado()
                protocolo_gerado = gerar_protocolo()

                dados_chamado = {
                    'nome_solicitante': request.form['nome_solicitante'],
                    'cargo': request.form['cargo'],
                    'email': request.form['email'],
                    'telefone': request.form['telefone'],
                    'unidade_id': request.form['unidade'],
                    'problema_id': request.form['problema'],
                    'internet_item_id': request.form.get('internet_item', ''),
                    'descricao': request.form.get('descricao', ''),
                    'data_visita_str': request.form.get('data_visita', '').strip(),
                    'prioridade': request.form.get('prioridade', 'Normal')
                }

                unidade_obj = Unidade.query.get(dados_chamado['unidade_id'])
                problema_obj = ProblemaReportado.query.get(dados_chamado['problema_id'])
                
                if not unidade_obj or not problema_obj:
                    return jsonify({
                        'status': 'error',
                        'message': 'Unidade ou problema inválido.'
                    }), 400

                unidade_nome_completo = unidade_obj.nome
                problema_nome = problema_obj.nome
                
                internet_item_nome = ""
                if dados_chamado['internet_item_id']:
                    item_obj = ItemInternet.query.get(dados_chamado['internet_item_id'])
                    internet_item_nome = item_obj.nome if item_obj else ""

                data_visita = None
                if dados_chamado['data_visita_str']:
                    try:
                        data_visita = datetime.strptime(dados_chamado['data_visita_str'], '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({
                            'status': 'error',
                            'message': 'Formato de data inválido. Use AAAA-MM-DD.'
                        }), 400

                descricao_completa = dados_chamado['descricao']
                if problema_nome == 'Internet' and internet_item_nome:
                    descricao_completa = f"Item: {internet_item_nome}\nDescrição: {descricao_completa}"

                # Usar horário do Brasil para data de abertura
                data_abertura_brazil = get_brazil_time()

                novo_chamado = Chamado(
                    codigo=codigo_gerado,
                    protocolo=protocolo_gerado,
                    solicitante=dados_chamado['nome_solicitante'],
                    cargo=dados_chamado['cargo'],
                    email=dados_chamado['email'],
                    telefone=dados_chamado['telefone'],
                    unidade=unidade_nome_completo,
                    problema=problema_nome,
                    internet_item=internet_item_nome,
                    descricao=descricao_completa,
                    data_visita=data_visita,
                    status='Aberto',
                    prioridade=dados_chamado['prioridade'],
                    data_abertura=data_abertura_brazil.replace(tzinfo=None),
                    usuario_id=current_user.id  # Vincular ao usuário logado
                )

                db.session.add(novo_chamado)
                db.session.commit()

                if hasattr(current_app, 'socketio'):
                    current_app.socketio.emit('novo_chamado', {
                        'id': novo_chamado.id,
                        'codigo': codigo_gerado,
                        'protocolo': protocolo_gerado,
                        'solicitante': dados_chamado['nome_solicitante'],
                        'problema': problema_nome,
                        'unidade': unidade_nome_completo,
                        'status': 'Aberto',
                        'data_abertura': data_abertura_brazil.isoformat(),
                        'prioridade': dados_chamado['prioridade']
                    })

                visita_tecnica_texto = (
                    f"Sim, agendada para {data_visita.strftime('%d/%m/%Y')}"
                    if data_visita else "Não requisitada"
                )

                internet_item_texto = (
                    f"\nItem de Internet: {internet_item_nome}"
                    if problema_nome == 'Internet' and internet_item_nome
                    else ""
                )

                corpo_email = f"""
Seu chamado foi registrado com sucesso! Aqui estão os detalhes:

Chamado: {codigo_gerado}
Protocolo: {protocolo_gerado}
Prioridade: {dados_chamado['prioridade']}
Nome do solicitante: {dados_chamado['nome_solicitante']}
Cargo: {dados_chamado['cargo']}
Unidade: {unidade_nome_completo}
E-mail: {dados_chamado['email']}
Telefone: {dados_chamado['telefone']}
Problema reportado: {problema_nome}{internet_item_texto}
Descrição: {dados_chamado['descricao']}
Visita técnica: {visita_tecnica_texto}

⚠️ Caso precise acompanhar o status do chamado, utilize o código acima.

Atenciosamente,
Suporte Evoque!

Por favor, não responda este e-mail, essa é uma mensagem automática!
"""
                destinatarios = [dados_chamado['email'], EMAIL_TI]
                assunto_email = f"ACADEMIA EVOQUE - CHAMADO #{codigo_gerado}"

                sucesso_email = enviar_email(assunto_email, corpo_email, destinatarios)
                if not sucesso_email:
                    current_app.logger.warning(f"Falha ao enviar e-mail para o chamado {codigo_gerado}")

                return jsonify({
                    'status': 'success',
                    'codigo_chamado': codigo_gerado,
                    'protocolo_chamado': protocolo_gerado,
                    'notificacao_data': {
                        'id': novo_chamado.id,
                        'codigo': codigo_gerado,
                        'solicitante': dados_chamado['nome_solicitante'],
                        'problema': problema_nome,
                        'data_abertura': data_abertura_brazil.strftime('%d/%m/%Y %H:%M:%S')
                    }
                })

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao salvar chamado: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Erro ao abrir chamado. Tente novamente.'
                }), 500

        # Pré-preencher dados do usuário logado
        usuario_data = {
            'nome': f"{current_user.nome} {current_user.sobrenome}",
            'email': current_user.email
        }

        return render_template('abrir_chamado.html', 
                             unidades=unidades, 
                             problemas=problemas, 
                             itens_internet=itens_internet,
                             usuario_data=usuario_data)
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao processar página de chamados: {str(e)}")
        return render_template('abrir_chamado.html', unidades=[], problemas=[], itens_internet=[], 
                              error_message="Erro ao carregar unidades. Por favor, tente novamente mais tarde.")

@ti_bp.route('/api/meus-chamados')
@login_required
@setor_required('ti')
def api_meus_chamados():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 5  # 5 itens por página
        
        # Buscar chamados do usuário logado com paginação
        chamados_query = Chamado.query.filter_by(usuario_id=current_user.id).order_by(Chamado.data_abertura.desc())
        
        # Se não encontrar pelo usuario_id, buscar pelo email (fallback)
        if chamados_query.count() == 0:
            chamados_query = Chamado.query.filter_by(email=current_user.email).order_by(Chamado.data_abertura.desc())
        
        chamados_paginados = chamados_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        chamados_list = []
        for chamado in chamados_paginados.items:
            data_abertura_brazil = chamado.get_data_abertura_brazil()
            chamados_list.append({
                'id': chamado.id,
                'codigo': chamado.codigo,
                'protocolo': chamado.protocolo,
                'solicitante': chamado.solicitante,
                'problema': chamado.problema,
                'unidade': chamado.unidade,
                'status': chamado.status,
                'prioridade': chamado.prioridade,
                'data_abertura': data_abertura_brazil.strftime('%d/%m/%Y %H:%M') if data_abertura_brazil else 'Não informado',
                'descricao': chamado.descricao or 'Sem descrição',
                'data_visita': chamado.data_visita.strftime('%d/%m/%Y') if chamado.data_visita else None
            })
        
        return jsonify({
            'chamados': chamados_list,
            'pagination': {
                'page': chamados_paginados.page,
                'pages': chamados_paginados.pages,
                'per_page': chamados_paginados.per_page,
                'total': chamados_paginados.total,
                'has_next': chamados_paginados.has_next,
                'has_prev': chamados_paginados.has_prev
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados do usuário: {str(e)}")
        return jsonify({'error': 'Erro interno no servidor'}), 500

@ti_bp.route('/ver-meus-chamados', methods=['GET', 'POST'])
@login_required
@setor_required('ti')
def ver_meus_chamados():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        
        if not codigo:
            return jsonify({
                'status': 'error',
                'message': 'Código não informado.'
            }), 400

        if not codigo.startswith('EVQ-'):
            codigo = f"EVQ-{codigo.zfill(4)}"

        try:
            # Buscar chamado do usuário logado
            chamado = Chamado.query.filter_by(
                codigo=codigo, 
                usuario_id=current_user.id
            ).first()
            
            # Se não encontrar pelo usuario_id, buscar pelo email (fallback)
            if not chamado:
                chamado = Chamado.query.filter_by(
                    codigo=codigo,
                    email=current_user.email
                ).first()
            
            if not chamado:
                return jsonify({
                    'status': 'error',
                    'message': 'Chamado não encontrado ou você não tem permissão para visualizá-lo.'
                }), 404

            # Converter data de abertura para timezone do Brasil
            data_abertura_brazil = chamado.get_data_abertura_brazil()
            data_abertura_str = data_abertura_brazil.strftime('%d/%m/%Y %H:%M') if data_abertura_brazil else 'Não informado'

            resultado = {
                'tipo': 'chamado',
                'codigo_chamado': chamado.codigo,
                'protocolo': chamado.protocolo,
                'prioridade': chamado.prioridade,
                'status': chamado.status,
                'nome_solicitante': chamado.solicitante,
                'email': chamado.email or 'Não informado',
                'cargo': chamado.cargo,
                'telefone': chamado.telefone or 'Não informado',
                'unidade': chamado.unidade or 'Não informado',
                'problema_reportado': chamado.problema,
                'internet_item': chamado.internet_item or 'Não informado',
                'descricao': chamado.descricao or 'Sem descrição',
                'data_abertura': data_abertura_str,
                'visita_tecnica': 'Sim' if chamado.data_visita else 'Não requisitada',
                'data_visita_tecnica': chamado.data_visita.strftime('%d/%m/%Y') if chamado.data_visita else 'Não agendada',
            }
            
            return jsonify({
                'status': 'success',
                'resultado': resultado
            })

        except Exception as e:
            current_app.logger.error(f"Erro ao buscar chamado: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Erro interno no servidor.'
            }), 500

    return render_template('ver_meus_chamados.html')

@ti_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@ti_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

from .painel import painel_bp
ti_bp.register_blueprint(painel_bp, url_prefix='/painel')

# Registrar blueprints de agentes, grupos, auditoria e rotas avançadas
from .agentes import agentes_bp
from .grupos import grupos_bp
from .auditoria import auditoria_bp
from .rotas import rotas_bp
ti_bp.register_blueprint(agentes_bp, url_prefix='/painel')
ti_bp.register_blueprint(grupos_bp, url_prefix='/painel')
ti_bp.register_blueprint(auditoria_bp, url_prefix='/painel')
ti_bp.register_blueprint(rotas_bp, url_prefix='/painel')

@ti_bp.route('/api/chamados/recentes')
@login_required
@setor_required('ti')
def chamados_recentes():
    try:
        cinco_minutos_atras = get_brazil_time() - timedelta(minutes=5)
        chamados_recentes = Chamado.query.filter(
            Chamado.data_abertura >= cinco_minutos_atras.replace(tzinfo=None)
        ).order_by(Chamado.data_abertura.desc()).all()
        
        chamados_list = []
        for c in chamados_recentes:
            data_abertura_brazil = c.get_data_abertura_brazil()
            chamados_list.append({
                'id': c.id,
                'codigo': c.codigo,
                'solicitante': c.solicitante,
                'problema': c.problema,
                'data_abertura': data_abertura_brazil.strftime('%d/%m/%Y %H:%M:%S') if data_abertura_brazil else None,
                'status': c.status
            })
        
        return jsonify(chamados_list)
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar chamados recentes: {str(e)}")
        return jsonify({'error': 'Erro interno no servidor'}), 500
               
@ti_bp.route('/ajuda')
@login_required
@setor_required('ti')
def ajuda():
    faqs = [
        ("Como abrir um novo chamado?", 
         "<ol><li>Acesse o menu 'Abrir Chamado'</li><li>Preencha todos os campos obrigatórios</li><li>Clique em 'Enviar'</li><li>Anote o número do protocolo para acompanhamento</li></ol>"),
        ("Como acompanhar um chamado existente?", 
         "<ol><li>Acesse o menu 'Meus Chamados'</li><li>Digite o número do protocolo</li><li>Clique em 'Buscar'</li><li>Você verá o status atual e histórico</li></ol>"),
        ("O que fazer se esquecer o número do protocolo?", 
         "<ul><li>Verifique seu e-mail - enviamos uma confirmação</li><li>Contate o suporte TI com seus dados</li><li>Forneça data aproximada e detalhes do problema</li></ul>"),
        ("Quanto tempo leva para um chamado ser atendido?", 
         "<p>O tempo varia conforme a prioridade:</p><ul><li><strong>Crítico</strong>: 1 hora</li><li><strong>Alta</strong>: 4 horas</li><li><strong>Normal</strong>: 24 horas</li><li><strong>Baixa</strong>: 72 horas</li></ul>"),
        ("Como classificar a prioridade do meu chamado?", 
         "<p>Use estas diretrizes:</p><ul><li><strong>Crítico</strong>: Sistema totalmente inoperante</li><li><strong>Alta</strong>: Funcionalidade principal afetada</li><li><strong>Normal</strong>: Problema não impede operação</li><li><strong>Baixa</strong>: Dúvida ou melhoria</li></ul>"),
        ("Posso anexar arquivos ao chamado?", 
         "<p>Sim, na versão premium do sistema. Atualmente você pode:</p><ul><li>Descrever detalhadamente o problema</li><li>Incluir prints na descrição</li><li>Enviar arquivos posteriormente por e-mail</li></ul>")
    ]
    return render_template('ajuda.html', faqs=faqs)
