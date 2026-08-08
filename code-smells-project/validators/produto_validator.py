from marshmallow import Schema, fields, validate

from models.produto import CATEGORIAS_VALIDAS


class ProdutoSchema(Schema):
    nome = fields.String(required=True, validate=validate.Length(min=2, max=200))
    descricao = fields.String(load_default="", allow_none=True)
    preco = fields.Float(required=True, validate=validate.Range(min=0))
    estoque = fields.Integer(required=True, validate=validate.Range(min=0))
    categoria = fields.String(load_default="geral", validate=validate.OneOf(CATEGORIAS_VALIDAS))


class ProdutoBuscaSchema(Schema):
    q = fields.String(load_default="")
    categoria = fields.String(load_default=None, allow_none=True)
    preco_min = fields.Float(load_default=None, allow_none=True)
    preco_max = fields.Float(load_default=None, allow_none=True)
