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

## Formato de Detecção (Agnóstico de Linguagem)

Cada anti-pattern é procurado por padrões independentes de linguagem:
- Strings literais
- Palavras-chave conhecidas
- Estrutura de código
- Contexto de execução

Exemplos aplicáveis a Python, JavaScript, Java, PHP, Ruby, etc.
