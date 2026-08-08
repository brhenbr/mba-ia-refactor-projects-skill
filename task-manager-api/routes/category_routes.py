from flask import Blueprint, jsonify, request

from middleware.auth import admin_required, login_required
from services.category_service import CategoryService
from validators.category_validator import CategorySchema, CategoryUpdateSchema

category_bp = Blueprint('categories', __name__)

category_service = CategoryService()
category_schema = CategorySchema()
category_update_schema = CategoryUpdateSchema()


@category_bp.route('/categories', methods=['GET'])
@login_required
def get_categories(current_user_id):
    return jsonify(category_service.list_all()), 200


@category_bp.route('/categories', methods=['POST'])
@admin_required
def create_category(current_user_id):
    data = category_schema.load(request.get_json() or {})
    category = category_service.create(data)
    return jsonify(category.to_dict()), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(current_user_id, category_id):
    data = category_update_schema.load(request.get_json() or {})
    category = category_service.update(category_id, data)
    return jsonify(category.to_dict()), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(current_user_id, category_id):
    category_service.delete(category_id)
    return jsonify({'message': 'Categoria deletada'}), 200
