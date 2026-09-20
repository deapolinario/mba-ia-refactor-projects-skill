# Guidelines de Arquitetura MVC

## Objetivo

Estruturar o projeto em camadas com responsabilidades claras e sem acoplamento.

---

## Estrutura de Diretórios Alvo

```
project/
├── config/
│   ├── __init__.py
│   └── settings.py          # Carrega config de .env
│
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── task.py              # Task model
│   └── base.py              # Base model class
│
├── routes/
│   ├── __init__.py
│   ├── user_routes.py       # GET/POST/PUT/DELETE /users
│   └── task_routes.py       # GET/POST/PUT/DELETE /tasks
│
├── controllers/
│   ├── __init__.py
│   ├── user_controller.py   # Lógica de user (validação, regras)
│   └── task_controller.py   # Lógica de task (validação, regras)
│
├── database.py              # Inicialização do DB
├── app.py                   # Entry point
└── requirements.txt
```

---

## Responsabilidades por Camada

### Config (`config/settings.py`)

**Responsável por:**
- Carregar variáveis de ambiente
- Definir constantes da aplicação
- Validar configuração obrigatória no startup

**O que NÃO deve fazer:**
- Lógica de negócio
- Acesso a banco de dados
- Processamento de requests

**Exemplo:**
```python
# config/settings.py
import os

class Config:
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY não definida")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL não definida")

Config.validate()
```

---

### Models (`models/`)

**Responsável por:**
- Definir estrutura de dados (colunas, tipos)
- Relacionamentos entre entidades
- Métodos de serialização (`to_dict()`)
- Validações de dados básicas

**O que NÃO deve fazer:**
- Queries complexas (use methods simples)
- Lógica de negócio
- HTTP stuff (requests, responses)

**Exemplo:**
```python
# models/user.py
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String)
    role = db.Column(db.String, default='user')
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data
```

---

### Routes (`routes/`)

**Responsável por:**
- Mapear URLs → Controllers
- Extrair parâmetros de request
- Formatar response HTTP
- Validação de entrada básica

**O que NÃO deve fazer:**
- Lógica de negócio complexa
- Queries SQL diretas
- Estado mutável

**Exemplo:**
```python
# routes/user_routes.py
from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController

user_bp = Blueprint('users', __name__)

@user_bp.route('/users', methods=['GET'])
def list_users():
    users = UserController.list_all()
    return jsonify(users), 200

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    result = UserController.create(data)
    return jsonify(result), 201
```

---

### Controllers (`controllers/`)

**Responsável por:**
- Lógica de negócio / regras de domínio
- Coordenar models e services
- Validações complexas
- Orquestração de operações

**O que NÃO deve fazer:**
- Responder HTTP diretamente
- Acesso direto a banco de dados
- Rotear requests

**Exemplo:**
```python
# controllers/user_controller.py
from models.user import User
from database import db

class UserController:
    @staticmethod
    def create(data):
        # Validação
        if not data.get('email'):
            raise ValueError("Email obrigatório")
        
        # Verificar duplicata
        existing = User.query.filter_by(email=data['email']).first()
        if existing:
            raise ValueError("Email já existe")
        
        # Criar usuário
        user = User()
        user.email = data['email']
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return user.to_dict()
```

---

## Padrão de Fluxo (v1.0)

```
HTTP Request
    ↓
Routes (extrai parâmetros)
    ↓
Controller (valida + lógica)
    ↓
Models (acessa dados)
    ↓
Database
    ↓
Controller (processa resultado)
    ↓
Routes (formata response)
    ↓
HTTP Response
```

---

## Validação Pós-Refatoração

Verificar:
- ✅ Sem queries SQL em routes
- ✅ Sem queries SQL em models diretas
- ✅ Sem lógica de negócio em routes
- ✅ Config carregada de `.env`
- ✅ Sem hardcoded secrets
- ✅ Models com `to_dict()` seguro
- ✅ Controllers com métodos reutilizáveis
- ✅ Aplicação inicia sem erros
- ✅ Todos os endpoints funcionam

---

## Exceções Permitidas (v1.0)

Para manter simplicidade na v1.0, permitir:
- Services/ compartilhado entre controllers (não é MVP)
- Models com queries simples (`.filter_by()`)
- Middleware de autenticação em app.py
- Utilidades em utils/ (helpers, validators)
