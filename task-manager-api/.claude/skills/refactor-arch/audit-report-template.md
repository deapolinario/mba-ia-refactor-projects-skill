# Template de Relatório de Auditoria (Fase 2)

## Estrutura Padrão

```markdown
# Relatório de Auditoria - [PROJETO]

**Data:** [DATA]
**Stack:** [LINGUAGEM] + [FRAMEWORK] + [DB]
**Domínio:** [DESCRIÇÃO]

---

## Resumo Executivo

- **CRITICAL:** X achados
- **HIGH:** X achados
- **MEDIUM:** X achados
- **LOW:** X achados
- **Total:** X achados

---

## Findings Detalhados

### [CRITICAL] [Nome do Anti-Pattern]

**Arquivo:** `path/to/file.py` (Linhas: X-Y)

**Descrição:**
Explicação clara do problema encontrado.

**Código Problemático:**
\`\`\`python
# snippet de 3-5 linhas mostrando o problema
\`\`\`

**Impacto:**
- Consequência 1
- Consequência 2
- Consequência 3

**Refatoração Proposta:**
\`\`\`python
# código corrigido
\`\`\`

**Por quê:**
Explicação breve de segurança/arquitetura.

---

### [HIGH] [Nome do Anti-Pattern]

[Mesmo formato acima]

---

### [MEDIUM] [Nome do Anti-Pattern]

[Mesmo formato acima]

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Criação de `.env` com secrets
2. Conversão de queries SQL
3. Validação de startup
4. Teste de endpoints

**Confirmar refatoração? [y/n]**
```

---

## Regras para Preenchimento

1. **Ordenar por severidade:** CRITICAL → HIGH → MEDIUM → LOW
2. **Cada finding precisa ter:**
   - Arquivo e linhas exatas
   - Snippet de código
   - Impacto claro
   - Solução concreta
3. **Agrupar achados similares:** Se há 3 SQL Injections, listar como sub-findings
4. **Ser específico:** Não dizer "código ruim"; dizer "query concatenada sem parâmetros"
5. **Usar markdown para legibilidade:** Headers, code blocks, listas

---

## Exemplo Preenchido

```markdown
# Relatório de Auditoria - task-manager-api

**Data:** 2026-09-20
**Stack:** Python 3.9 + Flask 2.x + SQLite
**Domínio:** Task Manager API (users, tasks, categories)

---

## Resumo Executivo

- **CRITICAL:** 3 achados
- **HIGH:** 2 achados
- **MEDIUM:** 1 achado
- **LOW:** 0 achados
- **Total:** 6 achados

---

## Findings Detalhados

### [CRITICAL] Hardcoded SECRET_KEY

**Arquivo:** `app.py` (Linha: 13)

**Descrição:**
Chave secreta de sessão embarcada no código-fonte.

**Código Problemático:**
\`\`\`python
app.config['SECRET_KEY'] = 'super-secret-key-123'
\`\`\`

**Impacto:**
- Qualquer pessoa com acesso ao repositório pode falsificar sessões
- Violação de segurança de aplicação
- Impossível rodar produção com este código

**Refatoração Proposta:**
\`\`\`python
# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY não definida em variáveis de ambiente")

# app.py
from config import Config
app.config['SECRET_KEY'] = Config.SECRET_KEY
\`\`\`

**Por quê:**
Variáveis de ambiente não são versionadas no Git. `.env` fica local e é adicionado ao `.gitignore`.

---

[... mais findings ...]
```
