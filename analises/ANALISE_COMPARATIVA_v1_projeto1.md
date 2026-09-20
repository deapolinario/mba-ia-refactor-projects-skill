# Análise Comparativa: Skill vs. Análise Manual
## code-smells-project (Python/Flask)

**Data da Análise:** 2026-09-20  
**Objetivo:** Validar cobertura e acurácia da skill `refactor-arch`

---

## 📊 Resumo Estatístico

| Métrica | Análise Manual | Skill refactor-arch | Cobertura | Status |
|---------|----------------|-------------------|-----------|--------|
| **CRITICAL** | 5 achados | 6 achados | 100% + 1 extra | ✅ Excedeu |
| **HIGH** | 3 achados | 2 achados | 67% | ⚠️ Incompleto |
| **MEDIUM** | 4 achados | 0 achados | 0% | ❌ Perdeu |
| **LOW** | 2 achados | 0 achados | 0% | ❌ Perdeu |
| **TOTAL** | 14 achados | 8 achados | 57% | ⚠️ Cobertura Parcial |

---

## ✅ Achados Detectados pela Skill (Cobertura Correta)

### [CRITICAL] SQL Injection (5 instâncias)

**Skill Detectou:**
- ✅ `get_produto_por_id()` - linha 28
- ✅ `criar_produto()` - linhas 47-50
- ✅ `atualizar_produto()` - linhas 57-61
- ✅ `deletar_produto()` - linha 68
- ✅ `login_usuario()` - linhas 109-111

**Manual Indicava (linha 28, 48-50, 57-61, 92, 110, 140, 174, 188, 192, 220, 224, 280, 291):**
- Skill cobriu 5 de 13 SQL Injections mencionadas na análise manual

**Qualidade da Descrição:** ⭐⭐⭐⭐ Excelente
- Exemplos de exploit concretos (ex: `' OR '1'='1`, comentários SQL)
- Impacto bem explicado
- Refatoração clara com parameterized queries

---

### [CRITICAL] Hardcoded SECRET_KEY

**Skill Detectou:**
- ✅ `app.py` linha 7: `"minha-chave-super-secreta-123"`

**Manual Indicava:** ✅ Achado 1.2

**Qualidade:** ⭐⭐⭐⭐⭐ Excelente
- Explicação de OWASP A02:2021
- Proposta de `config.py` com `os.getenv()`
- Instruções de `.gitignore`

---

### [CRITICAL] Hardcoded Credentials em Seed

**Skill Detectou:**
- ✅ `database.py` linhas 75-83 (senhas plaintext: "admin123", "123456", "senha123")

**Manual Indicava:** ✅ Achado 1.3

**Qualidade:** ⭐⭐⭐⭐ Muito Bom
- Explicação clara de risco
- Sugestão de usar `werkzeug.security.generate_password_hash()`
- Mas **não mencionou MD5 vs. Bcrypt** (Manual apontava isso no projeto 3)

---

### [HIGH] Database Path Hardcoded

**Skill Detectou:**
- ✅ `database.py` linha 5: `db_path = "loja.db"`

**Manual Indicava:** ❌ Não foi detectado na análise manual
- Manual focou em CRITICAL e HIGH, mas não mencionou path hardcoded

**Status:** Achado novo da skill, válido

---

## ❌ Achados PERDIDOS pela Skill (Gaps Críticos)

### [CRITICAL] Endpoint de Query Arbitrária - `/admin/query`

**Manual Indicava (Achado 1.4):**
```
Arquivo: app.py, linhas 59-78
Problema: POST /admin/query permite executar QUALQUER SQL sem autenticação
Impacto: Acesso total ao BD, roubo de dados, exclusão total
```

