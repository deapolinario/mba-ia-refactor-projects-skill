# Log de Refatoração: ecommerce-api-legacy
**Data:** 2026-09-20
**Skill:** refactor-arch v2.2
**Fase 3:** Refactoring & Validation (sistemática)

---

## Findings Checklist (completa)

| # | Achado | Severidade | Status |
|---|--------|-----------|--------|
| 1 | Hardcoded Credentials (`utils.js`) | CRITICAL | ✅ Corrigido |
| 2 | Broken Access Control (`/api/admin/financial-report`, `DELETE /api/users/:id`) | CRITICAL | ✅ Corrigido |
| 3 | Weak Password Hashing (`badCrypto` — Base64) | HIGH | ✅ Corrigido |
| 4 | God Class (`AppManager.js`, 142 linhas) | HIGH | ✅ Corrigido |
| 5 | N+1 Queries + Callback Hell (financial-report) | HIGH | ✅ Corrigido |
| 6 | Global State Mutável (`globalCache`, `totalRevenue`) | HIGH | ✅ Corrigido |
| 7 | Logs Sensíveis — cartão de crédito em plaintext | MEDIUM | ✅ Corrigido |
| 8 | Magic Strings (status, prefixo de bandeira) | LOW | ✅ Corrigido |
| 9 | Monolithic Architecture | LOW | ✅ Corrigido (MVC completo) |
| — | *(fora do catálogo formal)* Orphaned records no delete de usuário | — | ✅ Corrigido (bônus) |

**Resultado:** 9/9 achados catalogados + 1 achado extra, todos `✅ Corrigido`. Zero itens adiados.

---

## Detalhamento

### CRITICAL 1: Hardcoded Credentials

**Arquivos:** `src/config.js` (novo), `.env` (novo), `.gitignore` (novo)

- `dbPass`, `paymentGatewayKey`, `dbUser`, `smtpUser` agora vêm de `process.env` via `dotenv`
- `.env` adicionado ao `.gitignore`
- `validate()` falha o boot em produção se secrets obrigatórios estiverem ausentes

### CRITICAL 2: Broken Access Control

**Arquivos:** `src/middleware/auth.js` (novo), `src/routes/reportRoutes.js`, `src/routes/userRoutes.js`

- Middleware `adminRequired` exige header `X-Admin-Token` == `ADMIN_TOKEN` (env var)
- Aplicado em `GET /api/admin/financial-report` e `DELETE /api/users/:id`

### HIGH 3: Weak Password Hashing

**Arquivos:** `src/controllers/checkoutController.js`, `src/database.js` (seed)

- `badCrypto()` (Base64 repetido, 10 chars) substituído por `bcrypt.hash(pwd, 10)`
- Seed do usuário de exemplo também usa bcrypt

### HIGH 4: God Class → MVC completo

**Removidos:** `src/AppManager.js` (142 linhas), `src/utils.js`
**Criados:** `src/config.js`, `src/database.js`, `src/middleware/auth.js`,
`src/models/{course,user,enrollment,payment,auditLog,report}.js`,
`src/controllers/{checkout,report,user}Controller.js`,
`src/routes/{checkout,report,user}Routes.js`, `src/utils/mask.js`

- Models: apenas queries (uma responsabilidade por entidade)
- Controllers: validação + orquestração, lançam erros tipados (`ValidationError`, `NotFoundError`, `PaymentDeniedError`) que as routes traduzem em status HTTP
- Routes: apenas mapeamento HTTP
- `app.js`: 22 linhas, apenas composição (registra routes, inicializa DB, sobe o listener)

### HIGH 5: N+1 Queries + Callback Hell

**Arquivo:** `src/models/report.js`

- De `1 + N_courses + 2·Σ(enrollments)` queries em callbacks aninhados (4 níveis) para **1 única query com LEFT JOIN**, agrupada em memória com `Map`
- Verificado com `db.on('trace', ...)`: exatamente 1 query executada por chamada ao endpoint

### HIGH 6: Global State Mutável

**Arquivo:** `src/database.js`

- `globalCache`/`totalRevenue` (module-level `let`, nunca sincronizados, `totalRevenue` nem chegava a ser incrementado) foram removidos
- Estado de conexão do banco agora vive em uma variável de módulo privada (`_db`) com uma única função de acesso controlado (`getDb()`) e inicialização idempotente (`initDb()`), sem mutação exposta externamente

### MEDIUM 7: Logs Sensíveis (cartão de crédito)

**Arquivo:** `src/utils/mask.js` (novo), `src/controllers/checkoutController.js`

- `maskCardNumber()` mascara todos os dígitos exceto os 4 primeiros/últimos
- Chave de pagamento nunca mais aparece em log (mostra apenas `***` se configurada)

### LOW 8: Magic Strings

**Arquivo:** `src/config.js`

- `config.paymentStatus.PAID/DENIED` e `config.cardBrandPrefixes.visa` centralizam valores antes hardcoded no meio da lógica de checkout

### LOW 9: Monolithic Architecture

Resolvido junto com o item 4 (estrutura MVC completa acima).

### Bônus (fora do catálogo formal): Orphaned Records

**Arquivos:** `src/controllers/userController.js`, `src/models/enrollment.js`, `src/models/payment.js`

- `DELETE /api/users/:id` agora remove `payments` → `enrollments` → `users` em cascata explícita, na ordem correta de dependência
- Validado: relatório financeiro após delete não mais lista o usuário removido nem seus pagamentos

---

## Validação Funcional (end-to-end)

Testado com `supertest` contra a app real (sem abrir porta), 11 cenários:

| Cenário | Resultado |
|---|---|
| Checkout válido (cartão Visa) | ✅ 200, log de cartão mascarado |
| Checkout cartão negado (não-Visa) | ✅ 400 |
| Checkout curso inexistente | ✅ 404 |
| Checkout dados faltando | ✅ 400 |
| Financial report sem token | ✅ 401 |
| Financial report com token errado | ✅ 401 |
| Financial report com token correto | ✅ 200, revenue agregado corretamente via JOIN |
| Delete user sem token | ✅ 401 |
| Delete user com token (cascade) | ✅ 200 |
| Financial report após delete | ✅ usuário removido não aparece mais |
| Checkout com email já cadastrado | ✅ reusa usuário existente |

Query count no financial-report confirmado via `db.on('trace', ...)`: **1 query** (era `1 + N + 2M`).

---

## Estrutura Final

```
ecommerce-api-legacy/
├── .env, .gitignore
├── package.json                    # bcrypt, dotenv adicionados
├── src/
│   ├── app.js                      # entry point (22 linhas)
│   ├── config.js                   # secrets + domínio
│   ├── database.js                 # init único + Promise wrapper
│   ├── middleware/
│   │   └── auth.js
│   ├── models/
│   │   ├── course.js
│   │   ├── user.js
│   │   ├── enrollment.js
│   │   ├── payment.js
│   │   ├── auditLog.js
│   │   └── report.js               # elimina N+1 via JOIN
│   ├── controllers/
│   │   ├── checkoutController.js
│   │   ├── reportController.js
│   │   └── userController.js
│   ├── routes/
│   │   ├── checkoutRoutes.js
│   │   ├── reportRoutes.js
│   │   └── userRoutes.js
│   └── utils/
│       └── mask.js
└── REFACTORING_LOG_v2_2.md
```

`AppManager.js` e `utils.js` (God Class original + config/state misturados) foram removidos.
