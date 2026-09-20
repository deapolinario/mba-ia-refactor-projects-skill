# Auditoria Pós-Fix (Self-Verification, Ciclo 2): task-manager-api
**Versão da Skill:** 3.0
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T12-42-10
**Contexto:** Fase 3, passo 7 (Self-Verification Loop), ciclo 2 — após corrigir os 2 achados CRITICAL de `audit-task-manager-api-2026-09-20T12-36-45.md`

---

## Findings Checklist (ciclo 2)

| # | Achado | Status |
|---|--------|--------|
| 1 | Privilege Escalation via `PUT /users/:id` (alterar role/active de outro usuário, ou autopromoção) | ✅ Corrigido |
| 2 | Privilege Escalation via `POST /users` (cadastro público aceitando `role` do payload) | ✅ Corrigido |

---

## Correções Aplicadas

### `controllers/user_controller.py: update()`
Adicionado parâmetro `requester` (o usuário autenticado fazendo a requisição). Regras:
- Só o próprio usuário ou um admin pode editar um perfil
- `role`/`active` só podem ser alterados por um admin — mesmo que o alvo seja o próprio usuário (impede autopromoção)

### `controllers/user_controller.py: create()`
Removida a leitura de `role` do payload — cadastro público sempre cria com `role='user'`. Provisionamento de admin continua possível via `seed.py` (bypassa o controller, cria via ORM direto — uso legítimo de bootstrap).

### `routes/user_routes.py`
`update_user` agora passa `g.current_user` ao controller e trata `PermissionError` como 403.

---

## Validação (exploits antes/depois + regressão)

| Cenário | Antes do fix | Depois do fix |
|---|---|---|
| Usuário comum promove outro a admin via `PUT` | 200 ✅ (exploit) | **403** |
| Usuário comum desativa outro usuário | 200 ✅ (exploit) | **403** |
| Usuário comum se autopromove | 200 ✅ (exploit) | **403** |
| Usuário comum edita nome de outro | 200 ✅ (exploit) | **403** |
| Usuário edita o **próprio** nome | 200 | **200** (preservado) |
| Admin promove/edita qualquer usuário | 200 | **200** (preservado) |
| Cadastro público com `role: admin` no payload | 201, role=admin ✅ (exploit) | **201, role=user** |

Suite de regressão completa (12 cenários: health, login, listagem, criação/listagem de tasks com joinedload, categorias públicas vs. protegidas, relatório, delete de usuário com cascade) reexecutada após o fix — todos os resultados preservados, nenhuma quebra.

---

## Self-Verification: Checklist dos 18 Anti-Patterns (releitura completa)

Idêntica à do ciclo 1 (`audit-task-manager-api-2026-09-20T12-14-27.md`) — nenhum dos 18 padrões formais foi reintroduzido pelo fix. Adicionalmente, a lógica de autorização de `update()`/`create()` foi testada com exploits reais, não apenas inspecionada.

**Findings: 0**

---

## Decisão do Self-Verification Loop

**0 achados → Fase 3 encerrada com sucesso (ciclo 2 de 3 possíveis).** Não é necessário perguntar ao usuário sobre continuar — não há mais achados pendentes.

**Status:** 🟢 Limpo. Nota para v3.1: a checklist de autorização deveria incluir explicitamente "testar se a lógica dentro do controller previne escalação de privilégio (IDOR em campos sensíveis como role/active)", não só "a rota tem guard de autenticação/role?" — esse foi o gap que permitiu este achado escapar do ciclo 1.
