# Refactor Architecture — Skill de Auditoria e Refatoração Automatizada

Skill `refactor-arch` para Claude Code que analisa, audita e refatora codebases legadas para o padrão MVC, de forma agnóstica de tecnologia. Testada e validada em 3 projetos reais (2x Python/Flask, 1x Node.js/Express), com correção completa aplicada, commitada e **confirmada por reauditoria final independente com 0 achados nos 3** (v3.1, incluindo teste funcional de autorização).

> Este é o enunciado original do desafio: [`README_enunciado.md`](README_enunciado.md).

---

## Sumário

- [A) Análise Manual](#a-análise-manual)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Antes de escrever qualquer linha da skill, os 3 projetos foram lidos e auditados manualmente, documentando achados com arquivo, linha e severidade exatos. Documento completo: [`analises/ANALISE_MANUAL.md`](analises/ANALISE_MANUAL.md).

### Projeto 1 — code-smells-project (Python/Flask, E-commerce)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1.1 | 🔴 CRITICAL | SQL Injection | `models.py` (13 ocorrências) | Strings concatenadas em query — qualquer parâmetro de entrada manipula o SQL executado |
| 1.2 | 🔴 CRITICAL | `SECRET_KEY` hardcoded | `app.py:7` | Chave de sessão/token no código-fonte, versionada no git |
| 1.3 | 🔴 CRITICAL | Senhas em texto plano | `database.py`, `models.py` | Usuários seedados e criados sem qualquer hash |
| 1.4 | 🔴 CRITICAL | `POST /admin/query` executa SQL arbitrário | `app.py:59-78` | Qualquer requisição sem autenticação roda SQL livre no banco |
| 1.5 | 🔴 CRITICAL | `POST /admin/reset-db` sem proteção | `app.py:47-57` | Apaga todos os dados, sem auth nem confirmação |
| 1.6 | 🟠 HIGH | God Module | `models.py` (315 linhas) | Uma única camada concentra queries, validação e transformação de 4 domínios |
| 1.7 | 🟠 HIGH | N+1 Queries | `models.py:187-231` | Loop dentro de loop de queries ao montar pedidos |
| 1.8 | 🟠 HIGH | Estado global mutável | `database.py:4,9` | Conexão global + `check_same_thread=False` sem sincronização |
| 1.9 | 🟡 MEDIUM | DEBUG ativo | `app.py:8` | Stack traces expostos em produção |
| 1.10 | 🟡 MEDIUM | Duplicação de código | `models.py:171-233` | Duas funções com a mesma lógica de montagem de pedido |
| 1.11 | 🟡 MEDIUM | Secret em response | `controllers.py:289` | `health_check()` retorna a `SECRET_KEY` |
| 1.12 | 🟡 MEDIUM | Log com PII | `controllers.py:161` | Email do usuário em `print()` |
| 1.13 | 🔵 LOW | Magic strings | `controllers.py:52-54` | Lista de categorias hardcoded, duplicável |
| 1.14 | 🔵 LOW | Falta de validação de entrada | `models.py:285-299` | Parâmetros de busca sem sanitização |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 2.1 | 🔴 CRITICAL | Credenciais hardcoded | `utils.js:2-6` | DB, gateway de pagamento e SMTP expostos no código |
| 2.2 | 🔴 CRITICAL | "Criptografia" falsa (Base64) | `utils.js:17-23` | `badCrypto()` não é hash — reversível trivialmente |
| 2.3 | 🔴 CRITICAL | Senha em texto plano | `AppManager.js:18` | Seed insere senha sem hash |
| 2.4 | 🔴 CRITICAL | Validação de cartão por 1 dígito | `AppManager.js:46` | Qualquer cartão iniciando em "4" é aprovado |
| 2.5 | 🔴 CRITICAL | Senha default silenciosa | `AppManager.js:68` | Bypass de autenticação se senha não enviada |
| 2.6 | 🟠 HIGH | God Class | `AppManager.js` (142 linhas) | Uma classe faz init de BD, rotas, checkout e relatório |
| 2.7 | 🟠 HIGH | Callback Hell | `AppManager.js:37-78` | 5 níveis de callbacks aninhados |
| 2.8 | 🟠 HIGH | Integridade referencial | `AppManager.js:131-137` | Delete de usuário deixa matrículas/pagamentos órfãos |
| 2.9 | 🟠 HIGH | Race condition | `AppManager.js:83-129` | Contadores decrementados manualmente em callbacks concorrentes |
| 2.10 | 🟠 HIGH | Error handling inconsistente | `AppManager.js:35-78` | Mistura `.send()`/`.json()` sem padrão |
| 2.11 | 🟡 MEDIUM | Estado global mutável | `utils.js:9-10` | `globalCache`/`totalRevenue` compartilhados entre requests |
| 2.12 | 🟡 MEDIUM | Log de dado sensível | `AppManager.js:45` | Número de cartão completo em `console.log` |

### Projeto 3 — task-manager-api (Python/Flask, Task Manager)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 3.1 | 🔴 CRITICAL | Senha (hash) exposta em JSON | `user.py`, `user_routes.py` | `to_dict()` inclui o hash da senha em toda response de usuário |
| 3.2 | 🔴 CRITICAL | Credenciais de email hardcoded | `notification_service.py:9-10` | Login SMTP real no código-fonte |
| 3.3 | 🔴 CRITICAL | `SECRET_KEY` hardcoded | `app.py:13` | Mesma classe de risco do projeto 1 |
| 3.4 | 🟠 HIGH | MD5 para hash de senha | `user.py:29` | Quebrado por rainbow table em milissegundos |
| 3.5 | 🟠 HIGH | N+1 Queries | `task_routes.py:41-56` | Query de User + Category por task, dentro de loop |
| 3.6 | 🟡 MEDIUM | `except:` genérico | `task_routes.py:62` | Silencia qualquer exceção, dificulta debug |
| 3.7 | 🟡 MEDIUM | Duplicação de lógica | `task_routes.py:30-80` | Cálculo de "overdue" repetido |
| 3.8 | 🟡 MEDIUM | DEBUG ativo | `app.py:34` | Mesma classe de risco do projeto 1 |
| 3.9 | 🟡 MEDIUM | Estado global em service | `notification_service.py:6` | Lista de notificações compartilhada entre instâncias |
| 3.10 | 🔵 LOW | Ternário desnecessário | `user.py:34-38` | `if/else` que poderia ser `return <condição>` |

**Total documentado manualmente: 44 problemas** — mínimo de 5 por projeto (com pelo menos 1 CRITICAL/HIGH e 2 MEDIUM/LOW cada) confirmado nos 3.

**Padrões recorrentes entre os 3 projetos:** hardcoded secrets, senha sem hash adequado, God Class/Module, N+1 queries, estado global mutável — foi esse conjunto que orientou o catálogo inicial da skill.

---

## B) Construção da Skill

### Decisões de design

A skill (`refactor-arch`) foi estruturada em **5 arquivos de referência**, cada um cobrindo exatamente uma das áreas de conhecimento obrigatórias, para manter o `SKILL.md` como um "roteiro executável" curto em vez de um documento monolítico:

| Arquivo | Área de conhecimento |
|---|---|
| `project-analysis.md` | Heurísticas de detecção de linguagem/framework/banco/arquitetura |
| `anti-patterns-catalog.md` | Catálogo de anti-patterns com sinais de detecção e severidade |
| `audit-report-template.md` | Formato padronizado do relatório da Fase 2 |
| `architecture-guidelines.md` | Regras do MVC alvo (responsabilidade de cada camada) |
| `refactoring-playbook.md` | Padrões de transformação com código antes/depois |
| `mvc-refactoring-guide.md` | Guia passo-a-passo específico para decompor uma God Class em MVC |

O `SKILL.md` define 3 fases sequenciais (Análise → Auditoria → Refatoração), cada uma apontando para os arquivos de referência relevantes, e a Fase 2 sempre pausa e pede confirmação explícita (`y`/`n`) antes de qualquer modificação.

### Catálogo de anti-patterns: o que foi incluído e por quê

O catálogo cresceu de **2 padrões** (v1.0, focado só em SQL Injection e secrets, para validar o esqueleto da skill) para **19 padrões** (v3.1), distribuídos assim:

| Severidade | Padrões |
|---|---|
| CRITICAL | SQL Injection, Hardcoded Secrets, Senhas em Texto Plano/Expostas, Dangerous Admin Endpoint, Broken Access Control, Privilege Escalation via Autorização Insuficiente |
| HIGH | Weak Password Hashing, God Classes, N+1 Queries, Global State Mutável, Regressão de Refatoração |
| MEDIUM | Code Duplication, Secrets em Responses, Logs Sensíveis, Exception Detail Leakage |
| LOW | Magic Strings, Ternários Desnecessários, Monolithic Architecture, Configuração Morta |

Cada padrão novo entrou **por causa de um achado real** que a versão anterior da skill deixou passar — não por completude teórica. Alguns exemplos:

- **Dangerous Admin Endpoint** e **Broken Access Control** (v2.2): a auditoria original não tinha detecção para o `POST /admin/query` do projeto 1 (executa SQL arbitrário) nem para rotas administrativas sem autenticação — apareciam nos projetos, mas a skill nunca reportava.
- **Regressão de Refatoração** (v2.2): ao refatorar uma conexão global para Singleton no projeto 1, o próprio refactor introduziu um bug (setup de schema rodando em toda request, não só uma vez) — isso motivou uma checklist de regressão obrigatória na Fase 3.
- **Privilege Escalation via Autorização Insuficiente** (v3.1): a mais recente. Uma reauditoria do projeto 3, já com todas as rotas sensíveis protegidas por `@login_required`, testou a lógica de autorização *dentro* dos controllers e encontrou que qualquer usuário comum conseguia se autopromover a admin via `PUT /users/:id` — porque presença do decorator não é o mesmo que autorização correta. Esse achado só é detectável testando funcionalmente, não relendo código, e por isso motivou uma mudança de processo (ver "Self-Verification Loop" abaixo), não só uma entrada no catálogo.

### Como a skill se tornou agnóstica de tecnologia

Três decisões deliberadas:

1. **Detecção por padrão estrutural, não por sintaxe de uma linguagem específica.** "Query dentro de loop" (N+1), "atribuição literal de valor parecido com secret" (hardcoded secrets), "if/else retornando True/False" (ternário desnecessário) são descritos de forma que se aplicam igualmente a `for t in tasks: User.query.get(...)` (Python) e a `courses.forEach(c => { this.db.all(...) })` (JavaScript).
2. **Catálogo e template de relatório em um arquivo; exemplos de código em outro.** `refactoring-playbook.md` sempre traz o antes/depois em pelo menos 2 linguagens quando o padrão se aplica a ambas (ex: parameterized queries em SQLite/Python e em SQLite/Node), para a skill nunca ficar "cega" para uma stack.
3. **Validação empírica nos 3 projetos, não só teórica.** A skill só foi considerada "pronta" numa versão depois de rodar de fato nos 3 — Python/Flask monolítico, Node.js/Express com callback hell, e Python/Flask parcialmente organizado. As diferenças de arquitetura entre eles forçaram a Fase 3 a ser adaptativa (ver `mvc-refactoring-guide.md`), em vez de assumir sempre "4 arquivos → MVC".

### Desafios encontrados e como foram resolvidos

| Desafio | Como foi resolvido |
|---|---|
| Fase 3 tratando só os achados "principais" e ignorando os demais silenciosamente (v2.0/v2.1) | v2.2 tornou a Fase 3 sistemática: todo achado da checklist termina em `✅ Corrigido`, `⏭️ Adiado (com justificativa)` ou `❌ Não aplicável` — nunca fica sem status |
| A skill declarava sucesso confiando no próprio log de refatoração, mas relatórios de reauditoria seguidos encontravam problemas que o log não cobria | v3.0 adicionou o **Self-Verification Loop**: ao final da Fase 3, a skill relê o código do zero e reaplica a Fase 2, gerando um novo relatório. Se 0 achados, encerra; se houver achados, **pergunta ao usuário** se deve continuar corrigindo (nunca decide isso por conta própria), com limite de 3 ciclos |
| Mesmo com o loop de v3.0, uma checagem só estrutural ("a rota tem o decorator de auth?") não pega falhas de autorização granular (ex: qualquer usuário logado podendo alterar o `role` de outro) | v3.1 tornou o self-verification também **funcional**: para todo endpoint de escrita com campos sensíveis, a skill agora simula requisições reais com um usuário de baixo privilégio e confirma que a escalação de privilégio falha |
| Provar que a skill não é o único ambiente onde ela funciona | Skill copiada e testada em `.claude/skills/refactor-arch/` dentro dos 3 projetos individualmente (além da cópia central usada durante o desenvolvimento) |

---

## C) Resultados

### Resumo dos relatórios de auditoria (Fase 2) por projeto

Relatórios completos entregues em `reports/audit-project-{1,2,3}.md` (mapeados abaixo para os relatórios com timestamp originais em `reports/`, preservados como histórico).

| Projeto | Relatório (Fase 2, pré-refactor) | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | `audit-project-1.md` | 3 | 3 | 3 | 1 | **14** |
| 2 — ecommerce-api-legacy | `audit-project-2.md` | 2 | 4 | 1 | 2 | **9** |
| 3 — task-manager-api | `audit-project-3.md` | 3 | 3 | 2 | 2 | **10** |

Os 3 relatórios batem com (e superam) o mínimo de 5 findings e pelo menos 1 CRITICAL/HIGH exigido pelos critérios de aceite.

### Comparação antes/depois da estrutura

| Projeto | Antes | Depois |
|---|---|---|
| **1 — code-smells-project** | 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), monolítico, sem `config` | 17 arquivos em MVC: `app.py` (entry point), `config.py`, `database.py` (Singleton), `auth.py` (decorators `login_required`/`role_required`/`owner_or_role_required`, adicionado na correção v3.1 de broken access control), `models/{produto,usuario,pedido}.py`, `controllers/{produto,usuario,pedido}_controller.py`, `routes/{produto,usuario,pedido,health}_routes.py` |
| **2 — ecommerce-api-legacy** | 3 arquivos (`app.js`, `AppManager.js` — 142 linhas de God Class, `utils.js`), callback hell | 17 arquivos em MVC: `app.js`, `config.js`, `database.js` (Promise wrapper), `middleware/auth.js`, `models/{course,user,enrollment,payment,auditLog,report}.js`, `controllers/{checkout,report,user}Controller.js`, `routes/{checkout,report,user}Routes.js`, `utils/mask.js` |
| **3 — task-manager-api** | 15 arquivos parcialmente organizados (`models/`, `routes/` já existiam, mas sem `controllers/`; toda validação/lógica de negócio direto nas rotas) | 27 arquivos com camada de controllers adicionada, autenticação real (token assinado + `login_required`/`role_required`), N+1 eliminado, e um bug de autorização granular corrigido: `auth/tokens.py`, `middleware/auth.py`, `controllers/{auth,task,user,category,report}_controller.py`, `routes/category_routes.py` (nova, separada de `report_routes.py`) |

