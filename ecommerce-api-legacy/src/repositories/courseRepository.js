const { Course } = require('../models/Course');

class CourseRepository {
    constructor(db) {
        this.db = db;
    }

    async findActiveById(id) {
        const row = await this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
        return Course.fromRow(row);
    }

    async findAll() {
        const rows = await this.db.all('SELECT * FROM courses');
        return rows.map(Course.fromRow);
    }
}

module.exports = { CourseRepository };
