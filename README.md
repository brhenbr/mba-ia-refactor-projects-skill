# Refatoração Arquitetural Automatizada com Skills — `refactor-arch`

Este repositório documenta a criação e execução da skill **`refactor-arch`**: uma skill de Claude Code capaz de analisar, auditar e refatorar qualquer projeto backend para o padrão MVC, de forma agnóstica de tecnologia. A skill foi construída e validada contra três projetos legados fornecidos como base do desafio:

| # | Projeto | Stack | Domínio |
|---|---|---|---|
| 1 | `code-smells-project/` | Python / Flask | API de E-commerce |
| 2 | `ecommerce-api-legacy/` | Node.js / Express | LMS API com checkout |
| 3 | `task-manager-api/` | Python / Flask (parcialmente organizado) | API de Task Manager |

---

## 1. Análise Manual

Antes de construir a skill, cada projeto foi analisado manualmente para identificar os principais anti-patterns arquiteturais e de segurança. Esta seção reproduz os achados dessa análise inicial (pré-refatoração).

### 1.1 Projeto 1 — `code-smells-project` (Python/Flask)

#### 🔴 CRITICAL

**1. SQL Injection em múltiplas funções**
- **Arquivo:** `models.py` (linhas 28, 48-49, 58-60, 68, 92, 110, 140, 148-150, etc.)
- **Explicação:** Concatenação direta de strings em queries SQL sem prepared statements. Exemplo na linha 28: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`. Um atacante pode injetar SQL malicioso através de parâmetros da API.

**2. Endpoint sem autenticação que permite SQL arbitrária**
- **Arquivo:** `app.py` (linhas 59-78)
- **Explicação:** O endpoint `/admin/query` aceita qualquer SQL do cliente sem validação. Qualquer pessoa pode fazer DELETE/DROP de tabelas inteiras executando SQL arbitrário.

#### 🟠 HIGH

**3. Secret Key hardcoded e exposto**
- **Arquivo:** `app.py` (linha 7) e `controllers.py` (linha 289)
- **Explicação:** Chave secreta `"minha-chave-super-secreta-123"` está no código-fonte e também retornada no endpoint `/health`. Qualquer pessoa com acesso ao repo consegue falsificar tokens.

**4. Endpoint de reset do banco sem autenticação**
- **Arquivo:** `app.py` (linhas 47-57)
- **Explicação:** O endpoint `/admin/reset-db` apaga TODOS os dados do banco sem pedir autenticação. Um atacante pode destruir dados de produção.

#### 🟡 MEDIUM

**5. Senhas armazenadas em texto plano**
- **Arquivo:** `models.py` (linhas 105-120 — `login_usuario`) e `database.py` (linha 76-83)
- **Explicação:** As senhas são armazenadas sem hash. Se o banco vazar, todas as senhas estão expostas. Deveria usar bcrypt ou similar.

**6. Problema N+1 queries — Ineficiência severa**
- **Arquivo:** `models.py` (linhas 187-200 e 219-232)
- **Explicação:** Para cada pedido retornado, faz uma query adicional para cada item. Se retorna 100 pedidos com 5 itens cada = 500+ queries! Deveria usar JOIN.

**Resumo dos impactos:** perda de dados (`reset-db`), roubo de credenciais (senhas em texto plano + secret exposta), acesso não autorizado (SQL injection), performance degradada (N+1 queries).

---

### 1.2 Projeto 2 — `ecommerce-api-legacy` (Node.js/Express)

#### 🔴 CRITICAL

**1. Credenciais sensíveis hardcoded no código**
- **Arquivo:** `utils.js` (linhas 2-5)
- **Explicação:** Passwords de banco, chaves de payment gateway e credenciais SMTP expostas diretamente no código (`"senha_super_secreta_prod_123"`, `"pk_live_1234567890abcdef"`). Qualquer pessoa com acesso ao repositório consegue acessar sistemas de produção.

#### 🟠 HIGH

**2. Criptografia fraca e inadequada para senhas**
- **Arquivo:** `utils.js` (linhas 17-23 — função `badCrypto`)
- **Explicação:** A função usa base64 (que é encoding, não criptografia) para "hash" de senha. O resultado é previsível e reversível. Deveria usar bcrypt ou argon2. Além disso, na linha 68 de `AppManager.js`, usa senha padrão `"123456"` se nenhuma for fornecida.

**3. Validação de cartão de crédito inadequada**
- **Arquivo:** `AppManager.js` (linhas 44-48)
- **Explicação:** Aceita qualquer número que comece com "4" como válido. Não valida CVC, data de vencimento, checksum (algoritmo de Luhn), ou tamanho. Um atacante pode fazer pagamentos com números fake.

#### 🟡 MEDIUM

**4. Deleção de usuário sem cascata — Violação de integridade referencial**
- **Arquivo:** `AppManager.js` (linhas 131-137)
- **Explicação:** O endpoint `DELETE /api/users/:id` deleta apenas o usuário mas deixa enrollments e payments órfãos e inconsistentes no banco. Deveria usar `ON DELETE CASCADE` ou validar dependências antes.

**5. Endpoint administrativo sem autenticação**
- **Arquivo:** `AppManager.js` (linhas 80-129)
- **Explicação:** O endpoint `/api/admin/financial-report` expõe dados financeiros sensíveis sem nenhuma verificação de autenticação. Qualquer pessoa consegue ver receitas e dados de alunos.

**6. Callback Hell / Race Condition no financial-report**
- **Arquivo:** `AppManager.js` (linhas 80-129)
- **Explicação:** Múltiplos níveis aninhados de callbacks (3+ níveis) tornam o código frágil. Mais crítico: usa contadores (`coursesPending`, `enrPending`) que podem falhar com requisições simultâneas, retornando resposta antes de todos os dados estarem prontos.

#### 🔵 LOW

**7. Nomes de variáveis muito abreviados e pouco descritivos**
- **Arquivo:** `AppManager.js` (linhas 29-33)
- **Explicação:** Usa `u`, `e`, `p`, `cid`, `cc` em vez de `username`, `email`, `password`, `courseId`, `creditCard`. Reduz legibilidade do código.

**8. Variáveis declaradas mas nunca utilizadas**
- **Arquivo:** `utils.js` (linha 10)
- **Explicação:** `totalRevenue` é declarado mas nunca usado na lógica da aplicação. Dead code que causa confusão.

**Resumo dos impactos:** vazamento de credenciais de produção, pagamentos fraudulentos, exposição de dados financeiros, inconsistência de dados no banco, comportamento imprevisível com requisições simultâneas.

---

### 1.3 Projeto 3 — `task-manager-api` (Python/Flask)

#### 🔴 CRITICAL

**1. Credenciais de email hardcoded no código**
- **Arquivo:** `services/notification_service.py` (linhas 9-10)
- **Explicação:** Senha SMTP e email do serviço expostos diretamente (`'email_password': 'senha123'`, `'email_user': 'taskmanager@gmail.com'`). Qualquer pessoa com acesso ao repositório consegue enviar emails em nome da aplicação.

#### 🟠 HIGH

**2. Falta total de autenticação e autorização nos endpoints**
- **Arquivo:** `routes/task_routes.py` (linhas 11-300) e `routes/user_routes.py` (linhas 10-212)
- **Explicação:** Todos os endpoints (GET, POST, PUT, DELETE) são públicos e sem proteção. Qualquer pessoa consegue: criar/deletar/modificar usuários de outros, ver todas as tasks, modificar tasks de outro usuário, acessar relatórios administrativos. O token retornado na linha 210 (`'token': 'fake-jwt-token-'`) é apenas string, não oferece segurança.

**3. Senha exposta em respostas de API**
- **Arquivo:** `models/user.py` (linha 21, método `to_dict()`)
- **Explicação:** O método `to_dict()` retorna o campo `password` no JSON de resposta. O hash MD5 (linhas 29-32) é criptograficamente quebrado e reversível com rainbow tables. Nunca deve retornar senha/hash na API.

**4. Secret key hardcoded e fraca**
- **Arquivo:** `app.py` (linha 13)
- **Explicação:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` está no código-fonte. Deveria usar variáveis de ambiente e uma chave forte e aleatória.

