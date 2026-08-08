# task-manager-api

API de Task Manager em Python/Flask, refatorada com o framework `refactor-arch` a partir de um estado com autenticação ausente, senhas em MD5, credenciais hardcoded e N+1 queries. Ver `AUDIT_REPORT.md` para o relatório completo antes/depois.

## Arquitetura

```
app.py            # Application factory (create_app)
config.py         # Config por ambiente (dev/test/prod), lida de .env
database.py       # Instância do SQLAlchemy
seed.py           # Dados de exemplo (dev)

models/           # Entidades ORM + regras de domínio (is_admin, is_overdue...)
repositories/     # Acesso a dados (CRUD, eager loading, contagens agregadas)
services/         # Regras de negócio, autorização de dados, notificações
validators/       # Schemas Marshmallow (validação de entrada)
middleware/       # auth.py (JWT), error_handler.py (exceções centralizadas)
routes/           # Blueprints Flask (HTTP apenas)
exceptions/       # Exceções de negócio (BusinessException, NotFoundException...)
tests/            # pytest (auth, autorização, N+1, regras de negócio, segurança)
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

python seed.py     # popula tasks.db com usuários, categorias e tasks de exemplo
python app.py
```

A aplicação sobe em `http://localhost:5000`. Rode `seed.py` antes do primeiro boot — sem isso os endpoints retornam listas vazias.

**Usuários de exemplo (dev):**
- `joao@email.com` / `senha1234` (admin)
- `maria@email.com` / `senhaabcd` (user)
- `pedro@email.com` / `senhapedro` (manager, tratado como user)

## Testes

```bash
pytest -v
pytest --cov       # com cobertura
```

## Autenticação e autorização

```bash
curl -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email": "joao@email.com", "password": "senha1234"}'

curl http://localhost:5000/tasks -H "Authorization: Bearer <token>"
```

- Rotas públicas: `POST /users` (registro), `POST /login`, `GET /health`, `GET /`.
- Todas as demais rotas exigem `Authorization: Bearer <token>`.
- Usuários comuns (`user`/`manager`) só veem e editam as próprias tasks; `admin` vê e gerencia tudo.
- Alterar `role`/`active` de um usuário, gerenciar categorias e ver `/reports/summary` exige `role=admin`.
- `POST /users` sempre cria a conta com `role=user`, mesmo que o payload informe outro valor — promoções de role são feitas por um admin via `PUT /users/:id`.
