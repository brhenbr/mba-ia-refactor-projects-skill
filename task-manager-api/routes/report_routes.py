from flask import Blueprint, jsonify

from middleware.auth import admin_required, owner_or_admin_required
from services.report_service import ReportService

report_bp = Blueprint('reports', __name__)

report_service = ReportService()


@report_bp.route('/reports/summary', methods=['GET'])
@admin_required
def summary_report(current_user_id):
    return jsonify(report_service.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@owner_or_admin_required('user_id')
def user_report(current_user_id, user_id):
    return jsonify(report_service.for_user(user_id)), 200
