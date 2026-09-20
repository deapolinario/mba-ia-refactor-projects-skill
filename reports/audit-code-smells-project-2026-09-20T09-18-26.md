# Relatório de Auditoria - code-smells-project

**Data:** 2026-09-20 09:18:26
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
- Roubo de dados sensíveis (emails, senhas)
- Alteração ou exclusão não autorizada de registros

**Refatoração Proposta:**
```python
# Usar parameterized queries com placeholders
cursor.execute("SELECT * FROM produtos WHERE id = ?", [id])

# INSERT com placeholders
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
    [nome, descricao, preco, estoque, categoria]
)

# LOGIN com placeholders
cursor.execute(
    "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
    [email, senha]
)
```

---

### [CRITICAL] Hardcoded SECRET_KEY

**Arquivo:** `app.py` (Linha: 7)

**Descrição:**
Chave secreta embarcada no código-fonte. Qualquer pessoa com acesso ao repositório pode falsificar sessões.

**Código Problemático:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Impacto:**
- Falsificação de sessões e tokens
- Impossível rodar em produção
- Violação de segurança de aplicação

**Refatoração Proposta:**
```python
# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY não definida em variáveis de ambiente")

Config.validate()

# app.py
from config import Config
app.config['SECRET_KEY'] = Config.SECRET_KEY
```

---

### [CRITICAL] Senhas em Texto Plano

**Arquivo:** `database.py` (Linhas: 76-78), `models.py` (sem hash)

**Descrição:**
Senhas armazenadas em texto plano sem hash. Breach garantido de contas de usuário.

**Código Problemático:**
```python
# database.py - seed com senhas literais
usuarios = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]

# models.py - login sem hash
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**Impacto:**
- Breach de contas de usuário
- Acesso não autorizado
- Violação de LGPD/GDPR

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
    return user
```

---

### [CRITICAL] God Module - models.py (315 linhas)

**Arquivo:** `models.py` (Linhas: 1-315)

**Descrição:**
Arquivo único com 315 linhas contendo todas as queries, validações e transformações para 4 domínios diferentes. Impossível testar em isolamento.

**Padrão Problemático:**
- 15+ funções sem separação de responsabilidade
- Lógica de BD misturada com transformações
- Sem reutilização de código

**Impacto:**
- Impossível testar cada função isoladamente
- Qualquer mudança pode quebrar tudo
- Difícil de manter e reutilizar

**Refatoração Proposta:**
Separar em estrutura MVC:
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

### [CRITICAL] N+1 Queries - Loops com Queries Dentro

**Arquivo:** `models.py` (Linhas: 171-201, 203-233)

**Descrição:**
Para cada pedido, queries adicionais por item. 10 pedidos = 40+ queries ao invés de 1 com join.

**Código Problemático:**
```python
# Linhas 171-201
for row in rows:  # Para cada pedido
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))  # +1 query
    itens = cursor2.fetchall()
    for item in itens:  # Para cada item
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))  # +1 query
```

**Impacto:**
- Performance exponencial degradada
- Timeout em listas grandes
- Consumo desnecessário de memória

**Refatoração Proposta:**
```python
# Single query com JOIN
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

### [CRITICAL] Endpoints Perigosos sem Proteção

**Arquivo:** `app.py` (Linhas: 47-78)

**Descrição:**
Endpoints `/admin/reset-db` e `/admin/query` executam operações críticas sem autenticação ou validação.

**Código Problemático:**
```python
# Linha 47-57 - Reset de banco sem autenticação
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")

# Linha 59-78 - Query arbitrária sem validação
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = dados.get("sql", "")
    cursor.execute(query)  # SQL injection + acesso total
```

**Impacto:**
- Perda total de dados
- Acesso completo ao banco
- Roubo de dados sensíveis

**Refatoração Proposta:**
Remover endpoints perigosos ou implementar autenticação forte.

---

### [HIGH] Secrets Expostas em Response

**Arquivo:** `controllers.py` (Linha: 289)

**Descrição:**
Endpoint `/health` retorna SECRET_KEY na resposta, visível em logs e monitoramento.

**Código Problemático:**
```python
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123"  # ❌ EXPOSTO!
}), 200
```

**Impacto:**
- Exposição de segredo em logs
- Violação de segurança

**Refatoração Proposta:**
```python
return jsonify({
    "status": "ok",
    "database": "connected",
    "counts": {
        "produtos": produtos,
        "usuarios": usuarios,
        "pedidos": pedidos
    },
    "versao": "1.0.0"
    # ✅ Remover secret_key, debug, db_path
}), 200
```

---

### [HIGH] Code Duplication

**Arquivo:** `models.py` (Linhas: 171-201 vs 203-233)

**Descrição:**
`get_pedidos_usuario()` e `get_todos_pedidos()` têm lógica idêntica.

**Refatoração Proposta:**
```python
def _format_pedido_com_itens(row, db):
    """Helper para formatar pedido com itens"""
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
`DEBUG = True` em ambiente que se apresenta como produção. Expõe stack traces.

**Refatoração Proposta:**
```python
from config import Config
app.config["DEBUG"] = Config.DEBUG
```

---

### [MEDIUM] Monolithic Architecture

**Arquivo:** `code-smells-project/` (Estrutura raiz)

**Descrição:**
Projeto sem separação clara de responsabilidades. Tudo em 4 arquivos.

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

## Próximas Etapas

Ao confirmar, a **Fase 3** executará refatoração completa para MVC com:
- ✅ SQL Injection fixes
- ✅ Secrets extraction
- ✅ Password hashing upgrade
- ✅ God Classes split
- ✅ N+1 Queries elimination
- ✅ Architecture restructuring

================================

**Total findings: 11 (6 CRITICAL, 3 HIGH, 2 MEDIUM)**

**Confirmar refatoração na Fase 3? (y/n)**
