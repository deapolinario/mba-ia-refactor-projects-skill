# MVC Refactoring Guide v2.2
**Status:** Em desenvolvimento para v2.2  
**Objetivo:** Guia passo-a-passo para refatorar God Classes em MVC

---

## Fase 3 Completa: God Class → MVC

### 📋 Pré-Requisitos
- [ ] Projeto tem `.env` com secrets
- [ ] Queries estão parametrizadas
- [ ] Logging mascarado
- [ ] Validação de syntax OK

### 🎯 Objetivo
Refatorar `models.py` (315 linhas, múltiplas responsabilidades) em:
- `models/` - Estrutura de dados apenas
- `routes/` - Mapeamento HTTP
- `controllers/` - Lógica de negócio

---

## Passo 1: Analise o God Class

**Arquivo:** `models.py`

**Funções atuais:**
- `get_todos_produtos()` → GET /produtos
- `get_produto_por_id(id)` → GET /produtos/:id
- `criar_produto(...)` → POST /produtos
- `atualizar_produto(...)` → PUT /produtos/:id
- `deletar_produto(id)` → DELETE /produtos/:id
- `get_todos_usuarios()` → GET /usuarios
- `get_usuario_por_id(id)` → GET /usuarios/:id
- `login_usuario(...)` → POST /login
- `criar_usuario(...)` → POST /usuarios
- `criar_pedido(...)` → POST /pedidos
- `get_pedidos_usuario(...)` → GET /pedidos/usuario/:id
- `get_todos_pedidos()` → GET /pedidos
- `atualizar_status_pedido(...)` → PUT /pedidos/:id/status
- `relatorio_vendas()` → GET /relatorios/vendas
- `buscar_produtos(...)` → GET /produtos/search

**Classificação:**
- ✅ **Queries de dados** (métodos com `cursor.execute`) → Models
- ✅ **Lógica HTTP** (GET, POST, PUT, DELETE) → Routes
- ✅ **Validação + Orquestração** → Controllers

---

## Passo 2: Criar Estrutura de Diretórios

```bash
# No projeto code-smells-project
mkdir -p models routes controllers
touch models/__init__.py routes/__init__.py controllers/__init__.py
```

**Estrutura final:**
```
code-smells-project/
├── config.py              # ✅ Já existe
├── database.py            # ✅ Já existe (refatorado)
├── app.py                 # ✅ Já existe (será atualizado)
├── controllers.py         # ❌ SERÁ REMOVIDO (migrado para controllers/)
├── models.py              # ❌ SERÁ REFATORADO (de 315 para 3 arquivos)
│
├── models/                # ✅ NOVO
│   ├── __init__.py
│   ├── produto.py         # Queries de produtos
│   ├── usuario.py         # Queries de usuarios
│   └── pedido.py          # Queries de pedidos
│
├── routes/                # ✅ NOVO
│   ├── __init__.py
│   ├── produto_routes.py  # GET/POST/PUT/DELETE /produtos
│   ├── usuario_routes.py  # GET/POST/PUT/DELETE /usuarios
│   └── pedido_routes.py   # GET/POST/PUT/DELETE /pedidos
│
└── controllers/           # ✅ NOVO
    ├── __init__.py
    ├── produto_controller.py  # Validação + lógica de produtos
    ├── usuario_controller.py  # Validação + lógica de usuarios
    └── pedido_controller.py   # Validação + lógica de pedidos
```

---

## Passo 3: Migrar Models (Queries)

### 3.1 Extrair Queries para `models/produto.py`

**ANTES (models.py linhas 4-314):**
```python
def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    # ... logic
```

**DEPOIS (models/produto.py):**
```python
from database import get_db

def get_todos_produtos():
    """Retorna todos os produtos"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "nome": row["nome"],
            # ...
        })
    return result

def get_produto_por_id(id):
    # ...

def criar_produto(nome, descricao, preco, estoque, categoria):
    # ...
```

**Regra:** Só incluir queries, SEM validação de negócio

### 3.2 Extrair Queries para `models/usuario.py`

```python
# Funções: get_todos_usuarios, get_usuario_por_id, login_usuario, criar_usuario
```

### 3.3 Extrair Queries para `models/pedido.py`

```python
# Funções: criar_pedido, get_pedidos_usuario, get_todos_pedidos, 
#          atualizar_status_pedido, relatorio_vendas
```

---

## Passo 4: Migrar Controllers (Lógica)

### 4.1 Extrair Lógica para `controllers/produto_controller.py`

**ANTES (controllers.py linhas 24-126):**
```python
def criar_produto():
    try:
        dados = request.get_json()
        
        # Validação
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        if "nome" not in dados:
            return jsonify({"erro": "Nome é obrigatório"}), 400
        
        # Lógica de negócio
        if preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        
        categorias_validas = ["informatica", "moveis", "vestuario", ...]
        if categoria not in categorias_validas:
            return jsonify({"erro": "Categoria inválida"}), 400
        
        # Criar
        id = models.criar_produto(nome, descricao, preco, estoque, categoria)
        return jsonify({"dados": {"id": id}}), 201
```

