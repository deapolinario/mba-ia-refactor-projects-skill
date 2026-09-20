# Log de Refatoração: code-smells-project
**Data:** 2026-09-20
**Skill:** refactor-arch v2.2
**Fase 3:** Refactoring & Validation (completa/sistemática)

---

## Contexto

A Fase 3 v2.1 (`REFACTORING_LOG_v2_1.md`) tratou apenas 5 dos 14 achados originais, de forma seletiva. Esta rodada (v2.2) trata **todos os achados pendentes**, mais 5 achados novos que a auditoria v2.1 nunca detectou, descobertos em revisão manual do código pós-refactoring.

---

## Findings Checklist (completa)

| # | Achado | Severidade | Status v2.1 | Status v2.2 |
|---|--------|-----------|--------------|--------------|
| 1 | SQL Injection (15+ queries) | CRITICAL | ✅ Corrigido | ✅ Mantido |
| 2 | Hardcoded Secrets | CRITICAL | ✅ Corrigido | ✅ Mantido |
| 3 | Secrets em Responses | CRITICAL/MEDIUM | ✅ Corrigido | ✅ Mantido |
| 4 | **Senhas em texto plano** | CRITICAL | ❌ Não tratado | ✅ **Corrigido agora** |
| 5 | **Dangerous admin endpoint (`/admin/query`)** | CRITICAL | ❌ Nunca detectado | ✅ **Removido** |
| 6 | **Broken access control (`/admin/*`)** | CRITICAL | ❌ Nunca detectado | ✅ **Corrigido (auth guard)** |
| 7 | Global State Mutável | HIGH | ✅ Corrigido | ✅ Mantido |
| 8 | **Regressão: setup rodando por-request** | HIGH | ❌ Introduzido pela própria v2.1 | ✅ **Corrigido** |
| 9 | God Class (`models.py`/`controllers.py`) | HIGH | ⏭️ Adiado | ✅ **Corrigido (MVC completo)** |
| 10 | N+1 Queries (pedidos) | HIGH | ⏭️ Adiado | ✅ **Corrigido (JOIN único)** |
| 11 | Logs Sensíveis (PII) | MEDIUM | ⚠️ Parcial (2/9 locais) | ✅ **Completo (9/9 locais)** |
| 12 | **Exception Detail Leakage (`str(e)`)** | MEDIUM | ❌ Nunca detectado | ✅ **Corrigido (~15 handlers)** |
| 13 | Code Duplication (lógica de pedido) | MEDIUM | ⏭️ Adiado | ✅ **Corrigido (helper único)** |
| 14 | Magic Strings (categorias/status) | LOW | ⏭️ Adiado | ✅ **Corrigido (Config)** |
| 15 | **Config morta (`Config.DEBUG` não aplicado)** | LOW | ❌ Nunca detectado | ✅ **Corrigido** |

**Resultado:** 15/15 achados com status `✅ Corrigido`. Zero itens adiados nesta rodada.

---

## Detalhamento das Correções Novas (v2.2)

### CRITICAL 4: Senhas em Texto Plano

**Arquivos:** `database.py`, `models/usuario.py`

- Seed do banco agora grava senhas com `generate_password_hash(..., method='pbkdf2:sha256')`
- `criar_usuario()` faz hash antes de persistir
- `login_usuario()` usa `check_password_hash()` em vez de comparar direto no SQL
- `get_todos_usuarios()`/`get_usuario_por_id()` fazem `SELECT id, nome, email, tipo, criado_em` — a coluna `senha` nunca sai do banco em queries usadas por responses

### CRITICAL 5+6: Dangerous Endpoint + Broken Access Control

**Arquivo:** `app.py`

- `/admin/query` (executava SQL arbitrário do body) foi **removido** por completo
- `/admin/reset-db` recebeu decorator `@admin_required`, que exige header `X-Admin-Token` correspondente a `ADMIN_TOKEN` (env var)

### HIGH 8: Regressão de Inicialização Por-Request

**Arquivo:** `database.py`

- `CREATE TABLE`/seed movidos do corpo de `get_db()` para `DatabaseManager.__init__` (`_setup_schema` + `_seed_if_empty`), guardado por `_initialized`
- `get_db()` agora só retorna a conexão, sem side-effects
- Validado com teste automatizado: 10 requests → `_setup_schema`/`_seed_if_empty` chamados **1x** cada (antes: 1x por request)

### HIGH 9 + 10 + MEDIUM 13: God Class, N+1 e Duplicação (MVC completo)

**Arquivos novos:** `models/produto.py`, `models/usuario.py`, `models/pedido.py`, `controllers/produto_controller.py`, `controllers/usuario_controller.py`, `controllers/pedido_controller.py`, `routes/produto_routes.py`, `routes/usuario_routes.py`, `routes/pedido_routes.py`, `routes/health_routes.py`
**Removidos:** `models.py`, `controllers.py` (320 + 294 linhas → 10 arquivos de responsabilidade única)

