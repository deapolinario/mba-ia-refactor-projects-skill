# Auditoria (Fases 1-2): task-manager-api
**Versão da Skill:** 3.0
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T12-36-45
**Contexto:** Reauditoria fresca pós Fase 3 v3.0 (commit `88a9bcb`, que havia terminado com self-verification limpo)

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Python 3.x
Framework:      Flask + SQLAlchemy
Database:       SQLite (tasks.db)
Domain:         Task Management / Project Management
Architecture:   Structured (MVC completo)
Source files:   22 files analyzed
DB tables:      3 (users, tasks, categories)
```

---

## PHASE 2: ARCHITECTURE AUDIT

A releitura dos 18 anti-patterns do catálogo (grep + leitura completa) não encontrou novos achados nos padrões formais. Porém, ao testar funcionalmente a **lógica de autorização dentro dos controllers** (não só "a rota tem `@login_required`?"), encontrei 2 variantes do achado #5 (Broken Access Control) que a self-verification anterior não cobriu — ela verificou presença de guards nas rotas, mas não testou se a lógica de negócio dentro do controller impedia escalação de privilégio.

### 🔴 [CRITICAL] Privilege Escalation via `PUT /users/:id`

**Arquivo:** `controllers/user_controller.py`, método `update()`

A rota tinha `@login_required` (autenticação OK), mas nenhuma checagem de **autorização**: qualquer usuário autenticado com role `user` podia chamar `PUT /users/<qualquer_id>` e alterar `role` (inclusive para `admin`) ou `active` de **qualquer outro usuário**, incluindo si mesmo.

**Confirmado via exploit manual:**
```
Alice (role=user) -> PUT /users/1 {"role": "admin"}  => 200, João Silva agora é admin
Alice (role=user) -> PUT /users/<bob_id> {"active": false}  => 200, Bob desativado
```

**Impacto:** Qualquer conta comprometida ou criada normalmente se torna admin em uma requisição, ou pode negar serviço a qualquer outro usuário.

---

### 🔴 [CRITICAL] Privilege Escalation via `POST /users` (cadastro público)

**Arquivo:** `controllers/user_controller.py`, método `create()`

O endpoint de cadastro é intencionalmente público (correto), mas aceitava o campo `role` do payload sem nenhuma restrição.

**Confirmado via exploit manual (sem autenticação prévia):**
```
POST /users {"name":"Invasor","email":"invasor@x.com","password":"123456","role":"admin"}
=> 201, conta criada direto como admin
```

**Impacto:** Mais grave que o anterior — nem exige uma conta existente. Qualquer visitante anônimo se torna admin.

---

## Resumo Executivo

| Severidade | Count |
|---|---|
| CRITICAL | 2 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |
| **TOTAL** | **2** |

**Causa raiz:** a self-verification do ciclo anterior (`88a9bcb`) verificou "toda rota sensível tem guard de autenticação/role?" mas não testou a lógica de autorização granular dentro dos controllers (quem pode alterar o quê de quem). Uma rota com `@login_required` pode ainda ter uma falha de authorization interna.

**Status:** Achados corrigidos na sequência (ver `REFACTORING_LOG_v3_0.md`, seção "Ciclo 2").