**DEPOIS (controllers/produto_controller.py):**
```python
from models.produto import (
    get_todos_produtos, 
    get_produto_por_id,
    criar_produto as criar_produto_db,
    # ...
)

class ProdutoController:
    VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", 
                        "eletronicos", "livros"]
    
    @staticmethod
    def validar_criacao(dados):
        """Validar dados para criação de produto"""
        if not dados:
            raise ValueError("Dados inválidos")
        
        nome = dados.get("nome", "").strip()
        if not nome or len(nome) < 3:
            raise ValueError("Nome deve ter mínimo 3 caracteres")
        
        preco = dados.get("preco", 0)
        if preco < 0:
            raise ValueError("Preço não pode ser negativo")
        
        categoria = dados.get("categoria", "geral")
        if categoria not in ProdutoController.VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida. Válidas: {ProdutoController.VALID_CATEGORIES}")
        
        return {
            "nome": nome,
            "descricao": dados.get("descricao", ""),
            "preco": preco,
            "estoque": dados.get("estoque", 0),
            "categoria": categoria
        }
    
    @staticmethod
    def criar(dados):
        """Validar e criar produto"""
        validated = ProdutoController.validar_criacao(dados)
        produto_id = criar_produto_db(**validated)
        return {"id": produto_id}
    
    @staticmethod
    def buscar_por_id(id):
        """Buscar produto por ID"""
        produto = get_produto_por_id(id)
        if not produto:
            raise ValueError("Produto não encontrado")
        return produto
```

**Regra:** Controllers tem métodos estáticos com lógica, models tem apenas queries

---

## Passo 5: Migrar Routes (HTTP)

### 5.1 Criar `routes/produto_routes.py`

**ANTES (app.py linhas 11-16, controllers.py linhas 5-126):**
```python
@app.route('/produtos', 'listar_produtos', controllers.listar_produtos, ...)
@app.route('/produtos/<int:id>', 'buscar_produto', controllers.buscar_produto, ...)
@app.route('/produtos', 'criar_produto', controllers.criar_produto, ...)
```

**DEPOIS (routes/produto_routes.py):**
```python
from flask import Blueprint, request, jsonify
from controllers.produto_controller import ProdutoController
import logging

logger = logging.getLogger(__name__)
produto_bp = Blueprint('produtos', __name__)

@produto_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    try:
        produtos = ProdutoController.listar()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return jsonify({"erro": "Erro interno"}), 500

@produto_bp.route('/produtos', methods=['POST'])
def criar_produto():
    try:
        dados = request.get_json()
        produto = ProdutoController.criar(dados)
        logger.info(f"Produto criado: {produto['id']}")
        return jsonify({"dados": produto, "sucesso": True}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao criar produto: {str(e)}")
        return jsonify({"erro": "Erro interno"}), 500

@produto_bp.route('/produtos/<int:id>', methods=['GET'])
def buscar_produto(id):
    try:
        produto = ProdutoController.buscar_por_id(id)
        return jsonify({"dados": produto, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 404
```

**Regra:** Routes é só HTTP mapping, sem lógica de negócio

---

## Passo 6: Atualizar `app.py`

**ANTES:**
```python
import controllers
app.add_url_rule("/produtos", "listar_produtos", 
                 controllers.listar_produtos, methods=["GET"])
```

**DEPOIS:**
```python
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp

app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)
```

---

## Passo 7: Validação Pós-Refactoring

✅ **Checklist:**
- [ ] Nenhuma query em `routes/`
- [ ] Nenhuma query em `app.py`
- [ ] Nenhuma lógica de HTTP em `models/`
- [ ] Nenhuma lógica de negócio em `routes/`
- [ ] Todos os controllers têm validação
- [ ] Aplicação inicia sem errors
- [ ] Todos os endpoints funcionam
- [ ] Logs mascarados (sem PII)
- [ ] Estrutura MVC validada

**Comando:**
```bash
python3 -c "from app import app; print('✅ App inicializa sem erros')"
```

---

## Exemplo Completo: Fluxo POST /produtos

```
Request: POST /produtos
  { "nome": "Notebook", "preco": 5000, "categoria": "informatica" }

↓ routes/produto_routes.py (linha 20)
  @produto_bp.route('/produtos', methods=['POST'])
  def criar_produto():
    dados = request.get_json()

↓ controllers/produto_controller.py (linha 15)
  ProdutoController.criar(dados)
    - Validar dados (nome, preço, categoria)
    - Chamar models.criar_produto_db()

↓ models/produto.py (linha 45)
  criar_produto_db(nome, descricao, preco, estoque, categoria)
    - cursor.execute("INSERT INTO ...")
    - return produto_id

↓ Back to controller
  return {"id": 123}

↓ Back to route
  return jsonify({"dados": {"id": 123}}), 201

↓ Response: {"dados": {"id": 123}, "sucesso": true}
```

---

## Checklist v2.2

### Executar em Phase 3
- [ ] Passo 1: Analizar God Class
- [ ] Passo 2: Criar diretórios (models/, routes/, controllers/)
- [ ] Passo 3: Migrar queries para models/
- [ ] Passo 4: Migrar lógica para controllers/
- [ ] Passo 5: Migrar HTTP para routes/
- [ ] Passo 6: Atualizar app.py com blueprints
- [ ] Passo 7: Validar tudo funciona
- [ ] Passo 8: Remover arquivos antigos (models.py, controllers.py)
- [ ] Passo 9: Git commit

---

## Tempo Estimado

| Etapa | Tempo |
|-------|-------|
| Análise | 5 min |
| Criar estrutura | 2 min |
| Migrar models | 10 min |
| Migrar controllers | 10 min |
| Migrar routes | 10 min |
| Atualizar app.py | 5 min |
| Validação | 5 min |
| **TOTAL** | **~47 min** |

---

## v2.2 Status

🔴 Não implementado ainda (Phase 3 incompleta)  
📋 Este guia servirá como base para v2.2  
⏳ Próximo: Aplicar esse guide no code-smells-project

