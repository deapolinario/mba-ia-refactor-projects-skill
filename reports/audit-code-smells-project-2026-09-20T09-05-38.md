# Relatório de Auditoria - code-smells-project

**Data:** 2026-09-20 09:15:42
**Stack:** Python 3.x + Flask 3.x + SQLite
**Domínio:** E-commerce API (produtos, usuarios, pedidos, itens_pedido)

---

## Resumo Executivo

- **CRITICAL:** 6 achados
- **HIGH:** 3 achados
- **MEDIUM:** 2 achados
- **Total:** 11 achados

---

## Findings Detalhados

### [CRITICAL] SQL Injection - String Concatenation em Queries

**Arquivo:** `models.py` (Linhas: 28, 48-50, 57-61, 92, 109-110, 127-128, 140, 148-150, 155-160, 174, 188, 192, 220, 224, 280, 291-297)

**Descrição:**
Queries SQL construídas por concatenação de strings sem parametrização. Permite manipulação arbitrária de SQL e acesso não autorizado.

**Código Problemático:**
```python
# Linha 28
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# Linhas 48-50
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
    nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
)

# Linhas 109-110
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**Impacto:**
- Acesso total ao banco de dados
- Roubo de dados sensíveis
- Alteração/exclusão não autorizada de registros

**Refatoração Proposta:**
```python
# Usar parameterized queries
cursor.execute("SELECT * FROM produtos WHERE id = ?", [id])
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
    [nome, descricao, preco, estoque, categoria]
)
cursor.execute(
    "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
    [email, senha]
)
```

---

### [CRITICAL] Hardcoded SECRET_KEY

**Arquivo:** `app.py` (Linha: 7)

**Descrição:**
Chave secreta embarcada no código-fonte. Qualquer pessoa com acesso ao repo pode falsificar sessões.

**Código Problemático:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Impacto:**
- Falsificação de sessões
- Impossível rodar em produção

**Refatoração Proposta:**
```python
# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não definida em variáveis de ambiente")

# app.py
from config import Config
app.config['SECRET_KEY'] = Config.SECRET_KEY
```

---

### [CRITICAL] Senhas em Texto Plano

**Arquivo:** `database.py` (Linhas: 76-78), `models.py` (sem hash)

**Descrição:**
Senhas armazenadas em texto plano sem hash. Breach garantido.

**Código Problemático:**
```python
# database.py
usuarios = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
]

# models.py - login sem hash
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**Impacto:**
- Breach de contas de usuário
- Acesso não autorizado

**Refatoração Proposta:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Ao criar usuário
senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')
cursor.execute(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
    [nome, email, senha_hash, tipo]
)

# Ao fazer login
cursor.execute("SELECT * FROM usuarios WHERE email = ?", [email])
user = cursor.fetchone()
if user and check_password_hash(user['senha'], senha):
    # Login válido
```

---

### [CRITICAL] God Module - models.py

**Arquivo:** `models.py` (Linhas: 1-315)

**Descrição:**
Arquivo com 315 linhas contendo todas as queries, validações e transformações. Impossível testar em isolamento.

**Impacto:**
- Impossível testar cada função isoladamente
- Qualquer mudança pode quebrar tudo
- Impossível reutilizar

**Refatoração Proposta:**
```
models/
  ├── __init__.py
  ├── produto.py
  ├── usuario.py
  └── pedido.py

controllers/
  ├── __init__.py
  ├── produto_controller.py
  ├── usuario_controller.py
  └── pedido_controller.py
```

---

### [CRITICAL] N+1 Queries

**Arquivo:** `models.py` (Linhas: 171-201, 203-233)

**Descrição:**
Para cada pedido, queries adicionais por item. 10 pedidos = 40+ queries ao invés de 1.

**Código Problemático:**
```python
for row in rows:  # Para cada pedido
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))  # +1 query
    itens = cursor2.fetchall()
    for item in itens:  # Para cada item
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))  # +1 query
```

**Impacto:**
- Performance exponencial
- Timeout em listas grandes

**Refatoração Proposta:**
```python
# Single query com joins
def get_pedidos_usuario(usuario_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT 
            p.id, p.usuario_id, p.status, p.total, p.criado_em,
            ip.produto_id, ip.quantidade, ip.preco_unitario,
            pr.nome as produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
        LEFT JOIN produtos pr ON ip.produto_id = pr.id
        WHERE p.usuario_id = ?
        ORDER BY p.id
    """, [usuario_id])
```

---

### [CRITICAL] Endpoints Perigosos

**Arquivo:** `app.py` (Linhas: 47-78)

**Descrição:**
`/admin/reset-db` e `/admin/query` executam operações críticas sem autenticação.

**Código Problemático:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    # Sem autenticação! Qualquer um pode deletar tudo
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")

@app.route("/admin/query", methods=["POST"])
def executar_query():
    # SQL injection garantida
    query = dados.get("sql", "")
    cursor.execute(query)
```

**Impacto:**
- Perda total de dados
- Acesso completo ao banco

**Refatoração Proposta:**
Remover esses endpoints ou implementar autenticação.

---

### [HIGH] Secrets Expostas em Response

**Arquivo:** `controllers.py` (Linha: 289)

**Descrição:**
`/health` retorna SECRET_KEY na resposta.

**Código Problemático:**
```python
return jsonify({
    "secret_key": "minha-chave-super-secreta-123"  # ❌ EXPOSTO!
}), 200
```

**Refatoração Proposta:**
Remover `secret_key`, `debug`, `db_path` da response.

---

### [HIGH] Code Duplication

**Arquivo:** `models.py` (Linhas: 171-201 vs 203-233)

**Descrição:**
`get_pedidos_usuario()` e `get_todos_pedidos()` têm lógica idêntica.

**Refatoração Proposta:**
```python
def _format_pedido_com_itens(row, db):
    """Helper reutilizável"""
    pedido = {...}
    return pedido

def get_pedidos_usuario(usuario_id):
    rows = db.cursor().execute("SELECT * FROM pedidos WHERE usuario_id = ?", [usuario_id])
    return [_format_pedido_com_itens(row, db) for row in rows]

def get_todos_pedidos():
    rows = db.cursor().execute("SELECT * FROM pedidos")
    return [_format_pedido_com_itens(row, db) for row in rows]
```

---

### [MEDIUM] DEBUG Mode Ativo

**Arquivo:** `app.py` (Linha: 8)

**Descrição:**
`DEBUG = True` expõe stack traces em produção.

**Refatoração Proposta:**
Carregar de `.env`: `DEBUG = os.getenv('DEBUG', 'False') == 'True'`

---

### [MEDIUM] Monolithic Architecture

**Arquivo:** `code-smells-project/` (Estrutura raiz)

**Descrição:**
Tudo em 4 arquivos raiz. Sem separação de responsabilidades.

**Refatoração Proposta:**
```
config/
  └── settings.py
models/
  ├── produto.py
  ├── usuario.py
  └── pedido.py
routes/
  ├── produto_routes.py
  ├── usuario_routes.py
  └── pedido_routes.py
controllers/
  ├── produto_controller.py
  ├── usuario_controller.py
  └── pedido_controller.py
app.py (limpo, apenas entry point)
```

---

## Resumo

✅ Relatório gerado com timestamp dinâmico: **2026-09-20T09-15-42**

Total findings: **11 (6 CRITICAL, 3 HIGH, 2 MEDIUM)**

**Confirmar refatoração na Fase 3? (y/n)**
