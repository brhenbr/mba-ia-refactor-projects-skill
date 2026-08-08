from marshmallow import Schema, fields, post_load, validate

VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DEFAULT_PRIORITY = 3


def _normalize_tags(data):
    if "tags" in data and data["tags"] is not None:
        tags = data["tags"]
        data["tags"] = ",".join(tags) if isinstance(tags, list) else tags
    return data


class TaskCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=MIN_TITLE_LENGTH, max=MAX_TITLE_LENGTH))
    description = fields.String(load_default="", allow_none=True)
    status = fields.String(load_default="pending", validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Integer(load_default=DEFAULT_PRIORITY, validate=validate.Range(min=1, max=5))
    user_id = fields.Integer(load_default=None, allow_none=True)
    category_id = fields.Integer(load_default=None, allow_none=True)
    due_date = fields.DateTime(format="%Y-%m-%d", load_default=None, allow_none=True)
    tags = fields.Raw(load_default=None, allow_none=True)

    @post_load
    def normalize_tags(self, data, **kwargs):
        return _normalize_tags(data)


class TaskUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=MIN_TITLE_LENGTH, max=MAX_TITLE_LENGTH))
    description = fields.String(allow_none=True)
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Integer(validate=validate.Range(min=1, max=5))
    user_id = fields.Integer(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    due_date = fields.DateTime(format="%Y-%m-%d", allow_none=True)
    tags = fields.Raw(allow_none=True)

    @post_load
    def normalize_tags(self, data, **kwargs):
        return _normalize_tags(data)


class TaskSearchSchema(Schema):
    q = fields.String(load_default="")
    status = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=1, max=5))
    user_id = fields.Integer(load_default=None, allow_none=True)
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
