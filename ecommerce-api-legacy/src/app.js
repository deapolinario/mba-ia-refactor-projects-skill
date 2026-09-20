const express = require('express');
const bcrypt = require('bcrypt');
const { config, validate } = require('./config');
const { initDb } = require('./database');
const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');

validate();

const app = express();
app.use(express.json());

app.use(checkoutRoutes);
app.use(reportRoutes);
app.use(userRoutes);

async function start() {
    await initDb(bcrypt);
    app.listen(config.port, () => {
        console.log(`Servidor rodando na porta ${config.port}...`);
    });
}

if (require.main === module) {
    start();
}

module.exports = { app, start };
