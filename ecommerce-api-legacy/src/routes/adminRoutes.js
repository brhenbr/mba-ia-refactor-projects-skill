const express = require('express');
const { authenticate, requireAdmin } = require('../middleware/auth');

function createAdminRoutes({ reportService }) {
    const router = express.Router();

    router.get('/admin/financial-report', authenticate, requireAdmin, async (req, res, next) => {
        try {
            const report = await reportService.getFinancialReport();
            res.status(200).json(report);
        } catch (err) {
            next(err);
        }
    });

    return router;
}

module.exports = { createAdminRoutes };