### Checklist de Validação (preenchido para os 3 projetos)

```markdown
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python nos projetos 1/3, Node.js no projeto 2)
- [x] Framework detectado corretamente (Flask nos projetos 1/3, Express no projeto 2)
- [x] Domínio da aplicação descrito corretamente (E-commerce, LMS/Checkout, Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (4, 3 e 15 arquivos, respectivamente)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido em audit-report-template.md
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (14, 9 e 10 nos 3 projetos)
- [x] Detecção de APIs deprecated incluída (avaliado — nenhuma ocorrência real nos 3 projetos, catálogo cobre o padrão)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (config/models/routes/controllers) nos 3 projetos
- [x] Configuração extraída para módulo de config, sem hardcoded (config.py / config.js + .env)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado (mensagens genéricas ao cliente, detalhe só em log interno)
- [x] Entry point claro (app.py / app.js reduzidos a composição)
- [x] Aplicação inicia sem erros nos 3 projetos
- [x] Endpoints originais respondem corretamente (validado com Flask test client / supertest / servidor real)
```

### Evidência de execução (logs reais, pós-refatoração)

**Projeto 1 — code-smells-project:**
```
GET /health -> 200 {'counts': {'pedidos': 0, 'produtos': 10, 'usuarios': 3}, 'database': 'connected', 'status': 'ok', 'versao': '1.0.0'}
GET /produtos -> 200 (10 produtos)
POST /admin/query (endpoint removido na refatoração) -> 404
```

