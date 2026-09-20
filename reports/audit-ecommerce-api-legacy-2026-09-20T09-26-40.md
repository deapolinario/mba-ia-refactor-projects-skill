# Relatório de Auditoria - ecommerce-api-legacy

**Data:** 2026-09-20 09:26:40
**Stack:** Node.js 14+ + Express 4.x + SQLite (in-memory)
**Domínio:** E-commerce/LMS API (users, enrollments, payments, checkout)

---

## Resumo Executivo

- **CRITICAL:** 7 achados
- **HIGH:** 3 achados
- **MEDIUM:** 2 achados
- **Total:** 12 achados

---

## Findings Detalhados

### [CRITICAL] Hardcoded Credenciais de Sistemas Externos

**Arquivo:** `utils.js` (Linhas: 2-6)

**Descrição:**
Todas as credenciais de sistemas externos embarcadas no código-fonte sem criptografia ou proteção.

**Código Problemático:**
```javascript
const dbUser = "admin";
const dbPass = "admin123";
const paymentGatewayKey = "sk-test-123456789";
const smtpUser = "noreply@loja.com";
const smtpPass = "smtp-password-123";
```

**Impacto:**
- Comprometimento de sistemas externos
- Acesso não autorizado a banco de dados
- Acesso a gateway de pagamento
- Acesso a servidor de email

**Refatoração Proposta:**
```javascript
// config.js
module.exports = {
    DB_USER: process.env.DB_USER,
    DB_PASS: process.env.DB_PASS,
    PAYMENT_GATEWAY_KEY: process.env.PAYMENT_GATEWAY_KEY,
    SMTP_USER: process.env.SMTP_USER,
    SMTP_PASS: process.env.SMTP_PASS
};

// .env
DB_USER=admin
DB_PASS=admin123
PAYMENT_GATEWAY_KEY=sk-test-123456789
SMTP_USER=noreply@loja.com
SMTP_PASS=smtp-password-123
```

---

### [CRITICAL] Fake Cryptography (Base64)

**Arquivo:** `utils.js` (Linhas: 17-23)

**Descrição:**
Função `badCrypto()` usa apenas Base64, não é criptografia real. Substring repetida 10.000x produz "ba" repetido.

**Código Problemático:**
```javascript
function badCrypto(data) {
    return Buffer.from(data).toString('base64');
}
```

**Impacto:**
- Dados criptografados são trivialmente descriptografáveis
- Qualquer pessoa pode recuperar dados em segundos
- Falsa sensação de segurança

**Refatoração Proposta:**
```javascript
const crypto = require('crypto');

function encryptData(data) {
    const key = process.env.ENCRYPTION_KEY;
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', Buffer.from(key), iv);
    
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    return iv.toString('hex') + ':' + encrypted;
}

function decryptData(encryptedData) {
    const key = process.env.ENCRYPTION_KEY;
    const parts = encryptedData.split(':');
    const iv = Buffer.from(parts[0], 'hex');
    const decipher = crypto.createDecipheriv('aes-256-cbc', Buffer.from(key), iv);
    
    let decrypted = decipher.update(parts[1], 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
}
```

---

### [CRITICAL] Senhas em Texto Plano

**Arquivo:** `AppManager.js` (Linha: 18)

**Descrição:**
Usuários criados com senhas em texto plano sem hash.

**Código Problemático:**
```javascript
// AppManager.js linha 18
const user = { id: 1, name: 'admin', password: 'admin123' };
db.run("INSERT INTO users VALUES (?, ?, ?)", [1, 'admin', 'admin123']);
```

**Impacto:**
- Breach de contas de usuário
- Acesso não autorizado
- Violação de LGPD/GDPR

**Refatoração Proposta:**
```javascript
const bcrypt = require('bcrypt');

async function createUser(name, password) {
    const hashedPassword = await bcrypt.hash(password, 10);
    db.run(
        "INSERT INTO users (name, password) VALUES (?, ?)",
        [name, hashedPassword]
    );
}

async function verifyPassword(inputPassword, hashedPassword) {
    return await bcrypt.compare(inputPassword, hashedPassword);
}
```

