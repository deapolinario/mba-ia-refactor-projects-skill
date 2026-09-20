from flask import Blueprint, request, jsonify
from controllers.category_controller import CategoryController
from middleware.auth import login_required, role_required

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(CategoryController.list_all()), 200


@category_bp.route('/categories', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def create_category():
    try:
        category = CategoryController.create(request.get_json())
        return jsonify(category), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
@role_required('admin', 'manager')
def update_category(cat_id):
    try:
        category = CategoryController.update(cat_id, request.get_json())
        return jsonify(category), 200
    except ValueError as e:
        status = 404 if 'não encontrada' in str(e) else 400
        return jsonify({'error': str(e)}), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'manager')
def delete_category(cat_id):
    try:
        CategoryController.delete(cat_id)
        return jsonify({'message': 'Categoria deletada'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