**Projeto 2 — ecommerce-api-legacy** (servidor real na porta 5099):
```
$ curl -X POST /api/checkout -d '{"usr":"Demo","eml":"demo@x.com","c_id":1,"card":"4111111111111111"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl /api/admin/financial-report -H "X-Admin-Token: ***"
[{"course":"Clean Architecture","revenue":1994,"students":[...]}, {"course":"Docker","revenue":0,"students":[]}]

# log interno do servidor:
Processando cartão 4111********1111 na chave ***    ← número mascarado, chave nunca impressa
```

**Projeto 3 — task-manager-api:**
```
POST /login -> 200 {'role': 'admin', 'name': 'João Silva', ...}   ← sem campo "password" na resposta
GET /tasks (com token) -> 200 (10 tasks)
POST /users {"role": "admin", ...} (cadastro público) -> 201, role retornado: 'user'   ← escalação de privilégio bloqueada
```

### Observações sobre o comportamento da skill em stacks diferentes

- **Python/Flask (projetos 1 e 3):** a skill lidou bem tanto com o monolito completo (projeto 1, 4 arquivos) quanto com a estrutura parcial (projeto 3, já com `models/`/`routes/`), mas precisou de instruções específicas na Fase 3 para não assumir "sempre criar do zero" — no projeto 3 a tarefa foi inserir uma camada de `controllers/` que não existia, preservando o que já estava organizado.
- **Node.js/Express (projeto 2):** os mesmos anti-patterns (SQL injection, secrets, N+1) precisaram de refatorações com sintaxe/idioma diferente (Promises em vez de exceções Python, `LEFT JOIN` via query builder em vez de SQLAlchemy `joinedload`), mas a **lógica de detecção e a estrutura MVC alvo foram as mesmas** — confirmando o agnosticismo pretendido.
- **Achado mais valioso do processo:** o Self-Verification Loop (v3.0/v3.1) encontrou, ele mesmo, achados que a primeira versão da Fase 3 tinha deixado passar em todos os 3 projetos — uma regressão de performance introduzida pelo próprio refactor (projeto 1), um N+1 residual fora do escopo original (projeto 1), configuração morta copiada do código legado (projeto 2) e uma falha de escalação de privilégio (projeto 3). Isso indicou que "a skill terminou de refatorar" não é o mesmo que "a skill confirmou que o resultado está correto" — e motivou tornar a reauditoria uma etapa obrigatória, não um passo opcional.

