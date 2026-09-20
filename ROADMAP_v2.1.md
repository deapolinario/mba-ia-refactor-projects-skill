# Roadmap Skill Refactor Architecture v2.1

**Data:** 2026-09-20
**Status:** Em planejamento
**Objetivo:** Preencher gaps identificados nas análises comparativas v2.0

---

## Gaps Identificados

### [MEDIUM] Secrets Expostas em Responses

**Projeto:** code-smells-project (Achado 1.11)
**Status Atual:** ❌ NÃO DETECTADO
**Localização:** `controllers.py` linha 289 (health_check)

**Problema:**
```python
def health_check():
    return jsonify({
        "secret_key": "minha-chave-super-secreta-123",  # ← EXPÕE!
        "debug": True,
        "ambiente": "producao"
    })
```

**Padrões a Detectar:**
- `return jsonify(...)` contendo `SECRET_KEY`, `PASSWORD`, `API_KEY`
- `res.json()` em Node.js contendo secrets
- Endpoints públicos (health_check, status, info) expondo dados sensíveis

**Refatoração:**
```python
# ❌ ANTES
return jsonify({
    "secret_key": "...",
    "debug": True
})

# ✅ DEPOIS
return jsonify({
    "status": "ok",
    "version": "1.0.0"
    # Remover todos os secrets
})
```

---

### [MEDIUM] Logs Sensíveis (PII)

**Projeto:** code-smells-project (Achado 1.12)
**Status Atual:** ❌ NÃO DETECTADO
**Localização:** `controllers.py` linha 161

**Problema:**
```python
# Python
print("Usuário criado: " + email)  # ← EXPÕE EMAIL

# Node.js
console.log(`Cartão: ${cc}`);  # ← EXPÕE CARTÃO
```

**Padrões a Detectar:**
- `print()`, `console.log()` com variáveis como email, password, cc, cpf
- `logger.*()` com dados sensíveis
- Email patterns: `\w+@\w+\.\w+`
- Cartão de crédito: `\d{16}` ou `\d{13}`
- CPF/SSN: `\d{3}\.\d{3}\.\d{3}-\d{2}`

**Refatoração:**
```python
# ✅ BOM
def mask_email(email):
    parts = email.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"

print(f"Usuário criado: {mask_email(email)}")
```

---

### [HIGH] Estado Global Mutável (Race Conditions)

**Projeto:** code-smells-project (Achado 1.8)
**Status Atual:** ❌ NÃO DETECTADO
**Localização:** `database.py` linhas 4, 10

**Problema:**
```python
# ❌ Global compartilhado
db_connection = None  # Variável global

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```

**Padrões a Detectar:**
- `global` keyword
- Variáveis no module level sem capitalização
- `check_same_thread=False` em SQLite
- Mutação de variáveis globais

**Refatoração:**
```python
# ✅ BOM
class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

### [LOW] Magic Strings e Magic Numbers

**Projeto:** code-smells-project (Achado 1.13)
**Status Atual:** ❌ NÃO DETECTADO
**Localização:** `controllers.py` linhas 52-54

**Problema:**
```python
# ❌ Hardcoded categories
categorias_validas = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
if categoria not in categorias_validas:
    return jsonify({"erro": "Categoria inválida"})
```

**Padrões a Detectar:**
- Listas/dicts hardcoded com múltiplos valores
- Magic numbers sem constantes
- Status codes hardcoded (200, 404, 500)

**Refatoração:**
```python
# ✅ BOM
# config.py
VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

# controllers.py
if categoria not in Config.VALID_CATEGORIES:
    return jsonify({"erro": "Categoria inválida"}), 400
```

---

### [LOW] Ternários Desnecessários

**Projeto:** task-manager-api (Achado 3.10)
**Status Atual:** ❌ NÃO DETECTADO
**Localização:** `user.py` linhas 34-38

**Problema:**
```python
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```

**Padrão a Detectar:**
```
if <condition>:
    return True
else:
    return False
```

**Refatoração:**
```python
def is_admin(self):
    return self.role == 'admin'
```

---

## Plano de Implementação v2.1

### Fase 1: Atualizar Anti-Patterns Catalog

**Arquivo:** `.claude/skills/refactor-arch/anti-patterns-catalog.md`

Adicionar 5 novos anti-patterns:
1. ✅ Secrets Expostas em Responses (MEDIUM)
2. ✅ Logs Sensíveis / PII Exposure (MEDIUM)
3. ✅ Global State Mutável (HIGH)
4. ✅ Magic Strings / Magic Numbers (LOW)
5. ✅ Ternários Desnecessários (LOW)

---

### Fase 2: Atualizar Refactoring Playbook

**Arquivo:** `.claude/skills/refactor-arch/refactoring-playbook.md`

Adicionar padrões de transformação:
1. ✅ Remover secrets de responses JSON
2. ✅ Mascarar dados sensíveis em logs
3. ✅ Converter global state para Singleton/DI
4. ✅ Extrair magic strings para config
5. ✅ Simplificar ternários

---

### Fase 3: Atualizar SKILL.md

**Arquivo:** `.claude/skills/refactor-arch/SKILL.md`

Atualizar:
- Versão: 1.0 → 2.1
- Fase 2 instruções: adicionar novos anti-patterns
- Limites: atualizar para incluir LOW findings

---

### Fase 4: Testar em 3 Projetos

Executar skill v2.1 em:
1. ✅ code-smells-project
2. ✅ ecommerce-api-legacy
3. ✅ task-manager-api

Gerar comparativas v2.1

---

## Métricas Esperadas v2.1

| Projeto | Cobertura v2.0 | Cobertura v2.1 | Δ |
|---------|----------------|----------------|---|
| code-smells-project | 79% (11/14) | ~93% (13/14) | +14% |
| ecommerce-api-legacy | 100% (12/12) | 100% (12/12) | - |
| task-manager-api | 90% (9/10) | 100% (10/10) | +10% |
| **Agregado** | **86%** | **~97%** | **+11%** |

---

## Timeline

- **Hora 1:** Atualizar anti-patterns-catalog.md
- **Hora 2:** Atualizar refactoring-playbook.md
- **Hora 3:** Atualizar SKILL.md
- **Hora 4:** Testar nos 3 projetos
- **Hora 5:** Gerar comparativas v2.1
- **Hora 6:** Commit v2.1

---

## Prioridade

🔴 **CRITICAL:**
- Secrets expostas em responses
- Logs sensíveis (PII)

🟠 **HIGH:**
- Estado global mutável

🟡 **MEDIUM:**
- Magic strings/numbers

🔵 **LOW:**
- Ternários desnecessários

---

## Dependências

- ✅ Nenhuma (self-contained)
- ✅ Não afeta skill v2.0 (apenas expande)
- ✅ Retrocompatível

---

## Kickoff

Pronto para começar? Responda:
1. ✅ Começar agora (v2.1 full)
2. ✅ Parcial (só CRITICAL/HIGH)
3. ✅ Adiar para depois

