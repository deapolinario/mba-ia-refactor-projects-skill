from sqlalchemy import func
from database import db
from models.category import Category
from models.task import Task
from utils.helpers import is_valid_color, DEFAULT_COLOR
from exceptions import NotFoundError, ValidationError


class CategoryController:

    @staticmethod
    def list_all():
        # v2.2: 1 query com LEFT JOIN + GROUP BY em vez de 1 COUNT() por
        # categoria dentro de um loop (N+1)
        rows = (
            db.session.query(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .all()
        )
        result = []
        for category, task_count in rows:
            data = category.to_dict()
            data['task_count'] = task_count
            result.append(data)
        return result

    @staticmethod
    def create(data):
        if not data:
            raise ValidationError('Dados inválidos')
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        color = data.get('color', DEFAULT_COLOR)
        if not is_valid_color(color):
            raise ValidationError('Cor inválida (formato esperado: #RRGGBB)')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = color

        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    @staticmethod
    def update(cat_id, data):
        category = Category.query.get(cat_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            if not is_valid_color(data['color']):
                raise ValidationError('Cor inválida (formato esperado: #RRGGBB)')
            category.color = data['color']

        db.session.commit()
        return category.to_dict()

    @staticmethod
    def delete(cat_id):
        category = Category.query.get(cat_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        db.session.delete(category)
        db.session.commit()
