import logging
from flask import Blueprint, request, jsonify
from controllers.produto_controller import ProdutoController
from auth import role_required

logger = logging.getLogger(__name__)
produto_bp = Blueprint('produtos', __name__)


@produto_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    try:
        produtos = ProdutoController.listar()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@produto_bp.route('/produtos/busca', methods=['GET'])
def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)
        resultados = ProdutoController.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@produto_bp.route('/produtos/<int:id>', methods=['GET'])
def buscar_produto(id):
    try:
        produto = ProdutoController.buscar_por_id(id)
        return jsonify({"dados": produto, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar produto {id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@produto_bp.route('/produtos', methods=['POST'])
@role_required('admin')
def criar_produto():
    try:
        dados = request.get_json()
        produto = ProdutoController.criar(dados)
        logger.info(f"Produto criado com ID: {produto['id']}")
        return jsonify({"dados": produto, "sucesso": True, "mensagem": "Produto criado"}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar produto: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@produto_bp.route('/produtos/<int:id>', methods=['PUT'])
@role_required('admin')
def atualizar_produto(id):
    try:
        dados = request.get_json()
        ProdutoController.atualizar(id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except ValueError as e:
        status = 404 if "não encontrado" in str(e) else 400
        return jsonify({"erro": str(e)}), status
    except Exception as e:
        logger.error(f"Erro ao atualizar produto {id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@produto_bp.route('/produtos/<int:id>', methods=['DELETE'])
@role_required('admin')
def deletar_produto(id):
    try:
        ProdutoController.deletar(id)
        logger.info(f"Produto {id} deletado")
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404
    except Exception as e:
        logger.error(f"Erro ao deletar produto {id}: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
