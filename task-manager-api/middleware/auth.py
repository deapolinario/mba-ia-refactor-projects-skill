from functools import wraps
from flask import request, jsonify, g
from auth.tokens import verify_token
from models.user import User


def login_required(f):
    """
    v2.2 - Broken Access Control fix: antes, NENHUMA rota verificava o
    token retornado por /login (era decorativo). Agora toda rota protegida
    exige `Authorization: Bearer <token>` válido e popula `g.current_user`.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autenticação ausente'}), 401

        token = auth_header[len('Bearer '):]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token inválido ou expirado'}), 401

        user = User.query.get(user_id)
        if not user or not user.active:
            return jsonify({'error': 'Usuário inválido ou inativo'}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Deve ser usado depois de @login_required (depende de g.current_user)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.current_user.role not in roles:
                return jsonify({'error': 'Permissão insuficiente'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
