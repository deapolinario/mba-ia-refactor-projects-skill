const bcrypt = require('bcrypt');
const { config } = require('../config');
const courseModel = require('../models/course');
const userModel = require('../models/user');
const enrollmentModel = require('../models/enrollment');
const paymentModel = require('../models/payment');
const auditLogModel = require('../models/auditLog');
const { maskCardNumber } = require('../utils/mask');

class ValidationError extends Error {}
class NotFoundError extends Error {}
class PaymentDeniedError extends Error {}

async function checkout({ usr, eml, pwd, c_id, card }) {
    if (!usr || !eml || !c_id || !card) {
        throw new ValidationError('Bad Request');
    }

    const course = await courseModel.findActiveById(c_id);
    if (!course) {
        throw new NotFoundError('Curso não encontrado');
    }

    let user = await userModel.findByEmail(eml);
    if (!user) {
        if (!pwd) {
            throw new ValidationError('Senha é obrigatória para novo cadastro');
        }
        const hash = await bcrypt.hash(pwd, 10);
        const userId = await userModel.create(usr, eml, hash);
        user = { id: userId };
    }

    // v2.2: mascarar número de cartão em logs (era logado em texto plano)
    console.log(`Processando cartão ${maskCardNumber(card)} na chave ${config.paymentGatewayKey ? '***' : '(não configurada)'}`);
    const status = card.startsWith(config.cardBrandPrefixes.visa)
        ? config.paymentStatus.PAID
        : config.paymentStatus.DENIED;

    if (status === config.paymentStatus.DENIED) {
        throw new PaymentDeniedError('Pagamento recusado');
    }

    const enrollmentId = await enrollmentModel.create(user.id, c_id);
    await paymentModel.create(enrollmentId, course.price, status);
    await auditLogModel.record(`Checkout curso ${c_id} por ${user.id}`);

    return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

module.exports = { checkout, ValidationError, NotFoundError, PaymentDeniedError };
