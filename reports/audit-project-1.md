# Auditoria Arquitetural: code-smells-project
**Versão da Skill:** 3.2 (20 anti-patterns, adiciona detecção de APIs deprecated)
**Data da Auditoria:** 2026-09-22
**Timestamp:** 2026-09-22T21-20-19
**Contexto:** Re-execução da skill após a v3.2 adicionar o Padrão 20 (APIs Deprecated) ao catálogo. Projeto já havia passado por 4 rodadas de refatoração anteriores (v2.1, v2.2, v3.1), incluindo um self-verification v3.1 com teste funcional completo de autorização (10 cenários, 0 achados — ver `audit-code-smells-project-2026-09-20T17-11-08.md`).

---

## PHASE 1: PROJECT ANALYSIS

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       Python 3
Framework:      Flask 3.1.1 (flask-cors)
Database:       SQLite (via sqlite3, loja.db — Singleton DatabaseManager)
Domain:         E-commerce API (produtos, pedidos, usuários, checkout) — auth
                 por sessão (auth.py: login_required/role_required/
                 owner_or_role_required) e guard admin mínimo por token
Architecture:   MVC (config/, database.py, models/, routes/, controllers/,
                 app.py como entry point) — resultado de 4 refatorações
                 anteriores (v2.1, v2.2, v3.1)
Source files:   17 files analyzed (excluindo .claude/, .venv/, __pycache__)
DB tables:      produtos, usuarios, pedidos, itens_pedido
================================
```

---

## PHASE 2: AUDIT COMPLETE

### Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 2 achados
- **Total:** 2 achados

Nota: o Padrão 20 (APIs Deprecated), motivo da atualização da skill para v3.2, não encontrou ocorrências neste projeto — não há uso de `datetime.utcnow()` ou equivalente; timestamps são gerados pelo próprio SQLite (`DEFAULT CURRENT_TIMESTAMP`).

### Findings

1. **[LOW]** Magic Numbers — faixas de desconto hardcoded (`10000`, `5000`, `1000`, `0.1`, `0.05`, `0.02`) em `models/pedido.py:137-142`, sem constante nomeada (diferente de `VALID_CATEGORIES`/`VALID_ORDER_STATUSES`, já centralizados em `Config` desde v2.2).
2. **[LOW]** Magic Numbers — limites de tamanho do nome do produto (`2`, `200`) hardcoded em `controllers/produto_controller.py:45,47`.

Relatório completo com snippets de código, impacto e refatoração proposta de cada achado: `audit-code-smells-project-2026-09-22T21-20-19.md`.

---

## PHASE 3: REFACTORING COMPLETE

Ambos os achados corrigidos:

1. `Config.FAIXAS_DESCONTO` (lista de tuplas `(limite, percentual)`) centraliza as faixas de desconto; `models/pedido.py::relatorio_vendas()` itera sobre a lista em vez de `if/elif` com literais
2. `Config.MIN_PRODUTO_NOME`/`MAX_PRODUTO_NOME` centralizam os limites de tamanho do nome do produto

### Self-Verification (Ciclo 1)

Código relido do zero + checklist completo dos 20 anti-patterns reaplicado. **0 achados novos** — nenhuma das mudanças tocou arquivos de autenticação/autorização, então a suíte funcional de 10 cenários já validada em `audit-code-smells-project-2026-09-20T17-11-08.md` permanece válida. Relatório completo: `audit-code-smells-project-2026-09-22T21-25-13.md`.

### Validação

- ✅ `python -m py_compile` em todos os arquivos: sem erros de sintaxe
- ✅ Servidor Flask inicia e responde em `/health`, `/login`, `/produtos`, `/pedidos`, `/relatorios/vendas`
- ✅ Testado via requisições HTTP reais: pedido de R$ 11.999,98 → desconto de R$ 1.200,00 (10%, faixa `> 10000`) calculado corretamente; `POST /produtos` com nome de 1/201 caracteres → 400; com 2 caracteres (limite válido) → 201

---

## PHASE 2: RE-EXECUÇÃO DE CONFIRMAÇÃO (Padrão 20 generalizado)

**Timestamp:** 2026-09-22T21-36-26

Após o Padrão 20 ser generalizado (deixou de ser específico a `datetime.utcnow()`/exemplos fixos de Python-Node e passou a ser um princípio de detecção agnóstico de linguagem — commit `1d48260`), a skill foi executada novamente do zero para confirmar o estado do projeto sob o catálogo corrigido.

**Resultado: 0 achados.** Aplicado o princípio geral do Padrão 20 contra a stack real (Python 3.9, Flask 3.1.1, Werkzeug, sqlite3, flask-cors 5.0.1) — nenhuma API atualmente deprecated em uso (verificado além de `datetime.utcnow()`: `flask.Markup`/`before_first_request`/`safe_str_cmp`, `collections.Iterable`/`Mapping`, `imp`/`distutils`/`optparse`/`urllib2`, adapters de datetime do `sqlite3`). Os 2 achados LOW corrigidos na rodada anterior permanecem estáveis. Relatório completo: `audit-code-smells-project-2026-09-22T21-36-26.md`.
