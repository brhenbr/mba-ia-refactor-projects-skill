const request = require('supertest');
const { buildTestApp } = require('./helpers/testApp');

describe('POST /api/auth/login', () => {
    let app;

    beforeEach(async () => {
        ({ app } = await buildTestApp());
    });

    test('returns a JWT for valid admin credentials', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'leonan@fullcycle.com.br', password: '123' });

        expect(res.status).toBe(200);
        expect(res.body.token).toBeDefined();
        expect(res.body.user.role).toBe('admin');
        expect(res.body.user.pass_hash).toBeUndefined();
    });

    test('rejects invalid password', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'leonan@fullcycle.com.br', password: 'wrong' });

        expect(res.status).toBe(401);
    });

    test('rejects unknown email', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: 'nobody@test.com', password: 'whatever' });

        expect(res.status).toBe(401);
    });

    test('rejects malformed input before it ever reaches the database', async () => {
        const res = await request(app)
            .post('/api/auth/login')
            .send({ email: "x' OR 1=1--", password: 'whatever' });

        expect(res.status).toBe(400);
    });
});
