# Skill: Refactor Architecture

**Versão:** 2.2 (18 anti-patterns: CRITICAL/HIGH/MEDIUM/LOW + validação de regressão)

**Objetivo:** Analisar, auditar e refatorar projetos legados para o padrão MVC, eliminando vulnerabilidades críticas, problemas arquiteturais e code smells.

**Mudança de princípio em v2.2:** a Fase 3 deixa de ser **seletiva** (só tratar os achados "principais") e passa a ser **sistemática** — TODO achado listado na Fase 2 deve ser resolvido ou explicitamente marcado como "adiado para próxima versão" no output, nunca silenciosamente ignorado.

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
   - Senhas em Texto Plano (armazenamento E comparação, não só hashing fraco)
   - Dangerous Admin Endpoint / Execução de SQL/código arbitrário via API
   - Broken Access Control (rotas administrativas/sensíveis sem auth)
   
   **HIGH:**
   - Weak Password Hashing (MD5, SHA1)
   - God Classes (arquivos 300+ linhas)
   - N+1 Queries (loops com queries)
   - Global State Mutável (race conditions)
   
   **MEDIUM:**
   - Code Duplication
   - Secrets Expostas em Responses
   - Logs Sensíveis (PII exposure)
   - Exception Detail Leakage (`str(e)` retornado ao cliente)
   
   **LOW:**
   - Magic Strings / Magic Numbers
   - Ternários Desnecessários
   - Monolithic Architecture (sem separação models/routes/controllers)
   - Configuração Morta (config criada mas não aplicada no ponto de uso)

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

1. **Antes de começar:** listar TODOS os achados da Fase 2 em uma checklist explícita (não trabalhar de memória). Cada item da checklist termina em um de três estados: `✅ Corrigido`, `⏭️ Adiado (com justificativa)`, ou `❌ Não aplicável`. Nunca deixar um achado sem status.

2. Aplicar refatorações conforme achados (prioridade: CRITICAL → HIGH → MEDIUM → LOW):

   **CRITICAL - SQL Injection:**
   - Converter queries com concatenation para parameterized queries
   - Usar ORM methods quando disponível

   **CRITICAL - Hardcoded Secrets:**
   - Criar `config.py` (Python) ou `config.js` (Node.js)
   - Carregar de `os.getenv()` ou `process.env`
   - Criar `.env` com valores reais, adicionar ao `.gitignore`

   **CRITICAL - Senhas em Texto Plano:**
   - Hash com bcrypt/argon2/PBKDF2 no cadastro (`generate_password_hash`)
   - Comparação via `check_password_hash()`, nunca `==`/`WHERE senha = ?`
   - Excluir coluna de senha de toda query de leitura usada em responses (`SELECT id, nome, email, ...` nunca `SELECT *` quando o resultado vai para o cliente)
   - Ver Padrão 15 em `refactoring-playbook.md`

   **CRITICAL - Dangerous Admin Endpoint:**
   - Remover endpoints que executam SQL/código arbitrário vindo do cliente
   - Se uso administrativo for real, restringir a allowlist fixa + auth
   - Ver Padrão 14 em `refactoring-playbook.md`

   **CRITICAL - Broken Access Control:**
   - Adicionar guard de autenticação/autorização em toda rota `/admin/*` ou equivalente
   - Ver Padrão 16 em `refactoring-playbook.md`

   **CRITICAL - God Classes / Monolithic Architecture:**
   - Separar em `models/`, `routes/`, `controllers/`
   - Cada arquivo com uma responsabilidade clara
   - Seguir guia passo-a-passo: `mvc-refactoring-guide.md`
   - Models: apenas queries. Routes: apenas HTTP mapping. Controllers: validação + lógica de negócio
   - Limpar `app.py` para apenas entry point

   **HIGH - Weak Password Hashing:**
   - Substituir MD5/SHA1 por bcrypt ou argon2
   - Aplicar em todos os `set_password()` e password checks

   **HIGH - N+1 Queries:**
   - Usar eager loading (`joinedload`, `include`) ou reescrever com JOIN
   - Converter loops com queries em single query

   **MEDIUM - Code Duplication:**
   - Extrair lógica duplicada em métodos/helpers
   - Centralizar transformações em `to_dict()` ou helpers

   **MEDIUM - Exception Detail Leakage:**
   - Nunca retornar `str(e)` na response ao cliente
   - Logar detalhado internamente (`logger.error`), responder mensagem genérica
   - Ver Padrão 17 em `refactoring-playbook.md`

   **LOW - Configuração Morta:**
   - Após criar qualquer `Config.X`, grep pelo literal antigo no projeto inteiro e substituir todas as ocorrências
   - Ver Padrão 19 em `refactoring-playbook.md`

3. Usar arquivo de referência: `refactoring-playbook.md`

4. **Checklist de Regressão (obrigatório, executar sempre — não só quando houver Singleton/DI):**
   - [ ] Toda lógica de setup/seed que antes rodava "uma vez" continua rodando uma vez (não foi movida para dentro de uma função chamada por request)
   - [ ] Nenhuma query nova foi introduzida dentro de loop (não trocar um N+1 por outro)
   - [ ] Toda config nova (`Config.X`) tem pelo menos um ponto de uso real (não é dead code)
   - [ ] Nenhum literal antigo (secret, debug flag, etc.) sobrou coexistindo com a nova config
   - Ver Padrão 18 (Anti-Patterns Catalog) e Padrão 18 em `refactoring-playbook.md`

