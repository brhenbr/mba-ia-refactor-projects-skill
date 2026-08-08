# Refactor Architecture Skill

## Overview

Esta skill fornece um framework completo para auditar, identificar e refatorar problemas arquiteturais em aplicações web. Ela é especializada em detectar anti-patterns, violações de segurança, ineficiências de performance e problemas de manutenibilidade em projetos Python/Flask e Node.js/Express.

## Propósito

Transformar código legado com problemas arquiteturais críticos em aplicações bem estruturadas, seguras e mantíveis seguindo princípios de Clean Architecture, MVC com separação de camadas e boas práticas de segurança.

## Escopo

- **Auditoria de código:** Identificação sistemática de anti-patterns e code smells
- **Análise de segurança:** Detecção de vulnerabilidades (SQL Injection, credenciais hardcoded, autenticação/autorização)
- **Otimização de performance:** N+1 queries, callback hell, operações ineficientes
- **Refatoração arquitetural:** Separação de responsabilidades, camadas bem definidas
- **Validação:** Garantir conformidade com regras de arquitetura após refatoração

## Casos de Uso Cobertos

1. **Aplicações legadas com SQL Injection** → Prepared statements + ORM
2. **Sem autenticação/autorização** → JWT + middleware de segurança
3. **Credenciais hardcoded** → Variáveis de ambiente + .env
4. **Senhas em texto plano/MD5** → Bcrypt/Argon2
5. **Código duplicado** → Refatoração para reutilização
6. **N+1 queries** → Eager loading + SQL otimizado
7. **Callback hell** → Async/await ou promises (Node.js) / async functions (Python)
8. **Validação inconsistente** → Camada centralizada de validação

## Fluxo de Uso

```
1. Rodando /refactor-audit [projeto]
   ↓
2. Skill analisa código contra anti-patterns.md
   ↓
3. Gera relatório detalhado (report-template.md)
   ↓
4. Aplica playbooks.md conforme severidade
   ↓
5. Refatora seguindo architecture-rules.md
   ↓
6. Valida contra heuristics.md
   ↓
7. Retorna código refatorado + relatório executivo
```

## Documentos de Referência

- **antipatterns.md:** 8+ anti-patterns com severidade, impacto e exemplos
- **architecture-rules.md:** Diretrizes MVC, separação de camadas, organização
- **refactoring-playbook.md:** Playbooks antes/depois com transformações passo-a-passo
- **heuristics.md:** Heurísticas de qualidade e checklist de validação
- **report-template.md:** Template estruturado para relatórios de auditoria

## Severidades Tratadas

| Severidade | Descrição | Ação |
|------------|-----------|------|
| CRITICAL | Risco imediato de segurança/perda de dados | Corrigir primeiro, bloqueia produção |
| HIGH | Impacto significativo em segurança/funcionalidade | Corrigir antes de merge |
| MEDIUM | Afeta manutenibilidade/performance | Agendar para próximo ciclo |
| LOW | Code quality, legibilidade | Melhorias contínuas |

## Modelo de Refatoração

Todas as refatorações seguem o padrão:

```
[ANTES]
❌ Problema descrito
❌ Código problemático (snippet)
⚠️ Impacto/riscos

[DEPOIS]
✅ Solução aplicada
✅ Código refatorado (snippet)
✅ Benefícios

[CHECKLIST]
- [ ] Passo 1
- [ ] Passo 2
- [ ] Validação
- [ ] Testes
```

## Princípios Guia

1. **Security First:** Toda refatoração prioriza segurança
2. **Separation of Concerns:** Camadas bem definidas (routes → services → models → db)
3. **DRY (Don't Repeat Yourself):** Código duplicado é combatido agressivamente
4. **SOLID Principles:** Responsabilidade única, aberto/fechado, substituição de Liskov, segregação de interface, inversão de dependência
5. **Performance:** Queries otimizadas, sem N+1, caching inteligente
6. **Testability:** Código facilmente testável com injeção de dependência

## Linguagens Suportadas

- **Python:** Flask, Django, FastAPI
- **Node.js:** Express, NestJS, Fastify
- **Princípios:** Aplicáveis a qualquer stack web

## Próximos Passos

Leia `antipatterns.md` para entender os problemas específicos e suas soluções.
