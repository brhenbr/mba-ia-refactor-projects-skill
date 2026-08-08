from flask import Blueprint, jsonify, request

from middleware.auth import admin_required
from services.produto_service import ProdutoService
from validators.produto_validator import ProdutoBuscaSchema, ProdutoSchema

produto_bp = Blueprint("produtos", __name__)
produto_service = ProdutoService()
produto_schema = ProdutoSchema()
produto_busca_schema = ProdutoBuscaSchema()


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    produtos = produto_service.listar()
    return jsonify({"dados": [p.to_dict() for p in produtos], "sucesso": True}), 200


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    params = produto_busca_schema.load(request.args.to_dict())
    resultados = produto_service.buscar(
        params["q"], params["categoria"], params["preco_min"], params["preco_max"]
    )
    return jsonify({"dados": [p.to_dict() for p in resultados], "total": len(resultados), "sucesso": True}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    produto = produto_service.buscar_por_id(produto_id)
    return jsonify({"dados": produto.to_dict(), "sucesso": True}), 200


@produto_bp.route("/produtos", methods=["POST"])
@admin_required
def criar_produto(current_user_id):
    dados = produto_schema.load(request.get_json() or {})
    produto = produto_service.criar(dados)
    return jsonify({"dados": produto.to_dict(), "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
@admin_required
def atualizar_produto(current_user_id, produto_id):
    dados = produto_schema.load(request.get_json() or {})
    produto = produto_service.atualizar(produto_id, dados)
    return jsonify({"dados": produto.to_dict(), "sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
@admin_required
def deletar_produto(current_user_id, produto_id):
    produto_service.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
