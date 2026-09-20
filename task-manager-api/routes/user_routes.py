from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController
from controllers.auth_controller import AuthController
from middleware.auth import login_required, role_required

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    return jsonify(UserController.list_all()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    try:
        return jsonify(UserController.get_by_id(user_id)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@user_bp.route('/users', methods=['POST'])
def create_user():
    try:
        user = UserController.create(request.get_json())
        return jsonify(user), 201
    except ValueError as e:
        status = 409 if 'já cadastrado' in str(e) else 400
        return jsonify({'error': str(e)}), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    try:
        user = UserController.update(user_id, request.get_json())
        return jsonify(user), 200
    except ValueError as e:
        if 'não encontrado' in str(e):
            return jsonify({'error': str(e)}), 404
        if 'já cadastrado' in str(e):
            return jsonify({'error': str(e)}), 409
        return jsonify({'error': str(e)}), 400


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    try:
        UserController.delete(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@login_required
def get_user_tasks(user_id):
    try:
        return jsonify(UserController.get_tasks(user_id)), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        result = AuthController.login(data.get('email'), data.get('password'))
        return jsonify({'message': 'Login realizado com sucesso', **result}), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 401
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
