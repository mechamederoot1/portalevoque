from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from auth.auth_helpers import setor_required
from datetime import datetime, date
from database import db, SolicitacaoCompra, User
from setores.ti.email_service import email_service
from jinja2 import Template
import os

compras_bp = Blueprint(
    'compras',
    __name__,
    template_folder='templates'
)

@compras_bp.route('/')
@login_required
@setor_required('Compras')
def index():
    try:
        return render_template('compras/index.html', current_year=datetime.now().year)
    except Exception as e:
        current_app.logger.error(f"Erro ao renderizar template de compras: {str(e)}")
        return redirect(url_for('main.index'))

@compras_bp.route('/nova-solicitacao')
@login_required
@setor_required('Compras')
def nova_solicitacao():
    """P��gina para criar nova solicitação de compra"""
    return render_template('compras/nova_solicitacao.html')

@compras_bp.route('/solicitacoes')
@login_required
@setor_required('Compras')
def solicitacoes():
    """Página de listagem de solicitações"""
    return render_template('compras/acompanhar_pedidos.html')

@compras_bp.route('/acompanhar-pedidos')
@login_required
@setor_required('Compras')
def acompanhar_pedidos():
    """Página para acompanhar pedidos de compra"""
    return render_template('compras/acompanhar_pedidos.html')

@compras_bp.route('/fornecedores')
@login_required
@setor_required('Compras')
def fornecedores():
    """Página de gerenciamento de fornecedores"""
    return render_template('compras/fornecedores.html')

@compras_bp.route('/relatorios')
@login_required
@setor_required('Compras')
def relatorios():
    """Página de relatórios de compras"""
    return render_template('compras/relatorios.html')

@compras_bp.route('/api/solicitacao', methods=['POST'])
@login_required
@setor_required('Compras')
def criar_solicitacao():
    """API para criar nova solicitação de compra"""
    try:
        dados = request.get_json()

        # Validar dados obrigatórios
        campos_obrigatorios = ['produto', 'quantidade', 'justificativa']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400

        # Aqui você pode implementar a lógica para salvar no banco
        # Por enquanto, apenas simular o sucesso

        current_app.logger.info(f'Nova solicitação de compra criada pelo usuário {current_user.usuario}')

        return jsonify({
            'sucesso': True,
            'mensagem': 'Solicitação criada com sucesso!',
            'protocolo': f'COMP-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        })

    except Exception as e:
        current_app.logger.error(f'Erro ao criar solicitação: {str(e)}')
        return jsonify({'erro': 'Erro interno do servidor'}), 500
