# Relatório de Auditoria - task-manager-api

**Data:** 2026-09-22
**Stack:** Python 3 + Flask 3.0.0 + SQLite (SQLAlchemy)
**Domínio:** Task Manager API (users, tasks, categories)
**Contexto:** Esta é uma re-auditoria com o catálogo v3.2. As auditorias anteriores (v2.2/v3.0/v3.1) já corrigiram SQL Injection, Hardcoded Secrets, Senha em Texto Plano, N+1 Queries, Broken Access Control e Privilege Escalation em `/users`. v3.2 adiciona o Padrão 20 (APIs Deprecated) ao catálogo, o que revelou o achado principal desta rodada.

---

## Resumo Executivo

- **CRITICAL:** 1 achado
- **HIGH:** 0 achados
- **MEDIUM:** 2 achados
- **LOW:** 2 achados
- **Total:** 5 achados

---

## Findings Detalhados

### [CRITICAL] Privilege Escalation via Autorização Insuficiente (IDOR) — Tasks e Reports

**Arquivo:** `routes/task_routes.py` (Linhas: 36-54), `controllers/task_controller.py` (Linhas: 70-105), `routes/report_routes.py` (Linhas: 13-19)

**Descrição:**
`PUT /tasks/<id>` e `DELETE /tasks/<id>` exigem apenas `@login_required` — qualquer usuário autenticado (role `user`) pode editar ou apagar a task de **qualquer outro usuário**, não só as próprias, porque `TaskController.update`/`delete` nunca recebem o `requester` nem checam `task.user_id`. O padrão de ownership-check já existe no projeto (`UserController.update`, corrigido na v3.1) mas não foi replicado para tasks. Adicionalmente, `GET /reports/user/<id>` também só exige `@login_required`, permitindo que qualquer usuário veja estatísticas de produtividade de qualquer outro usuário pelo ID.

**Código Problemático:**
```python
# routes/task_routes.py
@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    try:
        task = TaskController.update(task_id, request.get_json())  # ❌ sem requester
        ...

# controllers/task_controller.py
@staticmethod
def update(task_id, data):
    task = Task.query.get(task_id)
    ...
    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in validated:
            setattr(task, field, validated[field])  # ❌ nenhuma checagem de ownership
```

**Impacto:**
- Qualquer usuário autenticado (role `user`) pode alterar ou deletar tasks de terceiros — perda de dados e integridade
- Qualquer usuário autenticado pode ler relatório de produtividade de qualquer outro usuário via `/reports/user/<id>`
- É o mesmo Padrão 19 já corrigido em `/users` (v3.1), mas que não foi propagado para o domínio de tasks/reports — mostra que a correção pontual não cobriu todos os recursos com o mesmo formato de IDOR

**Refatoração Proposta:**
```python
# controllers/task_controller.py
@staticmethod
def update(task_id, data, requester):
    task = Task.query.get(task_id)
    if not task:
        raise ValueError('Task não encontrada')
    if task.user_id != requester.id and requester.role not in ('admin', 'manager'):
        raise PermissionError('Você só pode editar suas próprias tasks')
    ...

# routes/task_routes.py
@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    try:
        task = TaskController.update(task_id, request.get_json(), g.current_user)
        return jsonify(task), 200
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    ...
# Mesmo padrão para delete() e para ReportController.user_report (checar
# requester.id == user_id ou requester.role in ('admin','manager'))
```

**Por quê:**
Autenticação (`@login_required`) prova identidade; autorização (ownership check) prova permissão sobre aquele recurso específico. São coisas diferentes — o guard de auth por si só nunca é prova de que a lógica de autorização está correta (mesma lição do Padrão 19/v3.1, agora aplicada a um recurso diferente).

---

### [MEDIUM] APIs Deprecated/Obsoletas — `datetime.utcnow()`

**Arquivo:** `models/task.py` (Linhas: 15, 16, 49), `models/user.py` (Linha: 15), `models/category.py` (Linha: 11), `utils/helpers.py` (Linha: 28), `controllers/report_controller.py` (Linhas: 29, 60, 86), `services/notification_service.py` (Linha: 52), `seed.py` (Linhas: 66, 67, 69, 70, 74)

