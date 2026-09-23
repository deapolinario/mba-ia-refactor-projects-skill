# Auditoria (Fases 1-2): task-manager-api

**Contexto deste arquivo:** esta é a auditoria original (Fases 1-2, skill v3.0), a primeira execução completa da skill contra o projeto ainda não refatorado — é o que este arquivo deve documentar por exigência do enunciado (Fase 2 encontrando ≥5 achados, incluindo CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW). As rodadas de refatoração subsequentes estão documentadas nas seções abaixo, na ordem em que aconteceram, incluindo 2 achados CRITICAL adicionais (v3.1 e v3.2) que escaparam da self-verification anterior.

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

**Confirmar refatoração na Fase 3? (y/n)** → confirmado; ver seção seguinte.

---

## PHASE 3: REFATORAÇÃO (histórico de commits)

**Phase 3 sistemática + self-verification limpa (commit `88a9bcb`):** resolve os 10/10 achados desta auditoria. Hardcoded secrets → `config.py` + `.env`; hash de senha removido de `User.to_dict()`; Broken Access Control → token assinado real (`itsdangerous`) + `login_required`/`role_required` em todas as rotas sensíveis; MD5 → `werkzeug pbkdf2:sha256`; God Class → 5 controllers adicionados (`auth`/`task`/`user`/`category`/`report`), rotas reduzidas a mapeamento HTTP fino; N+1 eliminado (`joinedload`, `LEFT JOIN` + `GROUP BY`, medido: 21→2 queries para 10 tasks); `is_overdue()`/`calculate_percentage()`/`format_date()`/`process_task_data()` (já existiam, nunca eram chamados) passam a ser usados pelos controllers; email mascarado em log; `VALID_STATUSES`/`VALID_ROLES` consolidados em `Config`; 5 ternários desnecessários simplificados. Validado com 20 cenários end-to-end via Flask test client. **Self-verification (passo 7):** releitura independente dos 22 arquivos, checklist completa dos 18 padrões — 0 achados, ciclo encerra.

**v3.1 — self-verification ciclo 2, achado que a checagem estrutural não pegava (commit `b264380`):** uma nova reauditoria testou a lógica de autorização **dentro** dos controllers, não só a presença do decorator, e encontrou 2 CRITICAL que o ciclo 1 não pegava: `PUT /users/:id` tinha `@login_required` mas nenhuma checagem de ownership — qualquer usuário `role=user` alterava `role`/`active` de qualquer outro usuário, incluindo autopromoção a admin; `POST /users` (cadastro público, corretamente sem auth) aceitava `role` do payload sem restrição — visitante anônimo se cadastrava direto como admin. Corrigido: `UserController.update()` passa a checar ownership/role antes de aplicar mudanças a campos sensíveis; `UserController.create()` sempre força `role='user'`. Suíte de 12 cenários revalidada. Causa raiz registrada em `analises/REFACTORING_LOG_v3_0.md`: self-verification checava "a rota tem o decorator?", nunca testava a lógica de autorização dentro do controller — lição que motivou o Padrão 19 (v3.1) e o teste funcional obrigatório na self-verification.

---

## RE-EXECUÇÃO 2026-09-22T21-04-57 — Catálogo v3.2 (APIs Deprecated)

**Contexto:** skill atualizada para v3.2 (20 anti-patterns, Padrão 20 de APIs Deprecated). O achado que motivou essa atualização foi encontrado exatamente neste projeto.

### Resumo Executivo

- **CRITICAL:** 1 achado
- **HIGH:** 0 achados
- **MEDIUM:** 2 achados
- **LOW:** 2 achados
- **Total:** 5 achados

### Findings

1. **[CRITICAL]** Privilege Escalation / IDOR em `Tasks` e `Reports` (`routes/task_routes.py`, `controllers/task_controller.py`, `routes/report_routes.py`) — `PUT/DELETE /tasks/:id` e `GET /reports/user/:id` só exigiam `@login_required`, sem checar ownership; qualquer usuário autenticado editava/apagava tasks de terceiros ou lia relatório de produtividade alheio. Mesmo padrão já corrigido em `/users` (v3.1), nunca propagado para tasks/reports.

2. **[MEDIUM]** APIs Deprecated — `datetime.utcnow()` em **15 linhas / 7 arquivos** (`models/task.py`, `models/user.py`, `models/category.py`, `utils/helpers.py`, `controllers/report_controller.py`, `services/notification_service.py`, `seed.py`). Achado que motivou a atualização do catálogo para v3.2 (Padrão 20).

3. **[MEDIUM]** Code Duplication — dispatch de status HTTP por string-matching na mensagem de exceção (`'não encontrada' in str(e)`), repetido em 3 arquivos de rotas.

