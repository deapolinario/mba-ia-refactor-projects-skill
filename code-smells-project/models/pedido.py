from database import get_db
from models.produto import decrementar_estoque


def _agrupar_pedidos_com_itens(rows):
    """
    Recebe rows de um JOIN pedidos + itens_pedido + produtos e agrupa em
    dicts de pedido com lista de itens. Elimina N+1 (v2.1 tinha 1 query por
    pedido + 1 query por item) e a duplicação entre get_pedidos_usuario /
    get_todos_pedidos (v2.1 repetia essa lógica em 2 lugares).
    """
    pedidos_por_id = {}
    ordem = []
    for row in rows:
        pid = row["pedido_id"]
        if pid not in pedidos_por_id:
            pedidos_por_id[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": []
            }
            ordem.append(pid)
        if row["item_produto_id"] is not None:
            pedidos_por_id[pid]["itens"].append({
                "produto_id": row["item_produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return [pedidos_por_id[pid] for pid in ordem]


_JOIN_QUERY = """
    SELECT
        p.id AS pedido_id,
        p.usuario_id AS usuario_id,
        p.status AS status,
        p.total AS total,
        p.criado_em AS criado_em,
        ip.produto_id AS item_produto_id,
        ip.quantidade AS quantidade,
        ip.preco_unitario AS preco_unitario,
        prod.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos prod ON prod.id = ip.produto_id
"""


def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        _JOIN_QUERY + " WHERE p.usuario_id = ? ORDER BY p.id",
        [usuario_id]
    )
    return _agrupar_pedidos_com_itens(cursor.fetchall())


def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_JOIN_QUERY + " ORDER BY p.id")
    return _agrupar_pedidos_com_itens(cursor.fetchall())


def criar_pedido(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()

    total = 0
    produtos_cache = {}
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", [item["produto_id"]])
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        produtos_cache[item["produto_id"]] = produto
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        [usuario_id, total]
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        produto = produtos_cache[item["produto_id"]]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [pedido_id, item["produto_id"], item["quantidade"], produto["preco"]]
        )
        decrementar_estoque(item["produto_id"], item["quantidade"])

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        [novo_status, pedido_id]
    )
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
            SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
    """)
    row = cursor.fetchone()
    total_pedidos = row["total_pedidos"]
    faturamento = row["faturamento"]

    desconto = 0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": row["pendentes"] or 0,
        "pedidos_aprovados": row["aprovados"] or 0,
        "pedidos_cancelados": row["cancelados"] or 0,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
    }
