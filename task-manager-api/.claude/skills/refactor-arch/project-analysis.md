# Guia de Análise de Projeto

## Fase 1: Detecção de Stack

### Linguagem

**Python:**
- Arquivos: `*.py`
- Indicadores: `requirements.txt`, `setup.py`, `pyproject.toml`, `Pipfile`
- Keywords: `import`, `def`, `class`, `from ... import`

**Node.js:**
- Arquivos: `*.js`, `*.ts`
- Indicadores: `package.json`, `package-lock.json`, `yarn.lock`
- Keywords: `const`, `require()`, `import`, `module.exports`, `async/await`

**Java:**
- Arquivos: `*.java`

**Kotlin:**
- Arquivos: `*.kt`

---

### Framework

**Python:**
- `Flask`: `from flask import`, `@app.route`, `Blueprint`
- `Django`: `from django`, `models.Model`, `apps.py`, `manage.py`
- `FastAPI`: `from fastapi import`, `@app.get`, `@app.post`

**Node.js:**
- `Express`: `express()`, `app.get()`, `app.post()`, `router.use()`
- `Fastify`: `fastify()`, `fastify.get()`, `fastify.post()`
- `Koa`: `new Koa()`, `ctx.body`

**Java e Kotlin:**
- `Spring`: 

---

### Banco de Dados

**SQLite:**
- Indicador: `sqlite3`, `db.sqlite3`, `:memory:`, `database.py` com `sqlite3`

**PostgreSQL:**
- Indicador: `psycopg2`, `pg`, connection strings com `postgres://`

**MySQL:**
- Indicador: `mysql-connector`, `pymysql`, connection strings com `mysql://`

**In-Memory/Mock:**
- Indicador: `:memory:`, global objects simulating DB

---

## Fase 1: Mapeamento de Arquitetura

### Padrão 1: Monolito (Tudo em poucos arquivos)

**Sinais:**
- Pasta raiz com 2-5 arquivos Python/JS
- Sem subpastas `models/`, `routes/`, `controllers/`
- Lógica de BD, validação, roteamento no mesmo arquivo

**Estrutura típica:**
```
project/
├── app.py (ou app.js)
├── models.py
├── controllers.py
└── database.py
```

---

### Padrão 2: Parcialmente Organizado (Algumas separações)

**Sinais:**
- Subpastas `models/`, `routes/`, `services/`
- Mas sem padrão MVC claro
- Lógica espalhada entre camadas

**Estrutura típica:**
```
project/
├── app.py
├── models/
│   ├── user.py
│   └── task.py
├── routes/
│   ├── user_routes.py
│   └── task_routes.py
└── services/ (opcional)
    └── notification_service.py
```

---

## Fase 1: Output da Análise

Imprimir na tela:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       Python 3
Framework:      Flask 3.x
Database:       SQLite
Domain:         Task Manager API (users, tasks, categories)
Architecture:   Monolithic (files in root) / Partially Organized (with models/, routes/)
Source files:   X files analyzed
DB tables:      users, tasks, categories
================================
```

---

## Contagem de Arquivos

Contar apenas arquivos de código relevantes:
- Python: `*.py` (excluir `__pycache__`, `.venv`, tests se pedido)
- JavaScript: `*.js` (excluir `node_modules`)
- Não contar arquivos de config (`package.json`, `requirements.txt`, `.env`)

---

## Heurística de Domínio

Detectar o domínio pelo:
- Nome do projeto
- Modelos definidos (User, Product, Task, etc)
- Routes/endpoints existentes
- Descrição em README/comentários

Exemplos:
- "Task Manager" → `users, tasks, categories`
- "E-commerce" → `products, orders, users, payments`
- "LMS" → `students, courses, enrollments, assessments`
