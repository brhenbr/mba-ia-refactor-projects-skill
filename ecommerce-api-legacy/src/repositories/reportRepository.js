class ReportRepository {
    constructor(db) {
        this.db = db;
    }

    /**
     * Builds the full financial report (courses + students + revenue) in a
     * single query with JOINs, then groups the flat rows in memory —
     * avoids the 1 + N*2 query pattern of the original implementation.
     */
    async getFinancialReport() {
        const rows = await this.db.all(`
            SELECT
                c.id AS course_id,
                c.title AS course_title,
                u.name AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id
        `);

        const coursesById = new Map();

        for (const row of rows) {
            if (!coursesById.has(row.course_id)) {
                coursesById.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: [],
                });
            }

            const courseData = coursesById.get(row.course_id);

            if (row.student_name) {
                courseData.students.push({
                    student: row.student_name,
                    paid: row.payment_amount || 0,
                });
            }

            if (row.payment_status === 'PAID') {
                courseData.revenue += row.payment_amount;
            }
        }

        return Array.from(coursesById.values());
    }
}

module.exports = { ReportRepository };
