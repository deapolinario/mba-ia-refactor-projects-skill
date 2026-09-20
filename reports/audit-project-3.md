# Auditoria (Fases 1-2): task-manager-api
**Versão da Skill:** 3.0
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T10-41-21

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Python 3.x
Framework:      Flask + SQLAlchemy
Database:       SQLite (tasks.db)
Domain:         Task Management / Project Management
Architecture:   Partially Organized (models/routes/services/utils separados,
                 mas sem controllers — validação e lógica de negócio direto
                 nas rotas)
Source files:   15 files analyzed (1059 linhas totais)
DB tables:      3 (users, tasks, categories)
```

---

## PHASE 2: ARCHITECTURE AUDIT — varredura dos 18 anti-patterns do catálogo v3.0

| # | Anti-pattern | Severidade | Resultado |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Nenhum |
| 2 | Hardcoded Secrets | CRITICAL | 🔴 Achado |
| 3 | Senhas em Texto Plano/Expostas | CRITICAL | 🔴 Achado |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Nenhum |
| 5 | Broken Access Control | CRITICAL | 🔴 Achado |
| 6 | Weak Password Hashing | HIGH | 🟠 Achado |
| 7 | God Classes | HIGH | 🟠 Achado |
| 8 | N+1 Queries | HIGH | 🟠 Achado |
| 9 | Global State Mutável | HIGH | ✅ Nenhum ativo (ver nota) |
| 10 | Code Duplication | MEDIUM | 🟡 Achado |
| 11 | Secrets em Responses | MEDIUM | ✅ Nenhum (capturado no #3) |
| 12 | Logs Sensíveis (PII) | MEDIUM | 🟡 Achado |
| 13 | Exception Detail Leakage | MEDIUM | ✅ Nenhum |
| 14 | Magic Strings | LOW | 🔵 Achado |
| 15 | Ternários Desnecessários | LOW | 🔵 Achado |
| 16 | Monolithic Architecture | LOW/CRITICAL | 🟠 Achado (junto com #7) |
| 17 | Regressão de Refatoring | HIGH | N/A |
| 18 | Configuração Morta | LOW | N/A |

---

### [CRITICAL] 1. Hardcoded Secrets

**Arquivos:** `app.py:13`, `services/notification_service.py:9-10`

```python
# app.py
app.config['SECRET_KEY'] = 'super-secret-key-123'

# services/notification_service.py
self.email_user = 'taskmanager@gmail.com'
self.email_password = 'senha123'
```

---

### [CRITICAL] 2. Senha (hash) Exposta em Responses

**Arquivo:** `models/user.py`, linhas 16-24

```python
def to_dict(self):
    return {
        'id': self.id, 'name': self.name, 'email': self.email,
        'password': self.password,   # ← hash MD5 vai para TODA response de usuário
        'role': self.role, 'active': self.active, 'created_at': str(self.created_at)
    }
```

Usado em `GET /users`, `GET /users/:id`, `POST /users`, `PUT /users/:id` — qualquer um vê o hash de senha de qualquer usuário.

---

### [CRITICAL] 3. Broken Access Control (generalizado)

**Arquivos:** todas as rotas (`routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`)

`POST /login` retorna `'token': 'fake-jwt-token-' + str(user.id)`, mas **nenhuma rota verifica esse token** — não há middleware/decorator de auth em lugar nenhum. `DELETE /tasks/:id`, `DELETE /users/:id`, `POST/PUT/DELETE /categories`, todos os relatórios — tudo é público.

---

### [HIGH] 4. Weak Password Hashing

**Arquivo:** `models/user.py`, linhas 27-32 — `hashlib.md5()`.

---

### [HIGH] 5. God Class / Ausência de Controllers

**Arquivos:** `routes/task_routes.py` (299 linhas), `routes/report_routes.py` (223 linhas)

Rotas fazem parsing de request, validação de negócio completa e acesso a dados diretamente — sem camada de controller. `task_routes.py` está a 1 linha do limiar de 300 do catálogo.

---

### [HIGH] 6. N+1 Queries

**Arquivo:** `routes/task_routes.py` (`get_tasks`), `routes/report_routes.py` (`summary_report`)

```python
# task_routes.py - get_tasks(): para cada task, 2 queries extras
for t in tasks:
    if t.user_id:
        user = User.query.get(t.user_id)      # +1 por task
    if t.category_id:
        cat = Category.query.get(t.category_id)  # +1 por task

# report_routes.py - summary_report(): para cada user, 1 query extra
for u in users:
    user_tasks = Task.query.filter_by(user_id=u.id).all()  # +1 por user
```

---

### [MEDIUM] 7. Code Duplication (grave)

Lógica de "task atrasada" **reimplementada manualmente 4 vezes** apesar de `Task.is_overdue()` já existir em `models/task.py:50-60`:
- `routes/task_routes.py` → `get_tasks()` (linhas ~30-39) e `get_task()` (~71-80)
- `routes/report_routes.py` → `summary_report()` (~33-43) e `user_report()` (~132-135)

Helpers existentes e nunca usados:
- `utils/helpers.py: calculate_percentage()` — `report_routes.py` reimplementa `round((x/total)*100, 2) if total > 0 else 0` manualmente 3 vezes em vez de chamá-la (o import existe, a chamada não)
- `utils/helpers.py: format_date()` — importado em `report_routes.py`, nunca chamado
- `utils/helpers.py: process_task_data()` — validação completa de task já implementada, `task_routes.py` reimplementa tudo manualmente em `create_task()`/`update_task()` sem usá-la
- `utils/helpers.py: VALID_STATUSES`/`VALID_ROLES` — nunca importados; `user_routes.py:71,120` repete `['user', 'admin', 'manager']` hardcoded

---

### [MEDIUM] 8. Logs Sensíveis

**Arquivo:** `services/notification_service.py:21` — `print(f"Email enviado para {to}")` expõe o email do destinatário.

---

### [LOW] 9. Magic Strings

`VALID_STATUSES`/`VALID_ROLES` centralizados em `helpers.py` mas ignorados; listas de status/role repetidas hardcoded em `models/task.py` e `routes/user_routes.py`.

---

### [LOW] 10. Ternários Desnecessários (5 ocorrências)

- `models/user.py: is_admin()`
- `models/task.py: validate_status()`
- `utils/helpers.py: validate_email()`
- `utils/helpers.py: is_valid_color()`

Todos no padrão `if cond: return True; else: return False` → `return cond`.

---

## Nota fora do catálogo formal

`services/notification_service.py` — `NotificationService` **nunca é instanciado** em nenhum lugar do código atual (confirmado via `grep`). É dead code. As credenciais hardcoded dentro dela já estão capturadas no achado CRITICAL #1 independente do uso.

---

## Resumo Executivo

| Severidade | Count |
|---|---|
| CRITICAL | 3 |
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 2 |
| **TOTAL** | **10** |

**Status:** Fase 2 completa. Aguardando decisão do usuário sobre Fase 3.
