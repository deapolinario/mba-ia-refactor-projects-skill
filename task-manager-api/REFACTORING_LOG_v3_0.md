# Log de Refatoração: task-manager-api
**Data:** 2026-09-20
**Skill:** refactor-arch v3.0
**Fase 3:** Refactoring, Validation & Self-Verification (ciclo 1)

---

## Findings Checklist

| # | Achado | Severidade | Status |
|---|--------|-----------|--------|
| 1 | Hardcoded Secrets (SECRET_KEY + email credentials) | CRITICAL | ✅ Corrigido |
| 2 | Senha (hash) exposta em `User.to_dict()` | CRITICAL | ✅ Corrigido |
| 3 | Broken Access Control (nenhuma rota verificava o token) | CRITICAL | ✅ Corrigido |
| 4 | Weak Password Hashing (MD5) | HIGH | ✅ Corrigido |
| 5 | God Class / Ausência de Controllers | HIGH | ✅ Corrigido |
| 6 | N+1 Queries (`get_tasks`, `summary_report`, `get_categories`) | HIGH | ✅ Corrigido |
| 7 | Code Duplication (overdue reimplementado 4x, helpers nunca usados) | MEDIUM | ✅ Corrigido |
| 8 | Logs Sensíveis (email em plaintext) | MEDIUM | ✅ Corrigido |
| 9 | Magic Strings (`VALID_STATUSES`/`VALID_ROLES` nunca importados) | LOW | ✅ Corrigido |
| 10 | Ternários Desnecessários (5 ocorrências) | LOW | ✅ Corrigido |
| — | *(fora do catálogo)* `NotificationService` é dead code | — | ⏭️ Adiado — instanciá-lo está fora do escopo desta refatoração; credenciais corrigidas mesmo assim |

**Resultado:** 10/10 achados catalogados `✅ Corrigido`. 1 item fora do catálogo formal adiado com justificativa.

---

## Decisão de Design: Política de Autenticação

O achado CRITICAL #3 exigia decidir **quais rotas** proteger, já que a auditoria encontrou "nenhuma rota" com auth. Política adotada:

| Rota | Proteção |
|---|---|
| `POST /login`, `POST /users` (cadastro) | Pública |
| `GET /categories` | Pública (dado não sensível, usado em formulários) |
| `GET/PUT /users/*`, `GET /users/:id/tasks` | `login_required` |
| `DELETE /users/:id` | `login_required` + `role_required('admin')` |
| `/tasks/*` (todas) | `login_required` |
| `POST/PUT/DELETE /categories` | `login_required` + `role_required('admin', 'manager')` |
| `/reports/*` (todas) | `login_required` |

Token: assinado com `itsdangerous.URLSafeTimedSerializer` (já é dependência do Flask — nenhuma lib nova), expira em 24h (`Config.TOKEN_EXPIRATION_SECONDS`). Substitui o `'fake-jwt-token-' + str(user.id)` original, que nunca era verificado.

---

## Detalhamento

### CRITICAL 1: Hardcoded Secrets
`config.py` (novo) + `.env` (novo) + `.gitignore` (novo). `SECRET_KEY` sai de `app.py`; credenciais de email saem de `notification_service.py` — ambos via `os.getenv`.

### CRITICAL 2: Senha exposta
`User.to_dict()` (`models/user.py`) não retorna mais a coluna `password`.

### CRITICAL 3: Broken Access Control
`auth/tokens.py` (geração/verificação de token assinado) + `middleware/auth.py` (`login_required`, `role_required`) + `controllers/auth_controller.py` (login real). Ver política de rotas acima.

### HIGH 4: Weak Password Hashing
`hashlib.md5()` → `werkzeug.security.generate_password_hash/check_password_hash` (pbkdf2:sha256).

### HIGH 5: God Class / Controllers
**Criados:** `controllers/{auth,task,user,category,report}_controller.py`, `routes/category_routes.py` (separado de `report_routes.py` — categorias e relatórios são domínios diferentes).
**Reescritos (agora finos):** `routes/{task,user,report}_routes.py`, `app.py`.

### HIGH 6: N+1 Queries
- `TaskController.list_all/get_by_id`: `joinedload(Task.user, Task.category)` — de `1+2N` para 2 queries (medido: 21→2 com 10 tasks)
- `CategoryController.list_all`: `LEFT JOIN + GROUP BY` — de `1+N` para 1 query
- `ReportController.summary`: contagens por usuário via `GROUP BY` em vez de 1 query de tasks por usuário dentro de loop — 12 queries fixas (não escalam com nº de usuários, medido)

