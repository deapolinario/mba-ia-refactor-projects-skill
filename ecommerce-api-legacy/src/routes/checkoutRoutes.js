const express = require('express');
const checkoutController = require('../controllers/checkoutController');

const router = express.Router();

router.post('/api/checkout', async (req, res) => {
    try {
        const result = await checkoutController.checkout(req.body);
        res.status(200).json(result);
    } catch (err) {
        if (err instanceof checkoutController.ValidationError) {
            return res.status(400).send(err.message);
        }
        if (err instanceof checkoutController.NotFoundError) {
            return res.status(404).send(err.message);
        }
        if (err instanceof checkoutController.PaymentDeniedError) {
            return res.status(400).send(err.message);
        }
        if (err instanceof checkoutController.AuthenticationError) {
            return res.status(401).send(err.message);
        }
        console.error('Erro no checkout:', err.message);
        res.status(500).send('Erro interno do servidor');
    }
});

module.exports = router;
