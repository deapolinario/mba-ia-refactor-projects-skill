# Playbook de Refatoração

## v1.0 — SQL Injection & Hardcoded Secrets

### Padrão 1: Converter String Concatenation para Parameterized Query

**Problema:**
```python
# Python
user_id = request.args.get('id')
query = "SELECT * FROM users WHERE id = " + user_id
result = db.execute(query)

# Node.js
const userId = req.query.id;
const query = `SELECT * FROM users WHERE id = ${userId}`;
const result = db.query(query);
```

**Solução:**
```python
# Python - usando parameterized query
user_id = request.args.get('id')
query = "SELECT * FROM users WHERE id = ?"
result = db.execute(query, [user_id])

# Python - usando ORM
user = User.query.filter_by(id=user_id).first()
```

```javascript
// Node.js - usando parameterized query
const userId = req.query.id;
const query = "SELECT * FROM users WHERE id = ?";
const result = await db.query(query, [userId]);

// Node.js - usando ORM
const user = await User.findByPk(userId);
```

---

### Padrão 2: Extrair Secrets para Variáveis de Ambiente

**Problema:**
```python
# Python
SECRET_KEY = "minha-chave-super-secreta-123"
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890"

# Node.js
const SECRET_KEY = "minha-chave-super-secreta-123";
const DB_PASSWORD = "admin123";
const API_KEY = "sk-1234567890";
```

**Solução:**

**Arquivo: config.py / config.js**
```python
# Python
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    API_KEY = os.getenv('API_KEY')
    
    # Validação no startup
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não definida em variáveis de ambiente")
```

```javascript
// Node.js
class Config {
    static SECRET_KEY = process.env.SECRET_KEY;
    static DB_PASSWORD = process.env.DB_PASSWORD;
    static API_KEY = process.env.API_KEY;
    
    static validate() {
        if (!this.SECRET_KEY) {
            throw new Error("SECRET_KEY não definida em variáveis de ambiente");
        }
    }
}

Config.validate();
module.exports = Config;
```

**Arquivo: .env**
```
SECRET_KEY=minha-chave-super-secreta-123
DB_PASSWORD=admin123
API_KEY=sk-1234567890
```

**Arquivo: .gitignore (adicionar)**
```
.env
.env.local
```

---

### Padrão 3: Remover Secrets de Responses

**Problema:**
```python
# user.py
def to_dict(self):
    return {
        'id': self.id,
        'email': self.email,
        'password': self.password,  # ❌ NÃO expor
        'role': self.role
    }

# No endpoint
@app.route('/users/<id>')
def get_user(id):
    user = User.query.get(id)
    return jsonify(user.to_dict())  # ❌ Expõe senha
```

**Solução:**
```python
# user.py
def to_dict(self, include_password=False):
    data = {
        'id': self.id,
        'email': self.email,
        'role': self.role
    }
    if include_password:
        data['password'] = self.password
    return data

# No endpoint
@app.route('/users/<id>')
def get_user(id):
    user = User.query.get(id)
    return jsonify(user.to_dict(include_password=False))  # ✅ Seguro
```

---

### Padrão 4: Substituir MD5/SHA1 por Bcrypt/Argon2

**Problema:**
```python
# Python - MD5
import hashlib
user.password = hashlib.md5(pwd.encode()).hexdigest()

# Node.js - Sem hash
user.password = req.body.password
```

**Solução:**
```python
# Python
from werkzeug.security import generate_password_hash, check_password_hash

user.password = generate_password_hash(pwd, method='pbkdf2:sha256')

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

```javascript
// Node.js
const bcrypt = require('bcrypt');

user.password = await bcrypt.hash(pwd, 10);

async function checkPassword(pwd) {
    return await bcrypt.compare(pwd, this.password);
}
```

---

### Padrão 5: Separar God Class em MVC

**Problema:**
```python
# Tudo em um arquivo
class AppManager:
    def init_db(self): ...
    def create_user(self): ...
    def process_payment(self): ...
    def generate_report(self): ...
```

**Solução:**
```
models/
  └── user.py
controllers/
  └── user_controller.py
routes/
  └── user_routes.py
```

```python
# models/user.py
class User(db.Model):
    id = db.Column(...)
    email = db.Column(...)

# controllers/user_controller.py
class UserController:
    @staticmethod
    def create(data):
        # validação e lógica
        return User(...)

# routes/user_routes.py
@app.route('/users', methods=['POST'])
def create_user():
    result = UserController.create(request.json)
    return jsonify(result)
```

---

### Padrão 6: Eliminar N+1 Queries com Eager Loading

**Problema:**
```python
# Python - N+1
users = User.query.all()
for user in users:
    tasks = Task.query.filter_by(user_id=user.id).all()  # +1 query por user!

# Node.js - N+1
const users = await User.findAll();
for (const user of users) {
    user.tasks = await Task.findAll({ where: { userId: user.id } });  // +1 query!
}
```

**Solução:**
```python
# Python - Eager loading (1 query + 1 join)
from sqlalchemy.orm import joinedload
users = User.query.options(joinedload('tasks')).all()

