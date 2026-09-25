# Auditoria Arquitetural: code-smells-project

**Contexto deste arquivo:** esta é a auditoria original (Fases 1-2, skill v2.1), a primeira execução completa da skill contra o projeto ainda não refatorado — é o que este arquivo deve documentar por exigência do enunciado (Fase 2 encontrando ≥5 achados, incluindo CRITICAL/HIGH). As rodadas de refatoração subsequentes (Fase 3 do v2.1/v2.2/v3.1, e as reauditorias da v3.2) estão documentadas nas seções abaixo, na ordem em que aconteceram.

**Versão da Skill:** 2.1
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T09-38-22

---

## PHASE 1: PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       Python 3.x
Framework:      Flask
Database:       SQLite (loja.db)
Domain:         E-commerce / Product Management API
Architecture:   Monolithic
Source files:   4 files analyzed (app.py, models.py, controllers.py, database.py)
DB tables:      4 (produtos, usuarios, pedidos, itens_pedido)
================================
```

---

## PHASE 2: ARCHITECTURE AUDIT

### **CRÍTICO (CRITICAL)**

---

#### **1. SQL Injection - String Concatenation em Queries**

**Arquivo:** `models.py`
**Linhas:** 28, 48-50, 57-61, 68, 110, 127-128, 140, 148-150, 155-161, 163-166, 174, 188, 192, 220, 224, 279-281, 289-297

**Código Problemático:**
```python
# Linha 28
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

# Linhas 48-50
cursor.execute(
    "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES ('" +
    nome + "', '" + descricao + "', " + str(preco) + ", " + str(estoque) + ", '" + categoria + "')"
)

# Linhas 57-61
cursor.execute(
    "UPDATE produtos SET nome = '" + nome + "', descricao = '" + descricao +
    "', preco = " + str(preco) + ", estoque = " + str(estoque) +
    ", categoria = '" + categoria + "' WHERE id = " + str(id)
)

# Linha 68
cursor.execute("DELETE FROM produtos WHERE id = " + str(id))

# Linha 110 (login)
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**Impacto:** Bypass de autenticação (`email = "admin@loja.com' --"`), leitura/modificação/exclusão arbitrária de dados, `DROP TABLE` via campo `nome`. É o achado mais grave do projeto — presente em praticamente toda query do `models.py`, incluindo o login.

**Refatoração Proposta:** Parameterized queries (`?`) em todas as ocorrências — SELECT, INSERT, UPDATE, DELETE e login.

**Por quê:** Parâmetros posicionais garantem que dado e comando SQL nunca se misturam, eliminando a classe inteira de vulnerabilidade.

---

#### **2. Hardcoded Secrets**

**Arquivo:** `app.py`
**Linhas:** 7

```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**Impacto:** Qualquer pessoa com acesso ao repositório falsifica sessões, tokens JWT, CSRF protection e integridade de cookies.

**Refatoração Proposta:** `config.py` lendo de `os.getenv()`, `.env` com valores reais (gitignored).

---

#### **3. Passwords em Texto Plano**

**Arquivo:** `database.py` (dados iniciais) + `models.py` (armazenamento)
**Linhas:** 76, 83

```python
# database.py linha 76
("Admin", "admin@loja.com", "admin123", "admin"),

# models.py linha 83 (armazenado como-é)
cursor.executemany(
    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
    usuarios
)
```

**Descrição:** Senhas salvas em texto plano no banco de dados, sem hash algum (não é nem MD5/SHA1 fraco — é ausência total de hashing).

**Impacto:** Vazamento do banco expõe credenciais de todos os usuários instantaneamente (reutilização de senhas em outros sites, acesso não autorizado a contas).

**Refatoração Proposta:** `generate_password_hash`/`check_password_hash` (pbkdf2:sha256) no cadastro e login.

---

### **ALTO (HIGH)**

---

#### **4. God Class - models.py**

**Arquivo:** `models.py`
**Linhas:** 1-315 (315 linhas totais)

**Descrição:** Um único arquivo concentra queries SQL, validação, lógica de negócio e serialização para 4 domínios diferentes (produtos, usuários, pedidos, itens_pedido).

**Impacto:** Impossível testar em isolamento; qualquer mudança arrisca quebrar funcionalidades não relacionadas.

**Refatoração Proposta:** Separar em `models/`, `controllers/`, `routes/` por domínio, seguindo padrão MVC.

---

#### **5. N+1 Queries**

**Arquivo:** `models.py`
**Linhas:** 187-199 (get_pedidos_usuario), 219-231 (get_todos_pedidos)

**Código Problemático:**
```python
# Linha 187-199
for row in rows:
    pedido = {...}
    cursor2 = db.cursor()
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    itens = cursor2.fetchall()
    for item in itens:
        cursor3 = db.cursor()
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
        # ← Para cada pedido: +1 query de itens + N queries de produtos
