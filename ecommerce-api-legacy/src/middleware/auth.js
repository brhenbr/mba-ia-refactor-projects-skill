const jwt = require('jsonwebtoken');
const config = require('../config');
const { UnauthorizedError, ForbiddenError } = require('../exceptions');

function authenticate(req, res, next) {
    const header = req.headers.authorization;
    const token = header && header.startsWith('Bearer ') ? header.slice(7) : null;

    if (!token) {
        return next(new UnauthorizedError('Token ausente'));
    }

    try {
        const payload = jwt.verify(token, config.jwtSecret);
        req.user = { id: payload.sub, role: payload.role };
        return next();
    } catch (err) {
        return next(new UnauthorizedError('Token inválido ou expirado'));
    }
}

function requireAdmin(req, res, next) {
    if (!req.user || req.user.role !== 'admin') {
        return next(new ForbiddenError('Acesso restrito a administradores'));
    }
    return next();
}

module.exports = { authenticate, requireAdmin };
