from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task

ACTIVE_STATUSES_EXCLUDED_FROM_OVERDUE = ["done", "cancelled"]


class TaskRepository:
    def _eager(self, query):
        return query.options(joinedload(Task.user), joinedload(Task.category))

    def find_all(self, user_id=None):
        query = self._eager(Task.query)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.order_by(Task.id).all()

    def find_by_id(self, task_id):
        return self._eager(Task.query.filter_by(id=task_id)).first()

    def find_by_user(self, user_id):
        return self._eager(Task.query.filter_by(user_id=user_id)).order_by(Task.id).all()

    def search(self, q=None, status=None, priority=None, user_id=None, owner_id=None):
        """owner_id scopes results to a single user (non-admin callers);
        user_id is the optional filter param an admin may pass explicitly."""
        query = self._eager(Task.query)

        if owner_id is not None:
            query = query.filter(Task.user_id == owner_id)
        elif user_id is not None:
            query = query.filter(Task.user_id == user_id)

        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(Task.title.like(like), Task.description.like(like)))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)

        return query.order_by(Task.id).all()

    def create(self, task):
        db.session.add(task)
        db.session.commit()
        return task

    def update(self, task, data):
        for key, value in data.items():
            setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return task

    def delete(self, task):
        db.session.delete(task)
        db.session.commit()

    def count_total(self, user_id=None):
        query = Task.query
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.count()

    def count_by_status(self, status, user_id=None):
        query = Task.query.filter_by(status=status)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.count()

    def count_by_priority(self, priority, user_id=None):
        query = Task.query.filter_by(priority=priority)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.count()

    def _overdue_filter(self, query):
        return query.filter(
            Task.due_date.isnot(None),
            Task.due_date < datetime.utcnow(),
            Task.status.notin_(ACTIVE_STATUSES_EXCLUDED_FROM_OVERDUE),
        )

    def count_overdue(self, user_id=None):
        query = Task.query
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return self._overdue_filter(query).count()

    def find_overdue(self, user_id=None):
        query = Task.query
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return self._overdue_filter(query).order_by(Task.due_date).all()

    def count_created_since(self, since, user_id=None):
        query = Task.query.filter(Task.created_at >= since)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.count()

    def count_completed_since(self, since, user_id=None):
        query = Task.query.filter(Task.status == "done", Task.updated_at >= since)
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        return query.count()

    def counts_by_user_and_status(self):
        """Single grouped query used to build per-user productivity stats
        without looping a query per user (the original N+1)."""
        return (
            db.session.query(Task.user_id, Task.status, func.count(Task.id))
            .group_by(Task.user_id, Task.status)
            .all()
        )
