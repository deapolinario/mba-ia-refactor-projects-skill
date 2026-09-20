from sqlalchemy import func
from datetime import datetime, timedelta
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import format_date, calculate_percentage


class ReportController:

    @staticmethod
    def summary():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        status_counts = dict(
            db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        )
        priority_counts = dict(
            db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        )

        # v2.2: usa Task.is_overdue() em vez de reimplementar a checagem manual
        all_tasks = Task.query.all()
        overdue_tasks = [t for t in all_tasks if t.is_overdue()]

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done', Task.updated_at >= seven_days_ago
        ).count()

        # v2.2: 1 query com GROUP BY para total por usuário + 1 para completed
        # por usuário, em vez de 1 query de tasks por usuário dentro de um loop (N+1)
        totals_by_user = dict(
            db.session.query(Task.user_id, func.count(Task.id))
            .group_by(Task.user_id).all()
        )
        completed_by_user = dict(
            db.session.query(Task.user_id, func.count(Task.id))
            .filter(Task.status == 'done')
            .group_by(Task.user_id).all()
        )

        user_stats = []
        for u in User.query.all():
            total = totals_by_user.get(u.id, 0)
            completed = completed_by_user.get(u.id, 0)
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total)
            })

        return {
            'generated_at': format_date(datetime.utcnow()),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': status_counts.get('pending', 0),
                'in_progress': status_counts.get('in_progress', 0),
                'done': status_counts.get('done', 0),
                'cancelled': status_counts.get('cancelled', 0),
            },
            'tasks_by_priority': {
                'critical': priority_counts.get(1, 0),
                'high': priority_counts.get(2, 0),
                'medium': priority_counts.get(3, 0),
                'low': priority_counts.get(4, 0),
                'minimal': priority_counts.get(5, 0),
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'due_date': format_date(t.due_date),
                        'days_overdue': (datetime.utcnow() - t.due_date).days
                    }
                    for t in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    @staticmethod
    def user_report(user_id):
        user = User.query.get(user_id)
        if not user:
            raise ValueError('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)

        # v2.2: usa Task.is_overdue() em vez de reimplementar a checagem manual
        status_counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': status_counts['done'],
                'pending': status_counts['pending'],
                'in_progress': status_counts['in_progress'],
                'cancelled': status_counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(status_counts['done'], total)
            }
        }
