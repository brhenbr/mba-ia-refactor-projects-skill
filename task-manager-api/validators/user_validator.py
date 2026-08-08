from marshmallow import Schema, fields, validate

VALID_ROLES = ["user", "admin", "manager"]
MIN_PASSWORD_LENGTH = 8


class UserRegisterSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=MIN_PASSWORD_LENGTH))
    # role is intentionally NOT accepted here: public registration always creates a
    # plain 'user' account. Role changes go through UserUpdateSchema by an admin.


class UserUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    password = fields.String(load_only=True, validate=validate.Length(min=MIN_PASSWORD_LENGTH))
    role = fields.String(validate=validate.OneOf(VALID_ROLES))
    active = fields.Boolean()


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