#### 🟡 MEDIUM

**5. Código duplicado — Lógica de "overdue" repetida 5+ vezes**
- **Arquivo:** `task_routes.py` (linhas 30-39, 71-80), `user_routes.py` (linhas 171-180), `report_routes.py` (linhas 34-43, 132-135)
- **Explicação:** Mesma lógica de verificação de task atrasada está duplicada em múltiplas funções. Deveria ser um método reutilizável no modelo (já existe `is_overdue()` em `models/task.py` mas não é usado). Duplicação aumenta bugs e dificulta manutenção.

**6. Problema N+1 Queries em `get_tasks()`**
- **Arquivo:** `task_routes.py` (linhas 14-59)
- **Explicação:** Para cada task retornada, faz uma query adicional de usuário (linha 42) e outra de categoria (linha 51). Se há 100 tasks = 1 + 100 + 100 = 201 queries ao banco! Deveria usar eager loading com `joinedload()` ou `selectinload()`.

#### 🔵 LOW

**7. Nomes de variáveis muito abreviados**
- **Arquivo:** `task_routes.py` (linha 16: `t`), `user_routes.py` (linha 14: `u`)
- **Explicação:** Usa `t` para task e `u` para user em loops. Reduz legibilidade. Deveria usar `task` e `user` completo.

