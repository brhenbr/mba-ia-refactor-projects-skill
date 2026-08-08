from marshmallow import Schema, fields, validate


class UsuarioRegistroSchema(Schema):
    nome = fields.String(required=True, validate=validate.Length(min=2, max=200))
    email = fields.Email(required=True)
    senha = fields.String(required=True, validate=validate.Length(min=8))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    senha = fields.String(required=True)
