/**
 * Small in-memory key/value store encapsulated in a class instance
 * (as opposed to a module-level mutable object) so it can be
 * instantiated per-app/per-test instead of leaking shared state
 * across the whole process.
 */
class Cache {
    constructor() {
        this.store = new Map();
    }

    set(key, value) {
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }

    clear() {
        this.store.clear();
    }
}

module.exports = { Cache };
