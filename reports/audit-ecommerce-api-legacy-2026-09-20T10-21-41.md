# Auditoria (Fases 1-2): ecommerce-api-legacy
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

**Status:** Fase 2 completa. Aguardando decisão do usuário sobre Fase 3.