---

### [CRITICAL] Validação de Cartão Fraca

**Arquivo:** `AppManager.js` (Linha: 46)

**Descrição:**
Validação de cartão de crédito apenas por primeiro dígito. Qualquer cartão começando com "4" é aceito.

**Código Problemático:**
```javascript
const isValid = cc.startsWith("4") ? "PAID" : "DENIED";
```

**Impacto:**
- Fraude de pagamento
- Qualquer cartão falso começando com 4 é aceito
- Violação de PCI DSS

**Refatoração Proposta:**
```javascript
const Stripe = require('stripe');
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

async function processPayment(cardToken, amount) {
    try {
        const charge = await stripe.charges.create({
            amount: amount * 100,
            currency: 'usd',
            source: cardToken
        });
        return { status: 'PAID', chargeId: charge.id };
    } catch (error) {
        return { status: 'DENIED', error: error.message };
    }
}
```

---

### [CRITICAL] God Class - AppManager.js

**Arquivo:** `AppManager.js` (Linhas: 4-142)

**Descrição:**
Classe única fazendo tudo: inicialização de BD, setup de routes, checkout, relatórios, delete - todas as responsabilidades.

**Padrão Problemático:**
- 142 linhas em uma única classe
- Múltiplas responsabilidades misturadas
- Impossível testar em isolamento

**Impacto:**
- Impossível testar cada responsabilidade
- Qualquer mudança afeta tudo
- Difícil de manter e reutilizar

**Refatoração Proposta:**
```javascript
// models/User.js
class User {
    constructor(id, name, email) {...}
    save() {...}
}

// controllers/PaymentController.js
class PaymentController {
    static async processCheckout(userId, amount) {...}
}

// controllers/ReportController.js
class ReportController {
    static async generateReport() {...}
}

// routes/index.js
app.post('/checkout', PaymentController.processCheckout);
app.get('/report', ReportController.generateReport);
```

---

### [CRITICAL] Senhas Default Hardcoded

**Arquivo:** `AppManager.js` (Linha: 68)

**Descrição:**
Senha padrão "123456" usada quando nenhuma é fornecida.

**Código Problemático:**
```javascript
badCrypto(p || "123456")
```

**Impacto:**
- Bypass de autenticação
- Qualquer usuário pode logar com "123456"

**Refatoração Proposta:**
```javascript
// Exigir senha sempre
if (!password || password.length < 8) {
    throw new Error('Senha deve ter no mínimo 8 caracteres');
}

const hashedPassword = await bcrypt.hash(password, 10);
```

---

### [CRITICAL] Callback Hell - 5 Níveis de Aninhamento

**Arquivo:** `AppManager.js` (Linhas: 37-78)

**Descrição:**
Aninhamento profundo de 5 níveis de callbacks, tornando código ilegível e error handling quebrado.

**Código Problemático:**
```javascript
db.all("SELECT * FROM users", (err, users) => {
    if (err) res.json({ error: err });
    else {
        users.forEach(user => {
            db.all("SELECT * FROM enrollments WHERE userId = ?", [user.id], (err, enrollments) => {
                if (err) res.json({ error: err });
                else {
                    enrollments.forEach(enrollment => {
                        db.get("SELECT * FROM courses WHERE id = ?", [enrollment.courseId], (err, course) => {
                            // ... 5 níveis!
                        });
                    });
                }
            });
        });
    }
});
```

**Impacto:**
- Código ilegível
- Difícil de debugar
- Error handling quebrado
- Memory leaks possíveis