# Agora todos os tasks já estão carregados
for user in users:
    print(user.tasks)  # Sem queries adicionais
```

```javascript
// Node.js - Com include/eager loading
const users = await User.findAll({
    include: [{ association: 'tasks' }]
});

// Todos os tasks já carregados em 1 query
for (const user of users) {
    console.log(user.tasks);
}
```

---

### Padrão 7: Remover Duplicação com Funções/Helpers

**Problema:**
```python
# Lógica duplicada em 2 lugares
def get_all_orders():
    orders = Order.query.all()
    result = []
    for o in orders:
        result.append({
            'id': o.id,
            'user': o.user.name,
            'total': sum(item.price for item in o.items),
            'status': o.status
        })
    return result

def get_user_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    result = []
    for o in orders:  # ❌ DUPLICADO
        result.append({
            'id': o.id,
            'user': o.user.name,
            'total': sum(item.price for item in o.items),
            'status': o.status
        })
    return result
```

**Solução:**
```python
# Extrair em método/helper
class Order(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.name,
            'total': sum(item.price for item in self.items),
            'status': self.status
        }

def get_all_orders():
    return [o.to_dict() for o in Order.query.all()]

def get_user_orders(user_id):
    return [o.to_dict() for o in Order.query.filter_by(user_id=user_id).all()]
```

---

### Padrão 8: Estruturar como MVC

**Problema:**
```
project/
├── app.py
├── models.py (300+ linhas, tudo misturado)
└── requirements.txt
```

**Solução:**
```
project/
├── config.py
├── app.py (entry point limpo)
├── database.py (inicialização do DB)
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── order.py
├── routes/
│   ├── __init__.py
│   ├── user_routes.py
│   └── order_routes.py
├── controllers/
│   ├── __init__.py
│   ├── user_controller.py
│   └── order_controller.py
└── requirements.txt
```

**app.py limpo:**
```python
from flask import Flask
from config import Config
from database import db, init_db
from routes.user_routes import user_bp
from routes.order_routes import order_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
app.register_blueprint(user_bp)
app.register_blueprint(order_bp)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run()
```

---

---

### Padrão 9: Remover Secrets de Responses

**Problema:**
```python
@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "secret_key": SECRET_KEY,  # ❌ EXPÕE!
        "debug": DEBUG
    })
```

**Solução:**
```python
@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "version": "1.0.0"
        # ✅ Sem secrets
    })
```

---

### Padrão 10: Mascarar Dados Sensíveis em Logs

**Problema:**
```python
# Python
print(f"Email registrado: {email}")
print(f"Cartão: {cc}")

# Node.js
console.log(`Processando cartão: ${cc}`);
```

**Solução:**
```python
# Python
def mask_email(email):
    parts = email.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"

def mask_cc(cc):
    return cc[:4] + '*' * (len(cc) - 8) + cc[-4:]

print(f"Email: {mask_email(email)}")
print(f"Cartão: {mask_cc(cc)}")
```

```javascript
// Node.js
function maskEmail(email) {
    const parts = email.split('@');
    return `${parts[0].slice(0, 2)}***@${parts[1]}`;
}

function maskCC(cc) {
    return cc.slice(0, 4) + '*'.repeat(cc.length - 8) + cc.slice(-4);
}

console.log(`Email: ${maskEmail(email)}`);
console.log(`Cartão: ${maskCC(cc)}`);
```

---

### Padrão 11: Converter Global State para Singleton

**Problema:**
```python
# Global compartilhado
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```

**Solução:**
```python
# Singleton thread-safe
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=5
        )
        self._initialized = True

# Uso
db = DatabaseManager()
```

---

### Padrão 12: Extrair Magic Strings para Config

**Problema:**
```python
# Hardcoded categories
categorias_validas = ["informatica", "moveis", "vestuario", "geral"]

# Magic numbers
timeout = 30
max_retries = 3
```

**Solução:**
```python
# config.py
class Config:
    VALID_CATEGORIES = [
        "informatica",
        "moveis", 
        "vestuario",
        "geral"
    ]
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    
# controllers.py
from config import Config

if categoria not in Config.VALID_CATEGORIES:
    return jsonify({"erro": "Categoria inválida"}), 400
```

---

### Padrão 13: Simplificar Ternários

**Problema:**
```python
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```

**Solução:**
```python
def is_admin(self):
    return self.role == 'admin'
```

---

## v2.2 — Endpoints Perigosos, Auth, Exception Leakage, Regressões

### Padrão 14: Remover/Proteger Endpoint de SQL Arbitrário

**Problema:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    cursor.execute(query)  # ❌ Executa QUALQUER SQL do cliente
```

**Solução (remover é o padrão recomendado):**
```python
# ✅ Remover completamente o endpoint.
# Se debug de banco for realmente necessário, usar ferramenta externa
# (ex: sqlite3 CLI, DBeaver) nunca expor via API HTTP.
```

