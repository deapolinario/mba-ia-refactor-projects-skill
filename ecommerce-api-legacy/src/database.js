const sqlite3 = require('sqlite3').verbose();

let _db = null;
let _initialized = false;

/**
 * Wrapper Promise em torno do sqlite3 (callback-based). Preserva o `this`
 * do callback de `run` (contém lastID/changes), que util.promisify perderia.
 */
function dbGet(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function dbAll(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

function dbRun(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

async function setupSchema(db) {
    await dbRun(db, 'CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await dbRun(db, 'CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await dbRun(db, 'CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
    await dbRun(db, 'CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
    await dbRun(db, 'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seed(db, bcrypt) {
    const hash = await bcrypt.hash('123', 10);
    await dbRun(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', hash]);
    await dbRun(db, "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
    await dbRun(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await dbRun(db, "INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

/**
 * Inicializa o banco uma única vez (v2.2 - evita a regressão de setup
 * rodando por-request encontrada no code-smells-project). Chamadas
 * subsequentes reusam a mesma conexão sem repetir schema/seed.
 */
async function initDb(bcrypt) {
    if (_initialized) return _db;
    _db = new sqlite3.Database(':memory:');
    await setupSchema(_db);
    await seed(_db, bcrypt);
    _initialized = true;
    return _db;
}

function getDb() {
    if (!_db) {
        throw new Error('Database não inicializado — chame initDb() antes de getDb()');
    }
    return _db;
}

module.exports = { initDb, getDb, dbGet, dbAll, dbRun };
