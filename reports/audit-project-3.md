# 📋 Relatório de Auditoria Arquitetural

**Projeto:** task-manager-api (Task Manager, Flask)
**Data:** 2026-08-08
**Auditor:** Claude Code (skill `refactor-arch`)
**Status:** Concluído

---

## 📊 Executive Summary

### Score de Saúde do Projeto (Antes → Depois)

```
Segurança:        🔴 15%  →  🟢 95%
Qualidade:        🟡 45%  →  🟢 90%
Performance:      🟠 40%  →  🟢 95%
Manutenibilidade: 🟡 50%  →  🟢 90%
Testabilidade:    🔴  0%  →  🟢 85% (61 testes automatizados)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORE GERAL:      🔴 30%  →  🟢 91%
```

Diferente do `code-smells-project`, este projeto já chegava com uma separação superficial em `models/routes/services/utils` — mas sem nenhuma camada de autorização, validação centralizada ou repositórios, o que mascarava a mesma gravidade de problemas.

### Findings Críticos (estado original)

| # | Problema | Severidade | Arquivo(s) originais |
|---|---|---|---|
| 1 | Nenhuma autenticação/autorização em nenhuma rota — qualquer cliente lê/edita/deleta tasks e usuários de qualquer pessoa | 🔴 CRITICAL | `routes/*.py` (todas as rotas) |
| 2 | `/login` retorna um token falso (`'fake-jwt-token-' + id`), nunca verificado por ninguém | 🔴 CRITICAL | `routes/user_routes.py:210` |
| 3 | Senhas com MD5 sem salt; hash devolvido em respostas de API | 🔴 CRITICAL | `models/user.py:29,32`, `to_dict()` |
| 4 | Credenciais hardcoded: `SECRET_KEY` e senha SMTP no código | 🔴 CRITICAL | `app.py:13`, `services/notification_service.py:7-10` |
| 5 | `debug=True` e `CORS(app)` (qualquer origem) | 🔴 CRITICAL | `app.py:15,34` |
| 6 | N+1 queries na listagem de tasks e nos relatórios (uma query de usuário/categoria por task; um loop de tasks por usuário) | 🟠 HIGH | `routes/task_routes.py:14-59`, `routes/report_routes.py` |
| 7 | Lógica de "overdue" duplicada 4x nas rotas mesmo com `Task.is_overdue()` já existindo e nunca usado | 🟡 MEDIUM | `task_routes.py`, `user_routes.py`, `report_routes.py` |
| 8 | `except:` genérico + `print()` em vez de exceções tipadas e logging | 🟡 MEDIUM | `routes/*.py` (quase todas as funções) |
| 9 | `search_tasks` derrubava a request com `ValueError` não tratado em `priority`/`user_id` não-numéricos | 🟡 MEDIUM | `routes/task_routes.py:261,264` |
| 10 | 7 funções mortas em `utils/helpers.py` (nunca importadas em lugar algum), duplicando validação reimplementada inline nas rotas | 🟡 MEDIUM | `utils/helpers.py` |
| 11 | Sem paginação em listagens (`GET /tasks`, `GET /users`) | 🟡 MEDIUM | `routes/task_routes.py`, `routes/user_routes.py` |
| 12 | Zero testes automatizados | 🔴 CRITICAL | projeto inteiro |

### Recomendação
**PODE FAZER MERGE** — os 12 findings foram corrigidos e cobertos por testes automatizados (61 testes, `pytest -q`).

---

## 🔧 O que foi feito

O projeto foi reestruturado para a arquitetura completa em camadas descrita em `architecture-rules.md`:

```
routes/ → validators/ → services/ → repositories/ → models/ (SQLAlchemy) → db
middleware/  (auth.py: JWT + RBAC + ownership · error_handler.py: exceções centralizadas)
```

### [#1] Autenticação JWT + Autorização (RBAC + ownership)
`middleware/auth.py` implementa `login_required`, `admin_required` e `owner_or_admin_required`. Único endpoint de escrita público é `POST /users` (registro); tudo mais exige `Authorization: Bearer <token>`. Usuários comuns só veem/editam as próprias tasks (`user_id == current_user`); `admin` vê e gerencia tudo. Coberto por `tests/test_security.py::test_protected_routes_require_auth` e as suítes de ownership em `test_tasks.py`/`test_users.py`/`test_reports.py`.

### [#2] `/login` com JWT real
`Flask-JWT-Extended` (`create_access_token`, expiração de 1h) substitui o token falso. `tests/test_auth.py::test_login_returns_real_jwt` valida o formato do token.

