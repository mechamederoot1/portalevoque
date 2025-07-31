from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json
import os
import pytz

db = SQLAlchemy()

# Configurar timezone do Brasil
BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')

def get_brazil_time():
    """Retorna o horário atual do Brasil (São Paulo)"""
    return datetime.now(BRAZIL_TZ)

def utc_to_brazil(utc_datetime):
    """Converte datetime UTC para horário do Brasil"""
    if utc_datetime is None:
        return None
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.utc.localize(utc_datetime)
    return utc_datetime.astimezone(BRAZIL_TZ)

def brazil_to_utc(brazil_datetime):
    """Converte datetime do Brasil para UTC"""
    if brazil_datetime is None:
        return None
    if brazil_datetime.tzinfo is None:
        brazil_datetime = BRAZIL_TZ.localize(brazil_datetime)
    return brazil_datetime.astimezone(pytz.utc)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    sobrenome = db.Column(db.String(150), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    alterar_senha_primeiro_acesso = db.Column(db.Boolean, default=False)
    nivel_acesso = db.Column(db.String(50), nullable=False)
    setor = db.Column(db.String(255), nullable=True)
    _setores = db.Column(db.Text, nullable=True)
    bloqueado = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    ultimo_acesso = db.Column(db.DateTime, nullable=True)
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)

    # Relacionamento com chamados
    chamados = db.relationship('Chamado', backref='usuario_criador', lazy=True, foreign_keys='Chamado.usuario_id')
    
    # Relacionamentos com logs
    logs_acesso = db.relationship('LogAcesso', backref='usuario', lazy=True)
    logs_acoes = db.relationship('LogAcao', backref='usuario', lazy=True)
    
    # Relacionamento com alertas resolvidos
    alertas_resolvidos = db.relationship('AlertaSistema', backref='resolvido_por_usuario', lazy=True, foreign_keys='AlertaSistema.resolvido_por')
    
    # Relacionamento com backups
    backups_criados = db.relationship('BackupHistorico', backref='usuario', lazy=True)

    @property
    def setores(self):
        if self._setores:
            try:
                return json.loads(self._setores)
            except:
                return [self._setores] if self._setores else []
        return [self.setor] if self.setor else []
    
    @setores.setter
    def setores(self, value):
        if isinstance(value, list):
            self._setores = json.dumps(value)
            self.setor = value[0] if value else None
        elif value:
            self._setores = json.dumps([value])
            self.setor = value

    def tem_acesso_setor(self, setor_url):
        if self.nivel_acesso == 'Administrador':
            return True
            
        mapeamento_setores = {
            'ti': 'TI',
            'compras': 'Compras',
            'manutencao': 'Manutencao',
            'financeiro': 'Financeiro',
            'marketing': 'Marketing',
            'produtos': 'Produtos',
            'comercial': 'Comercial',
            'servicos': 'Outros'
        }
        
        setor_valor = mapeamento_setores.get(setor_url)
        if not setor_valor:
            return False
            
        setores_usuario = self.setores
        return setor_valor in setores_usuario

    def tem_permissao(self, permissao_necessaria):
        niveis_acesso = {
            'Administrador': ['Administrador'],
            'Gerente': ['Administrador', 'Gerente'],
            'Gerente Regional': ['Administrador', 'Gerente', 'Gerente Regional'],
            'Gestor': ['Administrador', 'Gerente', 'Gerente Regional', 'Gestor']
        }
        
        return self.nivel_acesso in niveis_acesso.get(permissao_necessaria, [])

    def __repr__(self):
        return f'<User {self.usuario} - {self.email}>'

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.senha_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha_hash, password)

class Chamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    protocolo = db.Column(db.String(20), unique=True, nullable=False)
    solicitante = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    unidade = db.Column(db.String(100), nullable=False)
    problema = db.Column(db.String(100), nullable=False)
    internet_item = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    data_visita = db.Column(db.Date, nullable=True)
    data_abertura = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_primeira_resposta = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Aberto')
    prioridade = db.Column(db.String(20), default='Normal')
    
    # Nova coluna para vincular ao usuário
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def get_data_abertura_brazil(self):
        """Retorna data de abertura no timezone do Brasil"""
        if self.data_abertura:
            if self.data_abertura.tzinfo:
                return self.data_abertura.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_abertura).astimezone(BRAZIL_TZ)
        return None

    def get_data_primeira_resposta_brazil(self):
        """Retorna data de primeira resposta no timezone do Brasil"""
        if self.data_primeira_resposta:
            if self.data_primeira_resposta.tzinfo:
                return self.data_primeira_resposta.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_primeira_resposta).astimezone(BRAZIL_TZ)
        return None

    def get_data_conclusao_brazil(self):
        """Retorna data de conclusão no timezone do Brasil"""
        if self.data_conclusao:
            if self.data_conclusao.tzinfo:
                return self.data_conclusao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_conclusao).astimezone(BRAZIL_TZ)
        return None

    def __repr__(self):
        return (
            f'<Chamado {self.codigo} | Protocolo: {self.protocolo} | '
            f'Solicitante: {self.solicitante} | Unidade: {self.unidade} | '
            f'Problema: {self.problema} | Status: {self.status}>'
        )

class Unidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))

    def __repr__(self):
        return f'<Unidade {self.nome}>'

class ProblemaReportado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    prioridade_padrao = db.Column(db.String(20), default='Normal')
    requer_item_internet = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ProblemaReportado {self.nome}>'

class ItemInternet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ItemInternet {self.nome}>'

class HistoricoTicket(db.Model):
    __tablename__ = 'historicos_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assunto = db.Column(db.String(255), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    destinatarios = db.Column(db.String(255), nullable=False)
    data_envio = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    
    chamado = db.relationship('Chamado', backref='tickets_enviados')
    usuario = db.relationship('User', backref='tickets_enviados')

    def __repr__(self):
        return f'<HistoricoTicket {self.id} - Chamado {self.chamado_id}>'

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    data_atualizacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))

    def __repr__(self):
        return f'<Configuracao {self.chave}>'

# ==================== TABELAS PARA FUNCIONALIDADES AVANÇADAS ====================

class LogAcesso(db.Model):
    """Tabela para registrar acessos dos usuários"""
    __tablename__ = 'logs_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_acesso = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_logout = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    user_agent = db.Column(db.Text, nullable=True)
    duracao_sessao = db.Column(db.Integer, nullable=True)  # em minutos
    ativo = db.Column(db.Boolean, default=True)
    session_id = db.Column(db.String(255), nullable=True)
    navegador = db.Column(db.String(100), nullable=True)
    sistema_operacional = db.Column(db.String(100), nullable=True)
    dispositivo = db.Column(db.String(50), nullable=True)  # desktop, mobile, tablet

    def get_data_acesso_brazil(self):
        """Retorna data de acesso no timezone do Brasil"""
        if self.data_acesso:
            if self.data_acesso.tzinfo:
                return self.data_acesso.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_acesso).astimezone(BRAZIL_TZ)
        return None

    def get_data_logout_brazil(self):
        """Retorna data de logout no timezone do Brasil"""
        if self.data_logout:
            if self.data_logout.tzinfo:
                return self.data_logout.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_logout).astimezone(BRAZIL_TZ)
        return None

    def calcular_duracao(self):
        """Calcula duração da sessão em minutos"""
        if self.data_logout and self.data_acesso:
            delta = self.data_logout - self.data_acesso
            return int(delta.total_seconds() / 60)
        return None

    def __repr__(self):
        return f'<LogAcesso {self.usuario_id} - {self.data_acesso}>'

class LogAcao(db.Model):
    """Tabela para registrar ações dos usuários"""
    __tablename__ = 'logs_acoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acao = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(100), nullable=True)  # login, chamado, usuario, configuracao, etc
    detalhes = db.Column(db.Text, nullable=True)
    dados_anteriores = db.Column(db.Text, nullable=True)  # JSON com dados antes da alteração
    dados_novos = db.Column(db.Text, nullable=True)  # JSON com dados após alteração
    data_acao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    sucesso = db.Column(db.Boolean, default=True)
    erro_detalhes = db.Column(db.Text, nullable=True)
    recurso_afetado = db.Column(db.String(255), nullable=True)  # ID do recurso afetado
    tipo_recurso = db.Column(db.String(100), nullable=True)  # tipo do recurso (chamado, usuario, etc)

    def get_data_acao_brazil(self):
        """Retorna data da ação no timezone do Brasil"""
        if self.data_acao:
            if self.data_acao.tzinfo:
                return self.data_acao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_acao).astimezone(BRAZIL_TZ)
        return None

    def __repr__(self):
        return f'<LogAcao {self.acao} - {self.data_acao}>'

