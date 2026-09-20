# Relatório de Auditoria - code-smells-project

**Data:** 2026-09-20  
**Stack:** Python 3 + Flask 3.1.1 + SQLite  
**Domínio:** E-commerce API (Gerenciamento de Produtos, Usuários, Pedidos)

---

## Resumo Executivo

- **CRITICAL:** 5 achados
- **HIGH:** 2 achados
- **Total:** 7 achados

---

## Findings Detalhados

### [CRITICAL] SQL Injection - Concatenação de Strings em Queries (get_produto_por_id)

**Arquivo:** `models.py` (Linha: 28)

**Descrição:**
Query SQL construída com concatenação de string, permitindo SQL Injection via parâmetro `id`.

**Código Problemático:**
```python
def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Impacto:**
- Atacante pode injetar SQL arbitrário através do parâmetro `id`
- Possibilidade de ler/modificar/deletar dados do banco
- Acesso não autorizado a informações sensíveis
- Exemplo de exploit: `GET /produtos/1 OR 1=1--`

**Refatoração Proposta:**
```python
def get_produto_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

**Por quê:**
Parameterized queries (placeholders `?`) garantem que o valor é escapado corretamente. O banco trata dados e SQL como coisas diferentes.

---

### [CRITICAL] SQL Injection - Concatenação em INSERT (criar_produto)

**Arquivo:** `models.py` (Linhas: 47-50)

**Descrição:**
INSERT construído com concatenação de strings. Valores de `nome`, `descricao`, e `categoria` vêm diretamente da requisição HTTP.

**Código Problemático:**
```python
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
    nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
)
```

**Impacto:**
- SQL Injection via campo `nome` ou `descricao`
- Exemplo: `nome = "'; DROP TABLE produtos; --"`
- Perda total de dados se atacante executar `DROP TABLE`
- Impossível validar entrada da aplicação se a query está concatenada

**Refatoração Proposta:**
```python
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
    (nome, descricao, preco, estoque, categoria)
)
```

**Por quê:**
Parâmetros posicionais (`?`) garantem segurança. O driver SQLite trata cada parâmetro como dado, nunca como comando.

---

### [CRITICAL] SQL Injection - Concatenação em UPDATE (atualizar_produto)

**Arquivo:** `models.py` (Linhas: 57-61)

**Descrição:**
UPDATE também está vulnerável. Múltiplos campos concatenados sem proteção.

**Código Problemático:**
```python
cursor.execute(
    "UPDATE produtos SET nome = '" + nome + "', descricao = '" + descricao +
    "', preco = " + str(preco) + ", estoque = " + str(estoque) +
    ", categoria = '" + categoria + "' WHERE id = " + str(id)
)
```

**Impacto:**
- SQL Injection em qualquer um dos 5 campos
- Possibilidade de modificar outros produtos
- Exemplo: `id = "1; UPDATE produtos SET preco = 0.01; --"`

**Refatoração Proposta:**
```python
cursor.execute(
    "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
    (nome, descricao, preco, estoque, categoria, id)
)
```

**Por quê:**
Placeholders evitam injection em toda a query, não apenas em valores.

---

### [CRITICAL] SQL Injection - Concatenação em DELETE (deletar_produto)

**Arquivo:** `models.py` (Linha: 68)

**Descrição:**
DELETE sem parâmetros. Parâmetro `id` é concatenado diretamente.

**Código Problemático:**
```python
def deletar_produto(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = " + str(id))
```

**Impacto:**
- Possibilidade de deletar todos os produtos com `id = "1 OR 1=1"`
- Perda irreversível de dados
- Impossível recuperar

**Refatoração Proposta:**
```python
cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
```

**Por quê:**
Simples, seguro, eficiente.

---

### [CRITICAL] SQL Injection - Login Vulnerável (login_usuario)

**Arquivo:** `models.py` (Linhas: 109-111)

**Descrição:**
Query de login concatenada. Attackers podem fazer bypass de autenticação.

**Código Problemático:**
```python
def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )
```

