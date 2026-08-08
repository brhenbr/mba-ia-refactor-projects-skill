from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from repositories.usuario_repository import UsuarioRepository


def login_required(f):
    """Exige JWT válido; injeta current_user_id (int) como primeiro argumento da view."""

    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        return f(current_user_id, *args, **kwargs)

    return decorated


def admin_required(f):
    """Exige JWT válido + role admin."""

    @wraps(f)
    @login_required
    def decorated(current_user_id, *args, **kwargs):
        usuario = UsuarioRepository().find_by_id(current_user_id)
        if not usuario or not usuario.is_admin():
            return jsonify({"erro": "Sem permissão"}), 403
        return f(current_user_id, *args, **kwargs)

    return decorated


def owner_or_admin_required(param_name):
    """Exige que o usuário autenticado seja dono do recurso (kwargs[param_name]) ou admin."""

    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(current_user_id, *args, **kwargs):
            recurso_usuario_id = kwargs.get(param_name)
            if recurso_usuario_id != current_user_id:
                usuario = UsuarioRepository().find_by_id(current_user_id)
                if not usuario or not usuario.is_admin():
                    return jsonify({"erro": "Sem permissão"}), 403
            return f(current_user_id, *args, **kwargs)

        return decorated

    return decorator
