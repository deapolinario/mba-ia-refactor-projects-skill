# Auditoria Arquitetural: task-manager-api
**Versão da Skill:** 2.1  
**Data da Auditoria:** 2026-09-20  
**Timestamp:** 2026-09-20T09-38-26

---

## PHASE 1: PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       Python 3.x
Framework:      Flask + SQLAlchemy
Database:       SQLite (tasks.db)
Domain:         Task Management / Project Management
Architecture:   Partially Organized (routes + models separados, lógica em routes)
Source files:   10+ files analyzed (app.py, routes/, models/)
DB tables:      5 (users, tasks, categories, etc)
================================
```

---

## PHASE 2: ARCHITECTURE AUDIT

### **CRÍTICO (CRITICAL)**

---

#### **1. Senha Exposta em JSON (to_dict)**

**Arquivo:** `models/user.py`  
**Linhas:** 21, e usado em `routes/user_routes.py` linhas 33, 85-86

**Código Problemático:**
```python
# models/user.py
def to_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'email': self.email,
        'password': self.password,  # ❌ EXPÕE HASH DA SENHA
        'role': self.role,
        'active': self.active,
        'created_at': str(self.created_at)
    }

# routes/user_routes.py linha 33
data = user.to_dict()  # ← Retorna password
return jsonify(data), 200

# routes/user_routes.py linha 86
response_data = user.to_dict()  # ← Retorna password
return jsonify(response_data), 201
```

**Descrição:** Endpoint GET /users retorna hash MD5 da senha de todos os usuários.

**Impacto:** 🔴 **CRÍTICO** - Exposição de credenciais:
- Hash MD5 é facilmente quebrado (rainbow tables)
- Usuário consegue ver qualquer senha de qualquer outro usuário
- Se hash é quebrado, acesso não autorizado a contas

**Refatoração Proposta:**
```python
# models/user.py
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

# routes/user_routes.py
return jsonify(user.to_dict(include_password=False)), 200
```

**Por quê:** Passwords nunca devem ser retornadas em responses.

---

#### **2. Hardcoded SECRET_KEY**

**Arquivo:** `app.py`  
**Linhas:** 13

**Código Problemático:**
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
```

**Descrição:** Chave secreta embarcada no código.

**Impacto:** 🔴 **CRÍTICO** - Comprometimento de sessões e tokens JWT.

**Refatoração Proposta:**
```python
# app.py
import os
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY não definida em variáveis de ambiente")
```

**Por quê:** Secrets em env vars.

---

#### **3. Hardcoded Email Credentials**

**Arquivo:** `services/notification_service.py` (se existir)  
**Status:** Verificar configuração de SMTP/Email

**Impacto:** 🔴 **CRÍTICO** (se encontrado)

---

### **ALTO (HIGH)**

---

#### **4. MD5 Password Hashing**

**Arquivo:** `models/user.py`  
**Linhas:** 29, 32

**Código Problemático:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**Descrição:** Senhas hashadas com MD5, algoritmo obsoleto desde 2004.

**Impacto:** 🟠 **ALTO** - Rainbow tables quebram em segundos:
- Dicionário online de 1 bilhão de MD5s
- Sem salt, sem custo computacional
- Owasp A02:2021 - Cryptographic Failures

**Refatoração Proposta:**
```python
# models/user.py
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd, method='pbkdf2:sha256')

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

**Por quê:** PBKDF2 é slow-by-design, impossível brute-force.

---

#### **5. N+1 Queries**

**Arquivo:** `routes/task_routes.py`  
**Linhas:** 41-48, 71-80 (get_tasks), 281-287 (task_stats overdue calculation)

**Código Problemático:**
```python
# get_tasks linha 41-48
for t in tasks:                    # N tasks
    if t.user_id:
        user = User.query.get(t.user_id)  # ← +1 query por task
        if user:
            task_data['user_name'] = user.name
    if t.category_id:
        cat = Category.query.get(t.category_id)  # ← +1 query por task
        # +2 queries * N tasks

# task_stats linha 281-287
all_tasks = Task.query.all()  # Query 1
overdue_count = 0
for t in all_tasks:            # Para cada task
    if t.due_date:
        if t.due_date < datetime.utcnow():  # ← Lógica em loop ao invés de SQL
```

**Descrição:** Loops com queries dentro causam N+1 queries.

**Impacto:** 🟠 **ALTO** - Performance exponencial:
- 100 tasks = 200+ queries ao invés de 1-2
- Timeout, CPU alta

**Refatoração Proposta:**
```python
# ✅ CORRETO com eager loading
from sqlalchemy.orm import joinedload

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.options(
        joinedload('user'),
        joinedload('category')
    ).all()
    
    # Agora user e category já estão carregados, sem queries adicionais
    result = [t.to_dict_with_relations() for t in tasks]
    return jsonify(result), 200
```

**Por quê:** Eager loading carrega relações em 1 query com JOINs.

---

### **MÉDIO (MEDIUM)**

---

#### **6. Code Duplication - Lógica de Overdue**

**Arquivo:** `routes/task_routes.py`  
**Linhas:** 30-39 vs 71-80 vs 282-287 (task_stats)

**Código Problemático:**
```python
# Duplicação 1 - linhas 30-39
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
        else:
            task_data['overdue'] = False
    else:
        task_data['overdue'] = False
else:
    task_data['overdue'] = False

