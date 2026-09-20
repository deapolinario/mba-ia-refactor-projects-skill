# Catálogo de Anti-Patterns

## v1.0 — SQL Injection & Hardcoded Secrets

### 1. SQL Injection (CRITICAL)

**Descrição:** Queries SQL construídas por concatenação de strings, permitindo manipulação e execução arbitrária de SQL.

**Sinais de Detecção:**
- String concatenation com operador `+`: `query = "SELECT * FROM users WHERE id = " + id`
- F-strings/Template literals: `f"SELECT * FROM users WHERE {condition}"`
- `.format()` em contexto SQL: `query.format(user_id=user_id)`
- Construção manual sem parâmetros

**Padrão Seguro:**
- Parameterized queries com `?` ou `:param`
- Prepared statements
- ORM methods (`.filter()`, `.where()`)
- Bind variables

**Impacto:** Exposição de dados, alteração não autorizada, exclusão de registros, acesso total ao banco.

---

### 2. Hardcoded Credentials (HIGH/CRITICAL)

**Descrição:** Secrets (API keys, senhas, tokens) embarcados no código-fonte.

**Sinais de Detecção:**
- Atribuições literais: `SECRET_KEY = "my-secret"`
- Padrões de nomes: `SECRET`, `PASSWORD`, `API_KEY`, `TOKEN`, `db_pass`, `smtp_password`
- Valores que pareçam reais (não "example", "todo", "xxx")
- URLs com credenciais: `postgres://user:pass@host`

**Padrão Seguro:**
- Variáveis de ambiente: `os.getenv('SECRET_KEY')`
- Arquivo `.env` com valores reais (não versionado)
- Config externo carregado no startup
- Valores padrão dummy apenas em dev

**Impacto:** Comprometimento de sistemas externos, acesso não autorizado, fraud, breach de dados sensíveis.

---

---

### 3. Weak Password Hashing (HIGH)

**Descrição:** Senhas com hash MD5, SHA1 ou sem hash.

**Sinais de Detecção:**
- `hashlib.md5()`, `hashlib.sha1()`
- `crypto.createHash('md5')`, `crypto.createHash('sha1')`
- Senhas salvas em texto plano
- Sem salt ou salt hardcoded

**Padrão Seguro:**
- `bcrypt` (recomendado)
- `argon2` (mais seguro)
- Sempre com salt aleatório

**Impacto:** Rainbow tables quebram hashes em segundos, acesso não autorizado.

---

### 4. God Class/Module (CRITICAL)

**Descrição:** Uma classe/arquivo faz tudo: queries, validações, roteamento, lógica de negócio.

**Sinais de Detecção:**
- Arquivo com 300+ linhas com múltiplas responsabilidades
- Métodos misturando DB + validação + HTTP
- Classe com 10+ métodos públicos sem padrão
- Sem separação models/controllers/routes

**Padrão Seguro:**
- Models: apenas dados
- Controllers: lógica de negócio
- Routes: mapeamento HTTP

**Impacto:** Impossível testar, manter ou reutilizar. Qualquer mudança quebra tudo.

---

### 5. N+1 Queries (HIGH)

**Descrição:** Loop com queries dentro. Para cada item, uma query extra.

**Sinais de Detecção:**
- `for item in items:` seguido de `query.filter(item.id)`
- Nested loops com queries
- Query em método chamado dentro de loop

**Padrão Seguro:**
- Eager loading: `User.query.options(joinedload('tasks')).all()`
- Joins: `SELECT users JOIN tasks ON ...`
- Single query com relacionamento carregado

**Impacto:** Performance exponencial. 100 itens = 100+ queries ao invés de 1.

---

### 6. Code Duplication (MEDIUM)

**Descrição:** Mesma lógica repetida em múltiplos lugares.

**Sinais de Detecção:**
- Blocos de código idênticos (3+ linhas)
- Lógica de validação repetida
- Transformações de dados repetidas
- Queries similares em múltiplos arquivos

**Padrão Seguro:**
- Extrair em função/método reutilizável
- Usar herança ou composition
- Centralizar em helpers/utils

**Impacto:** Mudanças precisam ser feitas em múltiplos lugares. Bugs aparecem em alguns mas não em outros.

---

### 7. Monolithic Architecture (CRITICAL)

**Descrição:** Projeto sem separação clara de responsabilidades. Tudo em poucos arquivos.

**Sinais de Detecção:**
- Raiz com app.py/app.js + models.py + routes em mesmo arquivo
- Sem pastas models/, routes/, controllers/
- Lógica de BD misturada com HTTP

