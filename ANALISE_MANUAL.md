# Análise Manual dos Projetos

> Este documento registra a análise manual dos 3 projetos antes da criação da skill.
> Cada achado está classificado por severidade e inclui localização exata no código.

## Projeto 1: code-smells-project (Python/Flask)

**Stack:** Python 3 + Flask + SQLite

### 🔴 CRITICAL

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 1.1 | SQL Injection | models.py | 28, 48-50, 57-61, 92, 110, 140, 174, 188, 192, 220, 224, 280, 291 | Strings concatenadas diretamente em queries SQL sem parametrização | Exposição de dados, alteração/exclusão não autorizada |
| 1.2 | Hardcoded SECRET_KEY | app.py | 7 | SECRET_KEY = "minha-chave-super-secreta-123" no código-fonte | Qualquer pessoa com acesso ao repo pode falsificar tokens |
| 1.3 | Senhas em texto plano | database.py, models.py | 76-78, 127-128 | Usuários criados sem hash de senha. Exemplos: "admin123", "123456", "senha123" | Acesso não autorizado a contas |
| 1.4 | Endpoint de query arbitrária | app.py | 59-78 | POST /admin/query permite executar qualquer SQL sem autenticação | Acesso total ao BD, roubo de dados, exclusão |
| 1.5 | Endpoint de reset sem proteção | app.py | 47-57 | POST /admin/reset-db deleta todos os dados sem autenticação/confirmação | Perda total de dados |

### 🟠 HIGH

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 1.6 | God Module | models.py | 1-315 | Arquivo único contém TODA lógica de negócio: queries, validações, transformações para 4 domínios | Impossível testar em isolamento, qualquer mudança quebra tudo |
| 1.7 | N+1 Queries | models.py | 187-199, 219-231 | Loop dentro de loop de queries. Ex: para cada pedido, query de itens; para cada item, query de produto | Performance degradada exponencialmente |
| 1.8 | Estado global mutável | database.py | 4, 9 | `db_connection` é global e reutilizado. `check_same_thread=False` permite race conditions | Dados corrompidos em concorrência |

### 🟡 MEDIUM

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 1.9 | DEBUG mode ativo | app.py | 8 | app.config["DEBUG"] = True em ambiente que se apresenta como produção | Exposição de stack traces, information disclosure |
| 1.10 | Duplicação de código | models.py | 202-233 vs 171-201 | `get_todos_pedidos()` e `get_pedidos_usuario()` têm lógica idêntica para montar pedidos | Mudanças devem ser feitas em 2 lugares |
| 1.11 | Secrets em response | controllers.py | 289 | health_check() retorna `"secret_key": "minha-chave-super-secreta-123"` | Exposição da chave em logs/monitoramento |
| 1.12 | Logs sensíveis | controllers.py | 161 | "Usuário criado: " + email (expõe email em logs) | Vazamento de PII em arquivos de log |

### 🔵 LOW

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 1.13 | Magic strings | controllers.py | 52-54 | Lista hardcoded de categorias válidas. Deveria vir de config | Se alterar, precisa mudar em 2 lugares |
| 1.14 | Falta de validação de entrada | models.py | 285-299 | Parâmetros de busca não validados (sql injection via LIKE) | Unpredictable behavior |

---

## Projeto 2: ecommerce-api-legacy (Node.js/Express)

**Stack:** Node.js + Express + SQLite (in-memory)

### 🔴 CRITICAL

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 2.1 | Hardcoded credenciais | utils.js | 2-6 | Todas as credenciais expostas: dbUser, dbPass, paymentGatewayKey, smtpUser | Comprometimento de sistemas externos |
| 2.2 | Fake crypto (Base64) | utils.js | 17-23 | `badCrypto()` usa apenas base64, não é criptografia. Substring(0,2) 10.000x = "ba" repetido | Qualquer pessoa descriptografa em segundos |
| 2.3 | Senhas em texto plano | AppManager.js | 18 | INSERT com senha 'admin123' sem hash | Acesso não autorizado |
| 2.4 | Validação de cartão fraca | AppManager.js | 46 | `cc.startsWith("4") ? "PAID" : "DENIED"` - valida apenas por primeiro dígito | Fraude: qualquer cartão começando com 4 é aceito |
| 2.5 | Senha default | AppManager.js | 68 | `badCrypto(p \|\| "123456")` - usa senha padrão se não informada | Bypass de autenticação |

