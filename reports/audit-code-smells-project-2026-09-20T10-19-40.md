# Auditoria (Fases 1-2 apenas): code-smells-project
**Versão da Skill:** 2.2
**Data da Auditoria:** 2026-09-20
**Timestamp:** 2026-09-20T10-19-40
**Contexto:** Reauditoria após fix do N+1 residual (commit `f1f8797`)

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

Apenas `models/pedido.py` foi alterado desde a auditoria anterior
(`audit-code-smells-project-2026-09-20T10-14-52.md`); os demais 15 arquivos
foram confirmados inalterados via `git log --oneline -1 -- <arquivos>` (todos
apontam para o commit `45d1131`, anterior ao fix atual).

| # | Anti-pattern | Severidade | Resultado |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Nenhum achado |
| 2 | Hardcoded Secrets | CRITICAL | ✅ Nenhum achado |
| 3 | Senhas em Texto Plano | CRITICAL | ✅ Nenhum achado |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Nenhum achado |
| 5 | Broken Access Control | CRITICAL | ✅ Nenhum achado |
| 6 | Weak Password Hashing | HIGH | ✅ Nenhum achado |
| 7 | God Classes | HIGH | ✅ Nenhum achado |
| 8 | N+1 Queries | HIGH | ✅ **Nenhum achado** — `criar_pedido` corrigido (commit `f1f8797`) |
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

## Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de achados | **0** |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

---

## Histórico de Auditorias (code-smells-project)

| Timestamp | Achados | Observação |
|---|---|---|
| 2026-09-20T08-45-00 | 11 | Skill v1.0/v2.0 inicial |
| 2026-09-20T09-18-26 | 11 | v2.0 final |
| 2026-09-20T09-38-22 | 14 | v2.1 (catálogo expandido) |
| 2026-09-20T09-53-39 | 6 | Pós Fase 3 v2.1 (seletiva) |
| 2026-09-20T10-11-42 | 0 | Pós Fase 3 v2.2 (sistemática) — mas baseada no log, não em releitura linha a linha |
| 2026-09-20T10-14-52 | 1 | Reauditoria lendo código atual → achou N+1 residual não coberto pelo log |
| **2026-09-20T10-19-40** | **0** | **Após fix do achado acima — confirmado por releitura completa** |

**Status:** 🟢 Projeto sem achados abertos nos 18 anti-patterns do catálogo v2.2.
