from flask import Blueprint, jsonify, request

from middleware.auth import login_required
from repositories.user_repository import UserRepository
from services.task_service import TaskService
from validators.task_validator import TaskCreateSchema, TaskSearchSchema, TaskUpdateSchema

task_bp = Blueprint('tasks', __name__)

task_service = TaskService()
user_repo = UserRepository()

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_search_schema = TaskSearchSchema()


def _is_admin(user_id):
    user = user_repo.find_by_id(user_id)
    return bool(user and user.is_admin())


def _serialize(task):
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


@task_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks(current_user_id):
    tasks = task_service.list_for(current_user_id, _is_admin(current_user_id))
    return jsonify([_serialize(t) for t in tasks]), 200


@task_bp.route('/tasks/search', methods=['GET'])
@login_required
def search_tasks(current_user_id):
    filters = task_search_schema.load(request.args.to_dict())
    tasks = task_service.search(current_user_id, _is_admin(current_user_id), filters)
    return jsonify([_serialize(t) for t in tasks]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
@login_required
def task_stats(current_user_id):
    stats = task_service.stats(current_user_id, _is_admin(current_user_id))
    return jsonify(stats), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(current_user_id, task_id):
    task = task_service.get_owned(task_id, current_user_id, _is_admin(current_user_id))
    return jsonify(_serialize(task)), 200


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task(current_user_id):
    data = task_create_schema.load(request.get_json() or {})
    task = task_service.create(data, current_user_id, _is_admin(current_user_id))
    return jsonify(_serialize(task)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(current_user_id, task_id):
    data = task_update_schema.load(request.get_json() or {})
    task = task_service.update(task_id, data, current_user_id, _is_admin(current_user_id))
    return jsonify(_serialize(task)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(current_user_id, task_id):
    task_service.delete(task_id, current_user_id, _is_admin(current_user_id))
    return jsonify({'message': 'Task deletada com sucesso'}), 200
