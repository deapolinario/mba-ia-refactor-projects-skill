# Relatório de Auditoria - ecommerce-api-legacy

**Data:** 2026-09-22
**Stack:** Node.js (CommonJS) + Express 4.18.2 + SQLite (sqlite3 5.1.6, in-memory)
**Domínio:** LMS API (courses, enrollments, payments, checkout, audit log)
**Contexto:** Catálogo v3.2 (20 anti-patterns, Padrão 20 generalizado). Projeto já havia passado por refatoração completa (9/9 achados v2.2) + fix de dead config + self-verification v3.1 (0 achados nos 19 padrões da época, incluindo suíte funcional de autorização). Esta rodada aplicou o mesmo rigor, mas testando um cenário de autenticação que a suíte funcional anterior não cobria.

---

## Resumo Executivo

- **CRITICAL:** 1 achado
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 0 achados
- **Total:** 1 achado

Nota: o Padrão 20 (APIs Deprecated) não encontrou ocorrências — nenhuma API deprecated do Node.js/Express/bcrypt/dotenv em uso (verificado além de exemplos óbvios: `new Buffer()`, `crypto.createCipher()`, `fs.exists()`, `util.isArray()`, padrões antigos de body-parser).

---

## Findings Detalhados

### [CRITICAL] Broken Authentication no Checkout — Impersonação de Conta Existente sem Verificação de Senha

**Arquivo:** `src/controllers/checkoutController.js` (Linhas: 14-30)

**Descrição:**
`checkout()` recebe `pwd` no payload e só o utiliza para **criar** um hash quando o email ainda não existe (`if (!user) { ...bcrypt.hash(pwd, 10)... }`). Quando o email **já existe** no banco, o código pula direto para `user = { id: userId }` implícito (na verdade usa o `user` retornado por `findByEmail`) e prossegue com o checkout **sem nunca chamar `bcrypt.compare(pwd, user.pass)`**. Ou seja: para qualquer email já cadastrado, o `pwd` enviado é completamente ignorado — correto, incorreto ou ausente, tanto faz.

Isso é uma falha de autenticação, não de autorização granular (Padrão 19 clássico é sobre campos sensíveis em rotas já autenticadas) — mas o mecanismo é o mesmo do IDOR: nada impede o requester de **operar sobre a conta de outro usuário** (criar enrollment/payment/audit-log atribuídos a ela) apenas conhecendo seu email.

**Código Problemático:**
```javascript
async function checkout({ usr, eml, pwd, c_id, card }) {
    ...
    let user = await userModel.findByEmail(eml);
    if (!user) {
        if (!pwd) {
            throw new ValidationError('Senha é obrigatória para novo cadastro');
        }
        const hash = await bcrypt.hash(pwd, 10);
        const userId = await userModel.create(usr, eml, hash);
        user = { id: userId };
    }
    // ❌ se `user` já existia, `pwd` nunca é comparado com `user.pass` — segue
    // direto para criar enrollment/payment em nome desse usuário
    ...
    const enrollmentId = await enrollmentModel.create(user.id, c_id);
    await paymentModel.create(enrollmentId, course.price, status);
    await auditLogModel.record(`Checkout curso ${c_id} por ${user.id}`);
}
```

**Prova de exploração (testado contra o servidor real, seed padrão — usuário `leonan@fullcycle.com.br` já existe):**
```bash
# Checkout com senha ERRADA para conta existente — sucesso (deveria falhar)
curl -X POST /api/checkout -d '{"usr":"Attacker","eml":"leonan@fullcycle.com.br","pwd":"totally-wrong","c_id":2,"card":"4111..."}'
→ 200 {"msg":"Sucesso","enrollment_id":2}

# Checkout SEM enviar senha alguma — sucesso (deveria falhar)
curl -X POST /api/checkout -d '{"usr":"Attacker2","eml":"leonan@fullcycle.com.br","c_id":1,"card":"4111..."}'
→ 200 {"msg":"Sucesso","enrollment_id":3}

# GET /api/admin/financial-report confirma: Leonan aparece com 2 matrículas em
# "Clean Architecture" (1 legítima do seed + 1 fraudulenta) e 1 em "Docker",
# revenue de "Clean Architecture" dobrado (997 → 1994) — tudo atribuído à
# conta dele sem que ele tenha feito nada.
```

