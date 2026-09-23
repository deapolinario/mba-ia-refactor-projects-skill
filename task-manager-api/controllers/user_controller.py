from database import db
from models.user import User
from models.task import Task
from config import Config
from utils.helpers import validate_email, MIN_PASSWORD_LENGTH
from exceptions import NotFoundError, ConflictError, ValidationError


class UserController:

    @staticmethod
    def list_all():
        return [u.to_dict() for u in User.query.all()]

    @staticmethod
    def get_by_id(user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in user.tasks]
        return data

    @staticmethod
    def create(data):
        """
        v3.0 - fix de escalação de privilégio: este endpoint é público
        (cadastro de conta) e aceitava um campo 'role' no payload sem
        nenhuma restrição — qualquer visitante anônimo podia se cadastrar
        direto como 'admin'. Confirmado via exploit manual. Cadastro
        público agora sempre cria com role='user'; promover alguém a
        admin/manager só é possível via PUT /users/:id por um admin
        existente (ver UserController.update).
        """
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not validate_email(email):
            raise ValidationError('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if User.query.filter_by(email=email).first():
            raise ConflictError('Email já cadastrado')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = 'user'

        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    @staticmethod
    def update(user_id, data, requester):
        """
        v3.0 - fix de escalação de privilégio: a rota exigia login, mas
        nada impedia um usuário comum de editar OUTRO usuário, ou de
        alterar role/active (o próprio ou de terceiros). Confirmado via
        exploit manual: usuário 'user' promovia qualquer conta a 'admin'
        através deste endpoint.

        Regra: um usuário só edita a si mesmo, exceto admin (edita qualquer
        um). 'role'/'active' só podem ser alterados por admin, mesmo que o
        alvo seja o próprio usuário (evita autopromoção).
        """
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        if not data:
            raise ValidationError('Dados inválidos')

        is_self = requester.id == user_id
        is_admin = requester.role == 'admin'

        if not is_self and not is_admin:
            raise PermissionError('Você só pode editar seu próprio usuário')

        if ('role' in data or 'active' in data) and not is_admin:
            raise PermissionError('Apenas administradores podem alterar role/active')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not validate_email(data['email']):
                raise ValidationError('Email inválido')
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in Config.VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    @staticmethod
    def delete(user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        Task.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def get_tasks(user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        tasks = Task.query.filter_by(user_id=user_id).all()
        result = []
        for t in tasks:
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            result.append(data)
        return result