**Se não puder remover (caso de uso legítimo administrativo):**
```python
# ✅ Restringir a allowlist de queries pré-aprovadas + auth obrigatória
ALLOWED_QUERIES = {
    "contar_usuarios": "SELECT COUNT(*) FROM usuarios",
    "contar_produtos": "SELECT COUNT(*) FROM produtos",
}

@app.route("/admin/query", methods=["POST"])
@admin_required
def executar_query():
    nome_query = request.get_json().get("query_name")
    if nome_query not in ALLOWED_QUERIES:
        return jsonify({"erro": "Query não permitida"}), 403
    cursor.execute(ALLOWED_QUERIES[nome_query])
```

**Por quê:** Execução de SQL arbitrário via HTTP nunca é seguro, independente de sanitização.

---

### Padrão 15: Hash de Senha + Remover Senha de Queries/Responses

**Problema:**
```python
def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        [email, senha]  # ❌ Compara texto plano
    )

def get_todos_usuarios():
    cursor.execute("SELECT * FROM usuarios")
    # ❌ row["senha"] vai para o JSON de response
```

**Solução:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def criar_usuario(nome, email, senha, tipo="cliente"):
    senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [nome, email, senha_hash, tipo]
    )

def login_usuario(email, senha):
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", [email])
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None

def get_todos_usuarios():
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    # ✅ Coluna senha nunca sai do banco
```

**Por quê:** Hash impede recuperação da senha original mesmo com acesso ao banco; excluir a coluna na query (não só no dict) evita vazamento mesmo se alguém esquecer de filtrar depois.

---

### Padrão 16: Proteger Endpoints Administrativos

**Problema:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    # ❌ Qualquer um pode chamar
```

**Solução:**
```python
from functools import wraps
from flask import request, jsonify
import os

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if not token or token != os.getenv("ADMIN_TOKEN"):
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    ...
```

**Por quê:** Toda rota que altera estado crítico precisa de barreira explícita — nunca confiar em "URL não documentada".

---

### Padrão 17: Não Vazar Detalhes de Exceção ao Cliente

**Problema:**
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500  # ❌ Vaza detalhes internos
```

**Solução:**
```python
except Exception as e:
    logger.error(f"Erro em criar_produto: {str(e)}")
    return jsonify({"erro": "Erro interno do servidor"}), 500
```

**Por quê:** Cliente não precisa (e não deve) saber detalhes de implementação; detalhes ficam nos logs internos para debug.

---

### Padrão 18: Corrigir Regressão de Inicialização Por-Request

**Problema:**
```python
def get_db():
    conn = _db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS ...")  # ❌ roda em toda request
    cursor.execute("SELECT COUNT(*) FROM produtos")   # ❌ query extra sempre
    if cursor.fetchone()[0] == 0:
        ...seed...
    return conn
```

**Solução:**
```python
class DatabaseManager:
    def __init__(self):
        if self._initialized:
            return
        self.connection = sqlite3.connect(...)
        self._setup_schema()   # ✅ roda uma única vez
        self._seed_if_empty()  # ✅ roda uma única vez
        self._initialized = True

    def _setup_schema(self):
        cursor = self.connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS ...")
        self.connection.commit()

    def _seed_if_empty(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            ...seed...

def get_db():
    return _db_manager.get_connection()  # ✅ sem side-effects
```

**Por quê:** Setup deve ser custo único de startup, não recorrente por request.

---

### Padrão 19: Aplicar Config Onde o Literal Antigo Estava

**Problema:**
```python
# config.py
DEBUG = os.getenv('FLASK_ENV') == 'development'

# app.py (esqueceram de usar!)
app.run(debug=True)  # ❌ literal antigo continua
```

**Solução:**
```python
# app.py
app.run(debug=Config.DEBUG)  # ✅ usa a config criada
```

**Validação:** Após criar qualquer config nova, `grep` pelo valor literal antigo no restante do projeto para confirmar que não sobrou nenhuma ocorrência.

---

## Validação Pós-Refatoração

Após aplicar cada padrão, validar:

1. **SQL Injection:**
   - ✅ Queries usam placeholders (`?` ou `:param`)
   - ✅ Não há concatenação de strings em queries
   - ✅ Aplicação startup sem erros
   - ✅ Endpoints retornam dados corretos

2. **Hardcoded Secrets:**
   - ✅ Arquivo `.env` criado com valores reais
   - ✅ `.env` adicionado ao `.gitignore`
   - ✅ Config carregado de `os.getenv()` ou `process.env`
   - ✅ Sem valores secretos no código-fonte
   - ✅ Validação de secrets obrigatórios no startup

---

## Linguagens Suportadas (v1.0)

- Python 3.x (Flask, Django, FastAPI)
- Node.js 14+ (Express, Fastify)
- Suporte para Java, PHP, Ruby em futuras versões
