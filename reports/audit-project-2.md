# 📋 Relatório de Auditoria Arquitetural

**Projeto:** ecommerce-api-legacy (Node.js/Express)
**Data:** 2026-08-08
**Auditor:** Claude Code
**Status:** Concluído

---

## 📊 Executive Summary

### Score de Saúde do Projeto (antes da refatoração)

```
Segurança:        🔴 15%
Qualidade:        🔴 25%
Performance:      🔴 20%
Manutenibilidade: 🔴 20%
Testabilidade:    🔴 0%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORE GERAL:      🔴 16%
```

### Findings Críticos

| # | Problema | Severidade | Arquivo | Linha |
|---|----------|-----------|---------|-------|
| 1 | Credenciais e chave de gateway de pagamento hardcoded | 🔴 CRITICAL | utils.js | 2-6 |
| 2 | Nenhuma autenticação/autorização em rotas administrativas | 🔴 CRITICAL | AppManager.js | 80, 131 |
| 3 | Hash de senha "fake" (não é criptografia) | 🔴 CRITICAL | utils.js | 17-23 |
| 4 | Número completo do cartão logado em texto plano | 🔴 CRITICAL | AppManager.js | 45 |
| 5 | N+1 queries no relatório financeiro | 🟠 HIGH | AppManager.js | 80-129 |
| 6 | Callback hell (4 níveis) no checkout e relatório | 🟠 HIGH | AppManager.js | 28-129 |
| 7 | Estado global mutável (`globalCache`, `totalRevenue`) | 🟡 MEDIUM | utils.js | 9-15 |
| 8 | `DELETE /users/:id` deixa matrículas/pagamentos órfãos | 🟡 MEDIUM | AppManager.js | 131-137 |
| 9 | Nenhuma validação de entrada (checkout aceita qualquer coisa) | 🟡 MEDIUM | AppManager.js | 28-35 |
| 10 | Cobertura de testes: 0% | 🟡 MEDIUM | — | — |

### Recomendação

**BLOQUEAR MERGE** (estado original) → após refatoração: **PODE FAZER MERGE**

---

## 🔍 Findings Detalhados

### [#1] Credenciais e Chave de Gateway de Pagamento Hardcoded

**Severidade:** 🔴 CRITICAL · **Categoria:** Segurança
**Arquivo:** `utils.js:2-6`

```javascript
const config = {
    dbUser: "admin_master",
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    ...
};
```

Uma chave de gateway de pagamento **live** commitada no código-fonte é publicamente
visível a qualquer pessoa com acesso ao repositório.

**Correção:** `src/config/index.js` carrega tudo via `process.env` (dotenv), com
`.env.example` documentando as variáveis e `.env` real fora do controle de versão.
A aplicação falha ao subir se `JWT_SECRET` não estiver definido em produção.

---

### [#2] Sem Autenticação/Autorização em Rotas Administrativas

**Severidade:** 🔴 CRITICAL · **Categoria:** Segurança
**Arquivo:** `AppManager.js:80` (`GET /api/admin/financial-report`), `AppManager.js:131`
(`DELETE /api/users/:id`)

Qualquer pessoa não autenticada conseguia ler o relatório financeiro completo (receita,
lista de alunos) e deletar qualquer usuário.

**Correção:** Middleware JWT (`src/middleware/auth.js`) com `authenticate` +
`requireAdmin`, aplicado às duas rotas. Login em `POST /api/auth/login` retorna um
token assinado com expiração de 1h. Cobertura de teste garante 401 sem token e 403
para usuário autenticado sem role `admin` (`tests/admin.test.js`).

---

### [#3] Hash de Senha "Fake"

**Severidade:** 🔴 CRITICAL · **Categoria:** Segurança
**Arquivo:** `utils.js:17-23`

```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```

Isso não é um hash criptográfico: é determinístico a partir de base64 e trunca para
10 caracteres — colisões triviais, reversível na prática.

**Correção:** `bcrypt` (10 rounds via `BCRYPT_ROUNDS`) em `checkoutService.js` e
comparado em `authService.js` via `bcrypt.compare`. Nenhum hash é retornado em
respostas de API (verificado em `tests/security.test.js`).

---

### [#4] Número de Cartão Logado em Texto Plano

**Severidade:** 🔴 CRITICAL · **Categoria:** Segurança
**Arquivo:** `AppManager.js:45`

```javascript
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```

PAN completo e a chave do gateway iam parar nos logs — violação direta de PCI-DSS.

**Correção:** `checkoutService.js` mascara o cartão (`maskCard`) antes de logar e a
chave do gateway nunca é logada.

---

### [#5] N+1 Queries no Relatório Financeiro

**Severidade:** 🟠 HIGH · **Categoria:** Performance
**Arquivo:** `AppManager.js:80-129`

Para C cursos e E matrículas totais, o endpoint original disparava
`1 + C + 2*E` queries (uma por curso, e duas por matrícula dentro do loop).

**Correção:** `reportRepository.getFinancialReport()` resolve tudo em **uma única
query** com `LEFT JOIN` entre `courses`, `enrollments`, `users` e `payments`,
agrupando os resultados em memória. Testado em `tests/security.test.js`
("resolves with a single query").

---

### [#6] Callback Hell (4 níveis) no Checkout e Relatório

**Severidade:** 🟠 HIGH · **Categoria:** Manutenibilidade
**Arquivo:** `AppManager.js:28-129`

Checkout e relatório financeiro tinham callbacks aninhados em até 4 níveis, com
contadores manuais (`enrPending`, `coursesPending`) para saber quando responder.

