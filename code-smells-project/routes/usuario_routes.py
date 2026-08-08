from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from middleware.auth import admin_required, owner_or_admin_required
from services.usuario_service import UsuarioService
from validators.usuario_validator import LoginSchema, UsuarioRegistroSchema

usuario_bp = Blueprint("usuarios", __name__)
usuario_service = UsuarioService()
registro_schema = UsuarioRegistroSchema()
login_schema = LoginSchema()


@usuario_bp.route("/usuarios", methods=["GET"])
@admin_required
def listar_usuarios(current_user_id):
    usuarios = usuario_service.listar()
    return jsonify({"dados": [u.to_dict() for u in usuarios], "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
@owner_or_admin_required(param_name="usuario_id")
def buscar_usuario(current_user_id, usuario_id):
    usuario = usuario_service.buscar_por_id(usuario_id)
    return jsonify({"dados": usuario.to_dict(), "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = registro_schema.load(request.get_json() or {})
    usuario = usuario_service.registrar(dados)
    return jsonify({"dados": usuario.to_dict(), "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = login_schema.load(request.get_json() or {})
    usuario = usuario_service.autenticar(dados["email"], dados["senha"])
    token = create_access_token(identity=str(usuario.id), additional_claims={"tipo": usuario.tipo})
    return jsonify({
        "dados": {"usuario": usuario.to_dict(), "access_token": token},
        "sucesso": True,
        "mensagem": "Login OK",
    }), 200
