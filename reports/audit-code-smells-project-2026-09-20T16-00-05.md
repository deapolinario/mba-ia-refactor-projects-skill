# Relatório de Auditoria - code-smells-project

**Data:** 2026-09-20
**Stack:** Python 3.x + Flask 3.1.1 + SQLite
**Domínio:** API de E-commerce ("Loja") — produtos, usuários, pedidos, itens de pedido
**Tipo de execução:** Reauditoria completa a frio (skill `/refactor-arch` reinvocada; releitura dos 18 arquivos `.py` sem confiar em logs de rodadas anteriores), incluindo o teste funcional de autorização obrigatório do Padrão 19 (v3.1).

---

## Resumo Executivo

- **CRITICAL:** 0 achados
- **HIGH:** 0 achados
- **MEDIUM:** 0 achados
- **LOW:** 0 achados
- **Total:** 0 achados

O projeto já passou por 3 rodadas anteriores de refatoração (v2.1, v2.2, v3.1 — commits até `9ae2433`). Esta execução relê o código do zero, sem tratar o log de refatoração como prova, e reaplica os 19 anti-patterns do catálogo + o teste funcional de autorização. Resultado: nenhum achado novo, nenhuma regressão.

---

## Checklist dos 19 Anti-Patterns (releitura completa)

| # | Anti-Pattern | Severidade | Status |
|---|---|---|---|
| 1 | SQL Injection | CRITICAL | ✅ Limpo — todas as queries parametrizadas (`?`), inclusive a busca dinâmica em `models/produto.py:buscar_produtos` e o `IN()` em `models/pedido.py:criar_pedido` (placeholders gerados, valores sempre via lista de params) |
| 2 | Hardcoded Secrets | CRITICAL | ✅ Limpo — `SECRET_KEY`/`DATABASE_PATH`/`ADMIN_TOKEN` via `Config`/`os.getenv`; nenhum `os.getenv`/`os.environ` fora de `config.py` |
| 3 | Senhas em Texto Plano (storage + comparação + exposição) | CRITICAL | ✅ Limpo — hash `pbkdf2:sha256` no cadastro e seed; comparação via `check_password_hash`; `models/usuario.py:_row_to_dict` nunca inclui a coluna `senha`; único `SELECT *` em `usuarios` é interno a `login_usuario`, cujo retorno é montado manualmente sem o campo `senha` |
| 4 | Dangerous Admin Endpoint | CRITICAL | ✅ Limpo — endpoint `/admin/query` (execução de SQL arbitrário) foi removido na v2.2; `/admin/reset-db` é uma ação fixa (não aceita SQL/código do cliente) |
| 5 | Broken Access Control | CRITICAL | ✅ Limpo — toda rota de escrita e toda rota de leitura sensível tem `@role_required`/`@owner_or_role_required`/`@login_required`/`@admin_required`; catálogo público (`GET /produtos*`) e cadastro/login permanecem intencionalmente públicos |
| 6 | Privilege Escalation via Autorização Insuficiente | CRITICAL | ✅ Limpo (estrutural **e** funcional — ver seção de teste funcional abaixo) — `POST /usuarios` nunca lê `tipo` do payload (`criar_usuario` do controller não repassa esse campo); `POST /pedidos` força `usuario_id` a partir da sessão, ignorando o payload |
| 7 | Weak Password Hashing (MD5/SHA1) | HIGH | ✅ Limpo — `pbkdf2:sha256` via Werkzeug |
| 8 | God Classes (300+ linhas) | HIGH | ✅ Limpo — maior arquivo é `models/pedido.py` com 154 linhas |
| 9 | N+1 Queries | HIGH | ✅ Limpo — `pedido.py` usa `_JOIN_QUERY` (1 query com LEFT JOIN) para listagens e `SELECT ... WHERE id IN (...)` (1 query) para validar itens do carrinho em `criar_pedido`, em vez de 1 query por item |
| 10 | Global State Mutável | HIGH | ✅ Aceitável — `DatabaseManager` é Singleton thread-safe (`threading.Lock`) com setup/seed rodando uma única vez em `__init__`, não por request; sem mutação de estado compartilhado fora da conexão de DB |
| 11 | Code Duplication | MEDIUM | ✅ Limpo — serialização centralizada em `_row_to_dict` (usuario/produto), query de pedidos centralizada em `_JOIN_QUERY` + `_agrupar_pedidos_com_itens` |
| 12 | Secrets Expostas em Responses | MEDIUM | ✅ Limpo — nenhuma rota retorna `SECRET_KEY`/`ADMIN_TOKEN`/hash de senha |
| 13 | Logs Sensíveis (PII) | MEDIUM | ✅ Limpo — `mask_email()` aplicado em todo log de login |
| 14 | Exception Detail Leakage | MEDIUM | ✅ Limpo — todo `except Exception as e` loga com `logger.error(str(e))` e responde mensagem genérica (`"Erro interno do servidor"`); os `except ValueError as e` que retornam `str(e)` ao cliente carregam apenas mensagens de validação controladas pelo próprio controller (ex: `"Nome é obrigatório"`), nunca detalhe de exceção interna |
| 15 | DEBUG Mode Ativo | MEDIUM | ✅ Limpo — `Config.DEBUG = os.getenv('FLASK_ENV') == 'development'`, controlado por env var, não hardcoded `True` |
| 16 | Magic Strings/Numbers | LOW | ✅ Limpo — categorias e status extraídos para `Config.VALID_CATEGORIES`/`Config.VALID_ORDER_STATUSES` |
| 17 | Ternários Desnecessários | LOW | ✅ Limpo — nenhuma ocorrência |
| 18 | Monolithic Architecture | LOW | ✅ Limpo — separação clara `config/`, `models/`, `routes/`, `controllers/`, `app.py` como entry point |
| 19 | Configuração Morta | LOW | ✅ Limpo — `Config.ADMIN_TOKEN` usado em `app.py:33`; nenhum literal antigo de secret coexistindo com a config nova |