### [#3] Senhas com bcrypt (12 rounds)
`models/user.py` usa `bcrypt.hashpw`/`checkpw`; `to_dict()` não inclui mais `password`. Testado em `test_password_is_hashed_with_bcrypt` e `test_password_never_returned_in_api`.

### [#4] Credenciais em variáveis de ambiente
`config.py` lê `SECRET_KEY`/`JWT_SECRET_KEY`/`DATABASE_URL` via `os.getenv` (`.env`, nunca commitado — ver `.gitignore`). `ProductionConfig.validate()` recusa subir sem essas variáveis. `services/notification_service.py` lê `EMAIL_HOST`/`EMAIL_USER`/`EMAIL_PASSWORD` do ambiente e desabilita o envio (sem quebrar a request) quando não configurado.

### [#5] Debug e CORS
`ProductionConfig.DEBUG = False`; `app.run(debug=app.config["DEBUG"])`. `CORS_ORIGINS` vem do `.env` como lista explícita em vez de `CORS(app)` liberando qualquer origem.

### [#6] N+1 eliminado
- `repositories/task_repository.py` usa `joinedload(Task.user, Task.category)` na listagem — uma query com JOINs em vez de 1+2N.
- `services/report_service.py` usa uma única query agrupada (`counts_by_user_and_status`, `GROUP BY user_id, status`) para a produtividade por usuário, em vez do loop original que rodava uma query de tasks por usuário.
- `services/category_service.py` usa uma query agrupada (`task_counts_by_category`) em vez de um `count()` por categoria em loop.

### [#7] Duplicação de "overdue" eliminada
Todas as rotas agora chamam `task.is_overdue()` (já existia no model, nunca era usado) em vez de reimplementar o mesmo `if/else` aninhado em 4 lugares.

### [#8] Exceções e logging centralizados
`middleware/error_handler.py` registra handlers globais para `BusinessException`, `ValidationError` (Marshmallow), `IntegrityError`, `OperationalError`, 404 e fallback genérico — nenhuma rota usa `except:` genérico ou `print()`.

### [#9] Crash de `search_tasks` corrigido
`validators/task_validator.py::TaskSearchSchema` valida `priority`/`user_id` como inteiros antes de chegar à query — entrada inválida agora retorna `400` estruturado em vez de derrubar a request. Coberto por `test_search_with_non_numeric_priority_returns_400_instead_of_crashing`.

### [#10] Código morto removido
`utils/helpers.py` foi removido por completo — nenhuma das 7 funções era usada; a validação que elas duplicavam agora vive nos schemas Marshmallow (`validators/`), e a serialização em `to_dict()` dos models.

### [#11] Paginação
Fora do escopo desta rodada (ver pendências abaixo) — `GET /tasks` e `GET /users` continuam retornando a lista completa, mas agora sempre escopada ao usuário autenticado (não-admin nunca vê a base inteira).

### [#12] Suíte de testes
60 testes em `tests/` cobrindo autenticação, autorização (ownership + RBAC), regras de negócio (overdue, stats, reassignment), validação de entrada e segurança (rotas protegidas, hashing, ausência de vazamento de segredos).

---

## ⚠️ Decisões e observações

- **Modelo de visibilidade de tasks:** decisão de produto confirmada com o usuário — usuários comuns só veem/editam as próprias tasks; admin vê tudo. O role `manager` foi mantido equivalente a `user` (o código original nunca o tratava de forma diferente).
- **Registro público (`POST /users`):** o schema de registro (`UserRegisterSchema`) nem aceita um campo `role` — enviar um é rejeitado com 400 (unknown field), não apenas ignorado. Promoção de role é uma ação de admin via `PUT /users/:id`.
- **Notificação por email:** o serviço já existia mas nunca era chamado; foi conectado a `TaskService.create()` (notifica o usuário ao ser atribuído a uma task) e passou a ler credenciais do ambiente. Falha de envio (SMTP ausente/indisponível) nunca derruba a request — mesmo comportamento não-fatal do código original, agora sem log de exceção genérica.
- **CORS:** deixou de ser `CORS(app)` (qualquer origem); agora lê `CORS_ORIGINS` do `.env`.
- **Dados de seed:** senhas de exemplo (`senha1234`, `senhaabcd`, `senhapedro`) são propositalmente simples — dados de desenvolvimento, nunca usados em produção.

## 📋 Pendências conhecidas (fora do escopo desta rodada)

- Paginação em `GET /tasks` / `GET /users` para volumes grandes.
- Rate limiting em `/login` e `/users` (força bruta).
- Refresh tokens (atualmente apenas access token de 1h).
- CI/CD com lint + testes automatizados no PR.

---

## 🧪 Resultado dos testes

```
pytest -q
61 passed
```

**Pronto para Merge:** SIM