- Seguiu `mvc-refactoring-guide.md` passo a passo
- `get_pedidos_usuario`/`get_todos_pedidos`: de N+1 (1 query de itens + 1 query de produto por item) para **1 única query com LEFT JOIN**, agrupada em Python via `_agrupar_pedidos_com_itens()` — essa função também elimina a duplicação que existia entre as duas funções antigas
- `relatorio_vendas()`: de 5 queries sequenciais para **1 query agregada** (`COUNT`/`SUM`/`CASE WHEN`)
- Serialização de produto/usuário centralizada em `_row_to_dict()` por model (elimina duplicação que existia em 3 funções de produto)

### MEDIUM 11: Logs Sensíveis (completar migração)

**Arquivos:** todos os controllers/routes

- Os `print()` remanescentes (`listar_produtos`, `criar_produto`, `deletar_produto`, `criar_pedido` except, `reset_database`) foram migrados para `logger`
- `mask_email()` preservado e usado no fluxo de login

### MEDIUM 12: Exception Detail Leakage

**Arquivos:** todos os controllers/routes

- Todo `except Exception as e: return jsonify({"erro": str(e)}), 500` passou a ser `logger.error(...)` + `return jsonify({"erro": "Erro interno do servidor"}), 500`
- Erros de validação (`ValueError`) continuam retornando mensagem específica (são seguros, não vazam detalhes internos) com status 400/404 conforme o caso

### LOW 14: Magic Strings

**Arquivo:** `config.py`

- `Config.VALID_CATEGORIES` e `Config.VALID_ORDER_STATUSES` centralizam as listas antes hardcoded em `controllers.py`

### LOW 15: Configuração Morta

**Arquivo:** `app.py`

- `app.run(debug=True)` → `app.run(debug=Config.DEBUG)`

---

## Checklist de Regressão (v2.2)

| Item | Resultado |
|------|-----------|
| Setup/seed roda uma única vez (não por request) | ✅ Validado com teste automatizado (1x em 10 requests) |
| Nenhum N+1 novo introduzido | ✅ `pedido.py` usa 1 query com JOIN; `criar_pedido` usa cache local em memória para evitar re-consultar produto já lido |
| Nenhuma config nova é dead code | ✅ `Config.DEBUG`, `Config.VALID_CATEGORIES`, `Config.VALID_ORDER_STATUSES` todos referenciados em pelo menos 1 ponto de uso |
| Nenhum literal antigo sobrou coexistindo com a config | ✅ `grep` confirmou zero ocorrências de `debug=True` hardcoded, zero listas de categoria/status duplicadas fora de `config.py` |

---

## Validação Funcional (end-to-end, não só sintaxe)

Testado com Flask test client contra app real (venv com `flask==3.1.1`):

| Teste | Resultado |
|-------|-----------|
| `GET /health` sem secrets na response | ✅ 200, sem `secret_key`/`debug`/`db_path` |
| `GET /produtos` | ✅ 200, 10 produtos |
| `POST /produtos` válido | ✅ 201 |
| `POST /produtos` categoria inválida (via `Config.VALID_CATEGORIES`) | ✅ 400 |
| `POST /usuarios` | ✅ 201 |
| `GET /usuarios` sem campo `senha` | ✅ 200, confirmado ausência do campo |
| `POST /login` com senha correta (hash) | ✅ 200 |
| `POST /login` com senha errada | ✅ 401, sem detalhes internos |
| `POST /pedidos` (exercita JOIN + decremento de estoque) | ✅ 201 |
| `GET /relatorios/vendas` (query agregada) | ✅ 200 |
| `POST /admin/query` | ✅ 404 (rota não existe mais) |
| `POST /admin/reset-db` sem token | ✅ 401 |
| `POST /admin/reset-db` com token correto | ✅ 200 |

Também validado manualmente com servidor real na porta 5001 (`curl /health`, `curl /produtos`).

---

## Estrutura Final

```
code-smells-project/
├── .env, .gitignore
├── app.py                        # entry point limpo (39 linhas de rotas raiz + blueprints)
├── config.py                     # secrets + domínio (categorias, status)
├── database.py                   # Singleton, setup 1x
├── models/
│   ├── produto.py
│   ├── usuario.py
│   └── pedido.py                 # elimina N+1 via JOIN
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── routes/
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   └── health_routes.py
├── REFACTORING_LOG_v2_1.md        # histórico da primeira rodada
└── REFACTORING_LOG_v2_2.md        # este documento
```

`models.py` e `controllers.py` (God Classes originais) foram removidos.
