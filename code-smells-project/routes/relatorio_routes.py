from flask import Blueprint, jsonify

from middleware.auth import admin_required
from services.relatorio_service import RelatorioService

relatorio_bp = Blueprint("relatorios", __name__)
relatorio_service = RelatorioService()


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
@admin_required
def relatorio_vendas(current_user_id):
    relatorio = relatorio_service.vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
