const { getDb, dbGet, dbRun } = require('../database');

async function findByEmail(email) {
    return dbGet(getDb(), 'SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

async function create(name, email, passwordHash) {
    const result = await dbRun(getDb(), 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return result.lastID;
}

async function deleteById(id) {
    return dbRun(getDb(), 'DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, create, deleteById };
