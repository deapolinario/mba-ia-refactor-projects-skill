# Log de Refatoração: code-smells-project
**Data:** 2026-09-20
**Skill:** refactor-arch v3.1
**Fase 3:** Refactoring, Validation & Self-Verification

---

## Contexto

As rodadas v2.1/v2.2 fecharam o catálogo antigo de 18 anti-patterns com 0 achados, mas nenhuma delas testava autorização **funcionalmente** — apenas verificavam presença de decorators/guards via releitura estrutural. A auditoria v3.1 (`../reports/audit-code-smells-project-2026-09-20T17-05-29.md`) rodou requisições reais sem autenticação contra a aplicação e confirmou 2 achados CRITICAL que a releitura estrutural nunca teria pego: o projeto não tinha **nenhum** mecanismo de sessão/autenticação para usuários comuns — `POST /login` validava credenciais mas não emitia sessão, e nenhuma rota fora de `/admin/*` verificava login.

---

## Findings Checklist (completa)

| # | Achado | Severidade | Status |
|---|--------|-----------|--------|
| 1 | Broken Access Control — escrita (`POST/PUT/DELETE /produtos`, `PUT /pedidos/<id>/status`) sem qualquer autenticação | CRITICAL | ✅ Corrigido |
| 2 | Broken Access Control / IDOR — leitura (`GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `GET /relatorios/vendas`) sem autenticação/ownership check | CRITICAL | ✅ Corrigido |
| 3 | `ADMIN_TOKEN` lido via `os.getenv` direto em `app.py`, fora do `Config` e não documentado em `.env` | LOW | ✅ Corrigido |

**Resultado:** 3/3 achados com status `✅ Corrigido`. Zero itens adiados.

---

## Detalhamento das Correções

### CRITICAL 1+2: Autenticação e Autorização

**Arquivo novo:** `auth.py`

- Introduzido mecanismo de sessão (cookie assinado com `Config.SECRET_KEY`, via `flask.session`) — `POST /login` agora grava `session["usuario_id"]` e `session["tipo"]` após validar credenciais.
- Três decorators reutilizáveis em `auth.py`:
  - `login_required` — exige sessão autenticada (qualquer `tipo`).
  - `role_required(role)` — exige sessão autenticada com `tipo` específico (usado para operações admin-only).
  - `owner_or_role_required(param_name, role)` — permite acesso se o requester for o dono do recurso (compara `session["usuario_id"]` com o parâmetro de rota) OU tiver o `role` informado.
- Decorators aplicados:
  - `routes/produto_routes.py`: `POST/PUT/DELETE /produtos` → `@role_required('admin')`. Leitura (`GET /produtos*`) permanece pública (catálogo de e-commerce).
  - `routes/usuario_routes.py`: `GET /usuarios` → `@role_required('admin')`; `GET /usuarios/<id>` → `@owner_or_role_required('id', 'admin')`. `POST /usuarios` (cadastro) e `POST /login` permanecem públicos.
  - `routes/pedido_routes.py`: `POST /pedidos` → `@login_required`, com `usuario_id` **forçado a partir da sessão** (`dados["usuario_id"] = session["usuario_id"]`) — o valor vindo do payload é sempre ignorado, prevenindo criação de pedidos em nome de outro usuário. `GET /pedidos`, `PUT /pedidos/<id>/status` e `GET /relatorios/vendas` → `@role_required('admin')`. `GET /pedidos/usuario/<usuario_id>` → `@owner_or_role_required('usuario_id', 'admin')`.
- Cadastro público (`POST /usuarios`) já forçava `tipo="cliente"` no model (`models/usuario.py`), independente do payload — confirmado com teste funcional que envio de `"tipo": "admin"` no payload não tem efeito algum.

### LOW 3: Configuração do Admin Token

**Arquivos:** `config.py`, `app.py`, `.env`

- `ADMIN_TOKEN` movido para `Config.ADMIN_TOKEN` (era `os.getenv("ADMIN_TOKEN")` direto em `app.py`).
- `.env` passou a documentar a variável com um valor de dev (`admin-dev-token-MUDE-EM-PROD`).
- Import de `os` removido de `app.py` por ficar sem uso após a mudança.

---

## Checklist de Regressão

| Item | Resultado |
|------|-----------|
| Setup/seed roda uma única vez | ✅ `database.py` não foi tocado nesta rodada |
| Nenhum N+1 novo introduzido | ✅ Nenhuma query nova em loop |
| Config nova (`Config.ADMIN_TOKEN`) tem ponto de uso real | ✅ `app.py:33` |
| Nenhum literal antigo sobrou | ✅ `os.getenv("ADMIN_TOKEN")` direto removido |

---

## Validação Funcional (Flask test client, sem mocks)

| Teste | Resultado |
|-------|-----------|
| Anônimo tenta `PUT /produtos/1` (tamper de preço) | ✅ 401, preço não muda |
| Anônimo tenta `GET /usuarios` (enumeração) | ✅ 401 |
| Anônimo lê catálogo (`GET /produtos*`) | ✅ 200 (continua público) |
| Anônimo se cadastra com `"tipo": "admin"` no payload | ✅ 201, usuário criado como `cliente` |
| Cliente autenticado acessa o próprio perfil/pedidos | ✅ 200 |
| Cliente autenticado tenta acessar perfil/pedidos de outro usuário | ✅ 403 |
| Cliente autenticado tenta rotas admin-only (listar usuários/pedidos, CRUD produtos, status de pedido, relatório) | ✅ 403 em todas |
| Cliente autenticado cria pedido com `usuario_id` forjado no payload | ✅ 201, pedido gravado com o `usuario_id` real da sessão |
| Admin autenticado acessa todas as rotas acima | ✅ 200/201 em todas |
| `/admin/reset-db` continua exigindo `X-Admin-Token` (via `Config.ADMIN_TOKEN`) | ✅ 401 sem token |
| `python -m py_compile` em todos os arquivos alterados/novos | ✅ Sem erros |

Banco de dados de teste (`loja.db`, git-ignored) resetado ao estado seed original após os testes — sem side-effects deixados.

---

## Self-Verification

Ver `../reports/audit-code-smells-project-2026-09-20T17-11-08.md` — releitura completa dos 18 arquivos `.py`, reaplicação dos 19 anti-patterns + reteste funcional de autorização. **0 achados.** Ciclo único, sem necessidade de correções adicionais.

---

## Estrutura Final (mudanças desta rodada)

```
code-smells-project/
├── auth.py                        # NOVO — login_required, role_required, owner_or_role_required
├── app.py                         # admin_required agora usa Config.ADMIN_TOKEN; import os removido
├── config.py                      # + Config.ADMIN_TOKEN
├── .env                           # + ADMIN_TOKEN documentado
├── routes/
│   ├── produto_routes.py          # writes protegidos por @role_required('admin')
│   ├── usuario_routes.py          # login emite sessão; listagem/detalhe protegidos
│   └── pedido_routes.py           # criação exige login + usuario_id forçado da sessão;
│                                   # listagem/status/relatório protegidos por admin/ownership
└── REFACTORING_LOG_v3_1.md        # este documento
```
