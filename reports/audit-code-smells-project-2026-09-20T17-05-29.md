# Auditoria: code-smells-project
**Versão da Skill:** 3.1
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T17-05-29
**Contexto:** Primeira auditoria deste projeto contra o catálogo v3.1 (19 padrões). Auditorias anteriores (até `audit-code-smells-project-2026-09-20T10-19-40.md`, skill v2.2) haviam fechado os 18 padrões daquele catálogo com 0 achados, mas eram baseadas em releitura estrutural — nenhuma delas testou autorização **funcionalmente**. Esta rodada roda o Padrão 19 (Privilege Escalation) com requisições reais via Flask test client, não apenas grep por decorators.

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Python 3.9
Framework:      Flask 3.1.1 (+ flask-cors)
Database:       SQLite (loja.db)
Domain:         E-commerce API (produtos, usuários, pedidos/carrinho, relatório de vendas)
Architecture:   Structured (MVC: config/, models/, routes/, controllers/, app.py)
Source files:   16 files analyzed
DB tables:      4 (produtos, usuarios, pedidos, itens_pedido)
```

---

## PHASE 2: ARCHITECTURE AUDIT — 19 anti-patterns (catálogo v3.1)

| # | Anti-pattern | Severidade | Resultado |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Nenhum achado — todas as queries usam placeholders `?` |
| 2 | Hardcoded Secrets | CRITICAL | ✅ Nenhum achado — `SECRET_KEY`/`DATABASE_PATH` via `os.getenv` |
| 3 | Senhas em Texto Plano | CRITICAL | ✅ Nenhum achado — hash pbkdf2:sha256, `senha` nunca sai em SELECT de response |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Nenhum achado — `/admin/query` continua removido |
| 5 | Broken Access Control (rotas admin) | CRITICAL | ✅ Nenhum achado — `/admin/reset-db` com `@admin_required` |
| 6 | **Privilege Escalation / Autorização Insuficiente** | **CRITICAL** | ❌ **2 achados novos** (ver abaixo) |
| 7 | Weak Password Hashing | HIGH | ✅ Nenhum achado |
| 8 | God Classes | HIGH | ✅ Nenhum achado (maior arquivo: 153 linhas) |
| 9 | N+1 Queries | HIGH | ✅ Nenhum achado — JOIN único em pedidos, `IN()` único em `criar_pedido` |
| 10 | Global State Mutável | HIGH | ✅ Nenhum achado — Singleton thread-safe, setup 1x |
| 11 | Code Duplication | MEDIUM | ✅ Nenhum achado |
| 12 | Secrets Expostas em Responses | MEDIUM | ✅ Nenhum achado |
| 13 | Logs Sensíveis (PII) | MEDIUM | ✅ Nenhum achado — `mask_email()` usado no login |
| 14 | Exception Detail Leakage | MEDIUM | ✅ Nenhum achado — todo `except Exception` retorna mensagem genérica |
| 15 | Magic Strings / Magic Numbers | LOW | ✅ Nenhum achado |
| 16 | Ternários Desnecessários | LOW | ✅ Nenhum achado |
| 17 | Monolithic Architecture | LOW/CRITICAL | ✅ Nenhum achado (MVC completo) |
| 18 | Regressão: setup por-request | HIGH | ✅ Nenhum achado |
| 19 | Configuração Morta | LOW | ❌ **1 achado novo** (ver abaixo) |

---

## Achados Detalhados

### CRITICAL-1: Broken Access Control — endpoints de escrita sensíveis sem qualquer autenticação

**Arquivos:** `routes/produto_routes.py:45-83`, `routes/pedido_routes.py:46-56`

O app não possui **nenhum mecanismo de sessão/token** para usuários comuns. `POST /login` (`routes/usuario_routes.py:44-56`) valida credenciais e retorna os dados do usuário, mas não emite nenhum token/cookie de sessão — e nenhuma rota depois disso verifica login. O único guard de autorização existente no projeto inteiro é `admin_required` em `app.py`, aplicado a uma única rota (`/admin/reset-db`).

Como resultado, qualquer requisição anônima pode:

```python
# routes/produto_routes.py:59-70
@produto_bp.route('/produtos/<int:id>', methods=['PUT'])
def atualizar_produto(id):
    try:
        dados = request.get_json()
        ProdutoController.atualizar(id, dados)   # sem checagem de auth/role
        ...

# routes/produto_routes.py:73-83
@produto_bp.route('/produtos/<int:id>', methods=['DELETE'])
def deletar_produto(id):
    ...
    ProdutoController.deletar(id)   # sem checagem de auth/role

# routes/pedido_routes.py:46-56
@pedido_bp.route('/pedidos/<int:pedido_id>/status', methods=['PUT'])
def atualizar_status_pedido(pedido_id):
    ...
    PedidoController.atualizar_status(pedido_id, dados.get("status", ""))  # sem checagem de auth/role
```

**Confirmado funcionalmente** (Flask test client, sem headers de autenticação, teste revertido logo em seguida — `loja.db` é git-ignored e não faz parte do repositório):

```
PUT /produtos/1  {"nome": "Notebook Gamer", "preco": 0.01, "estoque": 10, "categoria": "informatica"}
  -> 200 {"sucesso": true, "mensagem": "Produto atualizado"}