4. **[LOW]** Configuração Morta — `MIN_PASSWORD_LENGTH`, `MAX_TITLE_LENGTH`, `DEFAULT_COLOR` etc. definidas em `utils/helpers.py` mas nunca usadas; os mesmos valores apareciam hardcoded em outros pontos.

5. **[LOW]** Magic Numbers — escala de prioridade (1-5) e mapeamento de labels hardcoded/duplicado em 3 arquivos, sem constante centralizada (ao contrário de `VALID_TASK_STATUSES`, já corrigido em v2.2).

Relatório completo com snippets de código, impacto e refatoração proposta de cada achado: `audit-task-manager-api-2026-09-22T21-04-57.md`.

### Fase 3 (v3.2, rodada 1)

Todos os 5 achados foram corrigidos:

1. Ownership check adicionado em `TaskController.update`/`delete` e `ReportController.user_report` (checa `resource.user_id == requester.id` ou `requester.role in ('admin','manager')`)
2. Helper `utils.helpers.utcnow()` criado (`datetime.now(timezone.utc).replace(tzinfo=None)`, mantendo compatibilidade naive com `due_date`/colunas `db.DateTime` existentes) e usado nos 7 arquivos afetados — 0 ocorrências de `datetime.utcnow()` restantes, confirmado sem `DeprecationWarning`
3. `exceptions.py` criado (`NotFoundError`, `ConflictError`, `ValidationError`); controllers e rotas migrados do string-matching para `except <TipoEspecífico>`
4. `MIN_PASSWORD_LENGTH`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` aplicados nos pontos de uso reais (literais antigos removidos)
5. `Config.PRIORITY_LABELS`/`MIN_PRIORITY`/`MAX_PRIORITY` centralizam a escala de prioridade

**Self-Verification (Ciclo 1):** código relido do zero + checklist completo dos 20 anti-patterns reaplicado + teste funcional de autorização via requisições HTTP reais (Maria/user não edita/deleta/lê task ou relatório de terceiros → 403; edita o próprio → 200; admin tem override → 200). **0 achados novos.** Relatório completo: `audit-task-manager-api-2026-09-22T21-12-44.md`.

**Validação:**
- ✅ `python -m py_compile` em todos os arquivos: sem erros de sintaxe
- ✅ `db.create_all()` + `seed.py`: executam sem erros (confirma que a mudança de `utcnow()` não quebrou a comparação naive/aware em `Task.is_overdue()`)
- ✅ Servidor Flask inicia e responde em `/health`, `/`, `/login`, `/tasks`, `/reports/summary`, `/reports/user/<id>`, `/users`
- ✅ Status HTTP corretos (400/403/404/409) após a migração para exceções tipadas

---

## RE-EXECUÇÃO 2026-09-22T21-45-52 — Novos Achados (Padrão 19 e 20)

Uma re-auditoria anterior (2026-09-22T21-16-45) havia confirmado 0 achados. Esta rodada aplicou mais rigor — checar cada endpoint de escrita individualmente (lição do achado do ecommerce-api-legacy) e o Padrão 20 com conhecimento da versão real de cada dependência — e encontrou 2 novos achados:

1. **[CRITICAL]** IDOR/Mass Assignment em `POST /tasks` — `PUT`/`DELETE /tasks/:id` já checavam ownership desde a rodada anterior, mas `TaskController.create` nunca recebeu `requester` e usava `user_id` direto do payload, sem checar dono. Confirmado por exploração real: Maria (usuária comum) criou tasks (incluindo uma já `done`) atribuídas a João, distorcendo `/reports/user/1`.
2. **[MEDIUM]** `Query.get()` do SQLAlchemy — 15 ocorrências em 6 arquivos. Confirmado com `DeprecationWarning` real (SQLAlchemy 2.0.54: "Query.get() ... becomes a legacy construct in 2.0"). Achado relevante porque é um exemplo diferente do que originou o Padrão 20 (`datetime.utcnow()`), confirmando que a generalização do catálogo funciona para APIs de framework/ORM, não só da stdlib.

Ambos corrigidos: ownership check adicionado em `TaskController.create` (mesmo padrão de `update`/`delete`); as 15 ocorrências de `Query.get()` substituídas por `db.session.get()` (incluindo a variante com `joinedload` via parâmetro `options=`).

**Self-verification (ciclo 1): 0 achados novos.** Testado via requisições HTTP reais: exploit de criação bloqueado (403), override de admin funcional (201), todos os 15 pontos de `db.session.get()` exercitados sem erro, sem `DeprecationWarning` (`-W error::DeprecationWarning`).

Relatórios: `audit-task-manager-api-2026-09-22T21-45-52.md` (Fase 2) e `audit-task-manager-api-2026-09-22T21-49-16.md` (self-verification).
