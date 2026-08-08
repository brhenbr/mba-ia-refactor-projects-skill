import logging

from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from database import db
from exceptions import BusinessException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(BusinessException)
    def handle_business_exception(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"erro": err.messages, "sucesso": False}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        db.session.rollback()
        logger.warning("Violação de integridade: %s", err)
        return jsonify({"erro": "Conflito de dados", "sucesso": False}), 409

    @app.errorhandler(OperationalError)
    def handle_operational_error(err):
        db.session.rollback()
        logger.error("Erro operacional de banco de dados: %s", err)
        return jsonify({"erro": "Erro de banco de dados", "sucesso": False}), 503

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
