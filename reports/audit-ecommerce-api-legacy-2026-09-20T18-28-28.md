# Relatório de Auditoria - ecommerce-api-legacy

**Data:** 2026-09-20
**Stack:** Node.js + Express 4.18 + SQLite (in-memory)
**Domínio:** LMS (Learning Management System) com fluxo de checkout — users, courses, enrollments, payments, audit_logs

**Contexto:** este projeto já passou por um ciclo de refatoração (commits `9e51c29`, `2352f78`), anterior à adição do Padrão 19 (v3.1) e do teste funcional de autorização à skill. Esta auditoria releu o código do zero — 17 arquivos em `src/` — como uma Fase 2 nova, sem assumir que o trabalho anterior está correto.

---

## Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 1 achado
- **LOW:** 1 achado
- **Total:** 2 achados

Estrutura MVC (`config/`, `models/`, `routes/`, `controllers/`, `middleware/`, `utils/`) já implementada e consistente. SQL parametrizado em 100% das queries. Senhas com bcrypt. `.env` fora do git. Rotas administrativas (`DELETE /api/users/:id`, `GET /api/admin/financial-report`) protegidas por `adminRequired`. Report financeiro já usa JOIN único (sem N+1). Cartão mascarado em log.

**Padrão 19 (Privilege Escalation) — verificado estruturalmente:** não há endpoint de update/patch de usuário, nem coluna `role`/`is_admin` no schema, nem campo de privilégio aceito via payload em `POST /api/checkout` — `price` e `payment_status` são sempre resolvidos no servidor (`courseModel.findActiveById`, prefixo do cartão), nunca lidos do body do cliente. Não há, portanto, o vetor estrutural do Padrão 19 encontrado nos outros dois projetos. **Isso não substitui o teste funcional obrigatório da Fase 3 (passo 7.b2)** — será confirmado lá com requisições reais.

---

## Findings Detalhados

### [MEDIUM] Credencial Padrão Previsível no Fallback de Senha do Checkout

**Arquivo:** `src/controllers/checkoutController.js` (Linha: 26)

**Descrição:**
Em `checkout()`, quando o cliente não envia `pwd`, a aplicação cria a conta do usuário com a senha fixa `'123456'` (hasheada com bcrypt, mas o *valor* é sempre o mesmo e previsível). Não é um problema de hashing (bcrypt está correto) — é uma credencial padrão adivinhável atribuída silenciosamente sem o conhecimento do usuário.

**Código Problemático:**
```javascript
let user = await userModel.findByEmail(eml);
if (!user) {
    const hash = await bcrypt.hash(pwd || '123456', 10);
    const userId = await userModel.create(usr, eml, hash);
    user = { id: userId };
}
```

**Impacto:**
- Qualquer conta criada via checkout sem `pwd` explícito fica com senha `123456` — trivialmente adivinhável
- Hoje não há endpoint de login na aplicação, então não é explorável *neste momento*, mas é uma bomba-relógio: no dia em que um endpoint de autenticação for adicionado (evolução natural de um LMS), toda conta criada por este caminho estará comprometida por padrão
- Silencioso: o usuário não é informado de que uma senha previsível foi definida em seu nome

**Refatoração Proposta:**
```javascript
const crypto = require('crypto');

// ...
let user = await userModel.findByEmail(eml);
if (!user) {
    if (!pwd) {
        throw new ValidationError('Senha é obrigatória para novo cadastro');
    }
    const hash = await bcrypt.hash(pwd, 10);
    const userId = await userModel.create(usr, eml, hash);
    user = { id: userId };
}
```

**Por quê:**
Exigir a senha explicitamente no cadastro (em vez de inventar uma) elimina a credencial previsível sem adicionar complexidade — o campo já existe no payload (`pwd`), só não era obrigatório.

---

### [LOW] Configuração Morta / Semi-Morta

**Arquivo:** `src/config.js` (Linhas: 4, 15)

**Descrição:**
`config.dbPass` (de `DB_PASS`) é carregado do ambiente e incluído na lista de variáveis obrigatórias em produção (`validate()`), mas **nunca é referenciado em nenhum outro lugar do código** — o banco é SQLite em memória (`sqlite3.Database(':memory:')` em `src/database.js`) e não usa credenciais. É config morta: existe, é até exigida em produção, mas não tem ponto de uso real.

`config.paymentGatewayKey` está em situação parecida, mas parcial: é referenciado (`checkoutController.js:32`), porém apenas para decidir qual texto imprimir no log (`'***'` vs `'(não configurada)'`) — nunca é de fato enviado a um gateway de pagamento real (o "processamento" é só `card.startsWith(config.cardBrandPrefixes.visa)`). Uso decorativo, não funcional.

**Código Problemático:**
```javascript
// config.js
const config = {
    dbPass: process.env.DB_PASS,               // nunca lido fora deste arquivo
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,  // só vira '***' num log
    ...
};

function validate() {
    const required = ['dbPass', 'paymentGatewayKey']; // dbPass exigido sem uso real
    ...
}
```

**Impacto:**
- Falsa sensação de que `DB_PASS` é uma configuração relevante de segurança/infra
- Exigir `dbPass` em produção (`validate()`) pode bloquear deploy por uma variável que não faz nada
- Deixa dúvida para o próximo desenvolvedor: "isso é usado em algum lugar que não vi?"

**Refatoração Proposta:**
```javascript
// config.js — remover dbPass por completo (banco não usa credenciais)
const config = {
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    port: parseInt(process.env.PORT, 10) || 3000,
    adminToken: process.env.ADMIN_TOKEN,
    paymentStatus: { PAID: 'PAID', DENIED: 'DENIED' },
    cardBrandPrefixes: { visa: '4' }
};

function validate() {
    const required = ['paymentGatewayKey'];
    ...
}
```
Se o gateway de pagamento real vier a ser integrado, `paymentGatewayKey` passa a ter uso funcional (enviado numa chamada HTTP) em vez de só condicionar uma string de log.

**Por quê:**
Config sem ponto de uso é dívida técnica silenciosa — cresce até alguém remover a coisa errada achando que está "limpando código morto" e quebrar algo que na verdade dependia dela. Consistente com o Padrão 18 do catálogo (achado semelhante já foi corrigido neste mesmo projeto no commit `2352f78`, que removeu `dbUser`/`smtpUser` — `dbPass` ficou para trás).

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Tornar `pwd` obrigatório no cadastro via checkout (remove fallback previsível)
2. Remover `dbPass`/`DB_PASS` de `config.js`, `.env` e da lista `required` de `validate()`
3. Validação de startup (`node --check` + boot manual)
4. **Self-verification obrigatória (v3.1):** reler o código do zero, rodar o checklist de 19 padrões de novo, e **testar funcionalmente** os endpoints de escrita (`POST /api/checkout`, `DELETE /api/users/:id`) com requisições reais para confirmar que não há Padrão 19 (o achado estrutural acima é só a metade da verificação)

**Confirmar refatoração na Fase 3? (y/n)**
