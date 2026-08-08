import os

from flask import Blueprint, jsonify

from database import db
from middleware.auth import admin_required
from models.item_pedido import ItemPedido
from models.pedido import Pedido
from models.produto import Produto

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database(current_user_id):
    """Apaga produtos/pedidos para fins de teste. Bloqueado em produção."""
    if os.getenv("FLASK_ENV") == "production":
        return jsonify({"erro": "Operação não permitida em produção", "sucesso": False}), 403

    db.session.query(ItemPedido).delete()
    db.session.query(Pedido).delete()
    db.session.query(Produto).delete()
    db.session.commit()

    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
