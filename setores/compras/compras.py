from flask import Blueprint, render_template, current_app
from flask_login import login_required
from auth.auth_helpers import setor_required
from datetime import datetime
import os

compras_bp = Blueprint(
    'compras',
    __name__,
    template_folder='templates'
)

@compras_bp.route('/')
@login_required
@setor_required('Compras')  # Ajuste para 'Compras' com maiúscula, consistente com setor definido
def index():
    try:
        # Debug: mostrar o caminho do template
        base_path = os.path.dirname(__file__)
        templates_path = os.path.join(base_path, 'templates')
        current_app.logger.info(f"Procurando templates em: {templates_path}")
        
        if os.path.exists(templates_path):
            for root, dirs, files in os.walk(templates_path):
                current_app.logger.info(f"Pasta: {root}, Arquivos: {files}")
        else:
            current_app.logger.warning(f"Pasta de templates não encontrada: {templates_path}")
        
        return render_template('compras/index.html', current_year=datetime.now().year)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao renderizar template: {str(e)}")
        return f"""
        <h1>Debug - Erro no Template</h1>
        <p>Erro: {str(e)}</p>
        <p>Verifique se o arquivo está em: /setores/compras/templates/compras/index.html</p>
        <a href="{url_for('main.index')}">Voltar</a>
        """
