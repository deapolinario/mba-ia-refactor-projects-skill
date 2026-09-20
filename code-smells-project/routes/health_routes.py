import logging
from flask import Blueprint, jsonify
from database import get_db

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]

        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": produtos,
                "usuarios": usuarios,
                "pedidos": pedidos
            },
            "versao": "1.0.0"
        }), 200
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({"status": "erro"}), 500
