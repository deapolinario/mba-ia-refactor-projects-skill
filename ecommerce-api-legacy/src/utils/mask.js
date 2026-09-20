/**
 * v2.2 - mascarar dados sensíveis antes de logar (fix Logs Sensíveis/PII).
 */
function maskCardNumber(cardNumber) {
    if (!cardNumber || cardNumber.length < 8) return '****';
    return cardNumber.slice(0, 4) + '*'.repeat(cardNumber.length - 8) + cardNumber.slice(-4);
}

module.exports = { maskCardNumber };
