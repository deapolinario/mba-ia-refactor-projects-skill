const { getDb, dbRun } = require('../database');

async function record(action) {
    return dbRun(getDb(), "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

module.exports = { record };
