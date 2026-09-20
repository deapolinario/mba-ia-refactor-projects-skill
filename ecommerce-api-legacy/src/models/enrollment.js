const { getDb, dbAll, dbRun } = require('../database');

async function create(userId, courseId) {
    const result = await dbRun(getDb(), 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return result.lastID;
}

/**
 * v2.2 - fix de integridade referencial (achado fora do catálogo formal,
 * detectado na auditoria manual): antes, deletar um usuário deixava
 * enrollments/payments órfãos. Agora a exclusão em cascata é explícita.
 */
async function findIdsByUserId(userId) {
    const rows = await dbAll(getDb(), 'SELECT id FROM enrollments WHERE user_id = ?', [userId]);
    return rows.map((r) => r.id);
}

async function deleteByUserId(userId) {
    return dbRun(getDb(), 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

module.exports = { create, findIdsByUserId, deleteByUserId };
