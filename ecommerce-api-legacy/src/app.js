const express = require('express');

const { UserRepository } = require('./repositories/userRepository');
const { CourseRepository } = require('./repositories/courseRepository');
const { EnrollmentRepository } = require('./repositories/enrollmentRepository');
const { PaymentRepository } = require('./repositories/paymentRepository');
const { AuditLogRepository } = require('./repositories/auditLogRepository');
const { ReportRepository } = require('./repositories/reportRepository');

const { AuthService } = require('./services/authService');
const { CheckoutService } = require('./services/checkoutService');
const { UserService } = require('./services/userService');
const { ReportService } = require('./services/reportService');

const { Cache } = require('./utils/cache');

const { createAuthRoutes } = require('./routes/authRoutes');
const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { createAdminRoutes } = require('./routes/adminRoutes');
const { createUserRoutes } = require('./routes/userRoutes');

const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

/**
 * Wires repositories -> services -> routes for a given db instance.
 * Kept separate from server.js so tests can build an app around an
 * isolated in-memory database without binding a port.
 */
function createApp(db) {
    const userRepository = new UserRepository(db);
    const courseRepository = new CourseRepository(db);
    const enrollmentRepository = new EnrollmentRepository(db);
    const paymentRepository = new PaymentRepository(db);
    const auditLogRepository = new AuditLogRepository(db);
    const reportRepository = new ReportRepository(db);
    const cache = new Cache();

    const authService = new AuthService(userRepository);
    const checkoutService = new CheckoutService({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        cache,
    });
    const userService = new UserService(userRepository);
    const reportService = new ReportService(reportRepository);

    const app = express();
    app.use(express.json());

    app.get('/health', (req, res) => res.status(200).json({ status: 'ok' }));

    app.use('/api/auth', createAuthRoutes({ authService }));
    app.use('/api', createCheckoutRoutes({ checkoutService }));
    app.use('/api', createAdminRoutes({ reportService }));
    app.use('/api', createUserRoutes({ userService }));

    app.use(notFoundHandler);
    app.use(errorHandler);

    return app;
}

module.exports = { createApp };
