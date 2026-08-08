from flask import Blueprint, jsonify

from database import db
from models.produto import Produto
from models.usuario import Usuario
from models.pedido import Pedido

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    db.session.execute(db.select(1))

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": db.session.query(Produto).count(),
            "usuarios": db.session.query(Usuario).count(),
            "pedidos": db.session.query(Pedido).count(),
        },
        "versao": "2.0.0",
    }), 200
