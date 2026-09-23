# Skill: Refactor Architecture

**Versão:** 3.2 (20 anti-patterns + validação de regressão + self-verification loop com teste de autorização granular + detecção de APIs deprecated)

**Objetivo:** Analisar, auditar e refatorar projetos legados para o padrão MVC, eliminando vulnerabilidades críticas, problemas arquiteturais e code smells.

**Mudança de princípio em v2.2:** a Fase 3 deixa de ser **seletiva** (só tratar os achados "principais") e passa a ser **sistemática** — TODO achado listado na Fase 2 deve ser resolvido ou explicitamente marcado como "adiado para próxima versão" no output, nunca silenciosamente ignorado.

**Mudança de princípio em v3.0:** a Fase 3 deixa de confiar no próprio log de refatoração como prova de sucesso. Ao final, ela **se reaudita** — relê o código já refatorado do zero e roda a checklist de 18 anti-patterns de novo, exatamente como faria uma Fase 2 nova. Isso existe porque, na prática, essa reauditoria pegou coisas reais que o log de refatoração não pegava: uma regressão introduzida pela própria refatoração (setup de banco rodando por-request), um N+1 residual que sobrou fora do escopo original corrigido, e configuração morta copiada do código legado sem verificar se tinha uso. Se a reauditoria vier limpa, a skill encerra. Se encontrar algo, ela **pergunta ao usuário se deve continuar corrigindo** — nunca decide isso por conta própria — e, se autorizada, repete o ciclo (corrigir → validar → reauditar) até ficar limpo ou até um limite de 3 ciclos.

**Mudança de princípio em v3.1:** a self-verification da v3.0 provou ser insuficiente contra um tipo específico de achado — no task-manager-api, o ciclo 1 declarou 0 achados relendo o código e confirmando que toda rota sensível tinha `@login_required`/`@role_required`, mas isso é uma checagem **estrutural** (o decorator existe?). Uma reauditoria seguinte, testando a lógica de autorização **funcionalmente** com um usuário de baixo privilégio, encontrou 2 CRITICAL de escalação de privilégio que a checagem estrutural nunca poderia pegar: `PUT /users/:id` tinha o decorator certo mas nenhuma checagem de "quem pode alterar o quê", e `POST /users` (cadastro público) aceitava `role` do payload sem restrição. v3.1 adiciona o Padrão 19 (Autorização Granular) ao catálogo e, mais importante, torna esse teste funcional — não só estrutural — parte obrigatória do self-verification (Fase 3, passo 7).

**Mudança de princípio em v3.2:** o catálogo cobria segurança e arquitetura, mas não uso de **APIs deprecated/obsoletas** — categoria explicitamente exigida pelo enunciado do desafio, para qualquer API obsoleta em qualquer linguagem, não um caso específico. O gap apareceu na prática: `datetime.utcnow()` (deprecated desde Python 3.12, retorna datetime naive) é usado 15 vezes em `models/task.py` no task-manager-api e não foi apontado em nenhuma auditoria anterior, porque nenhum item do checklist da Fase 2 procurava por depreciação — o código "funciona", então passava despercebido. v3.2 adiciona o Padrão 20 (APIs Deprecated) ao catálogo como um **princípio geral de detecção** (qualquer API que a documentação oficial da stack em uso marca como deprecated, aplicando conhecimento da linguagem/framework detectados na Fase 1 — não uma lista fechada de exemplos) e ao checklist explícito da Fase 2 (categoria MEDIUM, escalando para HIGH quando a API deprecated também carrega um bug de correção/segurança).

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
   - Privilege Escalation via Autorização Insuficiente (rota autenticada, mas sem checagem de ownership/allowlist de campos sensíveis — ver Padrão 19)
   
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
   - APIs Deprecated/Obsoletas — qualquer função/método/módulo oficialmente marcado como deprecated pela linguagem/framework/biblioteca detectada na Fase 1, na versão em uso pelo projeto (não se limita a um exemplo específico; aplicar conhecimento da stack identificada, não só os exemplos listados — ver Padrão 20)
   
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

### Fase 3: Refactoring, Validation & Self-Verification

