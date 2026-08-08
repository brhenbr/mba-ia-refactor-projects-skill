# code-smells-project

API de E-commerce em Python/Flask, refatorada com o framework `refactor-arch` a partir de um estado legado com múltiplas vulnerabilidades críticas (SQL Injection, credenciais hardcoded, sem autenticação, senhas em texto plano, N+1 queries). Ver `AUDIT_REPORT.md` para o relatório completo antes/depois.

## Arquitetura

```
app.py            # Application factory (create_app)
config.py         # Config por ambiente (dev/test/prod), lida de .env
database.py       # Instância do SQLAlchemy
seed.py           # Dados de exemplo (dev/test apenas)

models/           # Entidades ORM + regras de domínio (is_admin, tem_estoque...)
repositories/      # Acesso a dados (CRUD, eager loading)
services/         # Regras de negócio, transações
validators/       # Schemas Marshmallow (validação de entrada)
middleware/        # auth.py (JWT), error_handler.py (exceções centralizadas)
routes/           # Blueprints Flask (HTTP apenas)
exceptions/       # Exceções de negócio (BusinessException, NotFoundException...)
tests/            # pytest (segurança, auth, N+1, regras de negócio)
```

Fluxo de uma requisição: `route → validator → service → repository → model → db`.

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# gere chaves com: python -c "import secrets; print(secrets.token_hex(32))"
# e preencha SECRET_KEY e JWT_SECRET_KEY no .env

python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot; em ambiente não-produção é populado com produtos e usuários de exemplo (ver `seed.py`).

**Usuários de exemplo (dev):** `admin@loja.com` / `admin123` (admin), `joao@email.com` / `123456` (cliente).

## Testes

```bash
pytest tests/ -v
```

## Autenticação

```bash
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email": "admin@loja.com", "senha": "admin123"}'

curl http://localhost:5000/usuarios -H "Authorization: Bearer <access_token>"
```

- Rotas públicas: `GET /produtos*`, `POST /usuarios` (registro), `POST /login`, `GET /health`.
- Demais rotas exigem `Authorization: Bearer <token>`; algumas exigem role `admin`.
