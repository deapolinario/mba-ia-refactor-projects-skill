from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import Config

"""
v2.2 - substitui o token decorativo `'fake-jwt-token-' + str(user.id)` (que
nunca era verificado em nenhuma rota) por um token assinado de verdade,
com expiração. Não é um sistema de auth completo (sem refresh token, sem
revogação) — é o guard mínimo necessário para eliminar o Broken Access
Control encontrado na auditoria.
"""

_SALT = 'task-manager-auth'


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


def generate_token(user_id):
    return _serializer().dumps({'user_id': user_id}, salt=_SALT)


def verify_token(token):
    """Retorna o user_id se o token for válido, ou None."""
    try:
        data = _serializer().loads(token, salt=_SALT, max_age=Config.TOKEN_EXPIRATION_SECONDS)
        return data.get('user_id')
    except (BadSignature, SignatureExpired):
        return None