5. Após aplicar refatorações:
   - Tentar dar startup na aplicação
   - Validar que não há erros de sintaxe (`python -m py_compile` / `node --check`)
   - Se possível, testar alguns endpoints chave
   - Reexecutar mentalmente a Fase 2 sobre o código final e confirmar que cada achado da checklist do passo 1 está de fato resolvido (não confiar em "deveria estar corrigido")

6. Imprimir output de validação, incluindo a checklist completa de achados com status individual:

```
================================
PHASE 3: REFACTORING COMPLETE
================================

Findings checklist (todos os achados da Fase 2, sem exceção):
  ✅ [CRITICAL] SQL Injection: X queries → parameterized
  ✅ [CRITICAL] Hardcoded Secrets: X values → config + .env
  ✅ [CRITICAL] Senhas em texto plano: hash aplicado + removidas de responses
  ✅ [CRITICAL] Dangerous admin endpoint: removido/protegido
  ✅ [CRITICAL] Broken access control: guard de auth adicionado
  ⏭️ [HIGH] God Class: adiado — justificativa: <motivo>
  ✅ [HIGH] N+1 Queries: X queries → eager loading/JOIN
  ✅ [MEDIUM] Exception leakage: X handlers → mensagem genérica + log
  ✅ [MEDIUM] Duplications removed: X patterns → helpers
  ✅ [LOW] Config morta: literal antigo substituído em X lugares

Regression checklist:
  ✅ Setup/seed roda uma única vez (não por request)
  ✅ Nenhum N+1 novo introduzido
  ✅ Nenhuma config nova é dead code
  ✅ Nenhum literal antigo sobrou

New structure (se MVC aplicado):
  ✓ config/ — configurações
  ✓ models/ — estrutura de dados
  ✓ routes/ — mapeamento HTTP
  ✓ controllers/ — lógica de negócio
  ✓ app.py — entry point limpo

Validation:
  ✓ Application boots without errors
  ✓ No syntax errors detected
  ✓ All secrets removed from source code
  ✓ No plaintext passwords in DB or responses
  ✓ No dangerous endpoints without auth
  ✓ No password hashes in MD5/SHA1
  ✓ No N+1 query patterns detected
  ✓ MVC structure verified

================================
```

---

## Referências Carregadas

- `project-analysis.md` → Heurísticas de detecção
- `anti-patterns-catalog.md` → Catálogo de problemas (18 padrões)
- `audit-report-template.md` → Formato de relatório
- `refactoring-playbook.md` → Padrões de transformação (19 padrões)
- `architecture-guidelines.md` → Guidelines MVC (visão geral)
- `mvc-refactoring-guide.md` → Guia passo-a-passo (Phase 3)

---

## Comportamento da Skill

1. **Agnóstica de tecnologia:** Deve funcionar em Python, Node.js, e outras linguagens
2. **Específica no relatório:** Apontar arquivo e linhas exatas
3. **Interativa:** Pausar na Fase 2 e pedir confirmação
4. **Segura:** Não fazer refatoração sem validação explícita do usuário
5. **Validadora:** Testar que a aplicação continua funcionando
6. **Sistemática (v2.2):** Fase 3 trata TODOS os achados da checklist, nunca seletivamente — item adiado precisa de justificativa explícita no output
7. **Auto-crítica (v2.2):** Fase 3 sempre roda o Checklist de Regressão antes de declarar sucesso, para pegar bugs introduzidos pela própria refatoração (ex: setup que passou a rodar por-request, config criada mas não aplicada)

---

## Limitações v2.2

- Suporte oficialmente para Python + Node.js (heurísticas agnósticas)
- Detecção de padrões é baseada em regex/heurística estrutural (pode ter falsos positivos)
- Refatoração MVC assume estrutura simples (monolito → camadas)
- Validação de endpoints é básica (apenas startup + sintaxe), sem testes automatizados de request/response
- Não trata bancos de dados não-SQL ou ORMs customizados
- Auth adicionada em endpoints administrativos é um guard mínimo (token), não um sistema de autenticação completo

---

## O Que v2.2 Cobre

✅ **CRITICAL:**
- SQL Injection
- Hardcoded Secrets
- Senhas em Texto Plano (armazenamento + comparação + exposição em responses)
- Dangerous Admin Endpoint (execução de SQL/código arbitrário)
- Broken Access Control (rotas administrativas sem auth)
- God Classes/Módulos (com guia MVC passo-a-passo)
- Monolithic Architecture

✅ **HIGH:**
- Weak Password Hashing (MD5, SHA1)
- N+1 Queries
- Global State Mutável
- Regressão de Refatoração (setup rodando por-request)

✅ **MEDIUM:**
- Code Duplication
- Secrets Expostas em Responses
- Logs Sensíveis (PII)
- Exception Detail Leakage (`str(e)` na response)
- DEBUG Mode Ativo

✅ **LOW:**
- Magic Strings / Magic Numbers
- Ternários Desnecessários
- Configuração Morta (criada mas não aplicada)

✅ **ARCHITECTURE:**
- Monolithic → MVC Refactoring (guia completo)

✅ **PROCESSO:**
- Checklist sistemática de achados (Fase 3 não pula itens silenciosamente)
- Checklist de regressão pós-refactoring

---

## Próximas Versões

v2.3: Testes automatizados de request/response (não só sintaxe) na validação da Fase 3
v3.0: Suporte para microserviços e arquiteturas distribuídas
v3.1: Sistema de autenticação completo (não só guard de token) no MVC guide
