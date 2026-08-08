const Joi = require('joi');
const { ValidationError } = require('../exceptions');

const schema = Joi.object({
    name: Joi.string().trim().min(2).max(120).required(),
    email: Joi.string().trim().email().required(),
    password: Joi.string().min(6).max(72).optional(),
    courseId: Joi.number().integer().positive().required(),
    cardNumber: Joi.string()
        .pattern(/^\d{13,19}$/)
        .required()
        .messages({ 'string.pattern.base': 'Número de cartão inválido' }),
});

function validateCheckout(payload) {
    const { error, value } = schema.validate(payload, {
        abortEarly: false,
        stripUnknown: true,
    });

    if (error) {
        throw new ValidationError(
            'Dados de checkout inválidos',
            error.details.map((d) => d.message)
        );
    }

    return value;
}

module.exports = { validateCheckout };
