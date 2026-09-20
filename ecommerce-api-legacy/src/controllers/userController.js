const userModel = require('../models/user');
const enrollmentModel = require('../models/enrollment');
const paymentModel = require('../models/payment');

/**
 * v2.2 - fix de integridade referencial: antes, deletar um usuário deixava
 * enrollments/payments órfãos no banco (achado fora do catálogo formal,
 * detectado na auditoria manual do relatório de 2026-09-20T10-21-41).
 * Agora a exclusão em cascata é explícita, na ordem correta de FKs.
 */
async function deleteUser(id) {
    const enrollmentIds = await enrollmentModel.findIdsByUserId(id);
    await paymentModel.deleteByEnrollmentIds(enrollmentIds);
    await enrollmentModel.deleteByUserId(id);
    await userModel.deleteById(id);
}

module.exports = { deleteUser };