**Código:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)  # ← EXECUTA QUALQUER SQL
```

**Skill Detectou:** ❌ NÃO
- Este é um **achado CRÍTICO** que foi completamente ignorado
- Qualquer pessoa pode chamar `POST /admin/query` com `{"sql": "DROP TABLE usuarios"}`
- Não há autenticação, autorização ou validação

**Impacto de Severidade:** 🔴 **CRÍTICO** - Qualquer pessoa apaga a base

---

### [CRITICAL] Endpoint de Reset sem Proteção - `/admin/reset-db`

**Manual Indicava (Achado 1.5):**
```
Arquivo: app.py, linhas 47-57
Problema: POST /admin/reset-db deleta TODOS os dados sem autenticação/confirmação
Impacto: Perda total de dados
```

**Código:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")  # ← DELETA TUDO
    db.commit()
```

**Skill Detectou:** ❌ NÃO
- Endpoint público que apaga **TODA A BASE DE DADOS**
- Sem autenticação, sem confirmação, sem audit
- Severidade: 🔴 **CRÍTICO**

---

### [HIGH] God Module (Achado 1.6)

**Manual Indicava:**
```
Arquivo: models.py (linhas 1-315)
Problema: Arquivo único contém TODA lógica de negócio:
  - Queries SQL (6+ funções)
  - Transformações de dados
  - Lógica de pedidos
  - Lógica de relatórios
Impacto: Impossível testar em isolamento, qualquer mudança quebra tudo
Severidade: HIGH (arquitetura)
```

**Skill Detectou:** ❌ NÃO
- Skill focou apenas em SQL Injection + Hardcoded Secrets (v1.0)
- Não detecta violações de princípios SOLID (Single Responsibility)

---

### [HIGH] N+1 Queries (Achado 1.7)

**Manual Indicava:**
```
Arquivo: models.py (linhas 187-199, 219-231)
Problema: Loop dentro de loop
  - Para cada pedido, faz query de itens (linha 188)
  - Para cada item, faz query de produto (linha 192)
  
get_pedidos_usuario():
  for row in rows:  # Loop 1: N pedidos
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ...")  # Query N
    for item in itens:  # Loop 2: M itens
      cursor3.execute("SELECT nome FROM produtos WHERE id = ...")  # Query N*M

Impacto: Performance degradada exponencialmente
Exemplo: 10 pedidos × 5 itens = 50 queries ao invés de 1

Severidade: HIGH (performance)
```

**Skill Detectou:** ❌ NÃO
- Skill v1.0 não foi programada para detectar padrões de performance
- Não faz análise de loops aninhados com queries

---

### [HIGH] Estado Global Mutável (Achado 1.8)

**Manual Indicava:**
```
Arquivo: database.py (linhas 4, 9)
Código:
  db_connection = None  # Variável global
  
  def get_db():
    global db_connection
    if db_connection is None:
      db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection

Problema: 
  - `db_connection` é compartilhada entre requests
  - `check_same_thread=False` desativa thread-safety
  - Race conditions em concorrência

Impacto: Dados corrompidos, comportamento impredizível
Severidade: HIGH (concorrência)
```

**Skill Detectou:** ❌ NÃO
- Skill v1.0 não analisa padrões de concorrência
- Não detecta `global` statements ou thread-safety issues

---

### [MEDIUM] DEBUG Mode Ativo (Achado 1.9)

**Manual Indicava:**
```
Arquivo: app.py (linha 8)
Código: app.config["DEBUG"] = True
Problema: Debug mode ativo em app que se apresenta como produção
Impacto: Exposição de stack traces, information disclosure
Severidade: MEDIUM
```

**Skill Detectou:** ❌ NÃO

---

### [MEDIUM] Duplicação de Código (Achado 1.10)

**Manual Indicava:**
```
Arquivo: models.py (202-233 vs 171-201)
Problema: `get_todos_pedidos()` e `get_pedidos_usuario()` têm lógica idêntica
Impacto: Mudanças devem ser feitas em 2 lugares
Severidade: MEDIUM (manutenibilidade)
```

**Skill Detectou:** ❌ NÃO

---

### [MEDIUM] Secrets em Response (Achado 1.11)

