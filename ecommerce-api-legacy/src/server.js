const { Database } = require('./db');
const { initSchema, seed } = require('./db/schema');
const { createApp } = require('./app');
const config = require('./config');
const logger = require('./utils/logger');

async function start() {
    const db = new Database(':memory:');
    await initSchema(db);
    await seed(db);

    const app = createApp(db);

    app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

start().catch((err) => {
    logger.error('Falha ao iniciar aplicação', { message: err.message });
    process.exit(1);
});