**Impacto:**
- **Bypass de autenticação:** Email = `' OR '1'='1` permite login sem senha
- Exemplo de exploit:
  ```
  email = "admin@loja.com' --"
  senha = "qualquer coisa"
  # Resultado: SELECT * FROM usuarios WHERE email = 'admin@loja.com' --' AND senha = '...'
  # O comentário SQL ignora a verificação de senha
  ```
- Acesso não autorizado a contas de qualquer usuário

**Refatoração Proposta:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

**Por quê:**
Autenticação é crítica. Sem parameterized queries, o sistema é quebrado.

---

### [CRITICAL] Hardcoded SECRET_KEY

**Arquivo:** `app.py` (Linha: 7)

**Descrição:**
Chave secreta de sessão Flask embarcada no código-fonte com valor fixo.

**Código Problemático:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Impacto:**
- Qualquer pessoa com acesso ao repo pode falsificar sessões
- Alguém com acesso ao código-fonte pode assinar cookies maliciosos
- Violação de OWASP A02:2021 (Cryptographic Failures)
- Impossível rodar em produção de forma segura
- Se o repo vaza na internet, chave fica exposta forever

**Refatoração Proposta:**
```python
# Criar config.py
import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não definida em variáveis de ambiente")

# Em app.py
from config import Config
app.config["SECRET_KEY"] = Config.SECRET_KEY
```

**Arquivo `.env`:**
```
SECRET_KEY=sua-chave-aleatoria-gerada-aqui-256-bits
```

**E adicionar ao `.gitignore`:**
```
.env
```

**Por quê:**
Secrets nunca devem estar no código. `.env` é local, não é commitado. Produção injeta via variáveis de ambiente.

---

### [HIGH] Hardcoded Database Credentials (Implícito)

**Arquivo:** `database.py` (Linha: 5)

**Descrição:**
Path do banco de dados está hardcoded (`loja.db`). Enquanto SQLite local não é tão crítico quanto senhas, o padrão é centralizar config.

**Código Problemático:**
```python
db_path = "loja.db"
```

**Impacto:**
- Se em produção, caminhos podem ser diferentes (dev vs. staging vs. prod)
- Difícil fazer deploy em ambientes diferentes sem modificar código
- Impossível usar variável de ambiente para arquivo de credenciais de BD

**Refatoração Proposta:**
```python
import os

db_path = os.getenv('DATABASE_URL', 'loja.db')
```

**Por quê:**
Padrão de 12-factor app: config via variáveis de ambiente.

---

### [HIGH] Hardcoded Credentials em Seed de Banco

**Arquivo:** `database.py` (Linhas: 75-83)

**Descrição:**
Senhas padrão (plaintext) e dados de admin embarcados no código de inicialização.

**Código Problemático:**
```python
usuarios = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]
```

**Impacto:**
- Senhas padrão em plaintext no código
- Qualquer desenvolvedor vê as credenciais de admin
- Se leakado, atacante acessa com `admin@loja.com / admin123`
- Senhas não são hashed

**Refatoração Proposta:**
```python
# Em database.py, remover hardcoded users
# Criar seed_users.py:
import os
from werkzeug.security import generate_password_hash

usuarios_seed = [
    ("Admin", "admin@loja.com", os.getenv('ADMIN_PASSWORD', 'change-me'), "admin"),
    ("João Silva", "joao@email.com", os.getenv('USER1_PASSWORD', 'change-me'), "cliente"),
    ("Maria Santos", "maria@email.com", os.getenv('USER2_PASSWORD', 'change-me'), "cliente"),
]

# Aplicar hash antes de inserir
for nome, email, senha_raw, tipo in usuarios_seed:
    senha_hash = generate_password_hash(senha_raw)
    cursor.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo)
    )
```

**Por quê:**
1. Senhas nunca devem ser plaintext
2. Credenciais padrão devem vir de variáveis de ambiente
3. Usar `werkzeug.security` para hash seguro (PBKDF2)

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Conversão de todas as queries SQL para parameterized queries
2. Criação de `config.py` para gerenciar segredos
3. Criação de `.env` com valores de exemplo
4. Atualização de `.gitignore` para não versionar `.env`
5. Remoção de hardcoded secrets de `app.py` e `database.py`
6. Validação de startup e testes básicos

---

**Confirmar refatoração na Fase 3? (y/n)**