**Padrão Seguro:**
- `config/` → configurações
- `models/` → estrutura de dados
- `routes/` → mapeamento HTTP
- `controllers/` → lógica de negócio
- `app.py` → entry point limpo

**Impacto:** Difícil de testar, reutilizar ou escalar.

---

---

### 8. Secrets Expostas em Responses (MEDIUM)

**Descrição:** Endpoints públicos retornam dados sensíveis em responses HTTP.

**Sinais de Detecção:**
- `return jsonify()` ou `res.json()` contendo `SECRET_KEY`, `PASSWORD`, `API_KEY`
- Endpoints como `/health`, `/status`, `/info` retornando secrets
- Debug info em respostas de erro

**Padrão Seguro:**
- Retornar apenas dados não-sensíveis
- Manter secrets fora de responses

**Impacto:** Information disclosure, exposição em logs/monitoramento

---

### 9. Logs Sensíveis (PII Exposure) (MEDIUM)

**Descrição:** Logs contêm dados sensíveis como emails, cartões, CPF.

**Sinais de Detecção:**
- `print()`, `console.log()`, `logger.*()` com variáveis
- Pattern de email: `\w+@\w+\.\w+`
- Pattern de cartão: `\d{16}` ou `\d{13}`
- Pattern de CPF/SSN: `\d{3}\.\d{3}\.\d{3}-\d{2}`

**Padrão Seguro:**
- Mascarar dados sensíveis antes de logar
- Usar `mask_email()`, `mask_cc()`, etc

**Impacto:** PII exposure, LGPD/GDPR violation

---

### 10. Global State Mutável (HIGH)

**Descrição:** Variáveis globais compartilhadas entre requests causam race conditions.

**Sinais de Detecção:**
- `global` keyword
- Variáveis no module level sem capitalização
- `check_same_thread=False` em SQLite
- Mutação de variáveis globais

**Padrão Seguro:**
- Usar Singleton pattern
- Usar Dependency Injection
- Request-scoped state (Flask: `g`, Express: `req`)

**Impacto:** Race conditions, dados corrompidos, vazamento entre usuários

---

### 11. Magic Strings / Magic Numbers (LOW)

**Descrição:** Valores hardcoded sem constantes nomeadas.

**Sinais de Detecção:**
- Listas/dicts hardcoded com múltiplos valores
- Status codes hardcoded (200, 404, 500)
- Strings sem variáveis de config
- Números sem explicação (timeouts, limits)

**Padrão Seguro:**
- Extrair para Config/Enum
- Usar constantes nomeadas
- Centralizar em um arquivo de config

**Impacto:** Manutenibilidade, inconsistência

---

### 12. Ternários Desnecessários (LOW)

**Descrição:** If/else que retorna True/False poderia ser uma expressão.

**Sinais de Detecção:**
```
if <condition>:
    return True
else:
    return False
```

**Padrão Seguro:**
```
return <condition>
```

**Impacto:** Legibilidade

---

## v2.2 — Endpoints Perigosos, Auth e Regressões de Refactoring

### 13. Dangerous Admin Endpoint / Arbitrary Code Execution (CRITICAL)

**Descrição:** Endpoint que executa SQL (ou comando de sistema) construído a partir de input do cliente sem qualquer restrição — pior que SQL Injection acidental, é execução arbitrária *by design*.

**Sinais de Detecção:**
- `cursor.execute(query)` onde `query` vem de `request.get_json()`, `request.body`, `req.body`
- Rotas como `/admin/query`, `/exec`, `/run-sql`, `/debug/eval`
- `eval()`, `exec()`, `os.system()`, `subprocess.run()` com input do request

**Padrão Seguro:**
- Nunca expor execução de SQL/código arbitrário via API
- Se necessário para debug, restringir a ambiente local + allowlist de queries

**Impacto:** Comprometimento total do banco de dados e potencialmente do servidor. Pior que SQL Injection convencional pois não requer bypass — é a funcionalidade.

---

### 14. Plaintext Password Storage & Comparison (CRITICAL)

**Descrição:** Diferente de "Weak Hashing" (MD5/SHA1) — aqui não há hash *nenhum*. Senha é comparada e armazenada como veio do cliente, e frequentemente retornada em responses.

**Sinais de Detecção:**
- Query de login comparando coluna de senha direto: `WHERE senha = ?` / `WHERE password = ?`
- `INSERT INTO usuarios (..., senha, ...) VALUES (..., ?, ...)` com o valor bruto do request, sem `hash(...)` no caminho
- Query `SELECT *` em tabela de usuários cujo resultado (incluindo coluna de senha) é serializado direto em `jsonify()`/`res.json()`