class ConfiguracaoAvancada(db.Model):
    """Tabela para configurações avançadas do sistema"""
    __tablename__ = 'configuracoes_avancadas'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(20), default='string')  # string, number, boolean, json
    categoria = db.Column(db.String(50), nullable=True)  # sistema, backup, alertas, performance
    requer_reinicio = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_atualizacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    usuario_atualizacao = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def get_data_criacao_brazil(self):
        """Retorna data de criação no timezone do Brasil"""
        if self.data_criacao:
            if self.data_criacao.tzinfo:
                return self.data_criacao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_criacao).astimezone(BRAZIL_TZ)
        return None

    def get_data_atualizacao_brazil(self):
        """Retorna data de atualização no timezone do Brasil"""
        if self.data_atualizacao:
            if self.data_atualizacao.tzinfo:
                return self.data_atualizacao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_atualizacao).astimezone(BRAZIL_TZ)
        return None

    def get_valor_tipado(self):
        """Retorna valor convertido para o tipo correto"""
        if self.tipo == 'boolean':
            return self.valor.lower() in ['true', '1', 'yes', 'on']
        elif self.tipo == 'number':
            try:
                if '.' in self.valor:
                    return float(self.valor)
                return int(self.valor)
            except ValueError:
                return 0
        elif self.tipo == 'json':
            try:
                return json.loads(self.valor)
            except json.JSONDecodeError:
                return {}
        return self.valor

    def __repr__(self):
        return f'<ConfiguracaoAvancada {self.chave}>'

class AlertaSistema(db.Model):
    """Tabela para alertas do sistema"""
    __tablename__ = 'alertas_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # sistema, seguranca, performance, backup, etc.
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    severidade = db.Column(db.String(20), default='media')  # baixa, media, alta, critica
    categoria = db.Column(db.String(100), nullable=True)
    resolvido = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_resolucao = db.Column(db.DateTime, nullable=True)
    resolvido_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    observacoes_resolucao = db.Column(db.Text, nullable=True)
    automatico = db.Column(db.Boolean, default=False)  # Se foi criado automaticamente
    dados_contexto = db.Column(db.Text, nullable=True)  # JSON com dados adicionais
    contador_ocorrencias = db.Column(db.Integer, default=1)
    ultima_ocorrencia = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))

    def get_data_criacao_brazil(self):
        """Retorna data de criação no timezone do Brasil"""
        if self.data_criacao:
            if self.data_criacao.tzinfo:
                return self.data_criacao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_criacao).astimezone(BRAZIL_TZ)
        return None

    def get_data_resolucao_brazil(self):
        """Retorna data de resolução no timezone do Brasil"""
        if self.data_resolucao:
            if self.data_resolucao.tzinfo:
                return self.data_resolucao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_resolucao).astimezone(BRAZIL_TZ)
        return None

    def get_ultima_ocorrencia_brazil(self):
        """Retorna data da última ocorrência no timezone do Brasil"""
        if self.ultima_ocorrencia:
            if self.ultima_ocorrencia.tzinfo:
                return self.ultima_ocorrencia.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.ultima_ocorrencia).astimezone(BRAZIL_TZ)
        return None

    def incrementar_ocorrencia(self):
        """Incrementa contador de ocorrências e atualiza última ocorrência"""
        self.contador_ocorrencias += 1
        self.ultima_ocorrencia = get_brazil_time().replace(tzinfo=None)

    def __repr__(self):
        return f'<AlertaSistema {self.titulo} - {self.severidade}>'

class BackupHistorico(db.Model):
    """Tabela para histórico de backups"""
    __tablename__ = 'backup_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=True)
    tamanho_mb = db.Column(db.Float, nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # completo, dados, configuracoes, logs
    status = db.Column(db.String(20), default='em_progresso')  # em_progresso, concluido, erro, cancelado
    data_backup = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_inicio = db.Column(db.DateTime, nullable=True)
    data_fim = db.Column(db.DateTime, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    erro_detalhes = db.Column(db.Text, nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    automatico = db.Column(db.Boolean, default=False)
    hash_arquivo = db.Column(db.String(64), nullable=True)  # SHA256 do arquivo
    compressao = db.Column(db.String(20), nullable=True)  # gzip, zip, etc
    tabelas_incluidas = db.Column(db.Text, nullable=True)  # JSON com lista de tabelas
    registros_total = db.Column(db.Integer, nullable=True)
    tempo_execucao = db.Column(db.Integer, nullable=True)  # em segundos

    def get_data_backup_brazil(self):
        """Retorna data do backup no timezone do Brasil"""
        if self.data_backup:
            if self.data_backup.tzinfo:
                return self.data_backup.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_backup).astimezone(BRAZIL_TZ)
        return None

    def get_data_inicio_brazil(self):
        """Retorna data de início no timezone do Brasil"""
        if self.data_inicio:
            if self.data_inicio.tzinfo:
                return self.data_inicio.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_inicio).astimezone(BRAZIL_TZ)
        return None

    def get_data_fim_brazil(self):
        """Retorna data de fim no timezone do Brasil"""
        if self.data_fim:
            if self.data_fim.tzinfo:
                return self.data_fim.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_fim).astimezone(BRAZIL_TZ)
        return None

    def calcular_duracao(self):
        """Calcula duração do backup em segundos"""
        if self.data_fim and self.data_inicio:
            delta = self.data_fim - self.data_inicio
            return int(delta.total_seconds())
        return None

    def __repr__(self):
        return f'<BackupHistorico {self.nome_arquivo} - {self.status}>'

