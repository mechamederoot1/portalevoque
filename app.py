import os
from flask import Flask, session, request, redirect, url_for
from config import Config
from flask_login import LoginManager
from database import db, seed_unidades, User, Chamado, Unidade, ProblemaReportado, ItemInternet, HistoricoTicket, Configuracao
from setores.ti.routes import ti_bp
from auth.routes import auth_bp
from principal.routes import main_bp
from setores.compras.compras import compras_bp
from setores.financeiro.routes import financeiro_bp
from setores.manutencao.routes import manutencao
from setores.marketing.routes import marketing
from setores.produtos.routes import produtos
from setores.comercial.routes import comercial
from setores.outros.routes import outros_bp
from flask_login import LoginManager, login_required
from datetime import timedelta, datetime
from flask_socketio import SocketIO, emit
import json

# IMPORTAÇÕES DE SEGURANÇA
from security.middleware import SecurityMiddleware
from security.session_security import SessionSecurity
from security.security_config import SecurityConfig

app = Flask(
    __name__,
    template_folder='principal/templates',
    static_folder='static',
    instance_relative_config=True
)

# Carrega as configurações do objeto Config
app.config.from_object(Config)

# APLICAR CONFIGURAÇÕES DE SEGURANÇA
app.config.from_object(SecurityConfig)

# Configuração do Socket.IO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=False, 
    engineio_logger=False, 
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

# INICIALIZAR MIDDLEWARE DE SEGURANÇA
security_middleware = SecurityMiddleware(app)
session_security = SessionSecurity()

# Configura o LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Inicializa o SQLAlchemy com o app
db.init_app(app)

def add_missing_structures():
    """
    Função para adicionar tabelas e colunas faltantes automaticamente
    """
    try:
        print("🔄 Verificando estrutura do banco de dados...")

        # Criar todas as tabelas se não existirem
        db.create_all()

        print("✅ Verificação e atualização da estrutura do banco concluída!")

    except Exception as e:
        print(f"❌ Erro geral ao verificar/atualizar estrutura do banco: {str(e)}")
        return False

    return True

# MIDDLEWARE DE SEGURANÇA DE SESSÃO
@app.before_request
def security_before_request():
    """Verificações de segurança antes de cada requisição"""
    if '_session_id' not in session and request.endpoint not in ['static', None]:
        session_security.init_session()
    elif '_session_id' in session:
        if not session_security.validate_session():
            return redirect(url_for('auth.login'))

# Função para carregar usuário no Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user and user.bloqueado:
        session['bloqueado'] = True
        return None
    return user

# Adicionar socketio ao contexto da aplicação
app.socketio = socketio

# Registra blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(ti_bp, url_prefix='/ti')
app.register_blueprint(compras_bp, url_prefix='/compras')
app.register_blueprint(financeiro_bp, url_prefix='/financeiro')
app.register_blueprint(manutencao)
app.register_blueprint(marketing)
app.register_blueprint(produtos)
app.register_blueprint(comercial)
app.register_blueprint(outros_bp, url_prefix='/outros')

# CRIAR DIRETÓRIO DE LOGS SE NÃO EXISTIR
os.makedirs('logs', exist_ok=True)

# Cria as tabelas e popula dados iniciais dentro do contexto da aplicação
with app.app_context():
    try:
        # Adiciona estruturas faltantes
        if add_missing_structures():
            print("✅ Estruturas adicionais verificadas/criadas com sucesso!")
        else:
            print("⚠️  Algumas estruturas podem não ter sido criadas corretamente.")
        
        # INICIALIZAR SISTEMA DE SEGURANÇA
        print("🔒 Inicializando sistema de segurança...")
        print("✅ Middleware de segurança ativo")
        print("✅ Rate limiting configurado")
        print("✅ Validação de entrada ativa")
        print("✅ Headers de segurança configurados")
        print("✅ Sistema de auditoria ativo")
        print("✅ Proteção de sessão ativa")
            
    except Exception as e:
        print(f"❌ Erro durante a inicialização do banco: {str(e)}")
        print("⚠️  Verifique se:")
        print("   - O servidor MySQL está acessível")
        print("   - As credenciais estão corretas")

# Eventos Socket.IO
@socketio.on('connect')
def handle_connect():
    print(f'Cliente conectado: {request.sid}')
    emit('connected', {
        'message': 'Conectado ao servidor Socket.IO',
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Cliente desconectado: {request.sid}')

@socketio.on('join_admin')
def handle_join_admin(data):
    print(f'Admin {data.get("user_id")} entrou na sala de administradores')
    emit('admin_joined', {
        'message': 'Você está recebendo notificações administrativas',
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('test_notification')
def handle_test_notification():
    emit('notification_test', {
        'message': 'Teste de notificação realizado com sucesso!',
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

@socketio.on('ping')
def handle_ping():
    emit('pong', {'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Iniciando aplicação com proteções de segurança ativas...")
    print("🔌 Socket.IO configurado e ativo")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