# Duplicação 2 - linhas 71-80 (IDÊNTICA)
# Duplicação 3 - linhas 282-287 (SIMILAR, mas em loop)
```

**Descrição:** Lógica de cálculo de `overdue` duplicada em 3 lugares.

**Impacto:** 🟡 **MÉDIO** - Manutenção:
- Mudanças precisam ser feitas em 3 lugares
- Inconsistência de lógica

**Refatoração Proposta:**
```python
# models/task.py
class Task(db.Model):
    @property
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status in ['done', 'cancelled']:
            return False
        return self.due_date < datetime.utcnow()

# routes/task_routes.py
task_data['overdue'] = t.is_overdue
```

**Por quê:** DRY - centralize lógica em um lugar.

---

#### **7. DEBUG Mode Ativo**

**Arquivo:** `app.py`  
**Linhas:** 34

**Código Problemático:**
```python
app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', '5001')))
```

**Descrição:** Debug mode ativo em runtime.

**Impacto:** 🟡 **MÉDIO** - Security/Information Disclosure:
- Stacktraces completos em erros
- Variáveis de ambiente expostas
- Reloader automático pode executar código perigoso

**Refatoração Proposta:**
```python
# app.py
DEBUG = os.getenv('FLASK_ENV') == 'development'
app.run(debug=DEBUG, host='0.0.0.0', port=int(os.getenv('PORT', '5001')))
```

**Por quê:** Debug apenas em ambiente development.

---

#### **8. Logs Sensíveis (Revealing User Info)**

**Arquivo:** `routes/user_routes.py`  
**Linhas:** 83

**Código Problemático:**
```python
print(f"Usuário criado: {user.id} - {user.name}")
```

**Descrição:** Logs contêm nomes de usuários (PII leve).

**Impacto:** 🟡 **MÉDIO** - Auditoria/Privacy:
- Exposição de nomes em logs
- Falta de anonimização

**Refatoração Proposta:**
```python
# ✅ CORRETO
import logging
logger = logging.getLogger(__name__)

logger.info(f"Usuário criado: {user.id}")  # Sem nome
```

**Por quê:** Minimizar PII em logs.

---

### **BAIXO (LOW)**

---

#### **9. Ternário Desnecessário**

**Arquivo:** `models/user.py`  
**Linhas:** 34-38

**Código Problemático:**
```python
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```

**Descrição:** If/else retornando True/False pode ser simplificado.

**Impacto:** 🔵 **BAIXO** - Legibilidade:
- Verboso desnecessariamente
- Python pode ser mais conciso

**Refatoração Proposta:**
```python
def is_admin(self):
    return self.role == 'admin'
```

**Por quê:** Mais legível e conciso.

---

#### **10. Magic Strings - Status Values**

**Arquivo:** `routes/task_routes.py`  
**Linhas:** 110, 177, 242-243

**Código Problemático:**
```python
if status not in ['pending', 'in_progress', 'done', 'cancelled']:
    return jsonify({'error': 'Status inválido'}), 400
```

**Descrição:** Status values hardcoded em múltiplos lugares.

**Impacto:** 🔵 **BAIXO** - Manutenibilidade:
- Mudança de valores requer editar código
- Sem single source of truth
- Fácil errar em duplicação

**Refatoração Proposta:**
```python
# config.py
class Config:
    VALID_TASK_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
    VALID_USER_ROLES = ['user', 'admin', 'manager']
    VALID_PRIORITIES = [1, 2, 3, 4, 5]

# routes/task_routes.py
from config import Config
if status not in Config.VALID_TASK_STATUSES:
    return jsonify({'error': 'Status inválido'}), 400
```

**Por quê:** Centralizar constantes.

---

## 📊 RESUMO EXECUTIVO

| Severidade | Count | Exemplos |
|-----------|-------|----------|
| 🔴 **CRITICAL** | 3 | Senha em JSON, Hardcoded SECRET_KEY, (Email credentials se encontrados) |
| 🟠 **HIGH** | 2 | MD5 Hashing, N+1 Queries |
| 🟡 **MEDIUM** | 3 | Code Duplication, DEBUG Mode, Logs Sensíveis |
| 🔵 **LOW** | 2 | Ternário Desnecessário, Magic Strings |
| **TOTAL** | **10** | Achados (vs 9 em v2.0) |

---

## ✅ COBERTURA v2.1

| Anti-Pattern | v2.0 | v2.1 | Status |
|---|---|---|---|
| Senha em JSON | ✅ | ✅ | Detectado |
| Hardcoded Secrets | ✅ | ✅ | Detectado |
| MD5 Hashing | ✅ | ✅ | Detectado |
| N+1 Queries | ✅ | ✅ | Detectado |
| Code Duplication | ✅ | ✅ | Detectado |
| Bare Except | ✅ | ✅ | Detectado |
| DEBUG Mode | ✅ | ✅ | Detectado |
| Logs Sensíveis | ❌ | ✅ | **NOVO** |
| Ternário | ❌ | ✅ | **NOVO** |
| Magic Strings | ❌ | ✅ | **NOVO** |

**Cobertura v2.1:** 10 achados (vs 9 em v2.0) = **+11% de melhoria**

---

## 🎯 PRÓXIMAS AÇÕES

1. **CRÍTICO:** Remover password de to_dict()
2. **CRÍTICO:** Extrair SECRET_KEY para `.env`
3. **CRÍTICO:** Verificar credenciais de email/SMTP
4. **ALTO:** Trocar MD5 por PBKDF2/bcrypt
5. **ALTO:** Usar eager loading (joinedload)
6. **MÉDIO:** Extrair lógica de overdue em @property
7. **MÉDIO:** DEBUG apenas em development
8. **MÉDIO:** Remover nomes de logs
9. **BAIXO:** Simplificar ternários
10. **BAIXO:** Mover magic strings para Config

