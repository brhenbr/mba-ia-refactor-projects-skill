from database import db
from models.user import User


class UserRepository:
    def find_all(self):
        return User.query.all()

    def find_by_id(self, user_id):
        return db.session.get(User, user_id)

    def find_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def create(self, user):
        db.session.add(user)
        db.session.commit()
        return user

    def update(self, user, data):
        for key, value in data.items():
            setattr(user, key, value)
        db.session.commit()
        return user

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()
