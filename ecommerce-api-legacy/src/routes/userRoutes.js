const express = require('express');
const { authenticate, requireAdmin } = require('../middleware/auth');
const { ValidationError } = require('../exceptions');

function createUserRoutes({ userService }) {
    const router = express.Router();

    router.delete('/users/:id', authenticate, requireAdmin, async (req, res, next) => {
        try {
            const id = Number(req.params.id);
            if (!Number.isInteger(id) || id <= 0) {
                throw new ValidationError('Id de usuário inválido');
            }

            await userService.deleteUser(id);
            res.status(200).json({ message: 'Usuário deletado' });
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { createUserRoutes };