**8. Debug mode ativado em produção**
- **Arquivo:** `app.py` (linha 34)
- **Explicação:** `app.run(debug=True, host='0.0.0.0', port=5000)` ativa debug mode que expõe stack traces detalhados, permite REPL interativo, e causa reloads desnecessários. Deveria usar `False` em produção.

**Resumo dos impactos:** vazamento de credenciais de email, acesso não autorizado a dados, qualquer usuário consegue modificar dados de outro, performance degradada (N+1 queries), exposição de senhas/hashes de produção, código duplicado aumenta manutenção.

---

## 2. Documentação da Skill `/refactor-arch`

A skill vive em `.claude/skills/refactor-arch/` e é **copiada identicamente** para os três projetos (`code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`), provando que é agnóstica de tecnologia — o mesmo `SKILL.md` e o mesmo conjunto de arquivos de referência funcionam tanto em Flask quanto em Express.

### 2.1 Funcionamento em 3 fases

```
Fase 1: ANÁLISE  →  Fase 2: AUDITORIA (+ pausa)  →  [confirmação humana]  →  Fase 3: REFATORAÇÃO MVC
```

**Fase 1 — Análise**
Detecta a stack do projeto (linguagem, framework, dependências), mapeia a arquitetura atual (arquivos monolíticos vs. já organizados em camadas), identifica o domínio da aplicação e as tabelas/entidades do banco de dados, e imprime um resumo estruturado antes de prosseguir.

**Fase 2 — Auditoria / Pausa**
Cruza o código contra o catálogo de anti-patterns (`antipatterns.md`), gera um relatório de auditoria completo seguindo o formato de `report-template.md` — com cada finding classificado por severidade (CRITICAL/HIGH/MEDIUM/LOW), arquivo e linhas exatos — e **pausa a execução, pedindo confirmação explícita do usuário** antes de tocar em qualquer arquivo. Nenhuma modificação ocorre nesta fase.

**Fase 3 — Refatoração MVC**
Somente após a confirmação, reestrutura o projeto para o padrão MVC/camadas definido em `architecture-rules.md`, aplicando as transformações concretas descritas em `refactoring-playbook.md` para cada anti-pattern encontrado (ex.: SQL Injection → ORM/prepared statements, senhas em texto plano → bcrypt, credenciais hardcoded → variáveis de ambiente, N+1 → eager loading). Ao final, valida o resultado contra `heuristics.md` (checklist de qualidade e segurança) e confirma que a aplicação sobe sem erros e os endpoints originais continuam respondendo.

### 2.2 Papel dos 6 arquivos `.md` da skill

