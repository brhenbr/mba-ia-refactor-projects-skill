# Quality Heuristics & Validation Checklist

Heurísticas para validar que refatorações seguem boas práticas e código está pronto para produção.

---

## Security Heuristics

### ✅ Autenticação
- [ ] Todas rotas exceto `/login`, `/register`, `/health` requerem JWT ou session
- [ ] JWT tokens têm expiração (máximo 1 hora)
- [ ] Passwords são hashadas com bcrypt/argon2 (≥12 rounds)
- [ ] Nenhuma senha armazenada em texto plano
- [ ] Nenhum hash de senha retornado em APIs
- [ ] Tokens não são hardcoded no código
- [ ] /login retorna token seguro (não fake token)

### ✅ Autorização
- [ ] Cada rota valida se usuário tem permissão
- [ ] Usuários só acessam dados próprios (role-based access)
- [ ] Admin-only endpoints verificam role='admin'
- [ ] Sem endpoint de "reset admin" ou "magic links" sem proteção
- [ ] Endpoints privados retornam 403 se sem permissão

### ✅ Dados Sensíveis
- [ ] Credenciais (senhas, API keys) em variáveis de ambiente (.env)
- [ ] Nenhuma credencial no código-fonte
- [ ] .env adicionado ao .gitignore
- [ ] Nenhuma exposed debug info (stack traces, secret keys) em produção
- [ ] Debug mode desativado (app.run(debug=False))
- [ ] CORS não permite '*' (whitelist específicos)

### ✅ SQL & Database
- [ ] Todas queries usam prepared statements (? ou :param)
- [ ] Nenhuma concatenação de strings em SQL
- [ ] Nenhuma query raw com user input não-validado
- [ ] Queries usam ORM quando possível (SQLAlchemy, Sequelize)
- [ ] Foreign key constraints habilitadas (ON DELETE CASCADE se apropriado)
- [ ] Índices em colunas frequentemente filtradas

### ✅ Input Validation
- [ ] Entrada validada antes de usar (tipo, tamanho, formato)
- [ ] Validação centralizada (schemas, validators)
- [ ] Email validado (formato correto)
- [ ] Números em range correto (1-5 para priority, etc)
- [ ] Strings com tamanho máximo (evita buffer overflow conceitual)
- [ ] Dados inválidos retornam 400 Bad Request com mensagem clara

### ✅ HTTP Headers
- [ ] Content-Type: application/json em respostas JSON
- [ ] X-Content-Type-Options: nosniff (previne MIME sniffing)
- [ ] X-Frame-Options: DENY (previne clickjacking)
- [ ] Strict-Transport-Security em HTTPS (previne downgrade)
- [ ] Content-Security-Policy configurado (se há frontend)

---

## Code Quality Heuristics

### ✅ Arquitetura
- [ ] Código organizado em camadas (routes → services → repositories → models)
- [ ] Responsabilidades bem definidas (routes não fazem queries, services não retornam JSON)
- [ ] Nenhuma lógica de negócio em rotas
- [ ] Nenhuma query SQL em rotas (usar repository/service)
- [ ] Models contêm apenas dados + validações de domínio
- [ ] Services contêm lógica de negócio
- [ ] Repositories abstraem acesso a dados
- [ ] Existe `models/` com uma classe por entidade principal — **mesmo em stacks sem ORM** (driver SQL cru). Repository não devolve `row`/`rows` cru para o service: todo método de leitura passa o resultado do banco por `Model.fromRow(...)` antes de retornar (grep por `return this.db.get(`/`return this.db.all(`/`return cursor.fetchone()` sem transformação no meio é sinal de que falta essa camada)

### ✅ DRY (Don't Repeat Yourself)
- [ ] Nenhuma lógica duplicada (máximo 1 cópia)
- [ ] Funções reutilizáveis para validações comuns
- [ ] Métodos centralizados em modelos/utils
- [ ] Schemas reutilizados em múltiplas rotas
- [ ] Grep por padrão de duplicação: `is_overdue`, `overdue`, etc não deve ter 5+ ocorrências

### ✅ Naming
- [ ] Nomes de variáveis descritivos (não `u`, `t`, `d` para user, task, data)
- [ ] Funções têm verbo (create_task, get_user, is_overdue)
- [ ] Classes em PascalCase (User, Task, ProductRepository)
- [ ] Funções em snake_case (create_user, get_products)
- [ ] Constantes em UPPER_CASE (MAX_TITLE_LENGTH, VALID_STATUSES)
- [ ] Booleanos começam com `is_` ou `has_` (is_admin, has_tasks)