### 🟠 HIGH

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 2.6 | God Class | AppManager.js | 4-142 | Uma classe faz: init BD, setup routes, checkout, relatório, delete - todas as responsabilidades | Impossível testar, reutilizar, manter |
| 2.7 | Callback Hell | AppManager.js | 37-78 | Aninhamento profundo de 5 níveis de callbacks | Código ilegível, hard de debugar, error handling quebrado |
| 2.8 | Data Integrity | AppManager.js | 131-137 | DELETE de usuário sem cascade - deixa matrículas e pagamentos órfãos | Relatórios quebrados, referências inválidas |
| 2.9 | Race condition | AppManager.js | 83-129 | Múltiplos `db.all()` aninhados com contadores manually decrementados | Respostas fora de ordem, counts errados |
| 2.10 | Inconsistent error handling | AppManager.js | 35-78 | Mistura `res.status().send()`, `res.json()`, `res.send()` sem padrão | Clientes não sabem formato da resposta |

### 🟡 MEDIUM

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 2.11 | Global state mutável | utils.js | 9-10 | `globalCache = {}` e `totalRevenue = 0` compartilhados entre requests | Vazamento de dados entre usuários |
| 2.12 | Log de credencial | AppManager.js | 45 | `console.log(\`Processando cartão ${cc}...\`)` - expõe número do cartão | PCI DSS violation, vazamento em logs |

---

## Projeto 3: task-manager-api (Python/Flask)

**Stack:** Python 3 + Flask + SQLAlchemy + SQLite

### 🔴 CRITICAL

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 3.1 | Senha exposta em JSON | user.py + user_routes.py | 21, 33, 85, 129, 209 | `to_dict()` inclui `'password': self.password` em GET /users/<id>, POST /users, PUT /users/<id>, POST /login | Senhas expostas em respostas de API; GET /users (lista) está seguro mas endpoints específicos expõem hashes MD5 |
| 3.2 | Hardcoded credenciais de email | notification_service.py | 9-10 | `email_user = 'taskmanager@gmail.com'`, `email_password = 'senha123'` | Qualquer pessoa pode enviar emails como a app |
| 3.3 | Hardcoded SECRET_KEY | app.py | 13 | `app.config['SECRET_KEY'] = 'super-secret-key-123'` | Qualquer pessoa com acesso ao repo falsifica sessões |

### 🟠 HIGH

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 3.4 | MD5 para hashing | user.py | 29 | `hashlib.md5(pwd.encode()).hexdigest()` | MD5 é quebrado (rainbow tables), precisa 0.01s para crack |
| 3.5 | N+1 queries | task_routes.py | 41-46, 50-56 | Para cada task, faz query de User; para cada task, query de Category | Performance ruim em listas grandes |

### 🟡 MEDIUM

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 3.6 | Bare except | task_routes.py | 62 | `except:` sem tipo de exceção | Silencia exceções legítimas, hard de debugar |
| 3.7 | Duplicação de lógica | task_routes.py | 30-39 vs 71-80 | Cálculo de `overdue` repetido em 2 lugares | Mudanças precisam ser feitas em 2 lugares |
| 3.8 | DEBUG mode ativo | app.py | 34 | `app.run(debug=True)` em ambiente que se apresenta como v1.0 produção | Stack traces expostos |
| 3.9 | Global state em service | notification_service.py | 6 | `self.notifications = []` compartilhado entre todas as instâncias | Notificações de um usuário vazam para outro |

### 🔵 LOW

| # | Problema | Arquivo | Linha | Descrição | Impacto |
|---|----------|---------|-------|-----------|---------|
| 3.10 | Ternário desnecessário | user.py | 34-38 | `if self.role == 'admin': return True else: return False` | Deveria ser `return self.role == 'admin'` |

---

## Resumo Consolidado

### Por Severidade (total de 44 achados)
- **CRITICAL:** 13 achados (SQL Injection, hardcoded secrets, exposição de dados, endpoints perigosos)
- **HIGH:** 13 achados (God Classes, callback hell, N+1, data integrity)
- **MEDIUM:** 12 achados (Debug mode, duplicação, bare except, global state)
- **LOW:** 6 achados (Magic strings, ternários desnecessários)

### Problemas mais frequentes (aparecem em múltiplos projetos)
1. **Hardcoded secrets/credenciais** - Projetos 1, 2, 3
2. **Senhas em texto plano** - Projetos 1, 2, 3
3. **God Classes/Modules** - Projetos 1, 2, 3
4. **DEBUG mode ativo** - Projetos 1, 3
5. **N+1 queries** - Projetos 1, 3
6. **Duplicação de código** - Projetos 1, 3
7. **Global state mutável** - Projetos 2, 3

---

## Padrões de Refatoração Necessários

A skill precisará saber como:

1. **Detectar SQL Injection** → Converter para parameterized queries
2. **Extrair secrets** → Mover para config/env vars
3. **Hash de senha** → Usar bcrypt/argon2 em vez de MD5/plain text
4. **Dividir God Classes** → Separar em Models, Controllers, Services
5. **Eliminar N+1** → Eager loading / joins
6. **Remover duplicação** → Extrair em funções/métodos reutilizáveis
7. **Estruturar como MVC** → config/, models/, views/routes/, controllers/