**Objetivo:** Aplicar refatorações, validar que a aplicação continua funcionando, e **se reauditar** antes de declarar sucesso.

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

   **CRITICAL - Privilege Escalation via Autorização Insuficiente:**
   - Em handlers de update: checar ownership (`resource.owner_id == requester.id`) ou role antes de aplicar qualquer mudança
   - Campos sensíveis (`role`, `is_admin`, `active`, `price`, saldo, etc.) só podem ser alterados por quem tem privilégio para isso — mesmo quando o alvo é o próprio requester (evita autopromoção)
   - Endpoints de cadastro público nunca leem campos de privilégio do payload — valor sempre fixo definido pelo servidor
   - Ver Padrões 20-21 em `refactoring-playbook.md`

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

   **MEDIUM - APIs Deprecated/Obsoletas:**
   - Para cada API deprecated identificada (qualquer uma, não só as listadas como exemplo no catálogo): consultar a documentação oficial da versão em uso para o substituto indicado na própria mensagem/aviso de depreciação
   - Aplicar a substituição em TODAS as ocorrências (grep pelo nome do método/módulo no projeto inteiro, não só a primeira)
   - Ver Padrão 20 em `anti-patterns-catalog.md` e Padrão 22 em `refactoring-playbook.md` (exemplos multi-linguagem)

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

6. Imprimir output de validação, incluindo a checklist completa de achados com status individual. **Este output é intermediário** — o status final só é declarado depois do passo 7 (self-verification):