class RelatorioGerado(db.Model):
    """Tabela para histórico de relatórios gerados"""
    __tablename__ = 'relatorios_gerados'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_relatorio = db.Column(db.String(255), nullable=False)
    tipo_relatorio = db.Column(db.String(100), nullable=False)  # usuarios, chamados, sla, auditoria
    formato = db.Column(db.String(20), nullable=False)  # pdf, csv, excel
    parametros = db.Column(db.Text, nullable=True)  # JSON com parâmetros do relatório
    nome_arquivo = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=True)
    tamanho_kb = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='gerando')  # gerando, concluido, erro
    data_geracao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_conclusao = db.Column(db.DateTime, nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    erro_detalhes = db.Column(db.Text, nullable=True)
    registros_processados = db.Column(db.Integer, nullable=True)
    tempo_execucao = db.Column(db.Integer, nullable=True)  # em segundos

    def get_data_geracao_brazil(self):
        """Retorna data de geração no timezone do Brasil"""
        if self.data_geracao:
            if self.data_geracao.tzinfo:
                return self.data_geracao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_geracao).astimezone(BRAZIL_TZ)
        return None

    def get_data_conclusao_brazil(self):
        """Retorna data de conclusão no timezone do Brasil"""
        if self.data_conclusao:
            if self.data_conclusao.tzinfo:
                return self.data_conclusao.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_conclusao).astimezone(BRAZIL_TZ)
        return None

    def __repr__(self):
        return f'<RelatorioGerado {self.nome_relatorio} - {self.status}>'

class ManutencaoSistema(db.Model):
    """Tabela para registrar atividades de manutenção do sistema"""
    __tablename__ = 'manutencao_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_manutencao = db.Column(db.String(100), nullable=False)  # limpeza_logs, otimizacao_bd, verificacao_integridade
    descricao = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='iniciada')  # iniciada, em_progresso, concluida, erro
    data_inicio = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_fim = db.Column(db.DateTime, nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    automatica = db.Column(db.Boolean, default=False)
    resultados = db.Column(db.Text, nullable=True)  # JSON com resultados da manutenção
    erro_detalhes = db.Column(db.Text, nullable=True)
    recursos_afetados = db.Column(db.Text, nullable=True)  # JSON com recursos afetados
    tempo_execucao = db.Column(db.Integer, nullable=True)  # em segundos

    def get_data_inicio_brazil(self):
        """Retorna data de início no timezone do Brasil"""
        if self.data_inicio:
            if self.data_inicio.tzinfo:
                return self.data_inicio.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_inicio).astimezone(BRAZIL_TZ)
        return None

    def get_data_fim_brazil(self):
        """Retorna data de fim no timezone do Brasil"""
        if self.data_fim:
            if self.data_fim.tzinfo:
                return self.data_fim.astimezone(BRAZIL_TZ)
            else:
                return pytz.utc.localize(self.data_fim).astimezone(BRAZIL_TZ)
        return None

    def __repr__(self):
        return f'<ManutencaoSistema {self.tipo_manutencao} - {self.status}>'

class AgenteSuporte(db.Model):
    """Tabela para agentes de suporte"""
    __tablename__ = 'agentes_suporte'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)
    especialidades = db.Column(db.Text, nullable=True)  # JSON com especialidades
    nivel_experiencia = db.Column(db.String(20), default='junior')  # junior, pleno, senior
    max_chamados_simultaneos = db.Column(db.Integer, default=10)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_atualizacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))

    # Relacionamento com usuário
    usuario = db.relationship('User', backref='agente_suporte')

    # Relacionamento com chamados atribuídos
    chamados_atribuidos = db.relationship('ChamadoAgente', backref='agente', lazy=True)

    @property
    def especialidades_list(self):
        if self.especialidades:
            try:
                return json.loads(self.especialidades)
            except:
                return []
        return []

    @especialidades_list.setter
    def especialidades_list(self, value):
        if isinstance(value, list):
            self.especialidades = json.dumps(value)
        else:
            self.especialidades = json.dumps([])

    def get_chamados_ativos(self):
        """Retorna número de chamados ativos atribuídos ao agente"""
        return ChamadoAgente.query.filter_by(
            agente_id=self.id,
            ativo=True
        ).join(Chamado).filter(
            Chamado.status.in_(['Aberto', 'Aguardando'])
        ).count()

    def pode_receber_chamado(self):
        """Verifica se o agente pode receber um novo chamado"""
        if not self.ativo:
            return False
        return self.get_chamados_ativos() < self.max_chamados_simultaneos

    def __repr__(self):
        return f'<AgenteSuporte {self.usuario.nome} - {self.nivel_experiencia}>'