### Confirmação Final (Reauditoria Completa Pós-v3.1)

Além do Self-Verification Loop embutido na Fase 3 (que já fechou em 0 achados ao final de cada refatoração), os 3 projetos foram submetidos a uma **reauditoria completa e independente**, com a skill `/refactor-arch` reinvocada do zero — relendo todo o código-fonte sem confiar em nenhum log de rodada anterior — contra os 19 anti-patterns do catálogo v3.1 e o teste funcional obrigatório de autorização (Padrão 19):

| Projeto | Relatório final | CRITICAL | HIGH | MEDIUM | LOW | Teste funcional de autorização |
|---|---|---|---|---|---|---|
| 1 — code-smells-project | `audit-code-smells-project-2026-09-20T16-00-05.md` | 0 | 0 | 0 | 0 | 29 asserções simuladas (anônimo/cliente/admin) — 29 PASS |
| 2 — ecommerce-api-legacy | `audit-ecommerce-api-legacy-2026-09-20T19-03-12.md` | 0 | 0 | 0 | 0 | 6 asserções (incl. injeção de `role`/`is_admin`/`price` no payload) — 6 PASS |
| 3 — task-manager-api | `audit-task-manager-api-2026-09-20T18-57-12.md` | 0 | 0 | 0 | 0 | 7 asserções (auto-promoção, edição de outro usuário, rotas admin-only) — 7 PASS |

