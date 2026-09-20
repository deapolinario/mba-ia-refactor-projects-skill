# Skill: Refactor Architecture

**Versão:** 2.1 (7 CRITICAL/HIGH + 5 MEDIUM/LOW anti-patterns)

**Objetivo:** Analisar, auditar e refatorar projetos legados para o padrão MVC, eliminando vulnerabilidades críticas, problemas arquiteturais e code smells.

---

## Fases de Execução

### Fase 1: Project Analysis

**Objetivo:** Detectar stack, mapear arquitetura atual e imprimir resumo.

**Instruções:**

1. Escanear o projeto e detectar:
   - Linguagem (Python, Node.js, Java, PHP, etc)
   - Framework (Flask, Django, Express,Spring, Fastify, etc)
   - Banco de dados (SQLite, PostgreSQL, MySQL, MongoDB, etc)
   - Domínio (que tipo de aplicação é: Task Manager, E-commerce, LMS, etc)
   - Número de arquivos analisados
   - Tabelas de banco de dados

2. Usar arquivo de referência: `project-analysis.md`

3. Imprimir output formatado:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       [DETECTADO]
Framework:      [DETECTADO]
Database:       [DETECTADO]
Domain:         [DESCRIÇÃO DO DOMÍNIO]
Architecture:   [Monolithic / Partially Organized / Structured]
Source files:   [NÚMERO] files analyzed
DB tables:      [LISTA]
================================
```

4. Caso não consiga detectar algo, pedir ao usuário que confirme.

---

### Fase 2: Architecture Audit

**Objetivo:** Procurar anti-patterns e gerar relatório estruturado.

**Instruções:**

1. Escanear **todos os arquivos** do projeto procurando por:
   
   **CRITICAL:**
   - SQL Injection (string concatenation em queries)
   - Hardcoded Secrets (SECRET_KEY, PASSWORD, API_KEY, etc)
   - Senhas em Texto Plano
   
   **HIGH:**
   - Weak Password Hashing (MD5, SHA1)
   - God Classes (arquivos 300+ linhas)
   - N+1 Queries (loops com queries)
   - Global State Mutável (race conditions)
   
   **MEDIUM:**
   - Code Duplication
   - Secrets Expostas em Responses
   - Logs Sensíveis (PII exposure)
   
   **LOW:**
   - Magic Strings / Magic Numbers
   - Ternários Desnecessários
   - Monolithic Architecture (sem separação models/routes/controllers)

2. Para cada achado:
   - Anotar arquivo e linhas exatas
   - Extrair snippet de código
   - Classificar severidade (CRITICAL ou HIGH)
   - Explicar impacto
   - Propor refatoração

3. Usar arquivo de referência: `anti-patterns-catalog.md` + `audit-report-template.md`

4. Gerar relatório seguindo o template, ordenado por severidade

5. Salvar o relatório automaticamente em `../reports/audit-{repo-name}-{timestamp}.md`:
   - Detectar o nome do repositório atual (code-smells-project, ecommerce-api-legacy, task-manager-api)
   - **IMPORTANTE:** Adicionar timestamp DINÂMICO (do momento ATUAL da execução)
   - Formato ISO: YYYY-MM-DDTHH-MM-SS (exemplo: 2026-09-20T09-15-42)
   - Criar pasta `../reports/` na raiz do exercício se não existir
   - **CADA execução deve gerar um arquivo DIFERENTE com timestamp diferente**
   - Exemplos:
     - Execução 1 (08:45): `audit-code-smells-project-2026-09-20T08-45-00.md`
     - Execução 2 (09:15): `audit-code-smells-project-2026-09-20T09-15-42.md` ← DIFERENTE!
     - Execução 3 (10:30): `audit-code-smells-project-2026-09-20T10-30-18.md` ← DIFERENTE!

6. **IMPORTANTE:** Pausar e pedir confirmação explícita antes de passar para Fase 3:

```
================================
PHASE 2: AUDIT COMPLETE
================================

[RELATÓRIO AQUI]

---

Total findings: X (X CRITICAL, X HIGH)