class ChamadoAgente(db.Model):
    """Tabela para atribuição de chamados a agentes"""
    __tablename__ = 'chamado_agente'

    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=False)
    agente_id = db.Column(db.Integer, db.ForeignKey('agentes_suporte.id'), nullable=False)
    data_atribuicao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_conclusao = db.Column(db.DateTime, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    observacoes = db.Column(db.Text, nullable=True)
    atribuido_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relacionamentos
    chamado = db.relationship('Chamado', backref='agente_atribuido')
    atribuido_por_usuario = db.relationship('User', foreign_keys=[atribuido_por])

    def finalizar_atribuicao(self):
        """Finaliza a atribuição do chamado"""
        self.ativo = False
        self.data_conclusao = get_brazil_time().replace(tzinfo=None)

    def __repr__(self):
        return f'<ChamadoAgente Chamado:{self.chamado_id} - Agente:{self.agente_id}>'

class GrupoUsuarios(db.Model):
    """Tabela para grupos de usuários"""
    __tablename__ = 'grupos_usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_atualizacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    criado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relacionamentos
    criador = db.relationship('User', foreign_keys=[criado_por])
    membros = db.relationship('GrupoMembro', backref='grupo', lazy=True, cascade='all, delete-orphan')
    unidades = db.relationship('GrupoUnidade', backref='grupo', lazy=True, cascade='all, delete-orphan')
    permissoes = db.relationship('GrupoPermissao', backref='grupo', lazy=True, cascade='all, delete-orphan')

    def get_membros_count(self):
        """Retorna número de membros ativos no grupo"""
        return GrupoMembro.query.filter_by(grupo_id=self.id, ativo=True).count()

    def get_unidades_count(self):
        """Retorna número de unidades no grupo"""
        return GrupoUnidade.query.filter_by(grupo_id=self.id).count()

    def __repr__(self):
        return f'<GrupoUsuarios {self.nome}>'

class GrupoMembro(db.Model):
    """Tabela para membros dos grupos"""
    __tablename__ = 'grupo_membros'

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_usuarios.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_adicao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    ativo = db.Column(db.Boolean, default=True)
    adicionado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relacionamentos
    usuario = db.relationship('User', foreign_keys=[usuario_id], backref='grupos_participante')
    adicionado_por_usuario = db.relationship('User', foreign_keys=[adicionado_por])

    # Índice composto para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('grupo_id', 'usuario_id', name='uk_grupo_usuario'),)

    def __repr__(self):
        return f'<GrupoMembro Grupo:{self.grupo_id} - Usuário:{self.usuario_id}>'

class GrupoUnidade(db.Model):
    """Tabela para unidades dos grupos"""
    __tablename__ = 'grupo_unidades'

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_usuarios.id'), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidade.id'), nullable=False)
    data_adicao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))

    # Relacionamentos
    unidade = db.relationship('Unidade', backref='grupos_participante')

    # Índice composto para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('grupo_id', 'unidade_id', name='uk_grupo_unidade'),)

    def __repr__(self):
        return f'<GrupoUnidade Grupo:{self.grupo_id} - Unidade:{self.unidade_id}>'

class GrupoPermissao(db.Model):
    """Tabela para permissões específicas dos grupos"""
    __tablename__ = 'grupo_permissoes'

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_usuarios.id'), nullable=False)
    permissao = db.Column(db.String(100), nullable=False)  # criar_chamados, visualizar_relatorios, etc
    concedida = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    concedida_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relacionamentos
    concedida_por_usuario = db.relationship('User', foreign_keys=[concedida_por])

    # Índice composto para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('grupo_id', 'permissao', name='uk_grupo_permissao'),)

    def __repr__(self):
        return f'<GrupoPermissao Grupo:{self.grupo_id} - {self.permissao}>'

