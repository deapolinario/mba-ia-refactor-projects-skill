import os

class Config:
    """Configurações centralizadas da aplicação"""

    # Secrets (carregadas de variáveis de ambiente)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'loja.db')

    # Admin (guard mínimo para rotas administrativas — v2.2)
    ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

    # Flask
    DEBUG = os.getenv('FLASK_ENV') == 'development'

    # Domínio (v2.2 - extraído de magic strings em controllers.py)
    VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
    VALID_ORDER_STATUSES = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

    # Domínio (v3.2 - extraído de magic numbers em models/pedido.py e
    # controllers/produto_controller.py)
    MIN_PRODUTO_NOME = 2
    MAX_PRODUTO_NOME = 200
    # (limite de faturamento, percentual de desconto), avaliados em ordem
    FAIXAS_DESCONTO = [
        (10000, 0.10),
        (5000, 0.05),
        (1000, 0.02),
    ]

    # Validação no startup
    @staticmethod
    def validate():
        if not os.getenv('SECRET_KEY') and os.getenv('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY deve ser definida em produção!")
