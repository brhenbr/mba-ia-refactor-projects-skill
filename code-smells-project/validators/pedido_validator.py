from marshmallow import Schema, fields, validate

from models.pedido import STATUS_VALIDOS


class ItemPedidoSchema(Schema):
    produto_id = fields.Integer(required=True)
    quantidade = fields.Integer(required=True, validate=validate.Range(min=1))


class PedidoCreateSchema(Schema):
    itens = fields.List(fields.Nested(ItemPedidoSchema), required=True, validate=validate.Length(min=1))


class StatusUpdateSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf(STATUS_VALIDOS))