```
================================
PHASE 3: REFACTORING APPLIED (pendente self-verification — ver passo 7)
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

7. **Self-Verification Loop (v3.0, expandido em v3.1, obrigatório, roda sempre que a Fase 3 for executada):**

   a. **Reler o código do zero.** Ler novamente todos os arquivos atuais do projeto (não os arquivos "que deveriam ter sido alterados" — o conjunto completo), exatamente como se fosse uma Fase 2 nova sendo executada por alguém sem acesso ao log de refatoração desta sessão. Não aceitar o checklist do passo 6 como prova — ele documenta intenção, a releitura confirma resultado.

   b. **Rodar a checklist completa dos 20 anti-patterns** (`anti-patterns-catalog.md`) contra esse código. Isso inclui padrões fora do escopo dos achados originais da Fase 2 — a reauditoria pode (e deve) encontrar coisas novas, incluindo regressões introduzidas pela própria refatoração deste ciclo.

   b2. **Teste Funcional de Autorização (v3.1, obrigatório — não é opcional mesmo se o passo `b` não apontar nada).** O Padrão 19 (Privilege Escalation) não é detectável só relendo/grepando o código — uma rota pode ter o decorator de auth certo e ainda ter uma falha de autorização na lógica interna do controller. Portanto, para todo endpoint de escrita (POST/PUT/PATCH/DELETE) que aceita ou pode alterar campos sensíveis (`role`, `is_admin`, `active`, `price`, saldo, `owner_id`, status de pagamento, ou qualquer campo que determine privilégio/propriedade), simular requisições reais (Flask test client / supertest / equivalente) com um usuário de **baixo privilégio** e confirmar:
      - Ele **não consegue** alterar esses campos sensíveis em si mesmo (ex: autopromoção a admin)
      - Ele **não consegue** alterar/deletar um recurso que pertence a outro usuário, quando o domínio exige ownership
      - Um endpoint de cadastro/criação **público** força o valor de qualquer campo de privilégio no servidor, ignorando o que vier no payload
      - Casos legítimos continuam funcionando (o próprio usuário edita seus dados não-sensíveis; um admin/role adequado consegue fazer a operação)
      
      Se qualquer uma dessas simulações tiver sucesso quando deveria falhar (ou falhar quando deveria ter sucesso), é um achado CRITICAL — tratar como qualquer outro achado do passo `b` (mesmo checklist, mesma decisão de continuar/parar no passo `e`/`f`/`g`).

   c. **Gerar um novo relatório de auditoria**, com timestamp novo, seguindo o mesmo padrão de nomenclatura da Fase 2 (`../reports/audit-{repo-name}-{timestamp}.md`), incluindo os resultados do passo `b2`.

   d. **Se 0 achados:** imprimir confirmação e encerrar o fluxo — não perguntar nada, a Fase 3 terminou com sucesso.

   ```
   ================================
   PHASE 3: SELF-VERIFICATION — CYCLE [N]
   ================================
   Re-read: [X] files
   Findings: 0
   Status: ✅ Clean — no further action needed
   ================================
   ```

   e. **Se houver 1+ achados:** imprimir a lista (severidade + resumo de cada um) e perguntar explicitamente ao usuário — nunca decidir por conta própria:

   ```
   ================================
   PHASE 3: SELF-VERIFICATION — CYCLE [N]
   ================================
   Re-read: [X] files
   Findings: [Y] ([lista: severidade + descrição curta de cada achado])

   **Deseja que eu continue corrigindo? (y/n)**
   ================================
   ```

   f. Se `y`/`yes`: voltar ao passo 2 desta Fase 3, tratando **apenas os achados encontrados neste ciclo** (não repetir o que já foi corrigido), e repetir o processo completo — refatorar → validar → self-verification (passo 7) — incrementando o contador de ciclo.

   g. Se `n`/`no`: parar. Reportar o estado final deixando explícito quais achados ficaram pendentes por decisão do usuário (não por limitação da skill).

   h. **Limite de segurança: máximo 3 ciclos.** Se ao final do 3º ciclo ainda houver achados, parar automaticamente **sem perguntar de novo**, reportar os achados remanescentes e recomendar revisão manual — evita loop infinito em casos onde a correção de um achado introduz outro indefinidamente.

---

## Referências Carregadas

- `project-analysis.md` → Heurísticas de detecção
- `anti-patterns-catalog.md` → Catálogo de problemas (20 padrões)
- `audit-report-template.md` → Formato de relatório
- `refactoring-playbook.md` → Padrões de transformação (22 padrões)
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
8. **Auto-verificadora (v3.0):** Fase 3 nunca termina só porque o checklist de intenção está todo `✅` — ela relê o código do zero e reaplica a Fase 2 sobre o resultado antes de declarar sucesso
9. **Nunca decide sozinha continuar corrigindo (v3.0):** se a self-verification encontra achados, a skill pergunta ao usuário — só continua o ciclo com `y`/`yes` explícito, e para automaticamente no limite de 3 ciclos independente da resposta
10. **Testa autorização funcionalmente, não só estruturalmente (v3.1):** presença de `@login_required`/`@role_required` numa rota não é aceita como prova de que a autorização está correta — o self-verification simula requisições reais com usuário de baixo privilégio contra endpoints de escrita sensíveis

---

## Limitações v3.2

- Suporte oficialmente para Python + Node.js (heurísticas agnósticas)
- Detecção de padrões é baseada em regex/heurística estrutural (pode ter falsos positivos)
- Refatoração MVC assume estrutura simples (monolito → camadas)
- Validação de endpoints é básica (apenas startup + sintaxe), sem testes automatizados de request/response
- Não trata bancos de dados não-SQL ou ORMs customizados
- Auth adicionada em endpoints administrativos é um guard mínimo (token), não um sistema de autenticação completo
- Self-verification loop tem limite fixo de 3 ciclos — projetos com achados encadeados profundos (fix de A introduz B, fix de B introduz C, ...) podem precisar de revisão manual após o limite
- Cada ciclo relê o projeto inteiro — em projetos grandes isso tem custo (tempo/tokens) proporcional ao tamanho, não incremental
- O teste funcional de autorização (passo 7.b2) depende de conseguir simular requisições (test client/supertest); em stacks sem essa capacidade fácil, a verificação fica só estrutural (mesma limitação da v3.0)
- A checagem de ownership/allowlist de campos sensíveis é heurística — não substitui um sistema de permissões (RBAC/ABAC) completo; para domínios com regras de autorização complexas (múltiplos níveis de hierarquia, permissões por recurso), a skill propõe o guard mínimo, não a modelagem completa

---

## O Que v3.2 Cobre

✅ **CRITICAL:**
- SQL Injection
- Hardcoded Secrets
- Senhas em Texto Plano (armazenamento + comparação + exposição em responses)
- Dangerous Admin Endpoint (execução de SQL/código arbitrário)
- Broken Access Control (rotas administrativas sem auth)
- Privilege Escalation via Autorização Insuficiente (rota autenticada sem ownership check/allowlist de campos sensíveis — IDOR, mass assignment de role/active)
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
- APIs Deprecated/Obsoletas (qualquer API marcada deprecated pela stack em uso — Python, Node.js, Java/Kotlin, PHP, Ruby, etc; ex: `datetime.utcnow()`, `mysql_*` do PHP, `each()` do Ruby)

✅ **LOW:**
- Magic Strings / Magic Numbers
- Ternários Desnecessários
- Configuração Morta (criada mas não aplicada)

✅ **ARCHITECTURE:**
- Monolithic → MVC Refactoring (guia completo)

✅ **PROCESSO:**
- Checklist sistemática de achados (Fase 3 não pula itens silenciosamente)
- Checklist de regressão pós-refactoring
- **Self-verification loop:** Fase 3 se reaudita relendo o código do zero e reaplicando os 20 anti-patterns, ao invés de confiar no próprio log de refatoração
- **Teste funcional de autorização (v3.1):** self-verification simula requisições com usuário de baixo privilégio contra endpoints de escrita sensíveis — não aceita a presença de um decorator como prova de autorização correta
- **Loop com controle do usuário:** achados na reauditoria nunca são corrigidos automaticamente — a skill pergunta e só continua com `y`/`yes` explícito
- **Limite de segurança:** máximo 3 ciclos de correção↔reauditoria, evitando loop infinito

---

## Próximas Versões

v3.3: Testes automatizados de request/response mais amplos (não só autorização) na validação da Fase 3
v3.4: Sistema de autenticação completo (não só guard de token) no MVC guide
v4.0: Suporte para microserviços e arquiteturas distribuídas
