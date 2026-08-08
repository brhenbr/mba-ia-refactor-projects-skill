require('dotenv').config();

function required(name, fallbackForTest) {
    const value = process.env[name];
    if (value) return value;

    if (process.env.NODE_ENV === 'test' && fallbackForTest !== undefined) {
        return fallbackForTest;
    }

    throw new Error(`Missing required environment variable: ${name}`);
}

const config = {
    env: process.env.NODE_ENV || 'development',
    port: parseInt(process.env.PORT || '3000', 10),
    jwtSecret: required('JWT_SECRET', 'test-secret-key-for-automated-tests-only'),
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '1h',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '10', 10),
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || null,
};

module.exports = config;
