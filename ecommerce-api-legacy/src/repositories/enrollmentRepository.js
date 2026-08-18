const { Enrollment } = require('../models/Enrollment');

class EnrollmentRepository {
    constructor(db) {
        this.db = db;
    }

    async create(userId, courseId) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return new Enrollment({ id: lastID, user_id: userId, course_id: courseId });
    }
}

module.exports = { EnrollmentRepository };
