---
name: refactor-arch
description: Analisa, audita e refatora um projeto backend (qualquer linguagem/framework) para o padrão MVC em 3 fases — Análise, Auditoria (com pausa de confirmação), Refatoração + Validação. Use quando o usuário pedir para auditar/refatorar a arquitetura de um projeto, ou invocar "/refactor-arch" explicitamente.
---

# Refactor Architecture Skill (`/refactor-arch`)

## Overview

Esta skill fornece um framework completo para auditar, identificar e refatorar problemas arquiteturais em aplicações web backend. Ela é agnóstica de tecnologia — funciona em qualquer linguagem/framework backend (validada em Python/Flask e Node.js/Express) — detectando anti-patterns, violações de segurança, ineficiências de performance, problemas de manutenibilidade e uso de APIs deprecated.

## Propósito

Transformar código legado com problemas arquiteturais críticos em aplicações bem estruturadas, seguras e mantíveis, seguindo o padrão MVC (Model-View-Controller / camadas) e boas práticas de segurança — com um humano no controle de quando as mudanças efetivamente são aplicadas.

## Escopo

- **Auditoria de código:** identificação sistemática de anti-patterns e code smells
- **Análise de segurança:** SQL Injection, credenciais hardcoded, autenticação/autorização ausente, criptografia fraca
- **Otimização de performance:** N+1 queries, callback hell, operações ineficientes
- **Modernização:** detecção de APIs/métodos deprecated
- **Refatoração arquitetural:** separação de responsabilidades, camadas bem definidas (MVC)
- **Validação:** garantir que a aplicação continua funcionando após a refatoração

## Documentos de Referência

| Arquivo | Quando é usado |
|---|---|
| `heuristics.md` | Fase 1 — heurísticas para detectar linguagem, framework, banco de dados e mapear a arquitetura atual |
| `antipatterns.md` | Fase 2 — catálogo de anti-patterns (12+, severidade CRITICAL/HIGH/MEDIUM/LOW, inclui APIs deprecated) usado para cruzar contra o código |
| `report-template.md` | Fase 2 — formato padronizado do relatório de auditoria |
| `architecture-rules.md` | Fase 3 — estrutura de camadas MVC alvo |
| `refactoring-playbook.md` | Fase 3 — transformações concretas (antes/depois) para cada anti-pattern encontrado |

---

## Fluxo de Execução — 3 Fases Sequenciais e Obrigatórias

A skill **nunca pula fase, nunca modifica código antes da Fase 3, e nunca conclui a Fase 3 sem validar o resultado.** Cada fase abaixo é um gate: a fase seguinte só começa quando a anterior termina.

```
FASE 1: ANÁLISE  →  FASE 2: AUDITORIA  →  ⏸ PAUSA (confirmação humana)  →  FASE 3: REFATORAÇÃO + VALIDAÇÃO
```

### FASE 1 — Análise (somente leitura)

Objetivo: entender o projeto antes de julgá-lo. Nenhum arquivo é modificado nesta fase.

1. Detectar a linguagem e o framework (arquivos de manifesto: `requirements.txt`/`pyproject.toml`, `package.json`, etc. — ver `heuristics.md`).
2. Listar as dependências relevantes (framework web, ORM/driver de banco, libs de auth).
3. Mapear a arquitetura atual: contar arquivos-fonte, identificar se já existe separação em camadas (`routes/`, `models/`, `services/`...) ou se é monolítico (poucos arquivos concentrando tudo).
4. Identificar o domínio da aplicação (ex.: e-commerce, task manager, LMS) e as tabelas/entidades do banco de dados.
5. Imprimir um resumo estruturado, no formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <domínio da aplicação>
Architecture:  <Monolítica | Parcialmente organizada | Em camadas> — <detalhe>
Source files:  <N> files analyzed
DB tables:     <lista de tabelas/entidades>
================================
```

### FASE 2 — Auditoria (somente leitura + geração de relatório)

Objetivo: produzir o relatório de auditoria completo. **Nenhum arquivo de código é modificado nesta fase.**

1. Cruzar o código, arquivo por arquivo, contra cada anti-pattern de `antipatterns.md` — incluindo explicitamente a checagem de **APIs/métodos deprecated** (versões de dependências, funções descontinuadas pela linguagem/framework).
2. Para cada problema encontrado, registrar: severidade (CRITICAL/HIGH/MEDIUM/LOW), categoria, arquivo e linha(s) exatas, descrição, impacto e recomendação.
3. Gerar o relatório completo seguindo `report-template.md`, com os findings **ordenados por severidade (CRITICAL → LOW)**.
4. Salvar o relatório em `reports/audit-project-N.md` (na raiz do repositório, fora do projeto individual).
5. Imprimir o resumo do relatório no terminal, no formato:

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<LOC> lines of code

Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

Findings
[CRITICAL] <título>
File: <arquivo>:<linhas>
Description: <descrição>
Impact: <impacto>
Recommendation: <recomendação>

... (demais findings, ordenados por severidade) ...

================================
Total: <N> findings
================================
```

