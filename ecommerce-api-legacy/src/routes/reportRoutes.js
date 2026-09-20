const express = require('express');
const reportController = require('../controllers/reportController');
const { adminRequired } = require('../middleware/auth');

const router = express.Router();

// v2.2: agora protegido por adminRequired (era acessível sem autenticação)
router.get('/api/admin/financial-report', adminRequired, async (req, res) => {
    try {
        const report = await reportController.getFinancialReport();
        res.json(report);
    } catch (err) {
        console.error('Erro ao gerar relatório financeiro:', err.message);
        res.status(500).send('Erro interno do servidor');
    }
});

module.exports = router;
