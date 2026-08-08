import logging

from flask import Blueprint, jsonify, request

from middleware.auth import admin_required, login_required, owner_or_admin_required
from services.pedido_service import PedidoService
from validators.pedido_validator import PedidoCreateSchema, StatusUpdateSchema

pedido_bp = Blueprint("pedidos", __name__)
pedido_service = PedidoService()
pedido_create_schema = PedidoCreateSchema()
status_update_schema = StatusUpdateSchema()
logger = logging.getLogger(__name__)


@pedido_bp.route("/pedidos", methods=["POST"])
@login_required
def criar_pedido(current_user_id):
    dados = pedido_create_schema.load(request.get_json() or {})
    pedido = pedido_service.criar(current_user_id, dados["itens"])

    logger.info("Pedido %s criado para usuário %s", pedido.id, current_user_id)

    return jsonify({"dados": pedido.to_dict(), "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.route("/pedidos", methods=["GET"])
@admin_required
def listar_todos_pedidos(current_user_id):
    pedidos = pedido_service.listar_todos()
    return jsonify({"dados": [p.to_dict() for p in pedidos], "sucesso": True}), 200


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
@owner_or_admin_required(param_name="usuario_id")
def listar_pedidos_usuario(current_user_id, usuario_id):
    pedidos = pedido_service.listar_por_usuario(usuario_id)
    return jsonify({"dados": [p.to_dict() for p in pedidos], "sucesso": True}), 200


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
@admin_required
def atualizar_status_pedido(current_user_id, pedido_id):
    dados = status_update_schema.load(request.get_json() or {})
    pedido = pedido_service.atualizar_status(pedido_id, dados["status"])

    logger.info("Pedido %s atualizado para status '%s'", pedido_id, dados["status"])

    return jsonify({"dados": pedido.to_dict(), "sucesso": True, "mensagem": "Status atualizado"}), 200
