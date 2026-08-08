const { AppError } = require('../exceptions');
const logger = require('../utils/logger');

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        if (err.statusCode >= 500) {
            logger.error(err.message, { stack: err.stack });
        }
        return res.status(err.statusCode).json({
            error: err.message,
            ...(err.details ? { details: err.details } : {}),
        });
    }

    logger.error('Erro não tratado', { message: err.message, stack: err.stack });
    return res.status(500).json({ error: 'Erro interno' });
}

function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

module.exports = { errorHandler, notFoundHandler };