**Padrão Seguro:**
- Hash com bcrypt/argon2/PBKDF2 antes de persistir
- Comparação via `check_password_hash()` / `bcrypt.compare()`, nunca `==` direto
- Excluir coluna de senha de qualquer serialização (`to_dict(include_password=False)`)

**Impacto:** Vazamento do banco expõe credenciais de todos os usuários instantaneamente, sem esforço de quebra.

---

### 15. Broken Access Control em Endpoints Sensíveis (CRITICAL/HIGH)

**Descrição:** Rotas que alteram estado crítico (reset de dados, execução de queries, alteração de permissões) sem nenhum middleware de autenticação/autorização.

**Sinais de Detecção:**
- Rotas com prefixo `/admin`, `/internal`, `/debug` sem decorator/middleware de auth antes do handler
- Ausência de checagem de token/sessão/role no início da função
- Comparar lista de rotas registradas vs lista de rotas com guard de auth

**Padrão Seguro:**
- Middleware/decorator de autenticação (`@login_required`, `@admin_required`)
- Verificação de role explícita no controller
- Nunca confiar apenas em "rota não documentada" como proteção

**Impacto:** Qualquer pessoa com a URL pode resetar dados, executar SQL ou escalar privilégios.

---

### 16. Exception Detail Leakage (MEDIUM)

**Descrição:** Handlers retornam `str(exception)` diretamente na response HTTP, vazando stack traces, nomes de tabelas/colunas, paths internos e — combinado com endpoints de SQL — mensagens de erro do banco que ajudam ataques error-based.

**Sinais de Detecção:**
- `return jsonify({"erro": str(e)})`, `res.status(500).json({error: err.message})`
- `except Exception as e:` seguido de exposição direta de `e` na response

**Padrão Seguro:**
- Logar o erro detalhado internamente (`logger.error(str(e))`)
- Retornar mensagem genérica ao cliente (`"Erro interno do servidor"`)
- Detalhar apenas em modo development controlado por flag de ambiente

**Impacto:** Information disclosure que facilita reconhecimento e exploração de outras vulnerabilidades.

---

### 17. Regressão de Refactoring: Inicialização Por-Request (HIGH)

**Descrição:** Ao refatorar conexão global para Singleton/DI, é comum mover a lógica de setup (criação de tabelas, seed de dados) para dentro da função chamada a cada request, ao invés de rodar apenas uma vez na inicialização do Singleton.

**Sinais de Detecção:**
- `CREATE TABLE IF NOT EXISTS` ou lógica de seed dentro de uma função tipo `get_db()`/`get_connection()` que é chamada em todo handler de rota
- Comparar: essa lógica deveria estar em `__init__`/`__new__` do Singleton, executada uma única vez

**Padrão Seguro:**
- Setup de schema/seed dentro do `__init__` do Singleton (guardado por `_initialized`)
- `get_db()`/`get_connection()` apenas retorna a conexão já existente, sem side-effects

**Impacto:** Overhead de queries extras em toda request; em bancos maiores pode causar contenção/lock desnecessário. É uma regressão de performance introduzida pelo próprio refactoring, não um problema do código legado original — **checklist de validação da Fase 3 deve pegar isso**.

---

### 18. Configuração Morta / Não Aplicada (LOW)

**Descrição:** Valor de configuração é criado (ex: `Config.DEBUG`) mas o código legado continua com o valor hardcoded no ponto de uso, tornando a config "morta".

**Sinais de Detecção:**
- Atributo definido em `Config`/`settings` nunca referenciado fora do próprio arquivo de config
- Valor hardcoded coexistindo com a config equivalente (ex: `app.run(debug=True)` com `Config.DEBUG` existindo)

**Padrão Seguro:**
- Todo ponto de uso deve referenciar a `Config`, nunca o literal
- Validação da Fase 3 deve grep pelo literal antigo para confirmar que não sobrou nenhuma ocorrência

**Impacto:** Falsa sensação de que o comportamento é configurável; em produção pode ligar debug/expor stack traces mesmo com `.env` configurado corretamente.

---

## Formato de Detecção (Agnóstico de Linguagem)

Cada anti-pattern é procurado por padrões independentes de linguagem:
- Strings literais
- Palavras-chave conhecidas
- Estrutura de código
- Contexto de execução

Exemplos aplicáveis a Python, JavaScript, Java, PHP, Ruby, etc.
