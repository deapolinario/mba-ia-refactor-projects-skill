# Auditoria (Fases 1-2 apenas): code-smells-project
**Versão da Skill:** 2.2
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T10-14-52
**Contexto:** Reauditoria pós Fase 3 completa (commits `0d31e2c` skill v2.2 + `45d1131` refactor sistemático)

---

## PHASE 1: PROJECT ANALYSIS

```
Language:       Python 3.x
Framework:      Flask
Database:       SQLite (loja.db)
Domain:         E-commerce / Product Management API
Architecture:   Structured (MVC: models/, routes/, controllers/)
Source files:   16 files analyzed
DB tables:      4 (produtos, usuarios, pedidos, itens_pedido)
```

---

## PHASE 2: ARCHITECTURE AUDIT — varredura dos 18 anti-patterns do catálogo v2.2

| # | Anti-pattern | Severidade | Resultado |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Nenhum achado |
| 2 | Hardcoded Secrets | CRITICAL | ✅ Nenhum achado |
| 3 | Senhas em Texto Plano | CRITICAL | ✅ Nenhum achado |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Nenhum achado |
| 5 | Broken Access Control | CRITICAL | ✅ Nenhum achado |
| 6 | Weak Password Hashing | HIGH | ✅ Nenhum achado |
| 7 | God Classes | HIGH | ✅ Nenhum achado |
| 8 | N+1 Queries | HIGH | 🟡 **1 achado (ver detalhe)** |
| 9 | Global State Mutável | HIGH | ✅ Nenhum achado |
| 10 | Code Duplication | MEDIUM | ✅ Nenhum achado |
| 11 | Secrets em Responses | MEDIUM | ✅ Nenhum achado |
| 12 | Logs Sensíveis (PII) | MEDIUM | ✅ Nenhum achado |
| 13 | Exception Detail Leakage | MEDIUM | ✅ Nenhum achado |
| 14 | Magic Strings | LOW | ✅ Nenhum achado |
| 15 | Ternários Desnecessários | LOW | ✅ Nenhum achado |
| 16 | Monolithic Architecture | LOW/CRITICAL | ✅ Nenhum achado (MVC completo) |
| 17 | Regressão: setup por-request | HIGH | ✅ Nenhum achado |
| 18 | Configuração Morta | LOW | ✅ Nenhum achado |

---

### 🟡 [MEDIUM] N+1 Query remanescente em `criar_pedido`

**Arquivo:** `models/pedido.py`, linhas 76-84

**Código:**
```python
for item in itens:
    cursor.execute("SELECT * FROM produtos WHERE id = ?", [item["produto_id"]])
    produto = cursor.fetchone()
```

**Descrição:** A Fase 3 v2.2 eliminou o N+1 de leitura (`get_pedidos_usuario`/`get_todos_pedidos`, que escalava com o tamanho da tabela de pedidos), mas `criar_pedido` ainda executa 1 query de produto por item do carrinho, dentro de um loop — mesmo padrão estrutural, escopo menor (limitado ao nº de itens de 1 request).

**Impacto:** Baixo em volume típico (carrinho de poucos itens), mas seria o vetor de degradação se um pedido tivesse muitos itens.

**Refatoração proposta:**
```python
ids = [item["produto_id"] for item in itens]
placeholders = ",".join("?" * len(ids))
cursor.execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids)
produtos_por_id = {row["id"]: row for row in cursor.fetchall()}
```

---

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de achados | 1 |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 1 |
| LOW | 0 |

Comparado à auditoria pós-Fase 3 anterior (`audit-code-smells-project-2026-09-20T10-11-42.md`, 0 achados), esta reauditoria — feita lendo o código atual arquivo por arquivo em vez de assumir o log de refactoring — encontrou **1 ponto que passou despercebido**: um N+1 residual em escrita, distinto do N+1 de leitura já corrigido.

**Status:** Fase 2 completa. Aguardando decisão do usuário sobre Fase 3 (aplicar o fix do achado MEDIUM ou aceitar o risco no escopo atual).