### ✅ Functions
- [ ] Funções fazem uma coisa (single responsibility)
- [ ] Máximo 20 linhas por função (regra de ouro)
- [ ] Máximo 3-4 parâmetros (se mais, considerar objeto)
- [ ] Sem side effects invisíveis
- [ ] Testáveis (sem dependências ocultas)

### ✅ Imports
- [ ] Nenhum import circular
- [ ] Imports organizados (stdlib → third-party → local)
- [ ] Nenhum import não-utilizado
- [ ] Imports específicos (não `import *`)

### ✅ Comments
- [ ] Comentários explicam WHY, não WHAT
- [ ] Máximo 1 linha de comentário por conceito
- [ ] Nenhum comentário para código óbvio
- [ ] Docstrings em funções públicas (Python)

### ✅ Error Handling
- [ ] Nenhum `except:` ou `except Exception:` genérico
- [ ] Exceções específicas capturadas (IntegrityError, ValueError, etc)
- [ ] Erros logados (use logging, não print)
- [ ] Mensagens de erro úteis (não "Erro interno")
- [ ] Status HTTP apropriados (401, 403, 404, 409, 500, etc)

### ✅ Logging
- [ ] Usar logging module (não print statements)
- [ ] Níveis apropriados: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [ ] Logs estruturados com contexto (user_id, request_id, etc)
- [ ] Debug logs desativados em produção
- [ ] Nunca logar senhas ou tokens

---

## Performance Heuristics

### ✅ Queries
- [ ] Nenhuma N+1 query (grep `Query.get()` em loops)
- [ ] Eager loading para relacionamentos (joinedload, selectinload)
- [ ] JOINs em vez de loops
- [ ] Paginação para listas grandes (limit/offset)
- [ ] Índices em colunas filtradas (WHERE, ORDER BY)
- [ ] Não fazer SELECT * sem necessidade (selecionar campos)

### ✅ Caching
- [ ] Cache para dados read-heavy (relatórios, estatísticas)
- [ ] Invalidação de cache quando dados mudam
- [ ] Redis para cache distribuído (não em-memória)
- [ ] TTL apropriado (1 minuto para trending, 1 hora para static)
- [ ] Nunca cache dados sensíveis (senhas, tokens)

### ✅ Async Operations
- [ ] Emails enviados async (não bloqueando)
- [ ] Chamadas a APIs externas em async
- [ ] WebSockets para real-time (não polling)
- [ ] Long-running tasks em background workers (Celery, Bull)

### ✅ Resource Limits
- [ ] Timeout em requests (não esperar forever)
- [ ] Limite de file upload size
- [ ] Rate limiting em endpoints sensíveis (login, register)
- [ ] Máximo de conexões simultâneas gerenciado
- [ ] Cleanup de recursos (fechar conexões, deletar temp files)

---

## Testability Heuristics

### ✅ Unit Tests
- [ ] Serviços testáveis (dependency injection)
- [ ] Models com métodos testáveis
- [ ] Mínimo 70% de cobertura de código
- [ ] Testes para validações
- [ ] Testes para edge cases

### ✅ Integration Tests
- [ ] Rotas testadas com cliente HTTP (requests, fetch)
- [ ] Testes com banco de dados (não mocks)
- [ ] Autenticação testada
- [ ] Autorização testada
- [ ] Testes de erro (400, 401, 403, 404, 500)

### ✅ Mocks & Stubs
- [ ] APIs externas mockadas em testes
- [ ] Banco de dados real em testes (SQLite em-memória é OK)
- [ ] Nenhum mock desnecessário (não mockar ORM)
- [ ] Dados de teste realistas

---

## Maintainability Heuristics

### ✅ Documentation
- [ ] README.md com instruções de setup
- [ ] Docstrings em funções públicas
- [ ] Comentários em lógica complexa
- [ ] API docs (Swagger, OpenAPI)
- [ ] Changelog para mudanças significativas

### ✅ Version Control
- [ ] Commits atômicos (uma mudança por commit)
- [ ] Mensagens de commit claras (tipo: descrição)
- [ ] Branches para features (git flow)
- [ ] Pull requests com descrição
- [ ] Code review antes de merge

### ✅ Dependencies
- [ ] Dependências versionadas (não `*` ou `>=`)
- [ ] Sem dependências desnecessárias
- [ ] Regular updates de dependências
- [ ] Security scanning (dependabot, snyk)
- [ ] Preferir libs bem-mantidas (muitas stars, issues ativas)

### ✅ Configuration
- [ ] Ambiente configurável (dev, test, prod)
- [ ] Variáveis de ambiente para cada ambiente
- [ ] Nenhum hardcode de valores
- [ ] Config validada no boot (erro se obrigatório não setado)

---

## Deployment Readiness Checklist

