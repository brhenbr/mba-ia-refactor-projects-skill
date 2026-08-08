const bcrypt = require('bcrypt');
const config = require('../config');
const { NotFoundError, PaymentDeclinedError, ValidationError } = require('../exceptions');
const logger = require('../utils/logger');

function maskCard(cardNumber) {
    return `${'*'.repeat(Math.max(cardNumber.length - 4, 0))}${cardNumber.slice(-4)}`;
}

class CheckoutService {
    constructor({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditLogRepository,
        cache,
    }) {
        this.courseRepository = courseRepository;
        this.userRepository = userRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
        this.auditLogRepository = auditLogRepository;
        this.cache = cache;
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courseRepository.findActiveById(courseId);
        if (!course) {
            throw new NotFoundError('Curso não encontrado');
        }

        let user = await this.userRepository.findByEmail(email);

        if (!user) {
            if (!password) {
                throw new ValidationError('Senha é obrigatória para novos usuários');
            }
            const passHash = await bcrypt.hash(password, config.bcryptRounds);
            user = await this.userRepository.create({ name, email, passHash });
        }

        // Never log the full PAN — only a masked reference for traceability.
        logger.info('Processando pagamento', { card: maskCard(cardNumber) });
        const status = cardNumber.startsWith('4') ? 'PAID' : 'DENIED';

        if (status === 'DENIED') {
            throw new PaymentDeclinedError('Pagamento recusado');
        }

        const enrollmentId = await this.enrollmentRepository.create(user.id, course.id);
        await this.paymentRepository.create(enrollmentId, course.price, status);
        await this.auditLogRepository.create(`Checkout curso ${course.id} por ${user.id}`);

        this.cache.set(`last_checkout_${user.id}`, course.title);

        return { message: 'Sucesso', enrollmentId };
    }
}

module.exports = { CheckoutService };
