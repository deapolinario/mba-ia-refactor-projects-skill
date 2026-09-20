const { config } = require('../config');

/**
 * Guard mínimo para rotas administrativas/sensíveis (v2.2 - Broken Access
 * Control fix). Exige header X-Admin-Token igual ao ADMIN_TOKEN configurado.
 */
function adminRequired(req, res, next) {
    const token = req.headers['x-admin-token'];
    if (!config.adminToken || token !== config.adminToken) {
        return res.status(401).json({ erro: 'Não autorizado' });
    }
    next();
}

module.exports = { adminRequired };