### 🚀 Pre-Deployment
- [ ] Todos testes passando
- [ ] Code coverage ≥70%
- [ ] Code review aprovado
- [ ] Sem TODO, FIXME, XXX no código
- [ ] Sem debug prints
- [ ] Sem hardcoded credenciais
- [ ] Sem secrets em logs
- [ ] Database migrations criadas e testadas

### 🚀 Deployment
- [ ] Secrets configurados no servidor (não .env)
- [ ] Database pronto (migrations rodadas)
- [ ] Backup do banco antes de deploy
- [ ] Monitoring ativo (logs, errors, performance)
- [ ] Alertas configurados (CPU, memory, errors)
- [ ] Health check respondendo
- [ ] Graceful shutdown implementado

### 🚀 Post-Deployment
- [ ] Testes de smoke (endpoints básicos funcionam)
- [ ] Logs monitorados por erros
- [ ] Performance monitorada (latência, CPU, memory)
- [ ] Alertas revisados
- [ ] Rollback plan preparado se necessário

---

## Checklist Consolidado (Antes de Merge)

```
SEGURANÇA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [ ] Autenticação: todas rotas protegidas com @login_required
- [ ] Autorização: role/ownership verificados
- [ ] Credenciais: .env, nenhuma hardcoded
- [ ] Senhas: bcrypt/argon2, nunca retornar hash
- [ ] SQL: prepared statements, nenhuma concatenação
- [ ] Validação: entrada validada em schemas
- [ ] Tokens: expiration, nunca em logs
- [ ] Debug: desativado em produção

QUALIDADE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [ ] Arquitetura: camadas bem separadas
- [ ] Duplicação: nenhuma lógica duplicada
- [ ] Naming: descritivo (não abreviado)
- [ ] Funções: ≤20 linhas, single responsibility
- [ ] Imports: nenhum circular, tudo utilizado
- [ ] Erros: exceções específicas, bom logging
- [ ] Testes: ≥70% cobertura, tudo passa
- [ ] Documentação: README, docstrings, comments

PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [ ] N+1 Queries: nenhuma (grep .get em loops)
- [ ] Eager Loading: relacionamentos carregados
- [ ] Paginação: listas grandes paginadas
- [ ] Cache: dados read-heavy cacheados
- [ ] Async: operações I/O não-bloqueantes
- [ ] Índices: colunas filtradas têm índices

DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- [ ] Migrations: preparadas e testadas
- [ ] Logs: estruturados, sem sensíveis
- [ ] Monitoring: pronto
- [ ] Rollback: plano preparado
- [ ] Healthcheck: respondendo
- [ ] Secrets: configurados no servidor
```

---

## Red Flags (Pare e Revise!)

🚨 Se algum destes for verdadeiro, **não mergeie**:

1. ❌ `SELECT *` sem filtragem (N+1 queries)
2. ❌ `except:` ou `except Exception:` sem tipo específico
3. ❌ Senha ou API key em código-fonte
4. ❌ Query com concatenação de strings (SQL injection)
5. ❌ Endpoint admin sem `@admin_required`
6. ❌ Senha retornada em API response
7. ❌ `app.run(debug=True)` em produção
8. ❌ Lógica de negócio em rota (não em service)
9. ❌ Query SQL direto em rota (usar repository)
10. ❌ Código duplicado (mesma lógica 3+ vezes)
11. ❌ Nenhum teste (cobertura 0%)
12. ❌ Global variable mutable (cache global, contador global)
13. ❌ Repository devolve `row`/`rows` cru do banco para o service, sem passar por um model (`fromRow`) — inclusive em stacks sem ORM

Se encontrou qualquer uma, volte e corrija antes de continuar.

---

## Scoring Rubric

Use para avaliar qualidade geral:

### 🟢 Production Ready (Score ≥90%)
- Segurança: ✅ Todos checks
- Qualidade: ✅ Todos checks
- Performance: ✅ Todos checks
- Testes: ✅ ≥80% cobertura
- **Ação:** Deploy imediatamente

### 🟡 Needs Review (Score 70-89%)
- Segurança: ✅ Críticas resolvidas
- Qualidade: ⚠️ Alguns itens faltando
- Performance: ⚠️ Não otimizado
- Testes: ⚠️ 50-80% cobertura
- **Ação:** Adicionar mais testes, revisar qualidade

### 🔴 Not Ready (Score <70%)
- Segurança: ❌ Vulnerabilidades críticas
- Qualidade: ❌ Muitos problemas
- Performance: ❌ N+1 queries, etc
- Testes: ❌ <50% cobertura
- **Ação:** Voltar e refatorar

---

## Próximos Passos

1. Revisar checklist antes de cada merge
2. Usar `report-template.md` para documentar audit
3. Automatizar checks com linters e testes CI/CD