**Manual Indicava:**
```
Arquivo: controllers.py (linha 289)
Código: health_check() retorna `"secret_key": "minha-chave-super-secreta-123"`
Impacto: Exposição da chave em logs/monitoramento
Severidade: MEDIUM (information disclosure)
```

**Código:**
```python
def health_check():
    # ... outras queries ...
    return jsonify({
        "status": "ok",
        "secret_key": "minha-chave-super-secreta-123",  # ← EXPÕE CHAVE
        "debug": True,
        "ambiente": "producao"
    }), 200
```

**Skill Detectou:** ❌ NÃO
- Enquanto a skill detectou o hardcoding em `app.py`, não detectou a exposição na resposta

---

### [MEDIUM] Logs Sensíveis (Achado 1.12)

**Manual Indicava:**
```
Arquivo: controllers.py (linha 161)
Código: print("Usuário criado: " + email)
Problema: Email exposto em logs
Impacto: Vazamento de PII
Severidade: MEDIUM
```

**Skill Detectou:** ❌ NÃO

---

### [LOW] Magic Strings (Achado 1.13)

**Manual Indicava:**
```
Arquivo: controllers.py (52-54)
Lista hardcoded de categorias válidas
Severity: LOW
```

**Skill Detectou:** ❌ NÃO

---

### [LOW] Falta de Validação em LIKE (Achado 1.14)

**Manual Indicava:**
```
Arquivo: models.py (285-299)
Problema: Parâmetros de busca não validados (sql injection via LIKE)
Severity: LOW
```

**Skill Detectou:** ❌ NÃO
- Nota: A busca em `buscar_produtos()` também está concatenada:
  ```python
  query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
  ```
  Isto deveria ter sido detectado na lista de SQL Injections!

---

## 🔍 Análise Detalhada de Gaps

| Achado | Tipo | Manual | Skill | Motivo do Gap |
|--------|------|--------|-------|---------------|
| 1.1 SQL Injection (13 linhas) | CRITICAL | ✅ | ⚠️ 5/13 | Skill detectou ~40% das instâncias |
| 1.2 Hardcoded SECRET_KEY | CRITICAL | ✅ | ✅ | OK |
| 1.3 Senhas plaintext | CRITICAL | ✅ | ✅ | OK |
| 1.4 Endpoint /admin/query | CRITICAL | ✅ | ❌ | Skill não detecta endpoints arbitrários |
| 1.5 Endpoint /admin/reset-db | CRITICAL | ✅ | ❌ | Skill não detecta endpoints arbitrários |
| 1.6 God Module | HIGH | ✅ | ❌ | Fora do escopo v1.0 |
| 1.7 N+1 Queries | HIGH | ✅ | ❌ | Fora do escopo v1.0 |
| 1.8 Estado global | HIGH | ✅ | ❌ | Fora do escopo v1.0 |
| 1.9-1.14 MEDIUM/LOW | MEDIUM/LOW | ✅✅✅✅ | ❌❌❌❌ | Fora do escopo v1.0 |

---

## 🎯 Achados Que Skill Fez Mas Manual Não Detectou

### [HIGH] Hardcoded Database Path

**Skill Detectou:**
```python
db_path = "loja.db"  # ← Deveria ser carregado de env
```

**Manual Indicava:** ❌ Não mencionou
- Skill está correto: isto é uma má prática
- Mas severidade de HIGH é questionável para SQLite (não é credencial)

---

## 📈 Matriz de Cobertura

```
CRÍTICAS (5 esperadas):
├─ SQL Injection...................... ✅ ⚠️ (5/13 = 38%)
├─ SECRET_KEY hardcoded............... ✅ 100%
├─ Senhas plaintext................... ✅ 100%
├─ Endpoint /admin/query.............. ❌ 0%
└─ Endpoint /admin/reset-db........... ❌ 0%

ALTAS (3 esperadas):
├─ God Module......................... ❌ 0%
├─ N+1 Queries........................ ❌ 0%
├─ Estado global...................... ❌ 0%
└─ Database Path (skill extra)........ ⚠️ Questionável

MÉDIA/BAIXA (6 esperadas):
├─ DEBUG mode......................... ❌ 0%
├─ Duplicação de código............... ❌ 0%
├─ Secrets em response................ ❌ 0%
├─ Logs sensíveis..................... ❌ 0%
├─ Magic strings...................... ❌ 0%
└─ Falta de validação em LIKE......... ❌ 0%

TOTAL: 8/14 detectados (57% cobertura)
```

