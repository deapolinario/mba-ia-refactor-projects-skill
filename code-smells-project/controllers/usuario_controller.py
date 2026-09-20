import logging
from models import usuario as usuario_model

logger = logging.getLogger(__name__)


def mask_email(email):
    """Mascarar email para logs (v2.1 - Logs Sensíveis fix)."""
    parts = email.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"


class UsuarioController:

    @staticmethod
    def listar():
        return usuario_model.get_todos_usuarios()

    @staticmethod
    def buscar_por_id(id):
        usuario = usuario_model.get_usuario_por_id(id)
        if not usuario:
            raise ValueError("Usuário não encontrado")
        return usuario

    @staticmethod
    def criar(dados):
        if not dados:
            raise ValueError("Dados inválidos")

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            raise ValueError("Nome, email e senha são obrigatórios")

        usuario_id = usuario_model.criar_usuario(nome, email, senha)
        logger.info(f"Usuário criado: {usuario_id}")
        return {"id": usuario_id}

    @staticmethod
    def login(email, senha):
        if not email or not senha:
            raise ValueError("Email e senha são obrigatórios")

        usuario = usuario_model.login_usuario(email, senha)
        if usuario:
            logger.info(f"Login bem-sucedido: {mask_email(email)}")
            return usuario

        logger.warning(f"Login falhou: {mask_email(email)}")
        raise PermissionError("Email ou senha inválidos")
