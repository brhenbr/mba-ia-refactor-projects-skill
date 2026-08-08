from flask_jwt_extended import create_access_token

from exceptions import BusinessException, ConflictException, ForbiddenException, NotFoundException
from models.user import User
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo=None, task_repo=None):
        self.user_repo = user_repo or UserRepository()
        self.task_repo = task_repo or TaskRepository()

    def list_all(self):
        return self.user_repo.find_all()

    def get_by_id(self, user_id):
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("Usuário não encontrado")
        return user

    def register(self, data):
        if self.user_repo.find_by_email(data["email"]):
            raise ConflictException("Email já cadastrado")

        user = User(name=data["name"], email=data["email"], role="user")
        user.set_password(data["password"])
        return self.user_repo.create(user)

    def authenticate(self, email, password):
        user = self.user_repo.find_by_email(email)
        if not user or not user.check_password(password):
            raise BusinessException("Credenciais inválidas", status_code=401)
        if not user.active:
            raise ForbiddenException("Usuário inativo")

        token = create_access_token(identity=str(user.id))
        return user, token

    def update(self, user_id, data, acting_user_is_admin):
        user = self.get_by_id(user_id)

        if ("role" in data or "active" in data) and not acting_user_is_admin:
            raise ForbiddenException("Apenas administradores podem alterar role/active")

        if "email" in data:
            existing = self.user_repo.find_by_email(data["email"])
            if existing and existing.id != user_id:
                raise ConflictException("Email já cadastrado")

        password = data.pop("password", None)
        if password:
            user.set_password(password)

        return self.user_repo.update(user, data)

    def delete(self, user_id):
        user = self.get_by_id(user_id)
        for task in self.task_repo.find_by_user(user_id):
            self.task_repo.delete(task)
        self.user_repo.delete(user)

    def get_user_tasks(self, user_id):
        self.get_by_id(user_id)
        return self.task_repo.find_by_user(user_id)