Cada projeto contém uma cópia idêntica destes 6 arquivos em `.claude/skills/refactor-arch/`:

| Arquivo | Papel |
|---|---|
| **`SKILL.md`** | Ponto de entrada da skill. Descreve o overview, propósito, escopo, o fluxo das 3 fases, a tabela de severidades e os princípios guia (Security First, Separation of Concerns, DRY, SOLID, Performance, Testability). É o "prompt" que orquestra o uso dos demais arquivos. |
| **`antipatterns.md`** | Catálogo com 12 anti-patterns cobrindo as 4 severidades (CRITICAL: SQL Injection, credenciais hardcoded, autenticação ausente, criptografia fraca; HIGH: N+1 queries, callback hell; MEDIUM: código duplicado, variáveis globais, exception handling genérico, validação inconsistente, **APIs/métodos deprecated**; LOW: **magic numbers e nomenclatura pouco descritiva**), cada um com sinais de detecção, severidade, impacto e categoria — a base de conhecimento usada na Fase 2. |
| **`architecture-rules.md`** | Diretrizes da arquitetura-alvo: camadas MVC (routes/views → controllers → services → models/repositories → db), responsabilidade de cada camada e regras de organização de diretórios — a referência usada na Fase 3. |
| **`refactoring-playbook.md`** | Playbooks passo-a-passo de transformação (mínimo 8), cada um com exemplo de código "antes" e "depois" para resolver um anti-pattern específico do catálogo — aplicado durante a Fase 3. |
| **`heuristics.md`** | Checklist de heurísticas de qualidade (segurança, autenticação, performance, manutenibilidade) usado para validar o resultado da refatoração ao final da Fase 3. |
| **`report-template.md`** | Template estruturado do relatório de auditoria (Executive Summary, score de saúde do projeto, tabela de findings, seção "o que foi feito", decisões/observações, pendências, resultado dos testes) — formato seguido pela saída da Fase 2 e pelos relatórios em `reports/`. |

### 2.3 Comandos de uso

A skill é invocada a partir da raiz de cada projeto:

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução, a Fase 2 pausa e aguarda confirmação (`Proceed with refactoring (Phase 3)? [y/n]`) antes de qualquer alteração de código ser aplicada.

---

## 3. Relatórios

Os relatórios de auditoria gerados pela Fase 2 da skill (após a Fase 3 concluída, atualizados com o resultado "antes → depois") estão salvos em [`reports/`](reports/):

| Relatório | Projeto | Conteúdo |
|---|---|---|
| [`reports/audit-project-1.md`](reports/audit-project-1.md) | `code-smells-project` (Flask) | 13 findings (8 CRITICAL, 1 HIGH, 4 MEDIUM). Score geral 26% → 90%, com 27 testes automatizados cobrindo segurança, autorização e regressão de N+1. |
| [`reports/audit-project-2.md`](reports/audit-project-2.md) | `ecommerce-api-legacy` (Express) | 10 findings cobrindo credenciais hardcoded, criptografia fraca, validação de pagamento e callback hell/race condition. Score geral inicial de 16%. |
| [`reports/audit-project-3.md`](reports/audit-project-3.md) | `task-manager-api` (Flask, parcialmente organizado) | Findings equivalentes de segurança e qualidade mesmo com separação superficial em `models/routes/services/utils` pré-existente. Score geral 30% → 91%, com 61 testes automatizados. |

Cada relatório segue o formato de `report-template.md`: Executive Summary com score de saúde do projeto, tabela de findings por severidade com arquivo/linhas exatos, seção "o que foi feito" (mapeando cada finding à correção aplicada), decisões e observações, pendências fora do escopo e resultado da suíte de testes.

---

## 4. Correções aplicadas após revisão

A primeira submissão recebeu o seguinte retorno:

> "O SKILL.md copiado nos três projetos não descreve as 3 fases do fluxo (não fala em pausar para confirmação antes da Fase 3 nem em validar boot e endpoints ao final dela), e o antipatterns.md não tem nenhum anti-pattern de severidade LOW nem cobre detecção de APIs deprecated."

Ações tomadas em resposta, replicadas identicamente nos 3 projetos:

