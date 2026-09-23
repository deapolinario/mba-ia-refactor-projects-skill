# Relatório de Auditoria - code-smells-project

**Data:** 2026-09-22
**Stack:** Python 3 + Flask 3.1.1 + SQLite (sqlite3 + Singleton `DatabaseManager`)
**Domínio:** E-commerce API (produtos, pedidos, usuários, checkout)
**Contexto:** Execução do catálogo v3.2 (20 anti-patterns, inclui detecção de APIs deprecated — Padrão 20). Projeto já passou por 4 rodadas de refatoração anteriores (v2.1, v2.2, v3.1), incluindo um self-verification v3.1 com teste funcional de autorização completo (10 cenários, 0 achados — ver `audit-code-smells-project-2026-09-20T17-11-08.md`).

---

## Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 2 achados
- **Total:** 2 achados

Nota: o Padrão 20 (APIs Deprecated), motivo desta atualização da skill para v3.2, não encontrou ocorrências neste projeto — não há uso de `datetime.utcnow()` ou equivalente; timestamps são gerados pelo próprio SQLite (`DEFAULT CURRENT_TIMESTAMP`).

---

## Findings Detalhados

### [LOW] Magic Numbers — Faixas de Desconto Hardcoded

**Arquivo:** `models/pedido.py` (Linhas: 137-142)

**Descrição:**
`relatorio_vendas()` calcula desconto aplicável com limiares e percentuais hardcoded (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`) diretamente no corpo da função, sem constante nomeada — diferente de `VALID_CATEGORIES`/`VALID_ORDER_STATUSES`, que já foram corretamente centralizados em `Config` numa refatoração anterior.

**Código Problemático:**
```python
desconto = 0
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
elif faturamento > 1000:
    desconto = faturamento * 0.02
```

**Impacto:** Regra de negócio (faixas/percentuais de desconto) fica implícita no meio do código; qualquer ajuste de política comercial exige encontrar e editar este trecho específico, sem um único lugar óbvio para consultar/alterar os valores.

**Refatoração Proposta:**
```python
# config.py
class Config:
    ...
    FAIXAS_DESCONTO = [
        (10000, 0.10),
        (5000, 0.05),
        (1000, 0.02),
    ]

# models/pedido.py
from config import Config

def _calcular_desconto(faturamento):
    for limite, percentual in Config.FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0
```

**Por quê:** Mesmo princípio já aplicado a `VALID_CATEGORIES`/`VALID_ORDER_STATUSES` neste projeto (v2.2) — só não foi estendido às regras de desconto.

---

### [LOW] Magic Numbers — Limites de Tamanho do Nome do Produto

**Arquivo:** `controllers/produto_controller.py` (Linhas: 45, 47)

**Descrição:**
`_validar_dados()` valida o tamanho do nome do produto com literais `2` e `200` diretamente na condição, sem constante nomeada — mesmo padrão do Padrão 18/11 do catálogo (comparável a `MIN_TITLE_LENGTH`/`MAX_TITLE_LENGTH` já identificado no task-manager-api).

**Código Problemático:**
```python
if len(nome) < 2:
    raise ValueError("Nome muito curto")
if len(nome) > 200:
    raise ValueError("Nome muito longo")
```

**Refatoração Proposta:**
```python
# config.py
class Config:
    ...
    MIN_PRODUTO_NOME = 2
    MAX_PRODUTO_NOME = 200

# controllers/produto_controller.py
if len(nome) < Config.MIN_PRODUTO_NOME:
    raise ValueError(f"Nome muito curto (mínimo {Config.MIN_PRODUTO_NOME} caracteres)")
if len(nome) > Config.MAX_PRODUTO_NOME:
    raise ValueError(f"Nome muito longo (máximo {Config.MAX_PRODUTO_NOME} caracteres)")
```

**Impacto:** Legibilidade e manutenibilidade — ajustar a regra exige localizar o literal em vez de um ponto único de configuração.

**Por quê:** Consistência com o restante do projeto, que já centraliza outras regras de domínio em `Config`.

---

## Verificações Sem Achados (catálogo v3.2 completo)

| Padrão | Resultado |
|---|---|
| SQL Injection | Nenhuma ocorrência — todas as queries usam parâmetros (`?`); `_JOIN_QUERY + " WHERE ..."` e `f"... IN ({placeholders})"` só concatenam SQL estático, valores sempre via bind params |
| Hardcoded Secrets | Nenhuma ocorrência — `.env` corretamente gitignored, `Config` usa `os.getenv` |
| Senha em Texto Plano / Weak Hashing | Nenhuma ocorrência (`generate_password_hash`/`check_password_hash`, pbkdf2:sha256) |
| Dangerous Admin Endpoint | Nenhuma ocorrência (`/admin/query` já removido em v2.2) |
| Broken Access Control | Nenhuma ocorrência (`login_required`/`role_required`/`owner_or_role_required` em toda rota sensível) |
| Privilege Escalation / IDOR | Nenhuma ocorrência — `owner_or_role_required` protege `/usuarios/<id>` e `/pedidos/usuario/<id>`; `usuario_id` do pedido vem da sessão, nunca do payload; `tipo` nunca lido do payload em `POST /usuarios` |
| God Class / Monolithic Architecture | N/A — projeto em MVC (config/models/routes/controllers) |
| N+1 Queries | Nenhuma ocorrência (`_JOIN_QUERY` + `IN (...)` já eliminam os N+1 encontrados em v2.1/v2.2) |
| Global State Mutável | Nenhuma ocorrência (Singleton `DatabaseManager` thread-safe) |
| Code Duplication | Nenhuma ocorrência relevante (serialização centralizada em `_row_to_dict`) |
| Secrets Expostas em Responses | Nenhuma ocorrência |
| Logs Sensíveis (PII) | Nenhuma ocorrência (`mask_email` aplicado a todo log de login) |
| Exception Detail Leakage | Nenhuma ocorrência — todo `except Exception as e` loga internamente e retorna mensagem genérica |
| Regressão de Inicialização Por-Request | Nenhuma ocorrência (`_setup_schema`/`_seed_if_empty` rodam uma vez no `__init__` do Singleton) |
| Configuração Morta | Nenhuma ocorrência |
| Ternários Desnecessários | Nenhuma ocorrência |
| **APIs Deprecated (Padrão 20, novo na v3.2)** | **Nenhuma ocorrência** — sem uso de `datetime.utcnow()` ou equivalente |

---

## Próximas Etapas

Ao confirmar, a Fase 3 executará:
1. Extrair as faixas de desconto para `Config.FAIXAS_DESCONTO`
2. Extrair os limites de tamanho do nome do produto para `Config.MIN_PRODUTO_NOME`/`MAX_PRODUTO_NOME`
3. Validação de startup + boot da aplicação

**Confirmar refatoração na Fase 3? (y/n)**
