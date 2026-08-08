const LEVELS = ['debug', 'info', 'warn', 'error'];

function log(level, message, meta) {
    if (process.env.NODE_ENV === 'test' && process.env.VERBOSE_TESTS !== 'true') {
        return;
    }

    const entry = { level, message, ...(meta ? { meta } : {}) };
    // eslint-disable-next-line no-console
    console[level === 'debug' ? 'log' : level](JSON.stringify(entry));
}

const logger = {};
for (const level of LEVELS) {
    logger[level] = (message, meta) => log(level, message, meta);
}

module.exports = logger;
