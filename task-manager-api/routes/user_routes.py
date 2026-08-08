from flask import Blueprint, jsonify, request

from middleware.auth import admin_required, login_required, owner_or_admin_required
from repositories.user_repository import UserRepository
from services.user_service import UserService
from validators.user_validator import LoginSchema, UserRegisterSchema, UserUpdateSchema

user_bp = Blueprint('users', __name__)

user_service = UserService()
user_repo = UserRepository()

user_register_schema = UserRegisterSchema()
user_update_schema = UserUpdateSchema()
login_schema = LoginSchema()


def _is_admin(user_id):
    user = user_repo.find_by_id(user_id)
    return bool(user and user.is_admin())


@user_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user_id):
    users = user_service.list_all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@owner_or_admin_required('user_id')
def get_user(current_user_id, user_id):
    user = user_service.get_by_id(user_id)
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in user_service.get_user_tasks(user_id)]
    return jsonify(data), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = user_register_schema.load(request.get_json() or {})
    user = user_service.register(data)
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@owner_or_admin_required('user_id')
def update_user(current_user_id, user_id):
    data = user_update_schema.load(request.get_json() or {})
    user = user_service.update(user_id, data, _is_admin(current_user_id))
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user_id, user_id):
    user_service.delete(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@owner_or_admin_required('user_id')
def get_user_tasks(current_user_id, user_id):
    tasks = user_service.get_user_tasks(user_id)
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        result.append(data)
    return jsonify(result), 200


@user_bp.route('/login', methods=['POST'])
def login():
    data = login_schema.load(request.get_json() or {})
    user, token = user_service.authenticate(data['email'], data['password'])
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token
    }), 200
