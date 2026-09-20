import logging
from flask import Blueprint, request, jsonify, session
from controllers.usuario_controller import UsuarioController
from auth import role_required, owner_or_role_required

logger = logging.getLogger(__name__)
usuario_bp = Blueprint('usuarios', __name__)


@usuario_bp.route('/usuarios', methods=['GET'])
@role_required('admin')
def listar_usuarios():
    try:
        usuarios = UsuarioController.listar()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@usuario_bp.route('/usuarios/<int:id>', methods=['GET'])
@owner_or_role_required('id', 'admin')
def buscar_usuario(id):
    try:
        usuario = UsuarioController.buscar_por_id(id)
        return jsonify({"dados": usuario, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar usuário {id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@usuario_bp.route('/usuarios', methods=['POST'])
def criar_usuario():
    try:
        dados = request.get_json()
        usuario = UsuarioController.criar(dados)
        return jsonify({"dados": usuario, "sucesso": True}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@usuario_bp.route('/login', methods=['POST'])
def login():
    try:
        dados = request.get_json() or {}
        usuario = UsuarioController.login(dados.get("email", ""), dados.get("senha", ""))
        session["usuario_id"] = usuario["id"]
        session["tipo"] = usuario["tipo"]
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    except PermissionError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 401
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
