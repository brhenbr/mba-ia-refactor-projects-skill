class AppError extends Error {
    constructor(message, statusCode) {
        super(message);
        this.name = this.constructor.name;
        this.statusCode = statusCode;
    }
}

class ValidationError extends AppError {
    constructor(message, details = null) {
        super(message, 400);
        this.details = details;
    }
}

class UnauthorizedError extends AppError {
    constructor(message = 'Não autenticado') {
        super(message, 401);
    }
}

class ForbiddenError extends AppError {
    constructor(message = 'Sem permissão') {
        super(message, 403);
    }
}

class NotFoundError extends AppError {
    constructor(message = 'Recurso não encontrado') {
        super(message, 404);
    }
}

class ConflictError extends AppError {
    constructor(message = 'Conflito de dados') {
        super(message, 409);
    }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400);
    }
}

module.exports = {
    AppError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    PaymentDeclinedError,
};
