from sqlalchemy import func

from database import db
from models.category import Category
from models.task import Task


class CategoryRepository:
    def find_all(self):
        return Category.query.all()

    def find_by_id(self, category_id):
        return db.session.get(Category, category_id)

    def create(self, category):
        db.session.add(category)
        db.session.commit()
        return category

    def update(self, category, data):
        for key, value in data.items():
            setattr(category, key, value)
        db.session.commit()
        return category

    def delete(self, category):
        db.session.delete(category)
        db.session.commit()

    def task_counts_by_category(self):
        """Single grouped query for the task count of every category, used
        instead of a per-category count() call in a loop."""
        rows = db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
        return dict(rows)
