const bcrypt = require('bcrypt');
const config = require('../config');

async function initSchema(db) {
    await db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            pass_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            course_id INTEGER NOT NULL REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
            amount REAL NOT NULL,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    `);
}

/**
 * Seed data mirrors the original boilerplate fixtures. The admin
 * password is intentionally simple here — it's demo/seed data for an
 * in-memory dev database, not a production credential.
 */
async function seed(db) {
    const adminHash = await bcrypt.hash('123', config.bcryptRounds);

    await db.run(
        "INSERT INTO users (name, email, pass_hash, role) VALUES (?, ?, ?, 'admin')",
        ['Leonan', 'leonan@fullcycle.com.br', adminHash]
    );

    await db.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)"
    );

    const enrollment = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)'
    );

    await db.run(
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, 997.00, 'PAID')",
        [enrollment.lastID]
    );
}

module.exports = { initSchema, seed };