**Correção:** `src/db/index.js` promisifica `run/get/all/exec` sobre `sqlite3`, e
todos os services/repositories usam `async/await` com `try/catch` delegando para
`errorHandler` central.

---

### [#7] Estado Global Mutável

**Severidade:** 🟡 MEDIUM · **Categoria:** Confiabilidade
**Arquivo:** `utils.js:9-15`

```javascript
let globalCache = {};
let totalRevenue = 0;
```

Módulo-level mutável, compartilhado entre todas as requisições do processo, sem
nenhum motivo para não ser encapsulado.

**Correção:** `src/utils/cache.js` encapsula o cache em uma classe `Cache`,
instanciada uma vez por `createApp(db)` (uma instância por processo/teste, não um
singleton implícito exportado por referência). `totalRevenue` foi removido — não era
lido em lugar nenhum do código original.

---

### [#8] `DELETE /users/:id` Deixa Dados Órfãos

**Severidade:** 🟡 MEDIUM · **Categoria:** Integridade de Dados
**Arquivo:** `AppManager.js:131-137`

```javascript
this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
    res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
});
```

O próprio comentário da API admitia o problema.

**Correção:** `userRepository.deleteCascade()` roda em uma transação
(`db.transaction`) que remove pagamentos → matrículas → usuário, com rollback se
qualquer passo falhar. Coberto em `tests/admin.test.js`
("cascades enrollments and payments").

---

### [#9] Nenhuma Validação de Entrada

**Severidade:** 🟡 MEDIUM · **Categoria:** Qualidade
**Arquivo:** `AppManager.js:28-35`

O checkout só checava presença (`!u || !e || !cid || !cc`), sem validar formato de
email, tamanho de nome, formato do cartão, ou se `courseId` era um número válido.
Um novo usuário sem senha herdava a senha fixa `"123456"`.

**Correção:** `validators/checkoutValidator.js` e `validators/authValidator.js`
usam schemas Joi centralizados. Senha passa a ser **obrigatória** para novos
usuários (sem fallback fraco) — `tests/checkout.test.js`
("rejects a new user without a password").

---

## 📈 Comparativo Antes vs Depois

### Antes (Legado)

```
Segurança:   🔴 CRÍTICA (credenciais expostas, sem auth, hash fake, PAN em log)
Qualidade:   🔴 RUIM (callback hell, validação ausente, estado global)
Performance: 🔴 PÉSSIMA (N+1: até 1 + C + 2E queries no relatório)
Arquitetura: 2 arquivos (app.js, AppManager.js) + utils.js
Testes:      0%
```

### Depois (Refatorado)

```
Segurança:   🟢 JWT + bcrypt + .env + card masking + validação centralizada
Qualidade:   🟢 Arquitetura em camadas, DRY, exceções tipadas
Performance: 🟢 Relatório financeiro em 1 única query
Arquitetura: 24 arquivos organizados em config/db/repositories/services/
             validators/middleware/routes/utils
Testes:      21 testes de integração (Jest + Supertest), cobrindo auth,
             checkout, autorização e segurança
```

---

## 📋 Checklist de Implementação

### Fase 1: Segurança Crítica
- [x] Mover credenciais para `.env` / `config/index.js`
- [x] Implementar autenticação JWT (`POST /api/auth/login`)
- [x] Implementar autorização admin (`requireAdmin`) em rotas administrativas
- [x] Trocar hash fake por bcrypt
- [x] Mascarar número de cartão em logs

### Fase 2: Performance e Qualidade
- [x] Relatório financeiro: 1 query com JOIN em vez de N+1
- [x] Converter callbacks para async/await
- [x] Validação centralizada com Joi

### Fase 3: Manutenibilidade
- [x] Remover estado global mutável (cache encapsulado em classe)
- [x] `DELETE /users/:id` com cascade transacional
- [x] Exceções tipadas + error handler central (sem `catch` genérico vazando detalhes)

### Fase 4: Testing & Documentation
- [x] 21 testes de integração cobrindo auth, checkout, autorização, segurança
- [x] README atualizado com setup e fluxo de autenticação
- [x] `api.http` atualizado com exemplos de login/token

---

## 📊 Métricas de Sucesso

| Métrica | Antes | Depois |
|---------|-------|--------|
| Queries no relatório (2 cursos, 2 matrículas) | 1 + 2 + 2×2 = 7 | 1 |
| Testes | 0% | 21 testes passando |
| Vulnerabilidades críticas | 4 | 0 |
| Credenciais no código-fonte | 3 (dbPass, paymentGatewayKey, hash fake) | 0 |
| Endpoints admin sem proteção | 2 (financial-report, delete user) | 0 |

---

## 📝 Notas & Observações

### Pontos Positivos do Código Original
- Uso de prepared statements (`?`) já era consistente em todas as queries SQL —
  não havia SQL injection por concatenação, diferente do padrão comum nesse tipo de
  desafio.
- Separação mínima entre `app.js` (bootstrap) e `AppManager.js` (lógica) já indicava
  alguma intenção de organização.

### Decisões de Design
- Os nomes de campos do payload de `/api/checkout` foram normalizados de
  abreviações (`usr`, `eml`, `pwd`, `c_id`, `card`) para nomes descritivos (`name`,
  `email`, `password`, `courseId`, `cardNumber`), já que a reformulação da API é
  parte do escopo desta refatoração.
- O gateway de pagamento continua mockado (heurística "cartão começa com 4 =
  aprovado"), pois a integração real está fora do escopo deste desafio — o foco foi
  eliminar os vazamentos de dados sensíveis ao redor dele.

---

**Relatório Finalizado:** SIM
**Pronto para Merge:** SIM
