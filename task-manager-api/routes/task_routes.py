from flask import Blueprint, request, jsonify
from controllers.task_controller import TaskController
from middleware.auth import login_required

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
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        task = TaskController.create(request.get_json())
        return jsonify(task), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    try:
        task = TaskController.update(task_id, request.get_json())
        return jsonify(task), 200
    except ValueError as e:
        status = 404 if 'não encontrada' in str(e) else 400
        return jsonify({'error': str(e)}), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    try:
        TaskController.delete(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except ValueError as e:
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
