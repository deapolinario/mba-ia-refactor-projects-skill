# Relatório de Auditoria - task-manager-api

**Data:** 2026-09-22
**Stack:** Python 3 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.54) + SQLite
**Domínio:** Task Manager API (users, tasks, categories)
**Contexto:** Catálogo v3.2 (Padrão 20 generalizado). Projeto já havia confirmado 0 achados na rodada anterior (`audit-task-manager-api-2026-09-22T21-16-45.md`). Esta rodada aplicou mais rigor em dois pontos, motivados pela lição da auditoria do ecommerce-api-legacy (bug escapou por testar só um branch de um fluxo com múltiplos caminhos): (1) checar CADA operação de escrita individualmente por ownership, não confiar que "já foi corrigido em outro endpoint parecido" significa que todos estão corrigidos; (2) aplicar o Padrão 20 (APIs Deprecated) com conhecimento real da versão instalada de cada dependência, não só os exemplos do catálogo.

---

## Resumo Executivo

- **CRITICAL:** 1 achado
- **HIGH:** 0 achados
- **MEDIUM:** 1 achado
- **LOW:** 0 achados
- **Total:** 2 achados

---

## Findings Detalhados

### [CRITICAL] IDOR/Mass Assignment na Criação de Tasks — `user_id` Não Restrito ao Requester

**Arquivo:** `controllers/task_controller.py` (Linhas: 37-68), `routes/task_routes.py` (Linhas: 26-33)

**Descrição:**
`PUT`/`DELETE /tasks/:id` já checam ownership (`task.user_id != requester.id`) desde a correção anterior (v3.2, commit `b791f83`). Mas `POST /tasks` (criação) **nunca recebeu o mesmo tratamento**: `TaskController.create(data)` não recebe `requester` e usa `data.get('user_id')` diretamente do payload do cliente, sem checar se corresponde a quem está autenticado. Qualquer usuário `role=user` pode criar uma task atribuída a **qualquer outro `user_id` existente**.

**Código Problemático:**
```python
# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        task = TaskController.create(request.get_json())  # ❌ sem requester
        ...

# controllers/task_controller.py
@staticmethod
def create(data):
    ...
    user_id = data.get('user_id')  # ❌ vem direto do payload, sem checar dono
    if user_id and not User.query.get(user_id):
        raise NotFoundError('Usuário não encontrado')
    ...
    task.user_id = user_id
```

**Prova de exploração (testado contra o servidor real, seed padrão):**
```bash
# Maria (role=user, id=2) cria task atribuída a João (id=1)
POST /tasks {"title":"Task maliciosa","user_id":1,"status":"pending"} (Bearer <token da Maria>)
→ 201 Created, user_id: 1

# Maria cria uma SEGUNDA task, já como "done", para inflar as estatísticas de João
POST /tasks {"title":"Fake completed task","user_id":1,"status":"done","priority":1}
→ 201 Created, user_id: 1

# GET /reports/user/1 (como João) confirma: total_tasks subiu de 4 para 5+ com
# tasks que ele nunca criou, prontas para distorcer completion_rate/overdue
```

**Impacto:**
- Qualquer usuário autenticado pode poluir a lista de tasks de outro usuário (spam de tasks pendentes/atrasadas) ou forjar tasks `done` em nome de outra pessoa
- Distorce diretamente as métricas de `/reports/user/<id>` e `/reports/summary` — completion rate, overdue count e total_tasks deixam de refletir a realidade
- É o mesmo Padrão 19 (Privilege Escalation/IDOR) já corrigido em update/delete, mas nunca propagado para o endpoint de criação — mesma lição do achado do ecommerce-api-legacy: corrigir um branch/endpoint não garante que os irmãos dele também estão corrigidos

**Refatoração Proposta:**
```python
# controllers/task_controller.py
@staticmethod
def create(data, requester):
    ...
    user_id = data.get('user_id', requester.id)
    if user_id != requester.id and requester.role not in ('admin', 'manager'):
        raise PermissionError('Você só pode criar tasks para si mesmo')
    if user_id and not User.query.get(user_id):
        raise NotFoundError('Usuário não encontrado')
    ...

# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    try:
        task = TaskController.create(request.get_json(), g.current_user)
        return jsonify(task), 201
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    ...
```

**Por quê:** Mesmo princípio de `update`/`delete` — ownership check precisa existir em toda operação de escrita sobre o recurso, não só nas que "pareciam" mais óbvias na primeira auditoria.

---

### [MEDIUM] APIs Deprecated — `Query.get()` do SQLAlchemy (Legacy API desde 2.0)

**Arquivo:** `middleware/auth.py:24`, `controllers/report_controller.py:101`, `controllers/task_controller.py:33,50,54,73,86,91,104`, `controllers/category_controller.py:51,71`, `controllers/user_controller.py:17,78,122,131` (15 ocorrências, 6 arquivos)

**Descrição:**
O projeto usa `SQLAlchemy.query.get(id)` (ex: `User.query.get(user_id)`) em 15 pontos. Confirmado que a versão instalada (**SQLAlchemy 2.0.54**, via Flask-SQLAlchemy 3.1.1) já marca esse método como **legacy**, emitindo `DeprecationWarning` em tempo real:

```
DeprecationWarning: The Query.get() method is considered legacy as of the
1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method
is now available as Session.get() (deprecated since: 2.0)
```

Este é um exemplo diferente do achado que originou o Padrão 20 (`datetime.utcnow()` no Python) — confirma que o princípio generalizado do catálogo (aplicar conhecimento da versão real da stack detectada, não só os exemplos listados) funciona também para APIs de frameworks/ORMs, não só da stdlib.

**Código Problemático:**
```python
# controllers/user_controller.py
user = User.query.get(user_id)  # ❌ legacy desde SQLAlchemy 2.0

# controllers/task_controller.py
task = Task.query.options(joinedload(Task.user), joinedload(Task.category)).get(task_id)  # ❌ idem
```

**Refatoração Proposta:**
```python
from database import db

# Forma simples
user = db.session.get(User, user_id)  # ✅

# Forma com eager loading (substitui .query.options(...).get(...))
task = db.session.get(
    Task, task_id,
    options=[joinedload(Task.user), joinedload(Task.category)]
)  # ✅
```

**Impacto:** Não é um bug de correção hoje (o método ainda funciona), mas é uma remoção planejada — SQLAlchemy 2.x mantém compatibilidade só durante a série 2.x; a migração adiada acumula em 15 pontos que precisarão ser trocados de qualquer forma. Severidade MEDIUM (não escala para HIGH: não há bug de segurança/correção associado, só dívida técnica de API).

**Por quê:** Ver Padrão 20 em `anti-patterns-catalog.md` — aplicar o substituto oficial indicado na própria mensagem de depreciação (`Session.get()`) em todas as ocorrências.

---

## Verificações Sem Achados

Demais 18 padrões do catálogo v3.2: sem novas ocorrências, incluindo reteste funcional da correção de IDOR em update/delete (`PUT`/`DELETE /tasks/:id`, `GET /reports/user/:id`) confirmado ainda correto na rodada anterior.

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Ownership check em `TaskController.create` (CRITICAL)
2. Substituição das 15 ocorrências de `Query.get()` por `db.session.get()` (MEDIUM)
3. Validação de startup + teste funcional de autorização cobrindo especificamente `POST /tasks` com `user_id` de terceiros

**Confirmar refatoração na Fase 3? (y/n)**
