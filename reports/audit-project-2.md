# Auditoria (Fases 1-2): ecommerce-api-legacy
**Versão da Skill:** 3.2 (20 anti-patterns, Padrão 20 de APIs Deprecated generalizado para qualquer linguagem)
**Data da Auditoria:** 2026-09-22
**Timestamp:** 2026-09-22T21-40-07
**Contexto:** Projeto já havia passado por refatoração completa (9/9 achados v2.2) + fix de dead config + self-verification v3.1 (0 achados nos 19 padrões da época, incluindo suíte funcional de autorização — ver `audit-ecommerce-api-legacy-2026-09-20T19-03-12.md`). Esta rodada com o catálogo v3.2 encontrou um achado CRITICAL que havia escapado de todas as rodadas anteriores.

---

## PHASE 1: PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       Node.js (JavaScript, CommonJS)
Framework:      Express 4.18.2
Database:       SQLite (via sqlite3 5.1.6, in-memory ':memory:')
Domain:         LMS API (courses, enrollments, payments, checkout) — auth
                 por token admin, RBAC mínimo, audit log
Architecture:   MVC (config/, database.js, models/, routes/, controllers/,
                 middleware/, app.js como entry point)
Source files:   17 files analyzed (excluindo .claude/, node_modules/)
DB tables:      users, courses, enrollments, payments, audit_logs
================================
```

---

## PHASE 2: AUDIT COMPLETE

### Resumo Executivo

- **CRITICAL:** 1 achado
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 0 achados
- **Total:** 1 achado

Nota: o Padrão 20 (APIs Deprecated, generalizado na v3.2) não encontrou ocorrências — nenhuma API deprecated do Node.js/Express/bcrypt/dotenv em uso.

### Finding

**[CRITICAL] Broken Authentication no Checkout — Impersonação de Conta Existente sem Verificação de Senha**

`src/controllers/checkoutController.js:14-30` — quando o email do checkout já pertence a um usuário existente, o campo `pwd` enviado era completamente ignorado (nunca havia `bcrypt.compare`). Confirmado por exploração real contra o servidor: checkout com senha errada ou ausente para `leonan@fullcycle.com.br` (usuário do seed) retornava `200 Sucesso`, criando enrollment/payment/audit-log em nome dele. O `GET /api/admin/financial-report` confirmou o estrago — matrícula duplicada e receita inflada, tudo atribuído a uma conta que o "atacante" nunca autenticou.

Escapou da self-verification v3.1 porque a suíte funcional daquela rodada testou apenas o branch de cadastro **novo** (checkout sem senha → 400, correto) e nunca o branch de usuário **existente** com senha incorreta/ausente.

Relatório completo com prova de exploração, snippet e refatoração proposta: `audit-ecommerce-api-legacy-2026-09-22T21-40-07.md`.

---

## PHASE 3: REFACTORING COMPLETE

Correção aplicada em `checkoutController.js`: `pwd` passa a ser obrigatório em toda chamada (não só cadastro novo); para usuário existente, `bcrypt.compare(pwd, user.pass)` é chamado e lança nova exceção `AuthenticationError` (mapeada para HTTP 401 em `checkoutRoutes.js`) se a senha não confere.

### Self-Verification (Ciclo 1)

Código relido do zero + checklist completo dos 20 anti-patterns reaplicado + teste funcional repetindo o cenário do achado (senha errada/ausente para usuário existente) e os casos legítimos (senha correta, cadastro novo com/sem senha). **0 achados novos** — vetor de impersonação fechado, nenhum caso legítimo quebrado, `financial-report` confirmado sem entradas fraudulentas. Relatório completo: `audit-ecommerce-api-legacy-2026-09-22T21-42-55.md`.

### Validação

- ✅ `node --check` em todos os arquivos: sem erros de sintaxe
- ✅ Servidor inicia sem erros (`node src/app.js`)
- ✅ Testado via requisições HTTP reais: checkout com senha errada/ausente para usuário existente → 401/400; checkout com senha correta → 200; cadastro novo com/sem senha → 200/400; `financial-report` só com matrículas legítimas após os testes
