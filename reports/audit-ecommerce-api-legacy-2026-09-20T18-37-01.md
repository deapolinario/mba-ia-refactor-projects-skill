# Relatório de Auditoria - ecommerce-api-legacy (Self-Verification — Ciclo 1)

**Data:** 2026-09-20
**Stack:** Node.js + Express 4.18 + SQLite (in-memory)
**Domínio:** LMS com fluxo de checkout — users, courses, enrollments, payments, audit_logs

**Contexto:** reaudita o código após a correção dos 2 achados da Fase 2 (`audit-ecommerce-api-legacy-2026-09-20T18-28-28.md`). Releitura completa dos 17 arquivos de `src/`, do zero, sem assumir que a correção aplicada foi suficiente — mais o teste funcional de autorização obrigatório (v3.1, passo 7.b2).

---

## Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 0 achados
- **Total:** 0 achados

---

## Checklist dos 19 Anti-Patterns (Reaudita Estrutural)

| # | Padrão | Status |
|---|--------|--------|
| 1 | SQL Injection | ✅ Nenhuma — todas as queries parametrizadas (`?`), inclusive `IN (...)` dinâmico em `payment.js` |
| 2 | Hardcoded Credentials | ✅ Nenhuma — `.env` fora do git, `config.js` lê de `process.env` |
| 3 | Weak Password Hashing | ✅ bcrypt (`bcrypt.hash(pwd, 10)`) |
| 4 | God Class/Module | ✅ Maior arquivo (`checkoutController.js`) tem 49 linhas |
| 5 | N+1 Queries | ✅ `report.js` usa JOIN único |
| 6 | Code Duplication | ✅ Nenhuma duplicação relevante |
| 7 | Monolithic Architecture | ✅ MVC completo (config/models/routes/controllers/middleware/utils) |
| 8 | Secrets Expostas em Responses | ✅ Response do checkout retorna só `{msg, enrollment_id}`; hash de senha nunca sai do model |
| 9 | Logs Sensíveis (PII) | ✅ Cartão mascarado (`maskCardNumber`), chave de gateway nunca logada em claro |
| 10 | Global State Mutável | ✅ `_db`/`_initialized` seguem o padrão seguro do Padrão 17 (guard, sem side-effect por request) |
| 11 | Magic Strings/Numbers | ✅ `paymentStatus`/`cardBrandPrefixes` centralizados em `config.js` |
| 12 | Ternários Desnecessários | ✅ Nenhum encontrado |
| 13 | Dangerous Admin Endpoint | ✅ Nenhum endpoint executa SQL/código arbitrário vindo do cliente |
| 14 | Plaintext Password Storage | ✅ Sempre hash; nunca comparação/armazenamento em texto plano |
| 15 | Broken Access Control | ✅ `DELETE /api/users/:id` e `GET /api/admin/financial-report` exigem `X-Admin-Token` válido (confirmado funcionalmente, ver abaixo) |
| 16 | Exception Detail Leakage | ✅ Handlers retornam mensagem genérica ao cliente, `err.message` só em `console.error` |
| 17 | Regressão: Init Por-Request | ✅ `initDb` guardado por `_initialized`, chamado uma única vez em `start()` |
| 18 | Configuração Morta | ✅ **Corrigido neste ciclo** — `dbPass`/`DB_PASS` removido de `config.js`, `.env` e `validate()`; nenhum literal órfão restante (grep confirmou) |
| 19 | Privilege Escalation (Autorização Granular) | ✅ Ver teste funcional abaixo — não é suficiente concluir pela ausência estrutural de campo `role` |

---

## Teste Funcional de Autorização (v3.1, passo 7.b2 — obrigatório)

Aplicação subida localmente (`node src/app.js`) e testada com `curl` simulando um cliente sem privilégio algum (sem token, sem sessão — não há conceito de usuário autenticado além do admin token estático):

| # | Requisição | Esperado | Obtido | Resultado |
|---|-----------|----------|--------|-----------|
| 1 | `POST /api/checkout` sem `pwd` | 400 (agora exigido) | `400` | ✅ |
| 2 | `POST /api/checkout` com `pwd` válido | 200 | `200 {"msg":"Sucesso",...}` | ✅ |
| 3 | `POST /api/checkout` injetando `role:"admin"`, `is_admin:true`, `price:0.01` no payload | Campos ignorados; preço cobrado = preço real do curso no servidor | `200`, confirmado via `financial-report`: aluno "Atacante" pagou **997** (preço real de "Clean Architecture"), não 0.01 | ✅ Mass assignment sem efeito |
| 4 | `GET /api/admin/financial-report` sem token | 401 | `401` | ✅ |
| 5 | `GET /api/admin/financial-report` com token válido | 200 | `200` | ✅ |
| 6 | `DELETE /api/users/1` sem token (IDOR/broken access control) | 401 | `401` | ✅ |
| 7 | `DELETE /api/users/1` com token forjado | 401 | `401` | ✅ |

**Conclusão do teste funcional:** não existe endpoint de update/patch de usuário nem coluna de privilégio no schema (`users` só tem `id, name, email, pass`) — não há "campo sensível" algum para escalar via mass assignment, e o teste confirma isso na prática, não só por leitura estática. `price` e `payment_status` são sempre resolvidos no servidor (`courseModel.findActiveById`, prefixo do cartão), nunca aceitos do payload. **Nenhuma instância do Padrão 19 encontrada — nem estrutural, nem funcional.**

---

## Regression Checklist

- ✅ Setup/seed roda uma única vez (`initDb` guardado por `_initialized`, chamado em `start()`)
- ✅ Nenhuma query nova introduzida dentro de loop
- ✅ `paymentGatewayKey` (única config restante em `required`) tem ponto de uso real (condiciona o log em `checkoutController.js:32`)
- ✅ Nenhum literal antigo (`DB_PASS`, `'123456'`) sobrou coexistindo com a correção — grep confirmou zero ocorrências

---

## Status

```
================================
PHASE 3: SELF-VERIFICATION — CYCLE 1
================================
Re-read: 17 files
Findings: 0
Status: ✅ Clean — no further action needed
================================
```
