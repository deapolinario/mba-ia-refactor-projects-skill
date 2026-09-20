import os

class Config:
    """Configurações centralizadas da aplicação"""

    # Secrets (carregadas de variáveis de ambiente)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'loja.db')

    # Flask
    DEBUG = os.getenv('FLASK_ENV') == 'development'

    # Validação no startup
    @staticmethod
    def validate():
        if not os.getenv('SECRET_KEY') and os.getenv('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY deve ser definida em produção!")
