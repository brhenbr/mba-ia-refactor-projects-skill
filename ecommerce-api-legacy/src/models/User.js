const bcrypt = require('bcrypt');

/**
 * Domain object for a user row. Repositories build this from the raw
 * `users` row instead of handing snake_case DB columns (pass_hash) and
 * plain objects straight to services.
 */
class User {
    constructor({ id, name, email, pass_hash: passHash, role }) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.passHash = passHash;
        this.role = role;
    }

    static fromRow(row) {
        return row ? new User(row) : null;
    }

    isAdmin() {
        return this.role === 'admin';
    }

    verifyPassword(password) {
        return bcrypt.compare(password, this.passHash);
    }

    /** Shape returned to clients — never includes passHash. */
    toPublicJSON() {
        return { id: this.id, name: this.name, email: this.email, role: this.role };
    }
}

module.exports = { User };
