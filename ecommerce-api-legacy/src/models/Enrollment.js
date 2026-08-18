/**
 * Domain object for an enrollment row. Built by EnrollmentRepository
 * instead of returning the bare auto-increment id to services.
 */
class Enrollment {
    constructor({ id, user_id: userId, course_id: courseId }) {
        this.id = id;
        this.userId = userId;
        this.courseId = courseId;
    }

    static fromRow(row) {
        return row ? new Enrollment(row) : null;
    }
}

module.exports = { Enrollment };
