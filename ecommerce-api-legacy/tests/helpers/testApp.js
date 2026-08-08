const { Database } = require('../../src/db');
const { initSchema, seed } = require('../../src/db/schema');
const { createApp } = require('../../src/app');

async function buildTestApp() {
    const db = new Database(':memory:');
    await initSchema(db);
    await seed(db);
    const app = createApp(db);
    return { app, db };
}

module.exports = { buildTestApp };