GET /produtos/1
  -> preco: 0.01   (era 5999.99)
```

**Impacto:** qualquer cliente não autenticado pode alterar preço/estoque/categoria de qualquer produto, deletar produtos do catálogo, criar produtos arbitrários, e aprovar/cancelar/alterar o status de qualquer pedido de qualquer usuário. Isso é mass assignment total de campos sensíveis (`preco`, `estoque`, `status`) — a versão mais severa do Padrão 19, sem sequer a camada estrutural (decorator) que o task-manager-api tinha.

**Refatoração proposta:**
- Introduzir emissão de sessão/token no `POST /login` (ex: JWT ou `flask session`) contendo `usuario_id` + `tipo`.
- Criar decorators `login_required` e `role_required("admin")` (mesmo padrão de `admin_required` já existente em `app.py`, mas reaproveitável).
- Aplicar `role_required("admin")` em `POST/PUT/DELETE /produtos` e em `PUT /pedidos/<id>/status` — mutações de catálogo e aprovação de pedido são operações administrativas neste domínio.

---

### CRITICAL-2: Broken Access Control / IDOR — exposição de dados de outros usuários sem autenticação ou checagem de ownership

**Arquivos:** `routes/usuario_routes.py:9-28`, `routes/pedido_routes.py:26-43`

Pelo mesmo motivo do achado acima (nenhuma sessão é verificada em nenhuma rota fora de `/admin/*`):

```python
# routes/usuario_routes.py:9-16
@usuario_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    ...
    usuarios = UsuarioController.listar()   # retorna TODOS os usuários, sem auth

# routes/pedido_routes.py:36-43
@pedido_bp.route('/pedidos/usuario/<int:usuario_id>', methods=['GET'])
def listar_pedidos_usuario(usuario_id):
    ...
    pedidos = PedidoController.listar_por_usuario(usuario_id)  # qualquer usuario_id, sem checar se é o próprio requester
```

**Confirmado funcionalmente:**

```
GET /usuarios  (sem auth)
  -> 200, retorna nome/email/tipo de todos os 3 usuários seed, incluindo admin@loja.com
```

**Impacto:** enumeração completa da base de usuários (nome, email, tipo/role) por qualquer visitante anônimo — inclusive identificar qual conta é `admin`, facilitando ataques direcionados. `GET /pedidos` e `GET /pedidos/usuario/<id>` expõem histórico de compras (itens, valores) de qualquer usuário para qualquer outro usuário, sem checagem de ownership — IDOR clássico.

**Refatoração proposta:**
- `GET /usuarios` e `GET /pedidos` (listagem completa): restringir a `role_required("admin")`.
- `GET /pedidos/usuario/<usuario_id>`: exigir `login_required` e checar `usuario_id == requester.id` (ou `requester.tipo == "admin"`), retornando 403 caso contrário — mesmo padrão de ownership check do Padrão 20/21 do playbook.
- `GET /usuarios/<id>`: mesma regra (dono do recurso ou admin).

---

### LOW-1: Configuração de admin (`ADMIN_TOKEN`) fora do padrão de config centralizada

**Arquivos:** `app.py:34`, `.env`

`ADMIN_TOKEN` é lido diretamente via `os.getenv("ADMIN_TOKEN")` em `app.py`, em vez de passar por `config.py` como as demais secrets (`SECRET_KEY`, `DATABASE_PATH`). Além disso, `.env` não documenta essa variável — hoje ela está ausente do arquivo, então `admin_required` sempre nega acesso (`expected` é `None`), o que é seguro (fail-closed) mas deixa o endpoint administrativo inutilizável sem que isso esteja documentado em lugar nenhum.

**Impacto:** não é uma vulnerabilidade (a rota falha fechada), mas é uma inconsistência de configuração que pode confundir quem for operar o admin endpoint em produção.

**Refatoração proposta:** mover `ADMIN_TOKEN` para `Config` (`config.py`) junto das outras secrets, e adicionar a chave (comentada ou com placeholder) em `.env`.

---

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de achados | **3** |
| CRITICAL | 2 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 |

---

## Histórico de Auditorias (code-smells-project)

| Timestamp | Skill | Achados | Observação |
|---|---|---|---|
| 2026-09-20T08-45-00 | v1.0/v2.0 | 11 | Auditoria inicial |
| 2026-09-20T09-18-26 | v2.0 | 11 | v2.0 final |
| 2026-09-20T09-38-22 | v2.1 | 14 | Catálogo expandido |
| 2026-09-20T09-53-39 | v2.1 | 6 | Pós Fase 3 v2.1 (seletiva) |
| 2026-09-20T10-11-42 | v2.2 | 0 | Pós Fase 3 v2.2 (sistemática) — baseada no log |
| 2026-09-20T10-14-52 | v2.2 | 1 | Reauditoria → N+1 residual |
| 2026-09-20T10-19-40 | v2.2 | 0 | Após fix — releitura completa dos 18 padrões |
| **2026-09-20T17-05-29** | **v3.1** | **3** | **Primeiro teste funcional de autorização (Padrão 19) — achou 2 CRITICAL de Broken Access Control que a releitura estrutural v2.2 nunca cobria** |

**Status:** 🔴 2 achados CRITICAL abertos (Broken Access Control em rotas de escrita e leitura fora de `/admin/*`) + 1 LOW.
