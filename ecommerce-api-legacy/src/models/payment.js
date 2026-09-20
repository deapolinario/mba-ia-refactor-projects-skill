const { getDb, dbRun } = require('../database');

async function create(enrollmentId, amount, status) {
    const result = await dbRun(
        getDb(),
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]
    );
    return result.lastID;
}

async function deleteByEnrollmentIds(enrollmentIds) {
    if (enrollmentIds.length === 0) return;
    const placeholders = enrollmentIds.map(() => '?').join(',');
    return dbRun(getDb(), `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`, enrollmentIds);
}

module.exports = { create, deleteByEnrollmentIds };
