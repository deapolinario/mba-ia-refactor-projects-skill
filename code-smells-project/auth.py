from functools import wraps
from flask import session, jsonify


def login_required(f):
    """Exige uma sessão de usuário autenticado (v3.1 - CRITICAL-1/CRITICAL-2 fix)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario_id"):
            return jsonify({"erro": "Autenticação necessária"}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    """Exige sessão autenticada com o `tipo` (role) informado."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("usuario_id"):
                return jsonify({"erro": "Autenticação necessária"}), 401
            if session.get("tipo") != role:
                return jsonify({"erro": "Acesso negado"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def owner_or_role_required(param_name, role):
    """Permite acesso se o usuário autenticado for o dono do recurso
    (comparando `session['usuario_id']` com o parâmetro de rota `param_name`)
    ou tiver o `role` informado (ex: admin acessando dados de qualquer usuário)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("usuario_id"):
                return jsonify({"erro": "Autenticação necessária"}), 401
            recurso_id = kwargs.get(param_name)
            if session.get("tipo") != role and session.get("usuario_id") != recurso_id:
                return jsonify({"erro": "Acesso negado"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