Nenhum dos 3 relatórios finais encontrou achado novo ou regressão. O relatório do projeto 3 registra ainda uma nota informativa (não classificada como achado): `TaskController` permite editar/excluir tasks de outro usuário sem checagem de propriedade — mantido de propósito, pois o domínio é um quadro de tarefas compartilhado (não há regra de "só posso editar minhas próprias tasks" no seed/README do projeto), diferente de `User`, que é sempre pessoal. Fica sinalizado para uma decisão de produto futura, não como bug.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e configurado
- Python 3.9+ com `pip` (projetos 1 e 3) — dependências em `requirements.txt` de cada projeto
- Node.js 18+ com `npm` (projeto 2) — dependências em `package.json`

### Executar a skill em cada projeto

A skill já está copiada dentro de cada projeto em `<projeto>/.claude/skills/refactor-arch/`.

```bash
# Projeto 1 — code-smells-project
cd code-smells-project
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy
cd ../ecommerce-api-legacy
npm install
claude "/refactor-arch"

# Projeto 3 — task-manager-api
cd ../task-manager-api
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
claude "/refactor-arch"
```

Em cada execução: a skill imprime a Fase 1 (stack detectada), a Fase 2 (relatório de achados) e pausa pedindo confirmação (`y`/`n`) antes da Fase 3. Ao final da Fase 3, ela roda o Self-Verification Loop automaticamente — se encontrar algo, pergunta se deve continuar corrigindo.