**Refatoração Proposta:**
```javascript
// Usar async/await
async function getFullUserData() {
    try {
        const users = await db.all("SELECT * FROM users");
        
        for (const user of users) {
            const enrollments = await db.all(
                "SELECT * FROM enrollments WHERE userId = ?",
                [user.id]
            );
            
            for (const enrollment of enrollments) {
                const course = await db.get(
                    "SELECT * FROM courses WHERE id = ?",
                    [enrollment.courseId]
                );
                // ... muito mais limpo!
            }
        }
    } catch (error) {
        console.error(error);
    }
}
```

---

### [HIGH] Global State Mutável

**Arquivo:** `utils.js` (Linhas: 9-10)

**Descrição:**
Variáveis globais `globalCache` e `totalRevenue` compartilhadas entre requests.

**Código Problemático:**
```javascript
let globalCache = {};
let totalRevenue = 0;
```

**Impacto:**
- Vazamento de dados entre usuários
- Comportamento impredizível
- Memory leaks

**Refatoração Proposta:**
```javascript
// Usar Map com escopo de request
class RequestContext {
    constructor() {
        this.cache = new Map();
        this.revenue = 0;
    }
}

// Middleware
app.use((req, res, next) => {
    req.context = new RequestContext();
    next();
});
```

---

### [HIGH] Data Integrity - Orfanagem de Registros

**Arquivo:** `AppManager.js` (Linhas: 131-137)

**Descrição:**
DELETE de usuário sem cascade deixa matrículas e pagamentos órfãos.

**Código Problemático:**
```javascript
db.run("DELETE FROM users WHERE id = ?", [userId]);
// Não deleta enrollments e payments associados!
```

**Impacto:**
- Referências inválidas
- Relatórios quebrados
- Inconsistência de dados

**Refatoração Proposta:**
```javascript
// Usar transação com cascade
db.serialize(() => {
    db.run("DELETE FROM payments WHERE userId = ?", [userId]);
    db.run("DELETE FROM enrollments WHERE userId = ?", [userId]);
    db.run("DELETE FROM users WHERE id = ?", [userId]);
});
```

---

### [HIGH] Log de Credencial

**Arquivo:** `AppManager.js` (Linha: 45)

**Descrição:**
Número de cartão exposto em logs.

**Código Problemático:**
```javascript
console.log(`Processando cartão ${cc}...`);  // Expõe CC!
```

**Impacto:**
- Violação de PCI DSS
- Vazamento de dados sensíveis em logs

**Refatoração Proposta:**
```javascript
// Mascarar dados sensíveis
const maskedCC = cc.substring(0, 4) + '*'.repeat(cc.length - 8) + cc.substring(cc.length - 4);
console.log(`Processando cartão ${maskedCC}...`);
```

---

### [MEDIUM] Error Handling Inconsistente

**Arquivo:** `AppManager.js` (Linhas: 35-78)

**Descrição:**
Mistura `res.status().send()`, `res.json()`, `res.send()` sem padrão consistente.

**Impacto:**
- Clientes não sabem formato da resposta
- Difícil de tratar erros

**Refatoração Proposta:**
```javascript
// Usar middleware de erro centralizado
app.use((err, req, res, next) => {
    res.status(err.status || 500).json({
        error: err.message,
        timestamp: new Date().toISOString()
    });
});
```

---

### [MEDIUM] Race Condition - Múltiplos db.all Aninhados

**Arquivo:** `AppManager.js` (Linhas: 83-129)

**Descrição:**
Múltiplos `db.all()` aninhados com contadores decrementados manualmente causam race conditions.

**Impacto:**
- Respostas fora de ordem
- Counts incorretos
- Comportamento impredizível

**Refatoração Proposta:**
```javascript
// Usar Promise.all
const results = await Promise.all([
    db.all("SELECT * FROM users"),
    db.all("SELECT * FROM enrollments"),
    db.all("SELECT * FROM payments")
]);
```

---

## Próximas Etapas

Total findings: **12 (7 CRITICAL, 3 HIGH, 2 MEDIUM)**

**Confirmar refatoração na Fase 3? (y/n)**