---

## Teste Funcional de Autorização (Padrão 19, obrigatório v3.1)

Executado via Flask test client contra DB de teste isolado (arquivo temporário, sem tocar `loja.db`), simulando três perfis: anônimo, cliente de baixo privilégio, admin.

| # | Cenário | Esperado | Resultado |
|---|---|---|---|
| 1 | Cadastro público enviando `"tipo": "admin"` no payload | Usuário criado como `cliente`, campo ignorado | ✅ PASS |
| 2 | Anônimo tenta `PUT /produtos/1` (tamper de preço) | 401 | ✅ PASS |
| 3 | Anônimo tenta `GET /usuarios` (enumeração) | 401 | ✅ PASS |
| 4 | Anônimo tenta `POST /pedidos` | 401 | ✅ PASS |
| 5 | Anônimo lê catálogo `GET /produtos` | 200 (rota pública) | ✅ PASS |
| 6 | Cliente lê o próprio perfil (`GET /usuarios/<próprio id>`) | 200 | ✅ PASS |
| 7 | Cliente tenta ler perfil de outro usuário (IDOR) | 403 | ✅ PASS |
| 8 | Cliente tenta `GET /usuarios` (listagem admin-only) | 403 | ✅ PASS |
| 9 | Cliente tenta `PUT /produtos/1` (tamper de preço) | 403 | ✅ PASS |
| 10 | Cliente tenta `POST /produtos` | 403 | ✅ PASS |
| 11 | Cliente tenta `DELETE /produtos/1` | 403 | ✅ PASS |
| 12 | Cliente cria pedido forjando `usuario_id` de outro usuário no payload | 201, mas gravado com o `usuario_id` real da sessão | ✅ PASS |
| 13 | Cliente tenta `GET /pedidos/usuario/<outro id>` | 403 | ✅ PASS |
| 14 | Cliente tenta `GET /pedidos` (listagem admin-only) | 403 | ✅ PASS |
| 15 | Cliente tenta `PUT /pedidos/1/status` | 403 | ✅ PASS |
| 16 | Cliente tenta `GET /relatorios/vendas` | 403 | ✅ PASS |
| 17-24 | Admin executa as 8 operações acima (caso legítimo) | 200/201 em todas | ✅ PASS |
| 25 | Admin sem `X-Admin-Token` tenta `/admin/reset-db` | 401 | ✅ PASS |

**Total: 29 asserções, 29 PASS, 0 FAIL.**

---

## Validação de Regressão

| Item | Resultado |
|---|---|
| Setup/seed roda uma única vez (não por request) | ✅ `DatabaseManager.__init__` |
| Nenhum N+1 novo | ✅ Nenhuma query de leitura nova em loop |
| Config nova sem uso real | ✅ Nenhuma — todas as `Config.X` têm ponto de uso |
| Literal antigo coexistindo com config nova | ✅ Nenhum |
| `python -m py_compile` em todos os 18 arquivos `.py` | ✅ Sem erros |

---

## Conclusão

**0 achados.** O código refatorado nas rodadas v2.1/v2.2/v3.1 permanece correto: nenhuma regressão estrutural, nenhuma falha de autorização funcional. Não há necessidade de nova Fase 3 — não existe achado para corrigir.

Nenhuma ação adicional recomendada nesta execução.
