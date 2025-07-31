from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db, User, GrupoUsuarios, GrupoMembro, GrupoUnidade, GrupoPermissao, Unidade
from auth.utils import setor_required
import logging

logger = logging.getLogger(__name__)

grupos_bp = Blueprint('grupos', __name__)

def json_response(data, status=200):
    """Padroniza respostas JSON"""
    return jsonify(data), status

def error_response(message, status=400):
    """Padroniza respostas de erro"""
    return jsonify({'error': message}), status

@grupos_bp.route('/api/grupos', methods=['GET'])
@login_required
@setor_required('Administrador')
def listar_grupos():
    """Lista todos os grupos de usuários"""
    try:
        filtro = request.args.get('filtro', '').strip()
        
        query = db.session.query(GrupoUsuarios, User).join(User, GrupoUsuarios.criado_por == User.id)
        
        if filtro:
            query = query.filter(
                db.or_(
                    GrupoUsuarios.nome.ilike(f'%{filtro}%'),
                    GrupoUsuarios.descricao.ilike(f'%{filtro}%'),
                    User.nome.ilike(f'%{filtro}%')
                )
            )
        
        query = query.order_by(GrupoUsuarios.data_criacao.desc())
        
        grupos_data = []
        for grupo, criador in query.all():
            grupos_data.append({
                'id': grupo.id,
                'nome': grupo.nome,
                'descricao': grupo.descricao,
                'ativo': grupo.ativo,
                'membros_count': grupo.get_membros_count(),
                'unidades_count': grupo.get_unidades_count(),
                'criado_por': f"{criador.nome} {criador.sobrenome}",
                'data_criacao': grupo.data_criacao.strftime('%d/%m/%Y %H:%M') if grupo.data_criacao else None
            })
        
        return json_response(grupos_data)
        
    except Exception as e:
        logger.error(f"Erro ao listar grupos: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos', methods=['POST'])
@login_required
@setor_required('Administrador')
def criar_grupo():
    """Cria um novo grupo de usuários"""
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Dados não fornecidos')
        
        nome = data.get('nome', '').strip()
        if not nome:
            return error_response('Nome do grupo é obrigatório')
        
        # Verificar se nome já existe
        grupo_existente = GrupoUsuarios.query.filter_by(nome=nome).first()
        if grupo_existente:
            return error_response('Já existe um grupo com este nome')
        
        # Criar grupo
        grupo = GrupoUsuarios(
            nome=nome,
            descricao=data.get('descricao', '').strip(),
            ativo=data.get('ativo', True),
            criado_por=current_user.id
        )
        
        db.session.add(grupo)
        db.session.flush()  # Para obter o ID
        
        # Adicionar unidades se fornecidas
        unidades_ids = data.get('unidades', [])
        if unidades_ids:
            for unidade_id in unidades_ids:
                if Unidade.query.get(unidade_id):
                    grupo_unidade = GrupoUnidade(
                        grupo_id=grupo.id,
                        unidade_id=unidade_id
                    )
                    db.session.add(grupo_unidade)
        
        # Adicionar membros se fornecidos
        membros_ids = data.get('membros', [])
        if membros_ids:
            for usuario_id in membros_ids:
                if User.query.get(usuario_id):
                    membro = GrupoMembro(
                        grupo_id=grupo.id,
                        usuario_id=usuario_id,
                        adicionado_por=current_user.id
                    )
                    db.session.add(membro)
        
        db.session.commit()
        
        logger.info(f"Grupo '{nome}' criado por {current_user.nome}")
        
        return json_response({
            'id': grupo.id,
            'message': f'Grupo "{nome}" criado com sucesso'
        }, 201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar grupo: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>', methods=['GET'])
@login_required
@setor_required('Administrador')
def obter_grupo(grupo_id):
    """Obtém detalhes de um grupo específico"""
    try:
        grupo = GrupoUsuarios.query.get(grupo_id)
        if not grupo:
            return error_response('Grupo não encontrado', 404)
        
        # Buscar membros
        membros_query = db.session.query(GrupoMembro, User).join(User).filter(
            GrupoMembro.grupo_id == grupo_id,
            GrupoMembro.ativo == True
        )
        
        membros = []
        for membro, usuario in membros_query.all():
            membros.append({
                'id': membro.id,
                'usuario_id': usuario.id,
                'nome': f"{usuario.nome} {usuario.sobrenome}",
                'email': usuario.email,
                'nivel_acesso': usuario.nivel_acesso,
                'data_adicao': membro.data_adicao.strftime('%d/%m/%Y %H:%M') if membro.data_adicao else None
            })
        
        # Buscar unidades
        unidades_query = db.session.query(GrupoUnidade, Unidade).join(Unidade).filter(
            GrupoUnidade.grupo_id == grupo_id
        )
        
        unidades = []
        for grupo_unidade, unidade in unidades_query.all():
            unidades.append({
                'id': grupo_unidade.id,
                'unidade_id': unidade.id,
                'nome': unidade.nome,
                'data_adicao': grupo_unidade.data_adicao.strftime('%d/%m/%Y %H:%M') if grupo_unidade.data_adicao else None
            })
        
        # Buscar permissões
        permissoes = GrupoPermissao.query.filter_by(grupo_id=grupo_id).all()
        permissoes_data = []
        for permissao in permissoes:
            permissoes_data.append({
                'id': permissao.id,
                'permissao': permissao.permissao,
                'concedida': permissao.concedida,
                'data_criacao': permissao.data_criacao.strftime('%d/%m/%Y %H:%M') if permissao.data_criacao else None
            })
        
        grupo_data = {
            'id': grupo.id,
            'nome': grupo.nome,
            'descricao': grupo.descricao,
            'ativo': grupo.ativo,
            'data_criacao': grupo.data_criacao.strftime('%d/%m/%Y %H:%M') if grupo.data_criacao else None,
            'membros': membros,
            'unidades': unidades,
            'permissoes': permissoes_data
        }
        
        return json_response(grupo_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter grupo: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>', methods=['PUT'])
@login_required
@setor_required('Administrador')
def atualizar_grupo(grupo_id):
    """Atualiza informações de um grupo"""
    try:
        grupo = GrupoUsuarios.query.get(grupo_id)
        if not grupo:
            return error_response('Grupo não encontrado', 404)
        
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos')
        
        # Atualizar campos básicos
        if 'nome' in data:
            nome = data['nome'].strip()
            if not nome:
                return error_response('Nome não pode estar vazio')
            
            # Verificar duplicata
            grupo_existente = GrupoUsuarios.query.filter(
                GrupoUsuarios.nome == nome,
                GrupoUsuarios.id != grupo_id
            ).first()
            if grupo_existente:
                return error_response('Já existe um grupo com este nome')
            
            grupo.nome = nome
        
        if 'descricao' in data:
            grupo.descricao = data['descricao'].strip()
        
        if 'ativo' in data:
            grupo.ativo = data['ativo']
        
        grupo.data_atualizacao = db.func.now()
        db.session.commit()
        
        logger.info(f"Grupo '{grupo.nome}' atualizado por {current_user.nome}")
        
        return json_response({'message': 'Grupo atualizado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar grupo: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def excluir_grupo(grupo_id):
    """Exclui um grupo"""
    try:
        grupo = GrupoUsuarios.query.get(grupo_id)
        if not grupo:
            return error_response('Grupo não encontrado', 404)
        
        nome_grupo = grupo.nome
        
        # As relações serão excluídas automaticamente devido ao cascade
        db.session.delete(grupo)
        db.session.commit()
        
        logger.info(f"Grupo '{nome_grupo}' excluído por {current_user.nome}")
        
        return json_response({'message': f'Grupo "{nome_grupo}" excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir grupo: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>/membros', methods=['POST'])
@login_required
@setor_required('Administrador')
def adicionar_membro(grupo_id):
    """Adiciona um membro ao grupo"""
    try:
        grupo = GrupoUsuarios.query.get(grupo_id)
        if not grupo:
            return error_response('Grupo não encontrado', 404)
        
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos')
        
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return error_response('ID do usuário é obrigatório')
        
        usuario = User.query.get(usuario_id)
        if not usuario:
            return error_response('Usuário não encontrado')
        
        # Verificar se já é membro ativo
        membro_existente = GrupoMembro.query.filter_by(
            grupo_id=grupo_id,
            usuario_id=usuario_id,
            ativo=True
        ).first()
        
        if membro_existente:
            return error_response('Usuário já é membro deste grupo')
        
        # Reativar membro se existir inativo ou criar novo
        membro_inativo = GrupoMembro.query.filter_by(
            grupo_id=grupo_id,
            usuario_id=usuario_id,
            ativo=False
        ).first()
        
        if membro_inativo:
            membro_inativo.ativo = True
            membro_inativo.data_adicao = db.func.now()
            membro_inativo.adicionado_por = current_user.id
        else:
            membro = GrupoMembro(
                grupo_id=grupo_id,
                usuario_id=usuario_id,
                adicionado_por=current_user.id
            )
            db.session.add(membro)
        
        db.session.commit()
        
        logger.info(f"Usuário {usuario.nome} adicionado ao grupo '{grupo.nome}' por {current_user.nome}")
        
        return json_response({
            'message': f'Usuário {usuario.nome} adicionado ao grupo com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar membro: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>/membros/<int:membro_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def remover_membro(grupo_id, membro_id):
    """Remove um membro do grupo"""
    try:
        membro = GrupoMembro.query.filter_by(
            id=membro_id,
            grupo_id=grupo_id
        ).first()
        
        if not membro:
            return error_response('Membro não encontrado', 404)
        
        nome_usuario = membro.usuario.nome
        nome_grupo = membro.grupo.nome
        
        # Desativar ao invés de excluir para manter histórico
        membro.ativo = False
        db.session.commit()
        
        logger.info(f"Usuário {nome_usuario} removido do grupo '{nome_grupo}' por {current_user.nome}")
        
        return json_response({
            'message': f'Usuário {nome_usuario} removido do grupo com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover membro: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>/unidades', methods=['POST'])
@login_required
@setor_required('Administrador')
def adicionar_unidade(grupo_id):
    """Adiciona uma unidade ao grupo"""
    try:
        grupo = GrupoUsuarios.query.get(grupo_id)
        if not grupo:
            return error_response('Grupo não encontrado', 404)
        
        data = request.get_json()
        if not data:
            return error_response('Dados não fornecidos')
        
        unidade_id = data.get('unidade_id')
        if not unidade_id:
            return error_response('ID da unidade é obrigatório')
        
        unidade = Unidade.query.get(unidade_id)
        if not unidade:
            return error_response('Unidade não encontrada')
        
        # Verificar se já está no grupo
        grupo_unidade_existente = GrupoUnidade.query.filter_by(
            grupo_id=grupo_id,
            unidade_id=unidade_id
        ).first()
        
        if grupo_unidade_existente:
            return error_response('Unidade já está neste grupo')
        
        grupo_unidade = GrupoUnidade(
            grupo_id=grupo_id,
            unidade_id=unidade_id
        )
        
        db.session.add(grupo_unidade)
        db.session.commit()
        
        logger.info(f"Unidade {unidade.nome} adicionada ao grupo '{grupo.nome}' por {current_user.nome}")
        
        return json_response({
            'message': f'Unidade {unidade.nome} adicionada ao grupo com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar unidade: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/grupos/<int:grupo_id>/unidades/<int:grupo_unidade_id>', methods=['DELETE'])
@login_required
@setor_required('Administrador')
def remover_unidade(grupo_id, grupo_unidade_id):
    """Remove uma unidade do grupo"""
    try:
        grupo_unidade = GrupoUnidade.query.filter_by(
            id=grupo_unidade_id,
            grupo_id=grupo_id
        ).first()
        
        if not grupo_unidade:
            return error_response('Unidade não encontrada no grupo', 404)
        
        nome_unidade = grupo_unidade.unidade.nome
        nome_grupo = grupo_unidade.grupo.nome
        
        db.session.delete(grupo_unidade)
        db.session.commit()
        
        logger.info(f"Unidade {nome_unidade} removida do grupo '{nome_grupo}' por {current_user.nome}")
        
        return json_response({
            'message': f'Unidade {nome_unidade} removida do grupo com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover unidade: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/usuarios-disponiveis-grupo', methods=['GET'])
@login_required
@setor_required('Administrador')
def usuarios_disponiveis_grupo():
    """Lista usuários disponíveis para adicionar a grupos"""
    try:
        grupo_id = request.args.get('grupo_id')
        filtro = request.args.get('filtro', '').strip()
        
        query = User.query.filter(User.bloqueado == False)
        
        if grupo_id:
            # Excluir usuários que já são membros ativos do grupo
            subquery = db.session.query(GrupoMembro.usuario_id).filter(
                GrupoMembro.grupo_id == grupo_id,
                GrupoMembro.ativo == True
            )
            query = query.filter(~User.id.in_(subquery))
        
        if filtro:
            query = query.filter(
                db.or_(
                    User.nome.ilike(f'%{filtro}%'),
                    User.sobrenome.ilike(f'%{filtro}%'),
                    User.email.ilike(f'%{filtro}%'),
                    User.usuario.ilike(f'%{filtro}%')
                )
            )
        
        query = query.order_by(User.nome, User.sobrenome)
        
        usuarios_data = []
        for usuario in query.all():
            usuarios_data.append({
                'id': usuario.id,
                'nome': f"{usuario.nome} {usuario.sobrenome}",
                'email': usuario.email,
                'nivel_acesso': usuario.nivel_acesso,
                'setores': usuario.setores
            })
        
        return json_response(usuarios_data)
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários disponíveis: {str(e)}")
        return error_response('Erro interno no servidor')

@grupos_bp.route('/api/unidades-disponiveis-grupo', methods=['GET'])
@login_required
@setor_required('Administrador')
def unidades_disponiveis_grupo():
    """Lista unidades disponíveis para adicionar a grupos"""
    try:
        grupo_id = request.args.get('grupo_id')
        
        query = Unidade.query
        
        if grupo_id:
            # Excluir unidades que já estão no grupo
            subquery = db.session.query(GrupoUnidade.unidade_id).filter(
                GrupoUnidade.grupo_id == grupo_id
            )
            query = query.filter(~Unidade.id.in_(subquery))
        
        query = query.order_by(Unidade.nome)
        
        unidades_data = []
        for unidade in query.all():
            unidades_data.append({
                'id': unidade.id,
                'nome': unidade.nome
            })
        
        return json_response(unidades_data)
        
    except Exception as e:
        logger.error(f"Erro ao listar unidades disponíveis: {str(e)}")
        return error_response('Erro interno no servidor')
