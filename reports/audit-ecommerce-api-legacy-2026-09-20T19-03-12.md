# Relatório de Auditoria - ecommerce-api-legacy

**Data:** 2026-09-20
**Stack:** Node.js + Express 4.18 + SQLite (in-memory, via `sqlite3`)
**Domínio:** E-commerce/LMS — checkout de matrícula em cursos online (users, courses, enrollments, payments, audit_logs)

**Contexto:** este projeto já passou por dois ciclos completos da skill `refactor-arch` (commits `9e51c29`, `2352f78`, `9144532`) — incluindo uma self-verification v3.1 com teste funcional de autorização que fechou com 0 achados. Esta execução releu os 17 arquivos de `src/` do zero, do princípio, tratando o trabalho anterior como não-verificado (mesma disciplina de uma Fase 2 nova), e não encontrou nenhum achado adicional.

---

## Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 0 achados
- **Total:** 0 achados

---

## Checklist dos 19 Anti-Patterns

| # | Padrão | Status |
|---|--------|--------|
| 1 | SQL Injection | ✅ 100% das queries parametrizadas (`?`), inclusive o `IN (...)` dinâmico em `models/payment.js` |
| 2 | Hardcoded Secrets | ✅ `.env` não versionado (`.gitignore`, confirmado via `git ls-files`); `config.js` lê tudo de `process.env` |
| 3 | Senhas em Texto Plano | ✅ `bcrypt.hash(pwd, 10)` no cadastro; nunca comparação/armazenamento em claro; `pass` nunca sai do model para a response |
| 4 | Dangerous Admin Endpoint | ✅ Nenhum endpoint executa SQL/código arbitrário vindo do cliente |
| 5 | Broken Access Control | ✅ `DELETE /api/users/:id` e `GET /api/admin/financial-report` exigem `X-Admin-Token` (`adminRequired`, fail-closed se token não configurado) |
| 6 | Privilege Escalation (Autorização Granular) | ✅ Sem coluna `role`/`is_admin` no schema (`users`: `id, name, email, pass`), sem endpoint de update de usuário; `price`/`payment_status` sempre resolvidos no servidor, nunca lidos do payload |
| 7 | Weak Password Hashing | ✅ bcrypt (cost 10) |
| 8 | God Classes | ✅ Maior arquivo (`checkoutController.js`) tem 51 linhas |
| 9 | N+1 Queries | ✅ `models/report.js` usa 1 query com JOINs, agrupamento em memória |
| 10 | Global State Mutável | ✅ `_db`/`_initialized` em `database.js` — guard evita reinicialização; `initDb()` só é chamado uma vez, em `start()` antes do `listen` |
| 11 | Code Duplication | ✅ Nenhuma duplicação relevante entre models/controllers |
| 12 | Secrets Expostas em Responses | ✅ Response do checkout retorna só `{msg, enrollment_id}`; nenhuma rota retorna `pass` ou config |
| 13 | Logs Sensíveis (PII) | ✅ Número de cartão mascarado (`utils/mask.js`); `paymentGatewayKey` nunca logado em claro |
| 14 | Exception Detail Leakage | ✅ Todas as rotas capturam erro, logam `err.message` só via `console.error`, respondem mensagem genérica ao cliente |
| 15 | Magic Strings/Numbers | ✅ `paymentStatus`/`cardBrandPrefixes` centralizados em `config.js` |
| 16 | Ternários Desnecessários | ✅ Nenhum encontrado (o único ternário, em `checkoutController.js:36-38`, resolve um valor de fato condicional) |
| 17 | Monolithic Architecture | ✅ MVC completo: `config/`, `models/`, `routes/`, `controllers/`, `middleware/`, `utils/`; `app.js` é entry point limpo (16 linhas úteis) |
| 18 | Configuração Morta | ✅ Toda entrada de `config.js` tem uso real — `paymentGatewayKey` condiciona o log em `checkoutController.js:35`, `adminToken` é comparado em `middleware/auth.js`, `port` usado em `app.js` |
| 19 | Regressão de Refatoração (setup por-request / N+1 novo) | ✅ Nenhuma regressão — setup roda uma vez, nenhuma query nova em loop |

---

## Teste Funcional de Autorização (obrigatório, independente do resultado estrutural)

Simulação de requisições com um cliente sem privilégio algum contra todo endpoint de escrita:

| # | Requisição | Esperado | Resultado do código atual |
|---|-----------|----------|---------------------------|
| 1 | `POST /api/checkout` sem `pwd`, criando usuário novo | 400 | `ValidationError` lançado → `400` ✅ |
| 2 | `POST /api/checkout` injetando `role:"admin"`, `is_admin:true`, `price:0.01` no body | Campos ignorados; preço = preço real do curso | `checkout()` desestrutura só `{usr, eml, pwd, c_id, card}` — campos extras são descartados pelo destructuring; preço vem sempre de `courseModel.findActiveById(c_id).price` ✅ |
| 3 | `DELETE /api/users/:id` sem header `X-Admin-Token` | 401 | `adminRequired` retorna `401` antes de chamar o controller ✅ |
| 4 | `DELETE /api/users/:id` com token incorreto | 401 | comparação `token !== config.adminToken` falha → `401` ✅ |
| 5 | `GET /api/admin/financial-report` sem token | 401 | idem ✅ |
| 6 | `GET /api/admin/financial-report` com token válido (caso legítimo) | 200 | guard passa, `reportController.getFinancialReport()` executa ✅ |

**Conclusão:** não existe vetor de Padrão 19 nem estrutural nem funcional — não há campo de privilégio no schema, não há endpoint de update de usuário, e o destructuring explícito em `checkout()` já funciona como allowlist implícita de campos aceitos do payload.

---

## Observação (não é achado, é nota informativa)

`middleware/auth.js` compara o token com `!==` (comparação não constant-time). Isso não se qualifica como achado dentro do catálogo de 19 padrões desta skill (não é Broken Access Control — o guard existe e funciona corretamente; seria uma categoria de hardening adicional, timing-attack resistance, fora do escopo atual). Sinalizado aqui apenas para registro, sem ação proposta.

---

## Conclusão

Nenhum achado novo. O projeto permanece no estado confirmado pela self-verification do ciclo anterior (`audit-ecommerce-api-legacy-2026-09-20T18-37-01.md`). **Fase 3 não tem o que corrigir** — não há checklist de achados para processar.
