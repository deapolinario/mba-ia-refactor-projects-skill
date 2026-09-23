# Auditoria (Fases 1-2): task-manager-api
**Versão da Skill:** 3.2 (20 anti-patterns, adiciona detecção de APIs deprecated)
**Data da Auditoria:** 2026-09-22
**Timestamp:** 2026-09-22T21-04-57
**Contexto:** Re-execução da skill após a v3.2 adicionar o Padrão 20 (APIs Deprecated) ao catálogo — gap que o enunciado do desafio pede explicitamente e que as auditorias anteriores (v2.2/v3.0/v3.1, ver `audit-task-manager-api-2026-09-20T18-57-12.md`) não cobriam.

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Python 3
Framework:      Flask 3.0.0 (flask-sqlalchemy, flask-cors, marshmallow)
Database:       SQLite (via SQLAlchemy, tasks.db)
Domain:         Task Manager API (users, tasks, categories) — auth por token
                 assinado (itsdangerous) e RBAC (user/admin/manager)
Architecture:   Partially Organized (models/, routes/, controllers/,
                 services/, middleware/, auth/ já separados — resultado de
                 refatorações v2.2/v3.0/v3.1 anteriores)
Source files:   27 files analyzed (excluindo .claude/, __pycache__)
DB tables:      users, tasks, categories
```

---

## PHASE 2: AUDIT COMPLETE

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

---

## PHASE 3: REFACTORING COMPLETE

Todos os 5 achados foram corrigidos:

1. Ownership check adicionado em `TaskController.update`/`delete` e `ReportController.user_report` (checa `resource.user_id == requester.id` ou `requester.role in ('admin','manager')`)
2. Helper `utils.helpers.utcnow()` criado (`datetime.now(timezone.utc).replace(tzinfo=None)`, mantendo compatibilidade naive com `due_date`/colunas `db.DateTime` existentes) e usado nos 7 arquivos afetados — 0 ocorrências de `datetime.utcnow()` restantes, confirmado sem `DeprecationWarning`
3. `exceptions.py` criado (`NotFoundError`, `ConflictError`, `ValidationError`); controllers e rotas migrados do string-matching para `except <TipoEspecífico>`
4. `MIN_PASSWORD_LENGTH`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` aplicados nos pontos de uso reais (literais antigos removidos)
5. `Config.PRIORITY_LABELS`/`MIN_PRIORITY`/`MAX_PRIORITY` centralizam a escala de prioridade

### Self-Verification (Ciclo 1)

Código relido do zero + checklist completo dos 20 anti-patterns reaplicado + teste funcional de autorização via requisições HTTP reais (Maria/user não edita/deleta/lê task ou relatório de terceiros → 403; edita o próprio → 200; admin tem override → 200). **0 achados novos.** Relatório completo: `audit-task-manager-api-2026-09-22T21-12-44.md`.

### Validação

- ✅ `python -m py_compile` em todos os arquivos: sem erros de sintaxe
- ✅ `db.create_all()` + `seed.py`: executam sem erros (confirma que a mudança de `utcnow()` não quebrou a comparação naive/aware em `Task.is_overdue()`)
- ✅ Servidor Flask inicia e responde em `/health`, `/`, `/login`, `/tasks`, `/reports/summary`, `/reports/user/<id>`, `/users`
- ✅ Status HTTP corretos (400/403/404/409) após a migração para exceções tipadas