### MEDIUM 7: Code Duplication
- `Task.is_overdue()` (já existia) agora é chamado em `task_controller.py` e `report_controller.py` em vez de reimplementado
- `utils/helpers.py: calculate_percentage()`, `format_date()`, `process_task_data()` — agora efetivamente chamados pelos controllers (antes: import morto ou nem importados)
- `VALID_STATUSES`/`VALID_ROLES` de `helpers.py` removidos (duplicavam `Config.VALID_TASK_STATUSES`/`Config.VALID_ROLES`, única fonte agora)
- Bônus: `is_valid_color()` (helper existente, nunca usado) agora valida cor em `CategoryController.create/update`

### MEDIUM 8: Logs Sensíveis
`services/notification_service.py`: e-mail do destinatário mascarado antes do `print()`.

### LOW 9: Magic Strings
Ver MEDIUM 7 — mesma correção (`Config.VALID_TASK_STATUSES`/`VALID_ROLES`).

### LOW 10: Ternários Desnecessários
`User.is_admin()`, `Task.validate_status()`, `Task.validate_priority()`, `helpers.validate_email()`, `helpers.is_valid_color()` — todos simplificados para `return <condição>`.

---

## Regression Checklist (v2.2, sempre obrigatório)

| Item | Resultado |
|---|---|
| Setup/seed roda uma única vez (não por request) | ✅ `db.create_all()` roda no import do módulo, fora de qualquer handler |
| Nenhum N+1 novo introduzido | ✅ Confirmado via contagem de queries (ver abaixo) |
| Nenhuma config nova é dead code | ✅ Todo campo de `Config` tem uso real (checado com grep) |
| Nenhum literal antigo sobrou coexistindo com a config | ✅ `debug=True`, `'super-secret-key-123'`, listas de status/role hardcoded — todos substituídos |

---

## Validação Funcional (20 cenários end-to-end)

Testado com o `.venv` do próprio projeto contra a app real (Flask test client): health check, criação de usuário admin/comum, login correto/errado, `GET /users` sem/com token (sem campo `password`), `POST /tasks` sem/com token, listagem com `user_name`/`category_name`/`overdue` via JOIN, stats, categorias públicas, `POST /categories` sem token/role insuficiente/role correto, `reports/summary`, `DELETE /users/:id` role insuficiente/role correto (com cascade delete de tasks confirmado — task do usuário deletado desaparece de `GET /tasks`). Todos os 20 cenários com resultado esperado.

**Nota de dados legados:** o `tasks.db` pré-existente tinha usuários seedados com hash MD5 (código antigo). Rodar `seed.py` novamente (com `set_password()` já usando pbkdf2) recria os dados corretamente — isso não é uma regressão da refatoração, é migração de dados esperada ao mudar esquema de hash.

**Contagem de queries (antes → depois):**
- `GET /tasks` (10 tasks): 21 → **2**
- `GET /categories` (4 categorias): 5 → **1**
- `GET /reports/summary`: escalava com nº de usuários → **12 queries fixas**

---

## Estrutura Final

```
task-manager-api/
├── .env, .gitignore
├── config.py                       # secrets + domínio
├── app.py                          # entry point limpo
├── database.py
├── seed.py
├── auth/
│   └── tokens.py                   # geração/verificação de token assinado
├── middleware/
│   └── auth.py                     # login_required, role_required
├── models/
│   ├── user.py                     # sem password em to_dict, pbkdf2, ternário simplificado
│   ├── task.py                     # is_overdue() + validações simplificadas
│   └── category.py
├── controllers/
│   ├── auth_controller.py
│   ├── task_controller.py          # joinedload, usa process_task_data/is_overdue
│   ├── user_controller.py
│   ├── category_controller.py      # LEFT JOIN + GROUP BY, valida cor
│   └── report_controller.py        # GROUP BY em vez de loop, usa calculate_percentage
├── routes/
│   ├── task_routes.py              # fino, todas as rotas login_required
│   ├── user_routes.py              # fino, delete é role_required('admin')
│   ├── category_routes.py          # novo — separado de report_routes
│   └── report_routes.py            # fino, só summary + user_report
├── services/
│   └── notification_service.py     # secrets corrigidos, email mascarado em log
├── utils/
│   └── helpers.py                  # VALID_STATUSES/VALID_ROLES removidos (→ Config)
└── REFACTORING_LOG_v3_0.md
```

Próximo passo: **Self-Verification Loop (Fase 3, passo 7 da skill v3.0)**.
