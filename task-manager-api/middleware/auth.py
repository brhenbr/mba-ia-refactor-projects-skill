from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from repositories.user_repository import UserRepository


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
        user = UserRepository().find_by_id(current_user_id)
        if not user or not user.is_admin():
            return jsonify({"error": "Sem permissão"}), 403
        return f(current_user_id, *args, **kwargs)

    return decorated


def owner_or_admin_required(param_name):
    """Exige que o usuário autenticado seja dono do recurso (kwargs[param_name]) ou admin."""

    def decorator(f):
        @wraps(f)
        @login_required
        def decorated(current_user_id, *args, **kwargs):
            resource_user_id = kwargs.get(param_name)
            if resource_user_id != current_user_id:
                user = UserRepository().find_by_id(current_user_id)
                if not user or not user.is_admin():
                    return jsonify({"error": "Sem permissão"}), 403
            return f(current_user_id, *args, **kwargs)

        return decorated

    return decorator