---

## 🚨 Achados Críticos Que Faltaram

| Achado | Severidade | Impacto | Recomendação |
|--------|-----------|---------|--------------|
| `/admin/query` sem auth | 🔴 CRÍTICO | Acesso total ao BD | Adicionar v1.1 |
| `/admin/reset-db` sem auth | 🔴 CRÍTICO | Perda de dados | Adicionar v1.1 |
| SQL Injection incompleto (13 vs 5) | 🔴 CRÍTICO | 8 instâncias faltam | Melhorar regex |
| N+1 Queries | 🟠 HIGH | Performance | Adicionar v1.2 |
| God Module | 🟠 HIGH | Arquitetura | Fora do escopo |

---

## 💡 Recomendações de Melhoria

### Curto Prazo (v1.1)

1. **Expandir detecção de SQL Injection**
   - Detectar: `buscar_produtos()` (linhas 289-297)
   - Detectar: `get_usuario_por_id()` (linha 92)
   - Detectar: `get_pedidos_usuario()` (linha 174)
   - Detectar: `get_todos_pedidos()` (linha 220)
   - Usar regex mais abrangente para concatenação em queries

2. **Adicionar detecção de endpoints perigosos**
   - Procurar por `@app.route()` sem autenticação
   - Detecção de `cursor.execute()` direto de `request.get_json()`
   - Avisar sobre endpoints tipo `/admin/*` sem proteção

3. **Adicionar detecção de exposição de secrets**
   - Procurar por `return jsonify()` que inclui `SECRET_KEY`, `PASSWORD`, etc
   - Avisar sobre dados sensíveis em respostas HTTP

### Médio Prazo (v1.2)

4. **Adicionar detecção de N+1 Queries**
   - Detectar loops (`for x in ...`) dentro de funções que fazem queries
   - Avisar sobre performance

5. **Adicionar detecção de DEBUG mode**
   - Procurar por `DEBUG = True`
   - Procurar por `debug=True` em `app.run()`

### Longo Prazo (v2.0)

6. **Adicionar análise de arquitetura**
   - Detectar God Classes/Modules
   - Sugerir separação de responsabilidades
   - Validar padrão MVC

---

## ✨ Pontos Positivos da Skill

1. **Acurácia dos achados detectados:** Todos os 8 achados estão corretos
2. **Qualidade das refatorações propostas:** Exemplos concretos e bem explicados
3. **Explicações de segurança:** OWASP, PBKDF2, parameterized queries bem explicados
4. **Estrutura do relatório:** Muito bem organizado e legível
5. **Automation:** Gerou o relatório automaticamente

---

## 📋 Conclusão

**Cobertura Atual:** 57% (8/14 achados)

**Função Principal (SQL Injection + Hardcoded Secrets):** ✅ FUNCIONA
- SQL Injection: 5/13 detectadas (38%)
- Hardcoded Secrets: 3/3 detectadas (100%)

**Gaps Críticos:**
- Endpoints perigosos sem autenticação (2 CRITICAL não detectados)
- SQL Injections incompletas (8 instâncias faltam)
- Problemas de arquitetura e performance não detectados (esperado v1.0)

**Recomendação:**
✅ A skill é ÚTIL para detectar SQL Injection e secrets
⚠️ Mas INCOMPLETA para auditoria de segurança completa
❌ Não deve ser usada como única ferramenta de segurança

**Próxima Ação:** Melhorar v1.1 para detectar endpoints perigosos
