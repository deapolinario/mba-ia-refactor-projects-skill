import logging
from config import Config
from models import pedido as pedido_model

logger = logging.getLogger(__name__)


class PedidoController:

    @staticmethod
    def criar(dados):
        if not dados:
            raise ValueError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ValueError("Usuario ID é obrigatório")
        if not itens:
            raise ValueError("Pedido deve ter pelo menos 1 item")

        resultado = pedido_model.criar_pedido(usuario_id, itens)
        if "erro" in resultado:
            raise ValueError(resultado["erro"])

        logger.info(f"Pedido criado: {resultado['pedido_id']}")
        logger.debug("Enviando notificações (email, SMS, push)")
        return resultado

    @staticmethod
    def listar_por_usuario(usuario_id):
        return pedido_model.get_pedidos_usuario(usuario_id)

    @staticmethod
    def listar_todos():
        return pedido_model.get_todos_pedidos()

    @staticmethod
    def atualizar_status(pedido_id, novo_status):
        if novo_status not in Config.VALID_ORDER_STATUSES:
            raise ValueError("Status inválido")

        pedido_model.atualizar_status_pedido(pedido_id, novo_status)

        if novo_status == "aprovado":
            logger.info(f"Pedido {pedido_id} aprovado")
        elif novo_status == "cancelado":
            logger.info(f"Pedido {pedido_id} cancelado")

    @staticmethod
    def relatorio_vendas():
        return pedido_model.relatorio_vendas()
