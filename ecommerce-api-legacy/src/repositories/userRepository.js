class UserRepository {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT * FROM users WHERE email = ?', [email]);
    }

    findById(id) {
        return this.db.get('SELECT * FROM users WHERE id = ?', [id]);
    }

    async create({ name, email, passHash, role = 'user' }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass_hash, role) VALUES (?, ?, ?, ?)',
            [name, email, passHash, role]
        );
        return this.findById(lastID);
    }

    /**
     * Deletes a user along with their enrollments/payments in a single
     * transaction so no orphaned rows are left behind.
     */
    async deleteCascade(id) {
        return this.db.transaction(async () => {
            const enrollments = await this.db.all(
                'SELECT id FROM enrollments WHERE user_id = ?',
                [id]
            );

            for (const enrollment of enrollments) {
                await this.db.run('DELETE FROM payments WHERE enrollment_id = ?', [
                    enrollment.id,
                ]);
            }

            await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
            const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes > 0;
        });
    }
}

module.exports = { UserRepository };
