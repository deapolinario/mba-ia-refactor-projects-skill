# Como Executar a Skill Refactor Architecture

## Visão Geral

A skill `refactor-arch` analisa, audita e refatora projetos legados para o padrão MVC. Ela gera automaticamente relatórios de auditoria com **timestamps únicos** para preservar histórico.

## Executar a Skill (RECOMENDADO)

Execute o script centralizado de qualquer projeto:

```bash
# De qualquer projeto
cd code-smells-project
python3 ../.claude/skills/refactor-arch/scripts/run-refactor-audit.py
```

**O script detecta automaticamente:**
- ✅ Qual projeto está sendo analisado
- ✅ Timestamp atual (formato ISO)
- ✅ Cria `reports/` se não existir
- ✅ Gera arquivo com timestamp único

### O que o script faz automaticamente:

1. ✅ Detecta qual projeto está sendo auditado
2. ✅ Pega o timestamp atual (YYYY-MM-DDTHH-MM-SS)
3. ✅ Executa a skill `/refactor-arch`
4. ✅ Renomeia o relatório com timestamp correto
5. ✅ Lista o histórico de relatórios
6. ✅ Preserva todos os relatórios anteriores

### Exemplo de uso:

```bash
$ cd code-smells-project
$ python3 ../.claude/skills/refactor-arch/scripts/run-refactor-audit.py

================================================================================
🔍 Refactor Architecture Skill - v2.0
================================================================================

📁 Projeto: code-smells-project
⏰ Timestamp: 2026-09-20T09-15-42
📊 Gerando relatório com nome único...

▶️  Executando skill '/refactor-arch'...

[Skill executa...]

✅ Relatório salvo com timestamp: audit-code-smells-project-2026-09-20T09-15-42.md

📋 Histórico de relatórios:
   1. audit-code-smells-project-2026-09-20T08-45-00.md (8.8 KB)
   2. audit-code-smells-project-2026-09-20T09-05-38.md (7.9 KB)
   3. audit-code-smells-project-2026-09-20T09-15-42.md (7.9 KB)

================================================================================
✅ Skill executada com sucesso!
================================================================================
```

---

## Alternativa: Claude CLI Direto

Se preferir invocar a skill via Claude CLI (menos recomendado - perde automação de timestamp):

```bash
cd code-smells-project
claude "/refactor-arch"
```

⚠️ **Aviso:** Sem o script, você **pode perder relatórios anteriores** se o arquivo for sobrescrito.

---

## Estrutura de Arquivos

```
mba-ia-refactor-projects-skill/
├── reports/                              ← Relatórios gerados aqui
│   ├── audit-code-smells-project-2026-09-20T08-45-00.md
│   ├── audit-code-smells-project-2026-09-20T09-05-38.md
│   ├── audit-ecommerce-api-legacy-2026-09-20T10-30-15.md
│   └── audit-task-manager-api-2026-09-20T11-45-22.md
│
├── code-smells-project/
├── ecommerce-api-legacy/
├── task-manager-api/
│
└── .claude/
    └── skills/
        └── refactor-arch/
            ├── SKILL.md                  ← Instruções da skill
            ├── anti-patterns-catalog.md
            ├── refactoring-playbook.md
            ├── project-analysis.md
            ├── audit-report-template.md
            ├── architecture-guidelines.md
            └── scripts/
                └── run-refactor-audit.py ← Script único (centralizado)
```

---

## Formato do Nome do Relatório

`audit-{projeto}-{timestamp}.md`

Exemplos:
- `audit-code-smells-project-2026-09-20T09-15-42.md`
- `audit-ecommerce-api-legacy-2026-09-20T10-30-15.md`
- `audit-task-manager-api-2026-09-20T11-45-22.md`

**Cada execução gera um arquivo DIFERENTE** com timestamp único.

---

## Fases da Skill

### Fase 1: Project Analysis
- Detecta linguagem, framework, banco de dados
- Mapeia arquitetura atual
- Conta arquivos e tabelas

### Fase 2: Architecture Audit
- Escaneia código procurando por 7 anti-patterns:
  1. SQL Injection
  2. Hardcoded Secrets
  3. Weak Password Hashing
  4. God Classes
  5. N+1 Queries
  6. Code Duplication
  7. Monolithic Architecture
- Gera relatório estruturado (CRITICAL → HIGH → MEDIUM)
- **Salva automaticamente em `reports/audit-{projeto}-{timestamp}.md`**
- Pausa e pede confirmação antes da Fase 3

### Fase 3: Refactoring & Validation
- Aplica refatorações (se confirmado)
- Cria estrutura MVC
- Valida que a app funciona

---

## Fluxo Recomendado

```
1. Execute o script no projeto 1
   $ cd code-smells-project
   $ python3 ../run-refactor-audit.py
   
2. Fase 1 & 2 executam automaticamente
   → Relatório gerado com timestamp
   → Script pergunta se quer Fase 3
   
3. Responda (y/n) para Fase 3
   
4. Repita para os outros projetos
   $ cd ../ecommerce-api-legacy
   $ python3 ../run-refactor-audit.py
   
5. Verifique o histórico
   $ ls -lah reports/audit-*.md
```

---

## Troubleshooting

### "Script não encontrado"
Certifique-se de estar na raiz do projeto:
```bash
cd /Users/andreapolinario/workspace/mba_ia/mba-ia-refactor-projects-skill
python3 run-refactor-audit.py
```

### "Skill não encontrada"
A skill deve estar em `.claude/skills/refactor-arch/SKILL.md`

Verifique:
```bash
ls -la .claude/skills/refactor-arch/SKILL.md
```

### "Relatório não foi salvo"
Verifique que `reports/` existe:
```bash
ls -la reports/
```

Se não existir, crie:
```bash
mkdir -p reports
```

---

## Próximos Passos

1. ✅ Testar no projeto 1 (code-smells-project)
2. ✅ Testar no projeto 2 (ecommerce-api-legacy)
3. ✅ Testar no projeto 3 (task-manager-api)
4. ✅ Revisar relatórios gerados
5. ✅ Executar Fase 3 (refatoração)
6. ✅ Validar que apps funcionam após refatoração

---

## Versão da Skill

**v2.0** - Cobre:
- ✅ SQL Injection
- ✅ Hardcoded Secrets
- ✅ Weak Password Hashing (MD5/SHA1)
- ✅ God Classes
- ✅ N+1 Queries
- ✅ Code Duplication
- ✅ Monolithic → MVC Refactoring
