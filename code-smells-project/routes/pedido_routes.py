import logging
from flask import Blueprint, request, jsonify, session
from controllers.pedido_controller import PedidoController
from auth import login_required, role_required, owner_or_role_required

logger = logging.getLogger(__name__)
pedido_bp = Blueprint('pedidos', __name__)


@pedido_bp.route('/pedidos', methods=['POST'])
@login_required
def criar_pedido():
    try:
        dados = request.get_json() or {}
        dados["usuario_id"] = session["usuario_id"]  # nunca confiar no usuario_id do payload
        resultado = PedidoController.criar(dados)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
    except Exception as e:
        logger.error(f"Erro crítico ao criar pedido: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@pedido_bp.route('/pedidos', methods=['GET'])
@role_required('admin')
def listar_todos_pedidos():
    try:
        pedidos = PedidoController.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar todos os pedidos: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@pedido_bp.route('/pedidos/usuario/<int:usuario_id>', methods=['GET'])
@owner_or_role_required('usuario_id', 'admin')
def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = PedidoController.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar pedidos do usuário {usuario_id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
@role_required('admin')
def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json() or {}
        PedidoController.atualizar_status(pedido_id, dados.get("status", ""))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar status do pedido {pedido_id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@pedido_bp.route('/relatorios/vendas', methods=['GET'])
@role_required('admin')
def relatorio_vendas():
    try:
        relatorio = PedidoController.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de vendas: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
