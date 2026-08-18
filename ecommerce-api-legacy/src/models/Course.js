/**
 * Domain object for a course row. Built by CourseRepository from the raw
 * `courses` row instead of passing the raw row straight to services.
 */
class Course {
    constructor({ id, title, price, active }) {
        this.id = id;
        this.title = title;
        this.price = price;
        this.active = active;
    }

    static fromRow(row) {
        return row ? new Course(row) : null;
    }
}

module.exports = { Course };
