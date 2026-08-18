/**
 * Domain object for a payment row. Built by PaymentRepository instead of
 * returning the bare auto-increment id to services.
 */
class Payment {
    constructor({ id, enrollment_id: enrollmentId, amount, status }) {
        this.id = id;
        this.enrollmentId = enrollmentId;
        this.amount = amount;
        this.status = status;
    }

    static fromRow(row) {
        return row ? new Payment(row) : null;
    }

    isPaid() {
        return this.status === 'PAID';
    }
}

module.exports = { Payment };
