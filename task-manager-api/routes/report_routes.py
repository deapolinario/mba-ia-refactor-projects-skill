from flask import Blueprint, jsonify, g
from controllers.report_controller import ReportController
from middleware.auth import login_required
from exceptions import NotFoundError

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@login_required
def summary_report():
    return jsonify(ReportController.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@login_required
def user_report(user_id):
    try:
        return jsonify(ReportController.user_report(user_id, g.current_user)), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
