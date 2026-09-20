import logging
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from database import get_db
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp
from routes.health_routes import health_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
Config.validate()

CORS(app)

app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)
app.register_blueprint(health_bp)


def admin_required(f):
    """Guard mínimo para rotas administrativas (v2.2 - Broken Access Control fix)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        expected = Config.ADMIN_TOKEN
        if not expected or token != expected:
            return jsonify({"erro": "Não autorizado"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health"
        }
    })


@app.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
        logger.warning("Banco de dados resetado via /admin/reset-db")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao resetar banco: {str(e)}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

# v2.2: endpoint /admin/query REMOVIDO — executava SQL arbitrário vindo do
# cliente (Dangerous Admin Endpoint / CRITICAL). Nunca expor execução de SQL
# livre via API; usar ferramenta externa (sqlite3 CLI) para debug administrativo.

if __name__ == "__main__":
    get_db()
    logger.info("Servidor iniciado em http://localhost:5000")

    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
