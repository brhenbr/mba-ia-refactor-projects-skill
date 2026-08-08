from datetime import datetime, timedelta

from exceptions import NotFoundException
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository

VALID_STATUSES = ["pending", "in_progress", "done", "cancelled"]
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}


class ReportService:
    def __init__(self, task_repo=None, user_repo=None, category_repo=None):
        self.task_repo = task_repo or TaskRepository()
        self.user_repo = user_repo or UserRepository()
        self.category_repo = category_repo or CategoryRepository()

    def summary(self):
        tasks_by_status = {status: self.task_repo.count_by_status(status) for status in VALID_STATUSES}
        tasks_by_priority = {
            label: self.task_repo.count_by_priority(priority) for priority, label in PRIORITY_LABELS.items()
        }

        overdue_tasks = self.task_repo.find_overdue()
        overdue_list = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": str(t.due_date),
                "days_overdue": (datetime.utcnow() - t.due_date).days,
            }
            for t in overdue_tasks
        ]

        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        return {
            "generated_at": str(datetime.utcnow()),
            "overview": {
                "total_tasks": self.task_repo.count_total(),
                "total_users": len(self.user_repo.find_all()),
                "total_categories": len(self.category_repo.find_all()),
            },
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "overdue": {"count": len(overdue_list), "tasks": overdue_list},
            "recent_activity": {
                "tasks_created_last_7_days": self.task_repo.count_created_since(seven_days_ago),
                "tasks_completed_last_7_days": self.task_repo.count_completed_since(seven_days_ago),
            },
            "user_productivity": self._user_productivity(),
        }

    def _user_productivity(self):
        """Built from a single grouped query (counts_by_user_and_status) instead of
        running one Task query per user, which was the original N+1."""
        users = {u.id: u.name for u in self.user_repo.find_all()}
        totals = {uid: 0 for uid in users}
        completed = {uid: 0 for uid in users}

        for user_id, status, count in self.task_repo.counts_by_user_and_status():
            if user_id not in users:
                continue
            totals[user_id] += count
            if status == "done":
                completed[user_id] += count

        return [
            {
                "user_id": uid,
                "user_name": name,
                "total_tasks": totals[uid],
                "completed_tasks": completed[uid],
                "completion_rate": round((completed[uid] / totals[uid]) * 100, 2) if totals[uid] > 0 else 0,
            }
            for uid, name in users.items()
        ]

    def for_user(self, user_id):
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("Usuário não encontrado")

        tasks = self.task_repo.find_by_user(user_id)
        by_status = {status: 0 for status in VALID_STATUSES}
        high_priority = 0
        overdue = 0

        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        total = len(tasks)
        done = by_status["done"]

        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": {
                "total_tasks": total,
                "done": done,
                "pending": by_status["pending"],
                "in_progress": by_status["in_progress"],
                "cancelled": by_status["cancelled"],
                "overdue": overdue,
                "high_priority": high_priority,
                "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