### Como validar que a refatoração funcionou

```bash
# Python (projetos 1 e 3) — dentro do venv do projeto
python3 -c "
from app import app
c = app.test_client()
print(c.get('/health').status_code, c.get('/health').get_json())
"

# Node.js (projeto 2)
node -e "
const bcrypt = require('bcrypt');
const { initDb } = require('./src/database');
const { app } = require('./src/app');
initDb(bcrypt).then(() => app.listen(3000, () => console.log('rodando em :3000')));
"
```

Ou, para subir o servidor real e testar manualmente:

```bash
# Projeto 1
python3 app.py                      # http://localhost:5000

# Projeto 2
node src/app.js                     # http://localhost:3000 (ou PORT do .env)

# Projeto 3
python3 app.py                      # http://localhost:5001
```

Cada projeto tem seu próprio `.env` (criado durante a refatoração, fora do controle de versão) com os valores necessários — ver `.env.example` implícito nos respectivos `config.py`/`config.js` para a lista de variáveis esperadas.

---

## Estrutura do Repositório

```
.
├── README.md                              # este arquivo
├── README_enunciado.md                    # enunciado original do desafio
├── analises/                               # análise manual, logs de refatoração, comparativos de versão da skill
├── reports/                                # relatórios de auditoria (Fase 2) de todas as execuções, incluindo audit-project-{1,2,3}.md
├── .claude/skills/refactor-arch/           # skill (versão de referência/desenvolvimento)
├── code-smells-project/                    # Projeto 1 (Python/Flask) — refatorado + skill copiada em .claude/skills/
├── ecommerce-api-legacy/                   # Projeto 2 (Node.js/Express) — refatorado + skill copiada em .claude/skills/
└── task-manager-api/                       # Projeto 3 (Python/Flask) — refatorado + skill copiada em .claude/skills/
```
