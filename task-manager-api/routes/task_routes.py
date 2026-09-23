from flask import Blueprint, request, jsonify, g
from controllers.task_controller import TaskController
from middleware.auth import login_required
from exceptions import NotFoundError, ValidationError

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    try:
        return jsonify(TaskController.list_all()), 200
    except Exception:
        return jsonify({'error': 'Erro interno'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    try:
        return jsonify(TaskController.get_by_id(task_id)), 200
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        task = TaskController.create(request.get_json(), g.current_user)
        return jsonify(task), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    try:
        task = TaskController.update(task_id, request.get_json(), g.current_user)
        return jsonify(task), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    try:
        TaskController.delete(task_id, g.current_user)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@task_bp.route('/tasks/search', methods=['GET'])
@login_required
def search_tasks():
    results = TaskController.search(
        request.args.get('q', ''),
        request.args.get('status', ''),
        request.args.get('priority', ''),
        request.args.get('user_id', '')
    )
    return jsonify(results), 200


@task_bp.route('/tasks/stats', methods=['GET'])
@login_required
def task_stats():
    return jsonify(TaskController.stats()), 200