**Impacto:**
- Qualquer pessoa que conheça o email de um usuário cadastrado pode gerar matrículas/pagamentos/entradas de audit log em nome dele, sem credencial alguma
- Corrompe integridade financeira (`financial-report` conta receita/matrículas fraudulentas como reais)
- Audit log (`audit_logs`) passa a atribuir ações a usuários que nunca as realizaram — o próprio mecanismo de rastreabilidade fica não confiável
- Efeito colateral: permite enumeração de emails cadastrados (comportamento de erro/sucesso difere entre email existente vs novo sem senha)

**Refatoração Proposta:**
```javascript
const bcrypt = require('bcrypt');

async function checkout({ usr, eml, pwd, c_id, card }) {
    if (!usr || !eml || !pwd || !c_id || !card) {
        throw new ValidationError('Bad Request');
    }

    const course = await courseModel.findActiveById(c_id);
    if (!course) {
        throw new NotFoundError('Curso não encontrado');
    }

    let user = await userModel.findByEmail(eml);
    if (!user) {
        const hash = await bcrypt.hash(pwd, 10);
        const userId = await userModel.create(usr, eml, hash);
        user = { id: userId };
    } else {
        const senhaValida = await bcrypt.compare(pwd, user.pass);
        if (!senhaValida) {
            throw new ValidationError('Credenciais inválidas');
        }
    }
    // ... resto do fluxo inalterado
}
```

**Por quê:** `pwd` já era coletado e já existia `bcrypt` importado no controller — a peça que faltava era só a chamada de comparação no branch de usuário existente. O bug não é estrutural (falta um endpoint de auth inteiro), é uma linha de verificação que nunca foi escrita, mascarada pelo fato de o campo `pwd` já "parecer" estar sendo tratado (é usado no branch de criação).

**Nota de processo (por que escapou da self-verification v3.1):** a suíte funcional daquela rodada testou "checkout sem `pwd` criando usuário **novo**" (400 esperado, correto) e "injeção de campos de privilégio no payload" (bloqueado pelo destructuring), mas não testou o cenário "checkout com `pwd` incorreto/ausente para um email **já cadastrado**" — o teste cobria o branch de criação, não o branch de usuário existente. Reforça a mesma lição do Padrão 19: toda ramificação condicional relevante de um fluxo sensível precisa de teste funcional próprio, não só o caminho mais óbvio.

---

## Verificações Sem Achados

| Padrão | Resultado |
|---|---|
| SQL Injection | Nenhuma ocorrência — todas as queries parametrizadas |
| Hardcoded Secrets | Nenhuma ocorrência — `.env` gitignored, `config.js` usa `process.env` |
| Dangerous Admin Endpoint | Nenhuma ocorrência |
| Broken Access Control (rotas admin) | Nenhuma ocorrência — `adminRequired` protege `DELETE /api/users/:id` e `GET /api/admin/financial-report`, fail-closed |
| Weak Password Hashing | Nenhuma ocorrência (bcrypt cost 10) |
| God Class | Nenhuma ocorrência (maior arquivo: 51 linhas) |
| N+1 Queries | Nenhuma ocorrência (`report.js` usa 1 query com JOINs) |
| Global State Mutável | Nenhuma ocorrência (`_db`/`_initialized` com guard) |
| Code Duplication | Nenhuma ocorrência relevante |
| Secrets Expostas em Responses | Nenhuma ocorrência |
| Logs Sensíveis (PII) | Nenhuma ocorrência (`maskCardNumber` aplicado) |
| Exception Detail Leakage | Nenhuma ocorrência |
| Magic Strings/Numbers | Nenhuma ocorrência (`paymentStatus`/`cardBrandPrefixes` centralizados) |
| Monolithic Architecture | N/A — MVC completo |
| Configuração Morta | Nenhuma ocorrência |
| Regressão de Refatoração | Nenhuma ocorrência |
| **APIs Deprecated (Padrão 20, generalizado)** | **Nenhuma ocorrência** — sem uso de APIs Node/Express/bcrypt/dotenv deprecated |

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Adicionar verificação de senha (`bcrypt.compare`) para usuários existentes no checkout, lançando `ValidationError`/401 em caso de falha
2. Tornar `pwd` obrigatório em toda chamada de checkout (novo cadastro já exigia; passa a ser exigido também para usuário existente)
3. Teste funcional cobrindo especificamente o branch de usuário existente com senha errada/ausente
4. Validação de startup + boot da aplicação

**Confirmar refatoração na Fase 3? (y/n)**
