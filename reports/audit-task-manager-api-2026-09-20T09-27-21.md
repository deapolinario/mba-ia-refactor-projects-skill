# Relatório de Auditoria - task-manager-api

**Data:** 2026-09-20 09:27:21
**Stack:** Python 3.x + Flask 2.x + SQLAlchemy + SQLite
**Domínio:** Task Manager API (users, tasks, categories, notifications)

---

## Resumo Executivo

- **CRITICAL:** 3 achados
- **HIGH:** 2 achados
- **MEDIUM:** 4 achados
- **Total:** 9 achados

---

## Findings Detalhados

### [CRITICAL] Senha Exposta em JSON

**Arquivo:** `models/user.py` + `routes/user_routes.py` (Linhas: 21, 33, 85, 129, 209)

**Descrição:**
Método `to_dict()` inclui `password` na resposta JSON. Endpoints retornam hashes MD5 de senhas.

**Código Problemático:**
```python
# models/user.py linha 21
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,  # ❌ Expõe hash!
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at)
    }

# routes/user_routes.py linha 33
data = user.to_dict()  # Retorna com password!
```

**Impacto:**
- Hashes MD5 expostos em responses HTTP
- Quebráveis em rainbow tables
- Visível em logs e monitoramento

**Refatoração Proposta:**
```python
def to_dict(self, include_password=False):
    data = {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at)
    }
    if include_password:
        data['password'] = self.password
    return data

# Usar seguramente
user_data = user.to_dict(include_password=False)
```

---

### [CRITICAL] Hardcoded Email Credentials

**Arquivo:** `services/notification_service.py` (Linhas: 9-10)

**Descrição:**
Credenciais de email embarcadas no código.

**Código Problemático:**
```python
email_user = 'taskmanager@gmail.com'
email_password = 'senha123'
```

**Impacto:**
- Qualquer pessoa pode enviar emails como a aplicação
- Comprometimento de sistema de email

**Refatoração Proposta:**
```python
# config.py
import os

class Config:
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    
    @classmethod
    def validate(cls):
        if not cls.EMAIL_USER or not cls.EMAIL_PASSWORD:
            raise ValueError("Email credentials not set in environment")

# .env
EMAIL_USER=taskmanager@gmail.com
EMAIL_PASSWORD=senha123
```

---

### [CRITICAL] Hardcoded SECRET_KEY

**Arquivo:** `app.py` (Linha: 13)

**Descrição:**
Chave secreta embarcada no código-fonte.

**Código Problemático:**
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
```

**Impacto:**
- Qualquer pessoa com acesso ao repo falsifica sessões
- Impossível rodar em produção

**Refatoração Proposta:**
```python
from config import Config
app.config['SECRET_KEY'] = Config.SECRET_KEY
```

---

### [HIGH] MD5 para Hashing de Senhas

**Arquivo:** `models/user.py` (Linha: 29)

**Descrição:**
Usar MD5 para hash de senha é inseguro. MD5 é quebrado por rainbow tables.

**Código Problemático:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Impacto:**
- Rainbow tables quebram em 0.01 segundos
- Violação de OWASP A02:2021

**Refatoração Proposta:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd, method='pbkdf2:sha256')

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

---

### [HIGH] N+1 Queries

**Arquivo:** `routes/task_routes.py` (Linhas: 41-46, 50-56)

**Descrição:**
Para cada task, faz query de User e Category separadamente.

**Código Problemático:**
```python
# Linha 41-46
tasks = Task.query.all()
for task in tasks:
    user = User.query.get(task.user_id)  # +1 query por task
    category = Category.query.get(task.category_id)  # +1 query por task
```

**Impacto:**
- Performance degradada exponencialmente
- 100 tasks = 200+ queries ao invés de 1

**Refatoração Proposta:**
```python
from sqlalchemy.orm import joinedload

# Usar eager loading
tasks = Task.query.options(
    joinedload('user'),
    joinedload('category')
).all()

# Agora todos os dados estão carregados em 1 query
```

---

### [MEDIUM] DEBUG Mode Ativo

**Arquivo:** `app.py` (Linha: 34)

**Descrição:**
`app.run(debug=True)` em ambiente que se apresenta como produção.

**Código Problemático:**
```python
app.run(debug=True)
```

**Impacto:**
- Stack traces expostos
- Reloader de código ativo
- Information disclosure

**Refatoração Proposta:**
```python
from config import Config

app.run(debug=Config.DEBUG)

# .env
DEBUG=False
```

---

### [MEDIUM] Global State em Service

**Arquivo:** `services/notification_service.py` (Linha: 6)

**Descrição:**
`self.notifications` compartilhado entre todas as instâncias.

**Código Problemático:**
```python
class NotificationService:
    def __init__(self):
        self.notifications = []  # ❌ Compartilhado!
```

**Impacto:**
- Notificações de um usuário vazam para outro
- Comportamento impredizível

**Refatoração Proposta:**
```python
# Usar singleton com escopo de request
@app.before_request
def init_notifications():
    g.notifications = []

# Ou usar dependency injection
class NotificationService:
    def __init__(self):
        pass  # Sem estado compartilhado
```

---

### [MEDIUM] Bare Except sem Tipo

**Arquivo:** `routes/task_routes.py` (Linha: 62)

**Descrição:**
`except:` sem tipo de exceção silencia tudo.

**Código Problemático:**
```python
try:
    # ... código ...
except:  # ❌ Silencia TUDO
    return jsonify({'error': 'Erro'}), 500
```

**Impacto:**
- Exceções legítimas são silenciadas
- Difícil debugar
- Memory leaks não detectados

**Refatoração Proposta:**
```python
try:
    # ... código ...
except ValueError as e:
    logger.error(f"Validation error: {e}")
    return jsonify({'error': 'Invalid input'}), 400
except Exception as e:
    logger.exception("Unexpected error")
    return jsonify({'error': 'Internal server error'}), 500
```

---

### [MEDIUM] Duplicação de Lógica

**Arquivo:** `routes/task_routes.py` (Linhas: 30-39 vs 71-80)

**Descrição:**
Cálculo de `overdue` repetido em 2 lugares.

**Código Problemático:**
```python
# Linhas 30-39
if t.due_date < datetime.utcnow():
    if t.status != 'done':
        task_data['overdue'] = True

# Linhas 71-80 (DUPLICADO)
if t.due_date < datetime.utcnow():
    if t.status != 'done':
        task_data['overdue'] = True
```

**Impacto:**
- Mudanças devem ser feitas em 2 lugares
- Inconsistência possível

**Refatoração Proposta:**
```python
# models/task.py
@property
def is_overdue(self):
    if not self.due_date:
        return False
    return self.due_date < datetime.utcnow() and self.status not in ['done', 'cancelled']

# routes/task_routes.py (usar em ambos os lugares)
task_data['overdue'] = task.is_overdue
```

---

## Próximas Etapas

Total findings: **9 (3 CRITICAL, 2 HIGH, 4 MEDIUM)**

**Confirmar refatoração na Fase 3? (y/n)**