class EmailMassa(db.Model):
    """Tabela para histórico de emails em massa"""
    __tablename__ = 'emails_massa'

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupos_usuarios.id'), nullable=True)
    assunto = db.Column(db.String(255), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # alerta_seguranca, atualizacao, manutencao, etc
    destinatarios_count = db.Column(db.Integer, default=0)
    enviados_count = db.Column(db.Integer, default=0)
    falhas_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='preparando')  # preparando, enviando, concluido, erro
    data_criacao = db.Column(db.DateTime, default=lambda: get_brazil_time().replace(tzinfo=None))
    data_envio = db.Column(db.DateTime, nullable=True)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    erro_detalhes = db.Column(db.Text, nullable=True)

    # Relacionamentos
    grupo = db.relationship('GrupoUsuarios', backref='emails_enviados')
    criador = db.relationship('User', foreign_keys=[criado_por])
    destinatarios = db.relationship('EmailMassaDestinatario', backref='email_massa', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EmailMassa {self.assunto} - {self.status}>'

class EmailMassaDestinatario(db.Model):
    """Tabela para destinatários específicos de emails em massa"""
    __tablename__ = 'email_massa_destinatarios'

    id = db.Column(db.Integer, primary_key=True)
    email_massa_id = db.Column(db.Integer, db.ForeignKey('emails_massa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email_destinatario = db.Column(db.String(120), nullable=False)
    nome_destinatario = db.Column(db.String(150), nullable=True)
    status_envio = db.Column(db.String(20), default='pendente')  # pendente, enviado, falha
    data_envio = db.Column(db.DateTime, nullable=True)
    erro_envio = db.Column(db.Text, nullable=True)

    # Relacionamentos
    usuario = db.relationship('User', backref='emails_massa_recebidos')

    def __repr__(self):
        return f'<EmailMassaDestinatario {self.email_destinatario} - {self.status_envio}>'

def init_app(app):
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Migração: Adicionar usuario_id aos chamados existentes
        try:
            # Verificar se a coluna usuario_id existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('chamado')]
            
            if 'usuario_id' not in columns:
                # Adicionar a coluna se não existir
                db.engine.execute('ALTER TABLE chamado ADD COLUMN usuario_id INTEGER')
                db.engine.execute('ALTER TABLE chamado ADD FOREIGN KEY (usuario_id) REFERENCES user(id)')
                print("Coluna usuario_id adicionada à tabela chamado")
            
            # Vincular chamados existentes aos usuários baseado no email
            chamados_sem_usuario = Chamado.query.filter_by(usuario_id=None).all()
            for chamado in chamados_sem_usuario:
                usuario = User.query.filter_by(email=chamado.email).first()
                if usuario:
                    chamado.usuario_id = usuario.id
                    print(f"Chamado {chamado.codigo} vinculado ao usuário {usuario.nome}")
            
            db.session.commit()
            
        except Exception as e:
            print(f"Erro na migração: {str(e)}")
            db.session.rollback()
        
        # Atualizar setores dos usuários
        users = User.query.all()
        for user in users:
            if not user._setores and user.setor:
                user._setores = json.dumps([user.setor])
        
        # Inicializar configurações padrão se não existirem
        configuracoes_padrao = {
            'chamados': {
                'auto_atribuicao': False,
                'escalacao': True,
                'lembretes_sla': False,
                'prazo_padrao_sla': 24,
                'prioridade_padrao': 'Normal'
            },
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
            }
        }

        for chave, valor in configuracoes_padrao.items():
            if not Configuracao.query.filter_by(chave=chave).first():
                config = Configuracao(
                    chave=chave,
                    valor=json.dumps(valor)
                )
                db.session.add(config)
        
        # Inicializar configurações avançadas padrão
        configuracoes_avancadas_padrao = {
            'sistema.manutencao_modo': {
                'valor': 'false',
                'descricao': 'Ativa o modo de manutenção do sistema',
                'tipo': 'boolean',
                'categoria': 'sistema'
            },
            'sistema.debug_mode': {
                'valor': 'false',
                'descricao': 'Ativa o modo de debug para desenvolvimento',
                'tipo': 'boolean',
                'categoria': 'sistema'
            },
            'sistema.max_upload_size': {
                'valor': '10',
                'descricao': 'Tamanho máximo de upload em MB',
                'tipo': 'number',
                'categoria': 'sistema'
            },
            'sistema.session_timeout': {
                'valor': '30',
                'descricao': 'Timeout de sessão em minutos',
                'tipo': 'number',
                'categoria': 'sistema'
            },
            'backup.automatico_habilitado': {
                'valor': 'true',
                'descricao': 'Habilita backup automático',
                'tipo': 'boolean',
                'categoria': 'backup'
            },
            'backup.frequencia_horas': {
                'valor': '24',
                'descricao': 'Frequência de backup automático em horas',
                'tipo': 'number',
                'categoria': 'backup'
            },
            'backup.manter_arquivos': {
                'valor': '30',
                'descricao': 'Número de arquivos de backup a manter',
                'tipo': 'number',
                'categoria': 'backup'
            },
            'alertas.email_habilitado': {
                'valor': 'true',
                'descricao': 'Habilita envio de alertas por email',
                'tipo': 'boolean',
                'categoria': 'alertas'
            },
            'alertas.auto_resolucao': {
                'valor': 'false',
                'descricao': 'Habilita resolução automática de alertas',
                'tipo': 'boolean',
                'categoria': 'alertas'
            },
            'performance.cache_habilitado': {
                'valor': 'true',
                'descricao': 'Habilita cache do sistema',
                'tipo': 'boolean',
                'categoria': 'performance'
            },
            'performance.log_queries_lentas': {
                'valor': 'true',
                'descricao': 'Registra queries que demoram mais que 1 segundo',
                'tipo': 'boolean',
                'categoria': 'performance'
            },
            'logs.nivel_detalhamento': {
                'valor': 'INFO',
                'descricao': 'Nível de detalhamento dos logs (DEBUG, INFO, WARNING, ERROR)',
                'tipo': 'string',
                'categoria': 'logs'
            },
            'logs.rotacao_automatica': {
                'valor': 'true',
                'descricao': 'Habilita rotação automática de logs',
                'tipo': 'boolean',
                'categoria': 'logs'
            },
            'logs.manter_dias': {
                'valor': '90',
                'descricao': 'Número de dias para manter logs',
                'tipo': 'number',
                'categoria': 'logs'
            }
        }

        for chave, config_data in configuracoes_avancadas_padrao.items():
            if not ConfiguracaoAvancada.query.filter_by(chave=chave).first():
                config = ConfiguracaoAvancada(
                    chave=chave,
                    valor=config_data['valor'],
                    descricao=config_data['descricao'],
                    tipo=config_data['tipo'],
                    categoria=config_data['categoria']
                )
                db.session.add(config)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao inicializar configurações: {str(e)}")

def seed_unidades():
    unidades = [
        (1, "GUILHERMINA - 1"),
        (4, "DIADEMA - 4"),
        (5, "SHOPPING MAUÁ - 5"),
        (6, "RIBEIRÃO PIRES - 6"),
        (7, "HOMERO THON - 7"),
        (8, "AV. PORTUGAL - 8"),
        (9, "VALO VELHO - 9"),
        (10, "ITAMARATI - 10"),
        (11, "AV. RIO BRANCO - 11"),
        (12, "PEREIRA BARRETO - 12"),
        (13, "GIOVANNI BREDA - 13"),
        (14, "BOQUEIRÃO - 14"),
        (15, "PARQUE DO CARMO - 15"),
        (16, "ZAIRA - 16"),
        (17, "HELIOPOLIS - 17"),
        (19, "PIMENTAS - 19"),
        (20, "GUAIANASES - 20"),
        (21, "AV. GOIÁS - 21"),
        (22, "BOM CLIMA - 22"),
        (23, "CAMPO GRANDE - 23"),
        (24, "JAGUARÉ - 24"),
        (25, "ITAQUERA - 25"),
        (26, "EXTREMA - 26"),
        (27, "MOGI DAS CRUZES - 27"),
        (28, "ALAMEDA - 28"),
        (29, "JARDIM GOIAS - 29"),
        (30, "PASSEIO DAS AGUAS - 30"),
        (31, "SÃO VICENTE - 31"),
        (32, "CAMILÓPOLIS - 32"),
        (33, "INDAIATUBA - 33"),
        (34, "VILA PRUDENTE - 34"),
        (35, "LARANJAL PAULISTA - 35"),
        (36, "SACOMÃ - 36"),
        (37, "VILA NOVA - 37"),
        (38, "SAPOPEMBA - 38"),
        (39, "POÁ - 39"),
        (40, "CURITIBA - 40"),
        (41, "FRANCA - 41"),
        (130, "JARDIM SÃO PAULO - 130"),
        (131, "CARAPICUIBA - 131"),
        (42, "ITAQUERA 2 - 042"),
    ]

    for id_unidade, nome in unidades:
        if not Unidade.query.get(id_unidade):
            unidade = Unidade(id=id_unidade, nome=nome)
            db.session.add(unidade)
    
    problemas = [
        ("Catraca", "Crítica", False),
        ("Sistema EVO", "Normal", False),
        ("Notebook/Desktop", "Alta", False),
        ("TVs", "Normal", False),
        ("Internet", "Alta", True),
    ]
    
    for nome, prioridade, requer_item in problemas:
        if not ProblemaReportado.query.filter_by(nome=nome).first():
            problema = ProblemaReportado(
                nome=nome,
                prioridade_padrao=prioridade,
                requer_item_internet=requer_item
            )
            db.session.add(problema)
    
    itens_internet = [
        "Wi-fi",
        "Roteador/Modem",
        "Antenas",
        "Cabo de rede",
        "Switch",
        "DVR"
    ]
    
    for item in itens_internet:
        if not ItemInternet.query.filter_by(nome=item).first():
            db.session.add(ItemInternet(nome=item))
    
    db.session.commit()

def atualizar_lista_unidades(id_unidade, nome_unidade):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'database.py')
        
        with open(file_path, 'r', encoding='utf-8') as file:
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
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(content)
    except Exception as e:
        print(f"Erro ao atualizar database.py: {str(e)}")

# Funções auxiliares para logs e auditoria
def registrar_log_acesso(usuario_id, ip_address=None, user_agent=None, session_id=None):
    """Registra um novo log de acesso"""
    try:
        # Extrair informações do user agent
        navegador, sistema_operacional, dispositivo = extrair_info_user_agent(user_agent)
        
        log = LogAcesso(
            usuario_id=usuario_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            navegador=navegador,
            sistema_operacional=sistema_operacional,
            dispositivo=dispositivo
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        print(f"Erro ao registrar log de acesso: {str(e)}")
        db.session.rollback()
        return None

def registrar_log_logout(usuario_id, session_id=None):
    """Registra logout do usuário"""
    try:
        # Encontrar log de acesso ativo
        log_acesso = LogAcesso.query.filter_by(
            usuario_id=usuario_id,
            ativo=True,
            data_logout=None
        ).order_by(LogAcesso.data_acesso.desc()).first()
        
        if log_acesso:
            log_acesso.data_logout = get_brazil_time().replace(tzinfo=None)
            log_acesso.ativo = False
            log_acesso.duracao_sessao = log_acesso.calcular_duracao()
            db.session.commit()
            return log_acesso
    except Exception as e:
        print(f"Erro ao registrar logout: {str(e)}")
        db.session.rollback()
        return None

def registrar_log_acao(usuario_id, acao, categoria=None, detalhes=None, 
                      dados_anteriores=None, dados_novos=None, ip_address=None, 
                      user_agent=None, sucesso=True, erro_detalhes=None,
                      recurso_afetado=None, tipo_recurso=None):
    """Registra uma ação do usuário"""
    try:
        log = LogAcao(
            usuario_id=usuario_id,
            acao=acao,
            categoria=categoria,
            detalhes=detalhes,
            dados_anteriores=json.dumps(dados_anteriores) if dados_anteriores else None,
            dados_novos=json.dumps(dados_novos) if dados_novos else None,
            ip_address=ip_address,
            user_agent=user_agent,
            sucesso=sucesso,
            erro_detalhes=erro_detalhes,
            recurso_afetado=str(recurso_afetado) if recurso_afetado else None,
            tipo_recurso=tipo_recurso
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as e:
        print(f"Erro ao registrar log de ação: {str(e)}")
        db.session.rollback()
        return None

def extrair_info_user_agent(user_agent):
    """Extrai informações básicas do user agent"""
    if not user_agent:
        return None, None, None
    
    user_agent = user_agent.lower()
    
    # Detectar navegador
    navegador = None
    if 'chrome' in user_agent and 'edg' not in user_agent:
        navegador = 'Chrome'
    elif 'firefox' in user_agent:
        navegador = 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        navegador = 'Safari'
    elif 'edg' in user_agent:
        navegador = 'Edge'
    elif 'opera' in user_agent:
        navegador = 'Opera'
    else:
        navegador = 'Outro'
    
    # Detectar sistema operacional
    sistema_operacional = None
    if 'windows' in user_agent:
        sistema_operacional = 'Windows'
    elif 'mac' in user_agent:
        sistema_operacional = 'macOS'
    elif 'linux' in user_agent:
        sistema_operacional = 'Linux'
    elif 'android' in user_agent:
        sistema_operacional = 'Android'
    elif 'ios' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
        sistema_operacional = 'iOS'
    else:
        sistema_operacional = 'Outro'
    
    # Detectar dispositivo
    dispositivo = None
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        dispositivo = 'Mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        dispositivo = 'Tablet'
    else:
        dispositivo = 'Desktop'
    
    return navegador, sistema_operacional, dispositivo

def criar_alerta_sistema(tipo, titulo, descricao, severidade='media', categoria=None, 
                        automatico=True, dados_contexto=None):
    """Cria um novo alerta do sistema"""
    try:
        # Verificar se já existe alerta similar não resolvido
        alerta_existente = AlertaSistema.query.filter_by(
            tipo=tipo,
            titulo=titulo,
            resolvido=False
        ).first()
        
        if alerta_existente:
            # Incrementar contador de ocorrências
            alerta_existente.incrementar_ocorrencia()
            db.session.commit()
            return alerta_existente
        
        # Criar novo alerta
        alerta = AlertaSistema(
            tipo=tipo,
            titulo=titulo,
            descricao=descricao,
            severidade=severidade,
            categoria=categoria,
            automatico=automatico,
            dados_contexto=json.dumps(dados_contexto) if dados_contexto else None
        )
        db.session.add(alerta)
        db.session.commit()
        return alerta
    except Exception as e:
        print(f"Erro ao criar alerta do sistema: {str(e)}")
        db.session.rollback()
        return None
