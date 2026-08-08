const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const config = require('../config');
const { UnauthorizedError } = require('../exceptions');

class AuthService {
    constructor(userRepository) {
        this.userRepository = userRepository;
    }

    async login(email, password) {
        const user = await this.userRepository.findByEmail(email);
        if (!user) {
            throw new UnauthorizedError('Credenciais inválidas');
        }

        const matches = await bcrypt.compare(password, user.pass_hash);
        if (!matches) {
            throw new UnauthorizedError('Credenciais inválidas');
        }

        const token = jwt.sign({ sub: user.id, role: user.role }, config.jwtSecret, {
            expiresIn: config.jwtExpiresIn,
        });

        return {
            token,
            user: { id: user.id, name: user.name, email: user.email, role: user.role },
        };
    }
}

module.exports = { AuthService };
