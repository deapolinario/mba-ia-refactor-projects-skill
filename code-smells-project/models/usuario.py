from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash


def _row_to_dict(row):
    """Centraliza a serialização de usuário — nunca inclui a coluna senha."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"]
    }


def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    # Nunca selecionar a coluna "senha" quando o resultado vai para o cliente
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_usuario_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", [id])
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def login_usuario(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", [email])
    row = cursor.fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"]
        }
    return None


def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha, method='pbkdf2:sha256')
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [nome, email, senha_hash, tipo]
    )
    db.commit()
    return cursor.lastrowid