```

**Descrição:** Para cada pedido (N), fazem 1 query de itens + M queries de produtos. Resultado: 1 + N + (N*M) queries.

**Impacto:** Performance degrada exponencialmente com o volume de dados (10 pedidos = 30+ queries; 100 pedidos = 300+ queries).

**Refatoração Proposta:** Eager loading via `LEFT JOIN` + agrupamento em memória.

---

#### **6. Global State Mutável**

**Arquivo:** `database.py`
**Linhas:** 4, 8-10

```python
db_connection = None  # Variável global

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
```

**Descrição:** Conexão SQLite reaberta a cada request via `get_db()`, sem controle de concorrência (`check_same_thread=False` sem sincronização real).

**Impacto:** Race conditions e comportamento inconsistente sob carga concorrente.

**Refatoração Proposta:** Singleton thread-safe para gerenciar a conexão.

---

### **MÉDIO (MEDIUM)**

---

#### **7. Code Duplication**

**Arquivo:** `models.py`
**Linhas:** 187-199 vs 219-231

**Descrição:** Lógica de serialização de produto/pedido duplicada em múltiplos endpoints (`to_dict` reimplementado a cada função) — `get_pedidos_usuario` (187-199) e `get_todos_pedidos` (219-231) constroem o mesmo dicionário de pedido de forma idêntica.

**Refatoração Proposta:** Centralizar em métodos `to_dict()` por model.

---

#### **8. Secrets Expostas em Responses**

**Arquivo:** `controllers.py`
**Linhas:** 276-290 (health_check)

```python
def health_check():
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {...},
        "versao": "1.0.0",
        "ambiente": "producao",
        "db_path": "loja.db",
        "debug": True,
        "secret_key": "minha-chave-super-secreta-123"  # ❌ EXPÕE!
    }), 200
```

**Descrição:** Endpoint `/health` retorna a SECRET_KEY em plaintext para qualquer pessoa.

**Refatoração Proposta:** Retornar apenas `{"status": "ok", "versao": "..."}`.

---

#### **9. Logs Sensíveis (PII Exposure)**

**Arquivo:** `controllers.py`
**Linhas:** 161, 179, 182, 208-210, 248-250

```python
# Linha 161
print("Usuário criado: " + email)  # ← EXPÕE EMAIL

# Linha 179
print("Login bem-sucedido: " + email)  # ← EXPÕE EMAIL
```

**Descrição:** Emails e outros dados de usuário logados em texto plano via `print()`.

**Refatoração Proposta:** Mascarar (`mask_email()`) antes de logar.

---

### **BAIXO (LOW)**

---

#### **10. Magic Strings**

**Arquivo:** `controllers.py`
**Linhas:** 52-54

```python
categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
if categoria not in categorias_validas:
    return jsonify({"erro": "Categoria inválida. Válidas: " + str(categorias_validas)}), 400