1. **`SKILL.md` reescrito** com as 3 fases explícitas (`FASE 1 — Análise` → `FASE 2 — Auditoria` com o gate obrigatório `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` → `FASE 3 — Refatoração + Validação`), incluindo uma checklist de validação obrigatória (boot sem erros, endpoints originais respondendo, suíte de testes passando, heurísticas revisadas) antes de declarar a Fase 3 concluída.
2. **`antipatterns.md` ampliado** de 10 para 12 anti-patterns: `#11 Uso de APIs e Métodos Deprecated` (MEDIUM) e `#12 Magic Numbers e Nomenclatura Pouco Descritiva` (LOW) — cada um com exemplos Python/Node.js e correção. `refactoring-playbook.md` ganhou os playbooks #11 e #12 correspondentes.
3. **A skill foi executada novamente (Fases 1-3) nos 3 projetos** com o catálogo atualizado:
   - `code-smells-project`: 1 novo finding LOW (magic numbers em `relatorio_service.py`) corrigido.
   - `ecommerce-api-legacy`: 0 novos findings — código já não usava APIs deprecated nem tinha magic numbers relevantes.
   - `task-manager-api`: 16 ocorrências de `datetime.utcnow()` (deprecated desde Python 3.12) + variáveis abreviadas (`t`, `u`, `n`) encontradas e corrigidas. A correção do datetime expôs um bug real (comparação entre datetime aware e naive, `TypeError`) que foi corrigido junto — ver `reports/audit-project-3.md` para o detalhe.
   - Os 3 relatórios em `reports/` foram atualizados com uma seção "Re-auditoria" documentando essa segunda execução (findings, confirmação, correção e validação de boot/testes/endpoints).

O segundo retorno apontou um problema mais específico:

> "O architecture-rules.md da sua skill define uma camada de Models (Domain Objects), mas o ecommerce-api-legacy continua sem pasta models/: repositórios como courseRepository.js devolvem direto para os services as linhas cruas do banco (this.db.get/this.db.all), sem nenhuma classe de domínio. Reforce a Fase 3 para aplicar essa guideline também no ecommerce-api-legacy e rode a skill de novo nos 3 projetos."

Causa raiz: `architecture-rules.md` só tinha exemplo de Models em Python/SQLAlchemy — nada mostrava como essa camada deveria se parecer numa stack sem ORM (Node.js + driver `sqlite3` cru), então a Fase 3 original não soube o que gerar ali. Ações tomadas:

4. **`architecture-rules.md` reforçado** com um exemplo completo de Model sem ORM (classe + `fromRow(row)` estático, em JavaScript), um contraste explícito "❌ repository devolvendo row crua" vs. "✅ repository devolvendo entidade", e a frase "esta camada é obrigatória mesmo sem ORM". `heuristics.md` ganhou uma checklist item + red flag específicos (grep por `return this.db.get(`/`return this.db.all(` sem transformação no meio). `SKILL.md` (Fase 3) passou a exigir esse grep antes de declarar a fase concluída. Reforço sincronizado nos 3 projetos.
5. **Criado `ecommerce-api-legacy/src/models/`** com 4 classes de domínio (`User`, `Course`, `Enrollment`, `Payment`), cada uma com `fromRow(row)`. Os 4 repositories relevantes (`courseRepository`, `userRepository`, `enrollmentRepository`, `paymentRepository`) passaram a montar essas entidades em vez de devolver `row`/`lastID` crus; `checkoutService`/`authService` atualizados para consumir as entidades (`user.verifyPassword()`, `user.toPublicJSON()`, `enrollment.id`).
6. **Skill executada novamente nos 3 projetos**: `code-smells-project` e `task-manager-api` já usam ORM (SQLAlchemy) — confirmado que suas queries já retornam instâncias de `models/`, nenhum finding novo. `ecommerce-api-legacy` teve o finding (HIGH: camada de Models ausente) corrigido e validado (21 testes passando, boot limpo, checkout ponta-a-ponta testado via curl). Reportado em detalhe em `reports/audit-project-2.md`.
