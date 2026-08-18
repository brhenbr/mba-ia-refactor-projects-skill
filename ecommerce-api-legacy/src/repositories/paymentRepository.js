const { Payment } = require('../models/Payment');

class PaymentRepository {
    constructor(db) {
        this.db = db;
    }

    async create(enrollmentId, amount, status) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
        return new Payment({ id: lastID, enrollment_id: enrollmentId, amount, status });
    }
}

module.exports = { PaymentRepository };
