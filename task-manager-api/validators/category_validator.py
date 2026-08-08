from marshmallow import Schema, fields, validate


class CategorySchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(load_default="", allow_none=True, validate=validate.Length(max=300))
    color = fields.String(load_default="#000000", validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))


class CategoryUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=100))
    description = fields.String(allow_none=True, validate=validate.Length(max=300))
    color = fields.String(validate=validate.Regexp(r"^#[0-9a-fA-F]{6}$"))
