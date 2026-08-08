const sqlite3 = require('sqlite3').verbose();

class Database {
    constructor(filename = ':memory:') {
        this.raw = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.run(sql, params, function callback(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.get(sql, params, (err, row) => {
                if (err) return reject(err);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.all(sql, params, (err, rows) => {
                if (err) return reject(err);
                resolve(rows);
            });
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.raw.exec(sql, (err) => {
                if (err) return reject(err);
                resolve();
            });
        });
    }

    /**
     * Runs `work` inside a transaction, rolling back on any rejection.
     */
    async transaction(work) {
        await this.run('BEGIN TRANSACTION');
        try {
            const result = await work();
            await this.run('COMMIT');
            return result;
        } catch (err) {
            await this.run('ROLLBACK');
            throw err;
        }
    }

    close() {
        return new Promise((resolve, reject) => {
            this.raw.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = { Database };
