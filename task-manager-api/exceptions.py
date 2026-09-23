"""Exceções de domínio tipadas — substituem o dispatch de status HTTP por
string matching na mensagem de erro (`if 'não encontrada' in str(e)`), que
era duplicado em cada arquivo de rotas e frágil a mudanças de texto."""


class NotFoundError(Exception):
    """Recurso solicitado não existe. Rotas mapeiam para HTTP 404."""


class ConflictError(Exception):
    """Recurso já existe / conflita com estado atual. Rotas mapeiam para HTTP 409."""


class ValidationError(Exception):
    """Dados de entrada inválidos. Rotas mapeiam para HTTP 400."""
