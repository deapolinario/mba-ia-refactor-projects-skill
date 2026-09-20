# Auditoria (Fases 1-2): ecommerce-api-legacy
**Versão da Skill:** 2.2
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T10-31-10
**Contexto:** Reauditoria fresca (releitura linha a linha dos 17 arquivos atuais) pós Fase 3 (commit `9e51c29`)

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Node.js
Framework:      Express.js
Database:       SQLite (in-memory)
Domain:         E-commerce / LMS Platform
Architecture:   Structured (MVC: models/, routes/, controllers/, middleware/, utils/)
Source files:   17 files analyzed
DB tables:      5 (users, courses, enrollments, payments, audit_logs)
```

---

## PHASE 2: ARCHITECTURE AUDIT — varredura dos 18 anti-patterns do catálogo v2.2

| # | Anti-pattern | Resultado |
|---|---|---|
| 1 | SQL Injection | ✅ Nenhum — todas as queries parameterized, `IN (...)` construído só com placeholders |
| 2 | Hardcoded Secrets | ✅ Nenhum |
| 3 | Senhas em Texto Plano | ✅ Nenhum — `pass` (hash) nunca sai em response |
| 4 | Dangerous Admin Endpoint | ✅ Nenhum |
| 5 | Broken Access Control | ✅ Nenhum — `adminRequired` nas 2 rotas sensíveis |
| 6 | Weak Password Hashing | ✅ Nenhum — bcrypt |
| 7 | God Classes | ✅ Nenhum — maior arquivo tem 49 linhas |
| 8 | N+1 Queries | ✅ Nenhum — financial-report em 1 query; delete de usuário em 4 queries fixas (não escala com dados) |
| 9 | Global State Mutável | ✅ Nenhum (ver nota) |
| 10 | Code Duplication | ✅ Nenhum |
| 11 | Secrets em Responses | ✅ Nenhum |
| 12 | Logs Sensíveis (PII) | ✅ Nenhum — cartão mascarado, chave nunca impressa |
| 13 | Exception Detail Leakage | ✅ Nenhum — erros tipados com mensagens seguras; 500 genérico para inesperados |
| 14 | Magic Strings | ✅ Nenhum |
| 15 | Ternários Desnecessários | ✅ Nenhum |
| 16 | Monolithic Architecture | ✅ Nenhum |
| 17 | Regressão de Refatoring | ✅ Nenhum — `initDb()` idempotente |
| 18 | Configuração Morta | 🔵 **1 achado** |

---

### [LOW] Configuração Morta — `dbUser` e `smtpUser`

**Arquivo:** `src/config.js`, linhas 4 e 7

```javascript
const config = {
    dbUser: process.env.DB_USER,       // nunca referenciado fora deste arquivo
    dbPass: process.env.DB_PASS,        // usado em validate()
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER,    // nunca referenciado fora deste arquivo
    ...
};
```

**Descrição:** `dbUser` e `smtpUser` são carregados do `.env` mas nunca lidos em nenhum model/controller/route. São vestígios do `AppManager.js`/`utils.js` originais, que também nunca os usavam de fato (o banco é SQLite in-memory sem autenticação; não há envio de email implementado neste projeto). Confirmado via `grep -rn "dbUser\|smtpUser" src/` — zero ocorrências fora de `config.js`.

**Impacto:** Falsa sensação de que essas credenciais são necessárias/usadas; ruído em `.env` e `config.js`.

**Refatoração proposta:** Remover `dbUser`, `smtpUser`, `DB_USER`, `SMTP_USER` de `config.js` e `.env` — não há uso real a preservar neste escopo (SQLite in-memory, sem SMTP implementado).

---

## Nota sobre #9 (Global State Mutável)

`database.js` mantém `let _db = null` / `let _initialized = false` em escopo de módulo. Isso **não** é reincidência do achado original: antes, `globalCache`/`totalRevenue` eram exportados diretamente (`module.exports = { ..., globalCache, totalRevenue }`), permitindo mutação externa sem controle. Agora `_db`/`_initialized` nunca são exportados — só acessíveis via `getDb()`/`initDb()`, um padrão de encapsulamento de módulo idiomático em Node.js (equivalente a um Singleton). Documentado aqui para deixar explícito que a distinção foi considerada, não ignorada.

---

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de achados | 1 |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 1 |

**Status:** Fase 2 completa. Achado é de baixo risco (limpeza de configuração não utilizada) — aguardando decisão do usuário sobre aplicar o fix.