**Descrição:**
`datetime.utcnow()` é usado em 15 linhas (16 chamadas) espalhadas por 7 arquivos para gerar timestamps (`created_at`, `updated_at`, cálculo de overdue, relatórios, seed). É deprecated desde Python 3.12 (`DeprecationWarning: datetime.datetime.utcnow() is deprecated`) porque retorna um datetime **naive** (sem timezone), o que é uma fonte conhecida de bugs sutis de fuso horário.

**Código Problemático:**
```python
# models/task.py
created_at = db.Column(db.DateTime, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
...
def is_overdue(self):
    ...
    return self.due_date < datetime.utcnow()
```

**Impacto:**
- Quebra garantida em uma futura major do Python que remova a API (hoje só emite warning)
- Datetime naive já é fonte de bugs: nenhuma garantia de que todo o codebase trata o valor como UTC consistentemente; comparações com datetimes aware (se algum dia introduzidos, ex: via biblioteca externa) lançam `TypeError`
- Passou despercebido em 3 rodadas de auditoria anteriores porque nenhuma delas tinha esse padrão no catálogo — não é um erro de execução, e por isso não aparece em testes que não verificam deprecation warnings

**Refatoração Proposta:**
```python
from datetime import datetime, timezone

created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
```

**Nota de atenção para a Fase 3:** `due_date` é populado via `utils.helpers.parse_date()` (`datetime.strptime`), que retorna datetime **naive**. Se `created_at`/`updated_at`/`utcnow()` viram aware e `due_date` continuar naive, a comparação em `Task.is_overdue()` (`self.due_date < datetime.now(timezone.utc)`) lança `TypeError: can't compare offset-naive and offset-aware datetimes`. A Fase 3 precisa tratar os dois lados de forma consistente — ex: `datetime.now(timezone.utc).replace(tzinfo=None)` para manter compatibilidade com colunas `db.DateTime` naive, ou migrar `parse_date`/coluna para timezone-aware also. Este é exatamente o tipo de regressão que o self-verification (Fase 3, passo 7) deve pegar se não for tratado corretamente na primeira tentativa.

**Por quê:**
API deprecated tem prazo de validade conhecido — adiar a migração só transforma um fix simples hoje em um breaking change forçado depois. Ver Padrão 20 em `anti-patterns-catalog.md` e Padrão 22 em `refactoring-playbook.md`.

---

### [MEDIUM] Code Duplication — Dispatch de Erro por String Matching em Rotas

**Arquivo:** `routes/user_routes.py` (Linhas: 30, 43-46), `routes/task_routes.py` (Linha: 43), `routes/category_routes.py` (Linha: 32)

**Descrição:**
Três blueprints diferentes decidem o status HTTP a partir de `if 'não encontrada' in str(e)` / `'já cadastrado' in str(e)` — checagem de substring na mensagem da exceção, duplicada em cada arquivo de rotas, em vez de usar tipos de exceção distintos (ou um atributo de status na exceção).

**Código Problemático:**
```python
# repetido (com pequenas variações) em user_routes.py, task_routes.py, category_routes.py
except ValueError as e:
    status = 404 if 'não encontrada' in str(e) else 400
    return jsonify({'error': str(e)}), status
```

**Impacto:**
- Mudar o texto de uma mensagem de erro no controller (ex: "não encontrada" → "inexistente") quebra silenciosamente o mapeamento de status HTTP em qualquer rota que dependa dessa substring
- Lógica de mapeamento de erro duplicada em 3 lugares — correção precisa ser replicada manualmente

**Refatoração Proposta:**
```python
# exceptions.py (novo)
class NotFoundError(Exception): pass
class ConflictError(Exception): pass

# controllers usam os tipos específicos em vez de ValueError genérico
raise NotFoundError('Usuário não encontrado')

# routes/*.py — cada exceção mapeia para 1 status, sem string matching
except NotFoundError as e:
    return jsonify({'error': str(e)}), 404
except ConflictError as e:
    return jsonify({'error': str(e)}), 409
```

**Por quê:** Tipos de exceção são um contrato explícito; string matching na mensagem é frágil e acopla o texto de erro (potencialmente exibido ao usuário) à lógica de roteamento HTTP.

---

### [LOW] Configuração Morta — Constantes Definidas mas Nunca Usadas

**Arquivo:** `utils/helpers.py` (Linhas: 100-104), usado incorretamente em `utils/helpers.py:52,73` e `controllers/user_controller.py:49,104`

