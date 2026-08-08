from exceptions import ForbiddenException, NotFoundException
from models.task import Task
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from services.notification_service import NotificationService


class TaskService:
    def __init__(self, task_repo=None, user_repo=None, category_repo=None, notifier=None):
        self.task_repo = task_repo or TaskRepository()
        self.user_repo = user_repo or UserRepository()
        self.category_repo = category_repo or CategoryRepository()
        self.notifier = notifier or NotificationService()

    def list_for(self, current_user_id, is_admin):
        owner_id = None if is_admin else current_user_id
        return self.task_repo.find_all(user_id=owner_id)

    def search(self, current_user_id, is_admin, filters):
        owner_id = None if is_admin else current_user_id
        return self.task_repo.search(
            q=filters.get("q"),
            status=filters.get("status"),
            priority=filters.get("priority"),
            user_id=filters.get("user_id") if is_admin else None,
            owner_id=owner_id,
        )

    def get_owned(self, task_id, current_user_id, is_admin):
        task = self.task_repo.find_by_id(task_id)
        if not task:
            raise NotFoundException("Task não encontrada")
        if not is_admin and task.user_id != current_user_id:
            raise ForbiddenException("Sem permissão")
        return task

    def create(self, data, current_user_id, is_admin):
        assignee_id = data.get("user_id") if is_admin else current_user_id

        assignee = None
        if assignee_id:
            assignee = self.user_repo.find_by_id(assignee_id)
            if not assignee:
                raise NotFoundException("Usuário não encontrado")

        if data.get("category_id") and not self.category_repo.find_by_id(data["category_id"]):
            raise NotFoundException("Categoria não encontrada")

        task = Task(
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", 3),
            user_id=assignee_id,
            category_id=data.get("category_id"),
            due_date=data.get("due_date"),
            tags=data.get("tags"),
        )
        task = self.task_repo.create(task)

        if assignee:
            self.notifier.notify_task_assigned(assignee, task)

        return task

    def update(self, task_id, data, current_user_id, is_admin):
        task = self.get_owned(task_id, current_user_id, is_admin)

        if "user_id" in data:
            if not is_admin and data["user_id"] != current_user_id:
                raise ForbiddenException("Apenas administradores podem reatribuir tasks")
            if data["user_id"] and not self.user_repo.find_by_id(data["user_id"]):
                raise NotFoundException("Usuário não encontrado")

        if data.get("category_id") and not self.category_repo.find_by_id(data["category_id"]):
            raise NotFoundException("Categoria não encontrada")

        return self.task_repo.update(task, data)

    def delete(self, task_id, current_user_id, is_admin):
        task = self.get_owned(task_id, current_user_id, is_admin)
        self.task_repo.delete(task)

    def stats(self, current_user_id, is_admin):
        owner_id = None if is_admin else current_user_id
        total = self.task_repo.count_total(owner_id)
        done = self.task_repo.count_by_status("done", owner_id)

        return {
            "total": total,
            "pending": self.task_repo.count_by_status("pending", owner_id),
            "in_progress": self.task_repo.count_by_status("in_progress", owner_id),
            "done": done,
            "cancelled": self.task_repo.count_by_status("cancelled", owner_id),
            "overdue": self.task_repo.count_overdue(owner_id),
            "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
        }
