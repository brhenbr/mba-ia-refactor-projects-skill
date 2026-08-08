const express = require('express');
const { validateLogin } = require('../validators/authValidator');

function createAuthRoutes({ authService }) {
    const router = express.Router();

    router.post('/login', async (req, res, next) => {
        try {
            const { email, password } = validateLogin(req.body);
            const result = await authService.login(email, password);
            res.status(200).json(result);
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { createAuthRoutes };
