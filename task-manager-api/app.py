import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import config_by_name
from database import db, utc_now
from middleware.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app(env=None):
    env = env or os.getenv('FLASK_ENV', 'development')

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    config_class = config_by_name[env]
    if hasattr(config_class, 'validate'):
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    JWTManager(app)
    CORS(app, origins=app.config['CORS_ORIGINS'] or [])

    register_error_handlers(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'timestamp': str(utc_now())})

    @app.route('/')
    def index():
        return jsonify({'message': 'Task Manager API', 'version': '2.0'})

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    logging.getLogger(__name__).info('Servidor iniciado em http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
