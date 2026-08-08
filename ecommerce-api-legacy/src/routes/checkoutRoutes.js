const express = require('express');
const { validateCheckout } = require('../validators/checkoutValidator');

function createCheckoutRoutes({ checkoutService }) {
    const router = express.Router();

    router.post('/checkout', async (req, res, next) => {
        try {
            const data = validateCheckout(req.body);
            const result = await checkoutService.checkout(data);
            res.status(200).json(result);
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { createCheckoutRoutes };