```

**Descrição:** Lista de categorias hardcoded sem constante nomeada.

**Refatoração Proposta:** Extrair para `Config.VALID_CATEGORIES`.

---

## 📊 RESUMO EXECUTIVO

| Severidade | Count | Exemplos |
|-----------|-------|----------|
| 🔴 **CRITICAL** | 3 | SQL Injection (15+ ocorrências), Hardcoded Secrets, Passwords em texto plano |
| 🟠 **HIGH** | 3 | God Class, N+1 Queries (2 ocorrências), Global State |
| 🟡 **MEDIUM** | 3 | Code Duplication, Secrets em Response, Logs Sensíveis |
| 🔵 **LOW** | 1 | Magic Strings |
| **TOTAL** | **10 categorias / 14 achados únicos** | |

**Confirmar refatoração na Fase 3? (y/n)** → confirmado; ver seção seguinte.

---

## PHASE 3: REFATORAÇÃO (histórico de commits)

A refatoração deste projeto aconteceu em múltiplas passagens, cada uma revalidada com uma nova auditoria antes de prosseguir:

**v2.1 — Phase 3 (commit `f210e3e`):** primeira passagem, resolveu 5 dos 14 achados originais (SQL Injection em 15+ queries → parametrizadas; Hardcoded Secrets → `config.py` + `.env`; Secrets em Responses → `/health` sanitizado; Global State → `DatabaseManager` Singleton; Logs PII → `mask_email()`). Ainda seletiva, não sistemática.

**v2.2 — Phase 3 sistemática (commit `45d1131`):** reaudita o código e resolve os 15/15 achados restantes do catálogo v2.2 (incluindo os que a passagem v2.1 pulou): senhas em texto plano (hash + exclusão de `senha` de toda response), `/admin/query` (execução de SQL arbitrário) removido, `/admin/reset-db` protegido, regressão de setup-por-request corrigida, God Class decomposto em MVC (`models/`, `controllers/`, `routes/`), N+1 eliminado (JOIN único), exception leakage corrigido, duplicação removida, magic strings centralizadas em `Config`. Validado com 13 cenários funcionais via Flask test client + verificação manual em servidor real.

**Fix pontual (commit `f1f8797`):** reauditoria encontrou um N+1 residual do lado de escrita em `criar_pedido()` (1 SELECT por item do carrinho) que a passagem anterior não cobria — corrigido para 1 único `SELECT ... WHERE id IN (...)`.

**v3.1 — Broken Access Control funcional (commit `9ae2433`):** o teste funcional de autorização da skill v3.1 encontrou que toda rota fora de `/admin/*` não tinha autenticação alguma (qualquer requisição anônima alterava preço/estoque, deletava produtos, aprovava/cancelava pedidos) — gap que auditorias estruturais anteriores nunca detectaram, pois só checavam presença de decorator. Adicionado `auth.py` (`login_required`/`role_required`/`owner_or_role_required`) aplicado a todas as rotas sensíveis; criação de pedido passa a usar `usuario_id` da sessão, nunca do payload. Self-verification confirmou 0 achados com reteste funcional completo (ver `audit-code-smells-project-2026-09-20T17-11-08.md`).

---

## RE-EXECUÇÃO 2026-09-22T21-20-19 — Catálogo v3.2 (APIs Deprecated)

**Contexto:** skill atualizada para v3.2 (20 anti-patterns, Padrão 20 de APIs Deprecated). Projeto já em ótimo estado após as rodadas acima; esta execução verifica se o novo padrão encontra algo, e faz uma varredura completa de confirmação.

### Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 2 achados
- **Total:** 2 achados

Nota: o Padrão 20 (APIs Deprecated), motivo da atualização da skill para v3.2, não encontrou ocorrências neste projeto — não há uso de `datetime.utcnow()` ou equivalente; timestamps são gerados pelo próprio SQLite (`DEFAULT CURRENT_TIMESTAMP`).

### Findings

1. **[LOW]** Magic Numbers — faixas de desconto hardcoded (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`) em `models/pedido.py:137-142`, sem constante nomeada (diferente de `VALID_CATEGORIES`/`VALID_ORDER_STATUSES`, já centralizados em `Config` desde v2.2).
2. **[LOW]** Magic Numbers — limites de tamanho do nome do produto (`2`, `200`) hardcoded em `controllers/produto_controller.py:45,47`.

Relatório completo com snippets de código, impacto e refatoração proposta de cada achado: `audit-code-smells-project-2026-09-22T21-20-19.md`.

### Fase 3 (v3.2)

Ambos os achados corrigidos:

1. `Config.FAIXAS_DESCONTO` (lista de tuplas `(limite, percentual)`) centraliza as faixas de desconto; `models/pedido.py::relatorio_vendas()` itera sobre a lista em vez de `if/elif` com literais
2. `Config.MIN_PRODUTO_NOME`/`MAX_PRODUTO_NOME` centralizam os limites de tamanho do nome do produto

**Self-Verification (Ciclo 1):** código relido do zero + checklist completo dos 20 anti-patterns reaplicado. **0 achados novos** — nenhuma das mudanças tocou arquivos de autenticação/autorização, então a suíte funcional de 10 cenários já validada em `audit-code-smells-project-2026-09-20T17-11-08.md` permanece válida. Relatório completo: `audit-code-smells-project-2026-09-22T21-25-13.md`.

**Validação:**
- ✅ `python -m py_compile` em todos os arquivos: sem erros de sintaxe
- ✅ Servidor Flask inicia e responde em `/health`, `/login`, `/produtos`, `/pedidos`, `/relatorios/vendas`
- ✅ Testado via requisições HTTP reais: pedido de R$ 11.999,98 → desconto de R$ 1.200,00 (10%, faixa `> 10000`) calculado corretamente; `POST /produtos` com nome de 1/201 caracteres → 400; com 2 caracteres (limite válido) → 201

---

## RE-EXECUÇÃO 2026-09-22T21-36-26 — Confirmação Pós-Generalização do Padrão 20

Após o Padrão 20 ser generalizado (deixou de ser específico a `datetime.utcnow()`/exemplos fixos de Python-Node e passou a ser um princípio de detecção agnóstico de linguagem — commit `1d48260`), a skill foi executada novamente do zero para confirmar o estado do projeto sob o catálogo corrigido.

**Resultado: 0 achados.** Aplicado o princípio geral do Padrão 20 contra a stack real (Python 3.9, Flask 3.1.1, Werkzeug, sqlite3, flask-cors 5.0.1) — nenhuma API atualmente deprecated em uso (verificado além de `datetime.utcnow()`: `flask.Markup`/`before_first_request`/`safe_str_cmp`, `collections.Iterable`/`Mapping`, `imp`/`distutils`/`optparse`/`urllib2`, adapters de datetime do `sqlite3`). Os 2 achados LOW corrigidos na rodada anterior permanecem estáveis. Relatório completo: `audit-code-smells-project-2026-09-22T21-36-26.md`.
