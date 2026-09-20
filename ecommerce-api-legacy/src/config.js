require('dotenv').config();

const config = {
    dbUser: process.env.DB_USER,
    dbPass: process.env.DB_PASS,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
    smtpUser: process.env.SMTP_USER,
    port: parseInt(process.env.PORT, 10) || 3000,
    adminToken: process.env.ADMIN_TOKEN,

    // Domínio (v2.2 - extraído de magic strings do AppManager original)
    paymentStatus: { PAID: 'PAID', DENIED: 'DENIED' },
    cardBrandPrefixes: { visa: '4' }
};

function validate() {
    const required = ['dbPass', 'paymentGatewayKey'];
    const missing = required.filter((key) => !config[key]);
    if (missing.length > 0 && process.env.NODE_ENV === 'production') {
        throw new Error(`Variáveis obrigatórias não definidas em produção: ${missing.join(', ')}`);
    }
}

module.exports = { config, validate };
