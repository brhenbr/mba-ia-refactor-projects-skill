const Joi = require('joi');
const { ValidationError } = require('../exceptions');

const schema = Joi.object({
    email: Joi.string().trim().email().required(),
    password: Joi.string().min(1).max(72).required(),
});

function validateLogin(payload) {
    const { error, value } = schema.validate(payload, {
        abortEarly: false,
        stripUnknown: true,
    });

    if (error) {
        throw new ValidationError(
            'Credenciais inválidas',
            error.details.map((d) => d.message)
        );
    }

    return value;
}

module.exports = { validateLogin };
