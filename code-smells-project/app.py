import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import config_by_name
from database import db
from middleware.error_handler import register_error_handlers
from routes.admin_routes import admin_bp
from routes.health_routes import health_bp
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.relatorio_routes import relatorio_bp
from routes.usuario_routes import usuario_bp
from seed import seed_dados_iniciais


def create_app(env=None):
    env = env or os.getenv("FLASK_ENV", "development")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    config_class = config_by_name[env]
    if hasattr(config_class, "validate"):
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    JWTManager(app)
    CORS(app, origins=app.config["CORS_ORIGINS"] or [])

    register_error_handlers(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "2.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    with app.app_context():
        db.create_all()
        if env != "production":
            seed_dados_iniciais()

    return app


if __name__ == "__main__":
    app = create_app()
    logging.getLogger(__name__).info("Servidor iniciado em http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
