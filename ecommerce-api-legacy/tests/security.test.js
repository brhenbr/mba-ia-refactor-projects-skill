const bcrypt = require('bcrypt');
const request = require('supertest');
const { buildTestApp } = require('./helpers/testApp');

describe('Security', () => {
    test('passwords are hashed with bcrypt, never stored in plaintext', async () => {
        const { app, db } = await buildTestApp();

        await request(app).post('/api/checkout').send({
            name: 'Secure User',
            email: 'secure@test.com',
            password: 'mypassword123',
            courseId: 1,
            cardNumber: '4111222233334444',
        });

        const user = await db.get('SELECT * FROM users WHERE email = ?', ['secure@test.com']);
        expect(user.pass_hash).not.toBe('mypassword123');
        expect(user.pass_hash.startsWith('$2b$')).toBe(true);
        expect(await bcrypt.compare('mypassword123', user.pass_hash)).toBe(true);
    });

    test('login response never leaks the password hash', async () => {
        const { app } = await buildTestApp();

        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'leonan@fullcycle.com.br', password: '123' });

        expect(JSON.stringify(res.body)).not.toMatch(/pass_hash/);
        expect(JSON.stringify(res.body)).not.toMatch(/\$2b\$/);
    });

    test('rejects SQL injection payloads in login email before touching the database', async () => {
        const { app } = await buildTestApp();

        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: "'; DROP TABLE users; --", password: 'x' });

        expect(res.status).toBe(400);
    });

    test('rejects SQL injection payloads in checkout email', async () => {
        const { app } = await buildTestApp();

        const res = await request(app).post('/api/checkout').send({
            name: 'Attacker',
            email: "attacker' OR '1'='1",
            password: 'password123',
            courseId: 1,
            cardNumber: '4111222233334444',
        });

        expect(res.status).toBe(400);
    });

    test('financial report resolves with a single query (no N+1)', async () => {
        const { app, db } = await buildTestApp();

        const calls = [];
        const originalAll = db.all.bind(db);
        db.all = (...args) => {
            calls.push(args[0]);
            return originalAll(...args);
        };

        const loginRes = await request(app)
            .post('/api/auth/login')
            .send({ email: 'leonan@fullcycle.com.br', password: '123' });

        await request(app)
            .get('/api/admin/financial-report')
            .set('Authorization', `Bearer ${loginRes.body.token}`);

        const reportQueries = calls.filter((sql) => sql.includes('FROM courses'));
        expect(reportQueries.length).toBe(1);
    });
});
