# Auditoria (Fases 1-2): ecommerce-api-legacy

**Contexto deste arquivo:** esta é a auditoria original (Fases 1-2, skill v2.2), a primeira execução completa da skill contra o projeto ainda não refatorado — é o que este arquivo deve documentar por exigência do enunciado (Fase 2 encontrando ≥5 achados, incluindo CRITICAL/HIGH). As rodadas de refatoração subsequentes estão documentadas nas seções abaixo, na ordem em que aconteceram, terminando com um achado CRITICAL novo (v3.2) que havia escapado de todas as rodadas anteriores, incluindo a self-verification funcional.

**Versão da Skill:** 2.2
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T10-21-41

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Node.js 14+
Framework:      Express.js
Database:       SQLite (in-memory)
Domain:         E-commerce / LMS Platform
Architecture:   Monolithic
Source files:   3 files analyzed (app.js, AppManager.js, utils.js)
DB tables:      5 (users, courses, enrollments, payments, audit_logs)
```

---

## PHASE 2: ARCHITECTURE AUDIT — varredura dos 18 anti-patterns do catálogo v2.2

| # | Anti-pattern | Severidade | Resultado |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Nenhum — todas as queries usam placeholders `?` |
| 2 | Hardcoded Secrets | CRITICAL | 🔴 Achado |
| 3 | Senhas em Texto Plano | CRITICAL | ✅ Nenhum |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Nenhum |
| 5 | Broken Access Control | CRITICAL | 🔴 Achado |
| 6 | Weak Password Hashing | HIGH | 🟠 Achado |
| 7 | God Classes | HIGH | 🟠 Achado |
| 8 | N+1 Queries | HIGH | 🟠 Achado |
| 9 | Global State Mutável | HIGH | 🟠 Achado |
| 10 | Code Duplication | MEDIUM | ✅ Nenhum (capturado no #8) |
| 11 | Secrets em Responses | MEDIUM | ✅ Nenhum |
| 12 | Logs Sensíveis (PII) | MEDIUM | 🟡 Achado |
| 13 | Exception Detail Leakage | MEDIUM | ✅ Nenhum |
| 14 | Magic Strings | LOW | 🔵 Achado |
| 15 | Ternários Desnecessários | LOW | ✅ Nenhum |
| 16 | Monolithic Architecture | LOW/CRITICAL | 🔵 Achado |
| 17 | Regressão de Refatoring | HIGH | N/A — sem refatoração aplicada ainda |
| 18 | Configuração Morta | LOW | N/A — sem camada de config ainda |

---

### [CRITICAL] 1. Hardcoded Credentials

**Arquivo:** `src/utils.js`, linhas 2-6

```javascript
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    smtpUser: "no-reply@fullcycle.com.br",
    port: 3000
};
```

**Impacto:** Comprometimento de banco de dados (credencial admin) e do gateway de pagamento.

---

### [CRITICAL] 2. Broken Access Control

**Arquivo:** `src/AppManager.js`, linhas 80 e 131

```javascript
app.get('/api/admin/financial-report', (req, res) => { ... })   // sem auth
app.delete('/api/users/:id', (req, res) => { ... })              // sem auth
```

**Impacto:** Qualquer requisição sem autenticação acessa receita completa, nomes de alunos e valores pagos, ou deleta qualquer usuário.

---

### [HIGH] 3. Weak Password Hashing

**Arquivo:** `src/utils.js`, linhas 17-23

```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

**Impacto:** Não é criptografia — Base64 é reversível e o output de 10 caracteres é trivial de forçar por brute force.

---

### [HIGH] 4. God Class

**Arquivo:** `src/AppManager.js` (142 linhas)

Mistura inicialização de schema, 3 rotas HTTP completas (checkout, relatório financeiro, delete) e toda a lógica de negócio numa única classe, sem separação de camadas.

---

### [HIGH] 5. N+1 Queries + Callback Hell

**Arquivo:** `src/AppManager.js`, linhas 80-128 (`/api/admin/financial-report`)

Para N courses, 1 query de enrollments por course + 2 queries (user, payment) por enrollment → `1 + N + 2·ΣM` queries, em callbacks aninhados 4 níveis de profundidade.

---

### [HIGH] 6. Global State Mutável

**Arquivo:** `src/utils.js`, linhas 9-10

```javascript
let globalCache = {};
let totalRevenue = 0;
```

Estado de módulo mutável compartilhado entre todas as requisições, sem sincronização.

---

### [MEDIUM] 7. Logs Sensíveis — Cartão de Crédito

**Arquivo:** `src/AppManager.js`, linha 45