6. **GATE OBRIGATÓRIO — pausar e pedir confirmação explícita antes de qualquer alteração:**

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

   - Esta pergunta é feita ao usuário via prompt interativo (ou via ferramenta de pergunta ao usuário, se disponível) e a skill **aguarda a resposta**.
   - Se a resposta for `n`/`não`: a skill **para imediatamente**, sem tocar em nenhum arquivo. O relatório de auditoria já salvo é o entregável final desta execução.
   - Se a resposta for `y`/`sim`: a skill prossegue para a Fase 3.
   - É proibido interpretar silêncio, contexto de conversas anteriores ou instruções genéricas ("pode continuar com tudo") como confirmação para esta pergunta específica — a confirmação deve ser inequívoca e feita depois que o relatório já foi mostrado.

### FASE 3 — Refatoração + Validação (somente após confirmação)

Objetivo: eliminar os problemas encontrados e provar que a aplicação continua funcionando.

1. Reestruturar o projeto para o padrão de camadas descrito em `architecture-rules.md` (Models / Views-Routes / Controllers-Services, config isolada, error handling centralizado, entry point único). **A camada de Models é obrigatória independentemente de a stack ter ORM.** Em stacks com driver SQL cru (ex.: Node.js + `sqlite3`/`pg` sem Sequelize/TypeORM), criar `models/` com uma classe por entidade e um `fromRow(row)` estático — nenhum repository pode devolver a linha crua do banco (`row`/`rows`) direto para o service. Antes de declarar a Fase 3 concluída, grepar os repositories por `return this.db.get(`/`return this.db.all(`/equivalente sem transformação no meio — se aparecer, a camada de Models está incompleta.
2. Para cada finding do relatório da Fase 2, aplicar a transformação correspondente de `refactoring-playbook.md` (ex.: SQL Injection → ORM/prepared statements; credenciais hardcoded → variáveis de ambiente; senha em texto plano/MD5 → bcrypt; N+1 → eager loading; API deprecated → substituir pela API atual equivalente).
3. Rodar a suíte de testes automatizados existente, se houver (`pytest`, `npm test`, etc.), e corrigir regressões.
4. **Validação obrigatória — a Fase 3 só é considerada concluída se todos os itens abaixo forem checados de fato (não apenas assumidos):**
   - [ ] A aplicação inicia sem erros com o comando de boot do projeto (`flask run`, `npm start`, etc.)
   - [ ] Os endpoints que existiam **antes** da refatoração continuam respondendo, com o mesmo contrato observável (mesmo path, método e formato de resposta esperado) — validar com requisições reais (curl/http client) ou com a suíte de testes de integração existente
   - [ ] A suíte de testes automatizados passa (ou, se não existia suíte antes, os testes criados durante a refatoração passam)
   - [ ] Checklist de `heuristics.md` revisado — sem "red flags" remanescentes
5. Atualizar `reports/audit-project-N.md` com a seção "O que foi feito" (mapeando cada finding à correção aplicada), decisões/observações, pendências fora do escopo, e o resultado real da validação/testes.
6. Imprimir o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore de diretórios resultante>

Validation
 ✓/✗ Application boots without errors
 ✓/✗ All original endpoints respond correctly
 ✓/✗ Automated test suite passes
 ✓/✗ Zero anti-patterns remaining (per heuristics.md)
================================
```

   Se algum item da validação falhar (✗), a skill **não declara sucesso** — corrige o problema e valida novamente antes de considerar a Fase 3 concluída.

---

## Severidades Tratadas

| Severidade | Descrição | Ação |
|------------|-----------|------|
| CRITICAL | Falha grave de arquitetura/segurança: impede funcionamento correto, expõe dados sensíveis (credenciais hardcoded, SQL Injection) ou viola completamente a separação de responsabilidades ("God Class") | Corrigir primeiro, bloqueia produção |
| HIGH | Forte violação do padrão MVC/SOLID: lógica de negócio pesada em controllers, acoplamento forte sem DI, estado global mutável | Corrigir antes de merge |
| MEDIUM | Padronização, duplicação de código, gargalos de performance moderada (N+1, middlewares inadequados, validação ausente) | Agendar para próximo ciclo |
| LOW | Legibilidade, nomenclatura de variáveis, magic numbers | Melhorias contínuas |

## Princípios Guia

1. **Security First:** toda refatoração prioriza segurança
2. **Separation of Concerns:** camadas bem definidas (routes/views → controllers/services → models/repositories → db)
3. **DRY (Don't Repeat Yourself):** código duplicado é combatido agressivamente
4. **SOLID Principles:** responsabilidade única, aberto/fechado, substituição de Liskov, segregação de interface, inversão de dependência
5. **Performance:** queries otimizadas, sem N+1, caching inteligente
6. **Testability:** código facilmente testável, com injeção de dependência
7. **Human-in-the-loop:** nenhuma mudança de código acontece sem confirmação explícita após a auditoria

## Linguagens/Frameworks Suportados

- **Python:** Flask, Django, FastAPI
- **Node.js:** Express, NestJS, Fastify
- **Princípios:** aplicáveis a qualquer stack web — os arquivos de referência (`antipatterns.md`, `refactoring-playbook.md`) trazem exemplos em Python e Node.js lado a lado; para outras stacks, os mesmos princípios de detecção e correção se aplicam, adaptando a sintaxe.

## Próximos Passos

1. Leia `heuristics.md` para os sinais de detecção usados na Fase 1.
2. Leia `antipatterns.md` para o catálogo completo usado na Fase 2.
3. Leia `architecture-rules.md` e `refactoring-playbook.md` para a execução da Fase 3.