**Confirmar refatoração na Fase 3? (y/n)**
```

6. Se usuário responder `y` ou `yes`, prosseguir para Fase 3.
   Se `n` ou `no`, interromper e perguntar se deseja exportar o relatório.

---

### Fase 3: Refactoring & Validation

**Objetivo:** Aplicar refatorações e validar que a aplicação continua funcionando.

**Instruções:**

1. Aplicar refatorações conforme achados (prioridade: CRITICAL → HIGH → MEDIUM):

   **CRITICAL - SQL Injection:**
   - Converter queries com concatenation para parameterized queries
   - Usar ORM methods quando disponível

   **CRITICAL - Hardcoded Secrets:**
   - Criar `config.py` (Python) ou `config.js` (Node.js)
   - Carregar de `os.getenv()` ou `process.env`
   - Criar `.env` com valores reais, adicionar ao `.gitignore`

   **CRITICAL - God Classes:**
   - Separar em `models/`, `routes/`, `controllers/`
   - Cada arquivo com uma responsabilidade clara

   **HIGH - Weak Password Hashing:**
   - Substituir MD5/SHA1 por bcrypt ou argon2
   - Aplicar em todos os `set_password()` e password checks

   **HIGH - N+1 Queries:**
   - Usar eager loading (`joinedload`, `include`)
   - Converter loops com queries em single query com joins

   **MEDIUM - Code Duplication:**
   - Extrair lógica duplicada em métodos/helpers
   - Centralizar transformações em `to_dict()` ou helpers

   **CRITICAL - Monolithic Architecture:**
   - Criar estrutura: `config/`, `models/`, `routes/`, `controllers/`
   - Mover lógica para camadas apropriadas
   - Limpar `app.py` para apenas entry point

2. Usar arquivo de referência: `refactoring-playbook.md`

3. Após aplicar refatorações:
   - Tentar dar startup na aplicação
   - Validar que não há erros de sintaxe
   - Se possível, testar alguns endpoints chave

4. Imprimir output de validação:

```
================================
PHASE 3: REFACTORING COMPLETE
================================

Changes applied:
  ✓ SQL Injection fixes: X queries → parameterized
  ✓ Secrets extracted: X values → config + .env
  ✓ Password hashing upgraded: X → bcrypt/argon2
  ✓ God Classes split: X files → models + routes + controllers
  ✓ N+1 Queries eliminated: X queries → eager loading
  ✓ Duplications removed: X patterns → helpers
  ✓ Architecture restructured: → MVC pattern

New structure:
  ✓ config/ — configurações
  ✓ models/ — estrutura de dados
  ✓ routes/ — mapeamento HTTP
  ✓ controllers/ — lógica de negócio
  ✓ app.py — entry point limpo

Validation:
  ✓ Application boots without errors
  ✓ No syntax errors detected
  ✓ All secrets removed from source code
  ✓ No password hashes in MD5/SHA1
  ✓ No N+1 query patterns detected
  ✓ MVC structure verified

================================
```

---

## Referências Carregadas

- `project-analysis.md` → Heurísticas de detecção
- `anti-patterns-catalog.md` → Catálogo de problemas
- `audit-report-template.md` → Formato de relatório
- `refactoring-playbook.md` → Padrões de transformação
- `architecture-guidelines.md` → Guidelines MVC

---

## Comportamento da Skill

1. **Agnóstica de tecnologia:** Deve funcionar em Python, Node.js, e outras linguagens
2. **Específica no relatório:** Apontar arquivo e linhas exatas
3. **Interativa:** Pausar na Fase 2 e pedir confirmação
4. **Segura:** Não fazer refatoração sem validação explícita do usuário
5. **Validadora:** Testar que a aplicação continua funcionando

---

## Limitações v2.1

- Suporte oficialmente para Python + Node.js (heurísticas agnósticas)
- Detecção de padrões é baseada em regex (pode ter falsos positivos)
- Refatoração MVC assume estrutura simples (monolito → camadas)
- Validação de endpoints é básica (apenas startup + sintaxe)
- Não trata bancos de dados não-SQL ou ORMs customizados

---

## O Que v2.1 Cobre

✅ **CRITICAL:**
- SQL Injection
- Hardcoded Secrets
- Senhas em Texto Plano
- Endpoints Perigosos

✅ **HIGH:**
- Weak Password Hashing (MD5, SHA1)
- God Classes/Modules
- N+1 Queries
- Global State Mutável
- Data Integrity Issues

✅ **MEDIUM:**
- Code Duplication
- Secrets Expostas em Responses
- Logs Sensíveis (PII)
- DEBUG Mode Ativo

✅ **LOW:**
- Magic Strings / Magic Numbers
- Ternários Desnecessários

✅ **ARCHITECTURE:**
- Monolithic → MVC Refactoring

---

## Próximas Versões

v2.2: Detecção de APIs deprecated e code smell patterns
v3.0: Suporte para microserviços e arquiteturas distribuídas
v3.1: Validação de endpoints completa
