from models.user import User
from auth.tokens import generate_token
from exceptions import ValidationError


class AuthController:

    @staticmethod
    def login(email, password):
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise PermissionError('Credenciais inválidas')

        if not user.active:
            raise PermissionError('Usuário inativo')

        token = generate_token(user.id)
        return {'user': user.to_dict(), 'token': token}
