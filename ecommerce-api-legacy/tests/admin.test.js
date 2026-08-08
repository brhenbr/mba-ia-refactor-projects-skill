const request = require('supertest');
const { buildTestApp } = require('./helpers/testApp');

async function loginAsAdmin(app) {
    const res = await request(app)
        .post('/api/auth/login')
        .send({ email: 'leonan@fullcycle.com.br', password: '123' });
    return res.body.token;
}

describe('Admin & authorization', () => {
    let app;

    beforeEach(async () => {
        ({ app } = await buildTestApp());
    });

    test('financial report requires authentication', async () => {
        const res = await request(app).get('/api/admin/financial-report');
        expect(res.status).toBe(401);
    });

    test('financial report requires admin role', async () => {
        await request(app).post('/api/checkout').send({
            name: 'Regular',
            email: 'regular@test.com',
            password: 'password123',
            courseId: 1,
            cardNumber: '4111222233334444',
        });

        const loginRes = await request(app)
            .post('/api/auth/login')
            .send({ email: 'regular@test.com', password: 'password123' });

        const res = await request(app)
            .get('/api/admin/financial-report')
            .set('Authorization', `Bearer ${loginRes.body.token}`);

        expect(res.status).toBe(403);
    });

    test('financial report returns aggregated data for admin', async () => {
        const token = await loginAsAdmin(app);
        const res = await request(app)
            .get('/api/admin/financial-report')
            .set('Authorization', `Bearer ${token}`);

        expect(res.status).toBe(200);
        expect(Array.isArray(res.body)).toBe(true);
        expect(res.body[0]).toHaveProperty('course');
        expect(res.body[0]).toHaveProperty('revenue');
        expect(res.body[0]).toHaveProperty('students');
    });

    test('DELETE /api/users/:id requires admin', async () => {
        const res = await request(app).delete('/api/users/1');
        expect(res.status).toBe(401);
    });

    test('DELETE /api/users/:id cascades enrollments and payments', async () => {
        const token = await loginAsAdmin(app);

        const res = await request(app)
            .delete('/api/users/1')
            .set('Authorization', `Bearer ${token}`);

        expect(res.status).toBe(200);

        const reportRes = await request(app)
            .get('/api/admin/financial-report')
            .set('Authorization', `Bearer ${token}`);

        const cleanArch = reportRes.body.find((c) => c.course === 'Clean Architecture');
        expect(cleanArch.students).toHaveLength(0);
        expect(cleanArch.revenue).toBe(0);
    });

    test('DELETE /api/users/:id returns 404 for unknown user', async () => {
        const token = await loginAsAdmin(app);

        const res = await request(app)
            .delete('/api/users/9999')
            .set('Authorization', `Bearer ${token}`);

        expect(res.status).toBe(404);
    });
});
