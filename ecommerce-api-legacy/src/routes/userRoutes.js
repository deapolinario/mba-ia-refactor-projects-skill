const express = require('express');
const userController = require('../controllers/userController');
const { adminRequired } = require('../middleware/auth');

const router = express.Router();

// v2.2: agora protegido por adminRequired (era acessível sem autenticação)
// e faz cascade delete (era: "deletado, mas ficou sujo no banco")
router.delete('/api/users/:id', adminRequired, async (req, res) => {
    try {
        await userController.deleteUser(req.params.id);
        res.json({ mensagem: 'Usuário e dados relacionados removidos com sucesso' });
    } catch (err) {
        console.error('Erro ao deletar usuário:', err.message);
        res.status(500).send('Erro interno do servidor');
    }
});

module.exports = router;
