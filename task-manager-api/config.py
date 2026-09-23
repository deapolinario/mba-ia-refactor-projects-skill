import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configurações centralizadas da aplicação"""

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///tasks.db')
    DEBUG = os.getenv('FLASK_ENV') == 'development'

    # Auth (token assinado, expira em 24h por padrão)
    TOKEN_EXPIRATION_SECONDS = int(os.getenv('TOKEN_EXPIRATION_SECONDS', '86400'))

    # Notificações (v2.2 - extraído de services/notification_service.py)
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

    # Domínio (v2.2 - já existiam em utils/helpers.py mas nunca eram usados)
    VALID_TASK_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
    VALID_ROLES = ['user', 'admin', 'manager']

    # Domínio (v3.2 - centraliza a escala de prioridade, que antes era
    # hardcoded/duplicada em models/task.py, utils/helpers.py e
    # controllers/report_controller.py sem constante compartilhada)
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5
    PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

    @staticmethod
    def validate():
        if not os.getenv('SECRET_KEY') and os.getenv('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY deve ser definida em produção!")
