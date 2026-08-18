# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express. Refatorada para uma arquitetura em
camadas (`routes -> validators -> services -> repositories -> models`); veja
[`../reports/audit-project-2.md`](../reports/audit-project-2.md) para o antes/depois completo.

## Como rodar

```bash
npm install
cp .env.example .env   # edite os valores conforme necessário
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega
seeds automaticamente no boot (usuário admin `leonan@fullcycle.com.br` / senha `123`).

## Testes

```bash
npm test
```

## Autenticação

A maioria dos endpoints administrativos exige um JWT. Faça login para obter um token:

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "leonan@fullcycle.com.br", "password": "123"}'
```

Use o token retornado no header `Authorization: Bearer <token>` para acessar rotas
protegidas (`GET /api/admin/financial-report`, `DELETE /api/users/:id`).

Exemplos completos de requisições estão em `api.http`.

## Estrutura

```
src/
├── server.js              # bootstrap (db + app + listen)
├── app.js                 # monta dependências e rotas (usado também nos testes)
├── config/                 # configuração via variáveis de ambiente
├── db/                     # wrapper promisificado do sqlite3 + schema/seed
├── repositories/           # acesso a dados
├── services/                # regras de negócio
├── validators/               # validação de entrada (Joi)
├── middleware/                # autenticação JWT, tratamento de erros
├── routes/                     # HTTP handlers
└── utils/                       # logger e cache encapsulado
tests/                              # testes de integração (Jest + Supertest)
```