```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

**Impacto:** Expõe número de cartão completo e a chave do gateway de pagamento em logs — violação PCI-DSS.

---

### [LOW] 8. Magic Strings

**Arquivo:** `src/AppManager.js`, linha 46

```javascript
let status = cc.startsWith("4") ? "PAID" : "DENIED";
```

Strings de status e regra de validação de bandeira de cartão hardcoded.

---

### [LOW] 9. Monolithic Architecture

Sem separação `models/`, `routes/`, `controllers/` — tudo em `app.js` + `AppManager.js` + `utils.js`.

---

## Nota fora do catálogo (candidato a v2.3)

`DELETE /api/users/:id` não remove `enrollments`/`payments` relacionados (orphaned records). É um achado real de integridade de dados, mas não corresponde a nenhum dos 18 padrões atualmente catalogados.

---

## Resumo Executivo

| Severidade | Count |
|---|---|
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 1 |
| LOW | 2 |
| **TOTAL** | **9** |

**Confirmar refatoração na Fase 3? (y/n)** → confirmado; ver seção seguinte.

---

## PHASE 3: REFATORAÇÃO (histórico de commits)

**Phase 3 sistemática (commit `9e51c29`):** resolve os 9/9 achados desta auditoria. Hardcoded credentials → `.env` via `config.js` + `dotenv`; Broken Access Control → `adminRequired` (header `X-Admin-Token`) guardando `GET /api/admin/financial-report` e `DELETE /api/users/:id`; `badCrypto()` substituído por `bcrypt`; God Class (`AppManager.js`) decomposto em MVC completo (`config.js`, `database.js`, `middleware/auth.js`, `models/`, `controllers/`, `routes/`, `utils/mask.js`); N+1 + callback hell no financial-report → 1 única query com JOIN; estado global mutável removido; cartão de crédito mascarado em logs; magic strings centralizadas em `config.js`. Bônus fora do catálogo: cascade delete de `enrollments`/`payments` órfãos. Validado com 11 cenários end-to-end via supertest.

**Fix pontual (commit `2352f78`):** reauditoria encontrou config morta (`dbUser`/`smtpUser` carregados de env vars mas nunca referenciados) — removidos.

**v3.1 — self-verification (commit `9144532`):** reauditoria encontrou o checkout caindo para uma senha hardcoded `'123456'` quando o cliente omitia `pwd` (credencial previsível, ainda que não explorável na época) e uma config `DB_PASS` morta (banco é SQLite in-memory, nunca precisou de senha) — ambos corrigidos. Self-verification (incluindo o teste funcional de autorização obrigatório) confirmou 0 achados: sem vetor de Padrão 19 (privilege escalation) neste projeto, estrutural ou funcionalmente.

---

## RE-EXECUÇÃO 2026-09-22T21-40-07 — Catálogo v3.2, Broken Authentication Encontrado

**Contexto:** projeto já havia passado por refatoração completa (9/9 achados v2.2) + fix de dead config + self-verification v3.1 (0 achados nos 19 padrões da época, incluindo suíte funcional de autorização — ver `audit-ecommerce-api-legacy-2026-09-20T19-03-12.md`). Esta rodada, com o catálogo v3.2, encontrou um achado CRITICAL que havia escapado de todas as rodadas anteriores.

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

### Fase 3 (v3.2)

Correção aplicada em `checkoutController.js`: `pwd` passa a ser obrigatório em toda chamada (não só cadastro novo); para usuário existente, `bcrypt.compare(pwd, user.pass)` é chamado e lança nova exceção `AuthenticationError` (mapeada para HTTP 401 em `checkoutRoutes.js`) se a senha não confere.

**Self-Verification (Ciclo 1):** código relido do zero + checklist completo dos 20 anti-patterns reaplicado + teste funcional repetindo o cenário do achado (senha errada/ausente para usuário existente) e os casos legítimos (senha correta, cadastro novo com/sem senha). **0 achados novos** — vetor de impersonação fechado, nenhum caso legítimo quebrado, `financial-report` confirmado sem entradas fraudulentas. Relatório completo: `audit-ecommerce-api-legacy-2026-09-22T21-42-55.md`.

**Validação:**
- ✅ `node --check` em todos os arquivos: sem erros de sintaxe
- ✅ Servidor inicia sem erros (`node src/app.js`)
- ✅ Testado via requisições HTTP reais: checkout com senha errada/ausente para usuário existente → 401/400; checkout com senha correta → 200; cadastro novo com/sem senha → 200/400; `financial-report` só com matrículas legítimas após os testes
