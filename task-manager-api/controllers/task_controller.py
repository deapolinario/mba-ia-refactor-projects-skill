from sqlalchemy.orm import joinedload
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import process_task_data, DEFAULT_PRIORITY
from exceptions import NotFoundError, ValidationError


def _task_to_dict_with_relations(task):
    """
    v2.2 - centraliza a serialização de task + user_name/category_name +
    overdue, usando Task.is_overdue() em vez de reimplementar a lógica
    (era duplicada em 4 lugares diferentes no código original).
    """
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


class TaskController:

    @staticmethod
    def list_all():
        # v2.2: joinedload elimina o N+1 que buscava user/category por task
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        return [_task_to_dict_with_relations(t) for t in tasks]

    @staticmethod
    def get_by_id(task_id):
        task = db.session.get(
            Task, task_id,
            options=[joinedload(Task.user), joinedload(Task.category)]
        )
        if not task:
            raise NotFoundError('Task não encontrada')
        return _task_to_dict_with_relations(task)

    @staticmethod
    def create(data, requester):
        if not data:
            raise ValidationError('Dados inválidos')
        if not data.get('title'):
            raise ValidationError('Título é obrigatório')

        validated, error = process_task_data(data)
        if error:
            raise ValidationError(error)

        user_id = data.get('user_id', requester.id)
        if user_id != requester.id and requester.role not in ('admin', 'manager'):
            raise PermissionError('Você só pode criar tasks para si mesmo')
        if user_id and not db.session.get(User, user_id):
            raise NotFoundError('Usuário não encontrado')

        category_id = data.get('category_id')
        if category_id and not db.session.get(Category, category_id):
            raise NotFoundError('Categoria não encontrada')

        task = Task()
        task.title = validated.get('title')
        task.description = validated.get('description', '')
        task.status = validated.get('status', 'pending')
        task.priority = validated.get('priority', DEFAULT_PRIORITY)
        task.user_id = user_id
        task.category_id = category_id
        task.due_date = validated.get('due_date')
        task.tags = validated.get('tags')

        db.session.add(task)
        db.session.commit()
        return task.to_dict()

    @staticmethod
    def update(task_id, data, requester):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        if task.user_id != requester.id and requester.role not in ('admin', 'manager'):
            raise PermissionError('Você só pode editar suas próprias tasks')
        if not data:
            raise ValidationError('Dados inválidos')

        validated, error = process_task_data(data, existing_task=task)
        if error:
            raise ValidationError(error)

        if 'user_id' in data:
            if data['user_id'] and not db.session.get(User, data['user_id']):
                raise NotFoundError('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not db.session.get(Category, data['category_id']):
                raise NotFoundError('Categoria não encontrada')
            task.category_id = data['category_id']

        for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
            if field in validated:
                setattr(task, field, validated[field])

        db.session.commit()
        return task.to_dict()

    @staticmethod
    def delete(task_id, requester):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        if task.user_id != requester.id and requester.role not in ('admin', 'manager'):
            raise PermissionError('Você só pode deletar suas próprias tasks')
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def search(query, status, priority, user_id):
        tasks_query = Task.query
        if query:
            tasks_query = tasks_query.filter(
                db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
            )
        if status:
            tasks_query = tasks_query.filter(Task.status == status)
        if priority:
            tasks_query = tasks_query.filter(Task.priority == int(priority))
        if user_id:
            tasks_query = tasks_query.filter(Task.user_id == int(user_id))

        return [t.to_dict() for t in tasks_query.all()]

    @staticmethod
    def stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        # v2.2: usa Task.is_overdue() em vez de reimplementar a checagem
        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
