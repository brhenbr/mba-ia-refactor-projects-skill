from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    """Non-deprecated replacement for datetime.utcnow(). Returns a naive
    datetime (no tzinfo) to match the naive DateTime columns used across
    the models — mixing aware and naive datetimes raises TypeError on
    comparison."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
