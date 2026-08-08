from exceptions import NotFoundException
from models.category import Category
from repositories.category_repository import CategoryRepository


class CategoryService:
    def __init__(self, category_repo=None):
        self.category_repo = category_repo or CategoryRepository()

    def list_all(self):
        categories = self.category_repo.find_all()
        task_counts = self.category_repo.task_counts_by_category()

        result = []
        for category in categories:
            data = category.to_dict()
            data["task_count"] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def get_by_id(self, category_id):
        category = self.category_repo.find_by_id(category_id)
        if not category:
            raise NotFoundException("Categoria não encontrada")
        return category

    def create(self, data):
        category = Category(name=data["name"], description=data.get("description", ""), color=data.get("color", "#000000"))
        return self.category_repo.create(category)

    def update(self, category_id, data):
        category = self.get_by_id(category_id)
        return self.category_repo.update(category, data)

    def delete(self, category_id):
        category = self.get_by_id(category_id)
        self.category_repo.delete(category)
