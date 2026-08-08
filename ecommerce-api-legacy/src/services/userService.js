const { NotFoundError } = require('../exceptions');

class UserService {
    constructor(userRepository) {
        this.userRepository = userRepository;
    }

    async deleteUser(id) {
        const user = await this.userRepository.findById(id);
        if (!user) {
            throw new NotFoundError('Usuário não encontrado');
        }

        await this.userRepository.deleteCascade(id);
    }
}

module.exports = { UserService };
