const request = require('supertest');
const { buildTestApp } = require('./helpers/testApp');

describe('POST /api/checkout', () => {
    let app;

    beforeEach(async () => {
        ({ app } = await buildTestApp());
    });

    test('creates a new user, enrolls and charges a valid card', async () => {
        const res = await request(app).post('/api/checkout').send({
            name: 'Guilherme',
            email: 'gui@fullcycle.com.br',
            password: 'senhaforte',
            courseId: 2,
            cardNumber: '4111222233334444',
        });

        expect(res.status).toBe(200);
        expect(res.body.message).toBe('Sucesso');
        expect(res.body.enrollmentId).toBeDefined();
    });

    test('rejects declined card without creating enrollment', async () => {
        const res = await request(app).post('/api/checkout').send({
            name: 'Joao',
            email: 'joao@teste.com',
            password: 'anotherpass',
            courseId: 1,
            cardNumber: '5111222233334444',
        });

        expect(res.status).toBe(400);
        expect(res.body.error).toMatch(/recusado/i);
    });

    test('returns 404 for inactive or missing course', async () => {
        const res = await request(app).post('/api/checkout').send({
            name: 'Someone',
            email: 'someone@test.com',
            password: 'password123',
            courseId: 999,
            cardNumber: '4111222233334444',
        });

        expect(res.status).toBe(404);
    });

    test('validates required fields', async () => {
        const res = await request(app).post('/api/checkout').send({});
        expect(res.status).toBe(400);
        expect(res.body.details).toBeDefined();
    });

    test('rejects a new user without a password instead of defaulting to a weak one', async () => {
        const res = await request(app).post('/api/checkout').send({
            name: 'No Password',
            email: 'nopassword@test.com',
            courseId: 1,
            cardNumber: '4111222233334444',
        });

        expect(res.status).toBe(400);
    });

    test('reuses an existing user without requiring password again', async () => {
        const res = await request(app).post('/api/checkout').send({
            name: 'Leonan',
            email: 'leonan@fullcycle.com.br',
            courseId: 2,
            cardNumber: '4111222233334444',
        });

        expect(res.status).toBe(200);
    });
});
