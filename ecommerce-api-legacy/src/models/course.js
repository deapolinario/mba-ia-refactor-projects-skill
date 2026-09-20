const { getDb, dbGet } = require('../database');

async function findActiveById(id) {
    return dbGet(getDb(), 'SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

module.exports = { findActiveById };