**Descrição:**
`MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` e `DEFAULT_COLOR` são definidas em `utils/helpers.py` mas nunca importadas ou referenciadas em nenhum outro arquivo do projeto. Nos pontos onde deveriam ser usadas, os mesmos valores aparecem hardcoded como literais: `len(title) >= 3 and len(title) <= 200` (helpers.py:52), `1 <= p <= 5` (helpers.py:73, sem relação com `DEFAULT_PRIORITY`), `len(password) < 4` (user_controller.py:49 e 104, deveria usar `MIN_PASSWORD_LENGTH`), e `'#000000'` hardcoded em `category_controller.py` e `models/category.py` em vez de `DEFAULT_COLOR`.

**Código Problemático:**
```python
# utils/helpers.py — definidas mas mortas
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_COLOR = '#000000'

# controllers/user_controller.py — literal duplicado em vez da constante
if len(password) < 4:  # ❌ deveria ser MIN_PASSWORD_LENGTH
    raise ValueError('Senha deve ter no mínimo 4 caracteres')
```

**Impacto:**
Falsa sensação de que os limites são configuráveis num único lugar; na prática, mudar `MIN_PASSWORD_LENGTH` não afeta nada — o valor real está hardcoded em 2 lugares diferentes que precisariam ser encontrados e editados manualmente.

**Refatoração Proposta:**
```python
from utils.helpers import MIN_PASSWORD_LENGTH

if len(password) < MIN_PASSWORD_LENGTH:
    raise ValueError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
```

**Por quê:** Ver Padrão 18 em `anti-patterns-catalog.md` — validação da Fase 3 deve fazer grep dos literais antigos (`< 4`, `'#000000'`, `<= 200`) para confirmar que foram substituídos pela constante correspondente em todos os pontos de uso.

---

### [LOW] Magic Numbers — Escala de Prioridade (1-5) Sem Constante Nomeada

**Arquivo:** `models/task.py` (Linha: 42), `utils/helpers.py` (Linha: 73), `controllers/report_controller.py` (Linhas: 73-77)

**Descrição:**
A escala de prioridade de tasks (1 a 5) é validada com o literal `1 <= p <= 5` duplicado em `models/task.py` e `utils/helpers.py`, e o mapeamento de número → rótulo (`1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'`) é hardcoded em `report_controller.py` sem nenhuma constante ou enum compartilhado — diferente de `VALID_TASK_STATUSES`/`VALID_ROLES`, que já foram corretamente centralizados em `Config` numa refatoração anterior.

**Código Problemático:**
```python
# controllers/report_controller.py
'tasks_by_priority': {
    'critical': priority_counts.get(1, 0),
    'high': priority_counts.get(2, 0),
    'medium': priority_counts.get(3, 0),
    'low': priority_counts.get(4, 0),
    'minimal': priority_counts.get(5, 0),
},
```

**Refatoração Proposta:**
```python
# config.py
class Config:
    ...
    PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5

# report_controller.py
'tasks_by_priority': {
    label: priority_counts.get(num, 0)
    for num, label in Config.PRIORITY_LABELS.items()
},
```

**Impacto:** Legibilidade e manutenibilidade — adicionar uma 6ª prioridade exige editar 3 arquivos em vez de 1.

**Por quê:** Mesmo princípio já aplicado a `VALID_TASK_STATUSES`/`VALID_ROLES` neste projeto (v2.2) — só não foi estendido à escala de prioridade.

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Ownership check em `TaskController.update`/`delete` e `ReportController.user_report` (CRITICAL)
2. Substituição de todas as 15 ocorrências de `datetime.utcnow()` por `datetime.now(timezone.utc)`, com atenção à compatibilidade naive/aware em `Task.is_overdue()`
3. Introdução de exceções tipadas (`NotFoundError`/`ConflictError`) para eliminar o string-matching duplicado nas rotas
4. Aplicação das constantes já existentes (`MIN_PASSWORD_LENGTH`, `MAX_TITLE_LENGTH`, `DEFAULT_COLOR`) nos pontos de uso reais
5. Centralização da escala/labels de prioridade em `Config.PRIORITY_LABELS`
6. Validação de startup + teste funcional de autorização (self-verification obrigatório, incluindo o novo endpoint de tasks)

**Confirmar refatoração na Fase 3? (y/n)**
